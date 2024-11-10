import aprslib
from aprslib.parsing import parse
import pubsub
import time
import sys
import json
import time
import logging
import warnings
import random
import threading
import re
import os
import traceback
import meshtastic.stream_interface
import meshtastic.serial_interface
from datetime import datetime
from meshtastic.util import findPorts

from queue import Queue, Empty
from .__about__ import __version__
from ._aprs_client import APRSClient
from ._registry import CallSignRegistry

logger = logging.getLogger("aprstastic")

from aprslib.parsing import parse

MAX_APRS_TEXT_MESSAGE_LENGTH = 67
MAX_APRS_POSITION_MESSAGE_LENGTH = 43

APRS_SOFTWARE_ID = "APZMAG"  # Experimental Meshtastic-APRS Gateway
MQTT_TOPIC = "meshtastic.receive"
REGISTRATION_BEACON = "MESHID-01"
GATEWAY_BEACON_INTERVAL = 3600  # Station beacons once an hour

SERIAL_WATCHDOG_INTERVAL = 60  # Check the serial state every minute
MESHTASTIC_WATCHDOG_INTERVAL = (
    60 * 15
)  # After how long should we become worried the Meshtastic device is quiet?

# Beacons that mean unregister
APRS_TOMBSTONE = "N0NE-01"
MESH_TOMBSTONE = "!00000000"

# For uptime
TIME_DURATION_UNITS = (
    ("w", 60 * 60 * 24 * 7),
    ("d", 60 * 60 * 24),
    ("h", 60 * 60),
    ("m", 60),
    ("s", 1),
)


class Gateway(object):
    def __init__(self, config):
        self._config = config
        self._start_time = None

        self._gateway_id = None
        self._gateway_call_sign = None

        self._interface = None
        self._mesh_rx_queue = Queue()

        self._aprs_client = None
        self._max_aprs_message_length = config.get("max_aprs_message_length")
        if self._max_aprs_message_length is None:
            self._max_aprs_message_length = MAX_APRS_TEXT_MESSAGE_LENGTH

        self._reply_to = {}
        self._filtered_call_signs = []
        self._beacon_registrations = False

        self._next_beacon_time = 0
        self._next_serial_check_time = 0
        self._last_meshtastic_packet_time = 0

        self._id_to_call_signs = CallSignRegistry(config.get("data_dir"))

    def run(self):
        # For measuring uptime
        self._start_time = time.time()

        # Connect to the Meshtastic device
        device = self._config.get("meshtastic_interface", {}).get("device")

        self._interface = self._get_interface(device)
        if self._interface is None:
            raise ValueError("No meshtastic device detected or specified.")

        def on_recv(packet):
            self._mesh_rx_queue.put(packet)

        pubsub.pub.subscribe(on_recv, MQTT_TOPIC)
        node_info = self._interface.getMyNodeInfo()
        self._gateway_id = node_info.get("user", {}).get("id")
        logger.debug(f"Gateway device id: {self._gateway_id}")

        # Create an initial list of known call signs based on the device node database

        # Myself
        self._gateway_call_sign = self._config.get("call_sign", "").upper().strip()
        self._filtered_call_signs.append(self._gateway_call_sign)

        # The registraion beacon
        self._beacon_registrations = self._config.get("beacon_registrations", True)
        if self._beacon_registrations:
            self._filtered_call_signs.append(REGISTRATION_BEACON)

        # Recently seen nodes
        for node in self._interface.nodesByNum.values():
            presumptive_id = f"!{node['num']:08x}"

            if presumptive_id not in self._id_to_call_signs:
                continue

            # Heard more than a day ago
            last_heard = node.get("lastHeard")
            if last_heard is None or last_heard + 3600 * 24 < time.time():
                continue

            self._filtered_call_signs.append(self._id_to_call_signs[presumptive_id])

        # Connect to APRS IS
        aprsis_passcode = self._config.get("aprsis_passcode")
        self._aprs_client = APRSClient(
            self._gateway_call_sign,
            aprsis_passcode,
            "g/" + "/".join(self._filtered_call_signs),
        )

        logger.debug("Pausing for 2 seconds...")
        time.sleep(2.0)
        logger.debug("Starting main loop.")

        gateway_beacon = self._config.get("gateway_beacon", {})

        self._last_meshtastic_packet_time = self._start_time

        while True:
            # There are four independent steps performed by this loop: servicing watchdogs,
            # beaconing, reading from Meshtastic, and reading from APRS.
            # Make sure that errors in one don't stop the others.
            now = time.time()

            # 1. Service the watchdogs
            ############################
            reconnect = False

            # Periodically check on the state of the device serial connection
            if now > self._next_serial_check_time:
                self._next_serial_check_time = now + SERIAL_WATCHDOG_INTERVAL
                if self._interface.stream is None or not self._interface.stream.is_open:
                    logger.warn("Serial connection is not open.")
                    reconnect = True

            # Check if the Meshtastic device has gone silent a while
            if (
                reconnect == False
                and now - self._last_meshtastic_packet_time
                > MESHTASTIC_WATCHDOG_INTERVAL
            ):
                self._last_meshtastic_packet_time = now
                logger.warn("No message from Meshtastic device for 15 minutes.")
                reconnect = True
                # This might be a frozen device. It may not be recoverable.

            # Reconnect if needed
            if reconnect:
                logger.warn("Attempting to reconnect in 30 seconds.")
                time.sleep(30)
                try:
                    if pubsub.pub.isSubscribed(on_recv, MQTT_TOPIC):
                        pubsub.pub.unsubscribe(on_recv, MQTT_TOPIC)
                    self._interface = self._get_interface(device)
                    if self._interface is not None:
                        pubsub.pub.subscribe(on_recv, MQTT_TOPIC)
                except Exception as e:
                    logger.error(traceback.format_exc())

            # 2. Beacon the gateway position
            ################################
            try:
                if now > self._next_beacon_time and gateway_beacon.get("enabled"):
                    # If the latitude and longitude are not set in the config, then read it from the radio
                    gate_lat = gateway_beacon.get("latitude")
                    gate_lon = gateway_beacon.get("longitude")
                    if gate_lat is None or gate_lon is None:
                        gate_position = self._interface.getMyNodeInfo().get(
                            "position", {}
                        )
                        gate_lat = gate_position.get("latitude")
                        gate_lon = gate_position.get("longitude")

                    # If we still don't have a position, check again in one minute
                    if gate_lat is None or gate_lon is None:
                        self._next_beacon_time = now + 60
                    else:
                        self._send_aprs_gateway_beacon(
                            gate_lat,
                            gate_lon,
                            gateway_beacon.get("icon", "M&"),
                            "aprstastic: " + self._gateway_id,
                        )
                        self._next_beacon_time = now + GATEWAY_BEACON_INTERVAL
            except Exception as e:
                logger.error(traceback.format_exc())

            # 3. Read a Meshastic packet
            ############################
            try:
                mesh_packet = None
                try:
                    mesh_packet = self._mesh_rx_queue.get(block=False)
                except Empty:
                    pass

                if mesh_packet is not None:
                    self._process_meshtastic_packet(mesh_packet)
            except Exception as e:
                logger.error(traceback.format_exc())

            # 4. Read an APRS packet
            ########################
            try:
                aprs_packet = self._aprs_client.recv()
                if aprs_packet is not None:
                    self._process_aprs_packet(aprs_packet)
            except Exception as e:
                logger.error(traceback.format_exc())

            # Yield
            time.sleep(0.001)

    def _get_interface(
        self, device=None
    ) -> meshtastic.stream_interface.StreamInterface:
        if device is None:
            ports = meshtastic.util.findPorts(True)
            if len(ports) == 1:
                device = ports[0]
            else:
                logger.error(
                    "Please specify the correct serial port in 'aprstastic.yaml'. "
                    f"Possible values include: {ports}"
                )
                return None
        if device is not None:
            dev = meshtastic.serial_interface.SerialInterface(device)
            logger.info(f"Connected to: {device}")
            return dev
        else:
            return None

    def _process_meshtastic_packet(self, packet):
        self._last_meshtastic_packet_time = time.time()

        fromId = packet.get("fromId", None)
        toId = packet.get("toId", None)
        portnum = packet.get("decoded", {}).get("portnum")

        # Don't bother logging my telemetry
        if portnum != "TELEMETRY_APP" or fromId != self._gateway_id:
            logger.info(f"{fromId} -> {toId}: {portnum}")

        # Record that we have spotted the ID
        should_announce = self._spotted(fromId)

        if portnum == "POSITION_APP":
            if fromId not in self._id_to_call_signs:
                return

            position = packet.get("decoded", {}).get("position")
            self._send_aprs_position(
                self._id_to_call_signs[fromId],
                position.get("latitude"),
                position.get("longitude"),
                position.get("time"),
                "aprstastic: " + fromId,
            )

        if portnum == "TEXT_MESSAGE_APP":
            message_bytes = packet["decoded"]["payload"]
            message_string = message_bytes.decode("utf-8")

            if toId == "^all" and message_string.lower().strip().startswith("aprs?"):
                self._send_mesh_message(
                    fromId,
                    "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.",
                )
                return

            if toId != self._gateway_id:
                # Not for me
                return

            if message_string.strip() == "?":
                # Different call signs for registered and non-registered devices
                if fromId not in self._id_to_call_signs:
                    self._send_mesh_message(
                        fromId,
                        "Send and receive APRS messages by registering your call sign. HAM license required.\n\nReply with:\n!register [CALLSIGN]-[SSID]\nE.g.,\n!register N0CALL-1\n\nSee https://github.com/afourney/aprstastic for more.",
                    )
                    return
                else:
                    self._send_mesh_message(
                        fromId,
                        "Send APRS messages by replying here, and prefixing your message with the dest callsign. E.g., 'WLNK-1: hello'\n\nSee https://github.com/afourney/aprstastic for more.",
                    )
                    return

            if message_string.strip() == "!id" or message_string.strip() == "!version":
                # Let clients query the gateway call sign and version number
                self._send_mesh_message(
                    fromId,
                    f"Gateway call sign: {self._gateway_call_sign}, Uptime: {self._uptime()}, Version: {__version__}",
                )
                return

            if message_string.lower().strip().startswith("!register"):
                # Allow operatores to join
                m = re.search(
                    r"^!register:?\s+([a-z0-9]{4,7}\-[0-9]{1,2})$",
                    message_string.lower().strip(),
                )
                if m:
                    call_sign = m.group(1).upper()
                    if fromId in self._id_to_call_signs:
                        # Update
                        self._id_to_call_signs.add_registration(fromId, call_sign, True)
                        self._send_mesh_message(fromId, "Registration updated.")
                    else:
                        # New
                        self._id_to_call_signs.add_registration(fromId, call_sign, True)
                        self._spotted(fromId)
                        self._send_mesh_message(
                            fromId,
                            "Registered. Send APRS messages by replying here, and prefixing your message with the dest callsign. E.g., 'WLNK-1: hello' ",
                        )
                    self._spotted(fromId)  # Run this again to update subscriptions

                    # Beacon the registration to APRS-IS to facilitate building a shared roaming mapping
                    # which will be queried in future updates to aprstastic.
                    if self._beacon_registrations:
                        logger.info(
                            f"Beaconing registration {call_sign} <-> {fromId}, to {REGISTRATION_BEACON}"
                        )
                        self._send_aprs_message(call_sign, REGISTRATION_BEACON, fromId)
                else:
                    self._send_mesh_message(
                        fromId,
                        "Invalid call sign + ssid.\nSYNTAX: !register [CALLSIGN]-[SSID]\nE.g.,\n!register N0CALL-1",
                    )
                return

            if message_string.lower().strip().startswith("!unregister"):
                if fromId not in self._id_to_call_signs:
                    self._send_mesh_message(
                        fromId, "Device is not registered. Nothing to do."
                    )
                    return
                call_sign = self._id_to_call_signs[fromId]
                self._id_to_call_signs.add_registration(fromId, None, True)
                self._id_to_call_signs.add_registration(None, call_sign, True)

                if self._beacon_registrations:
                    logger.info(
                        f"Beaconing unregistration {APRS_TOMBSTONE} <-> {fromId}, to {REGISTRATION_BEACON}"
                    )
                    self._send_aprs_message(APRS_TOMBSTONE, REGISTRATION_BEACON, fromId)
                    logger.info(
                        f"Beaconing unregistration {call_sign} <-> {MESH_TOMBSTONE}, to {REGISTRATION_BEACON}"
                    )
                    self._send_aprs_message(
                        call_sign, REGISTRATION_BEACON, MESH_TOMBSTONE
                    )

                self._filtered_call_signs.remove(call_sign)
                self._aprs_client.set_filter("g/" + "/".join(self._filtered_call_signs))
                self._send_mesh_message(fromId, "Device unregistered.")
                return

            if fromId not in self._id_to_call_signs:
                self._send_mesh_message(
                    fromId,
                    "Unknown device. HAM license required!\nRegister by replying with:\n!register [CALLSIGN]-[SSID]\nE.g.,\n!register N0CALL-1",
                )
                return

            m = re.search(r"^([A-Za-z0-9]+(\-[A-Za-z0-9]+)?):(.*)$", message_string)
            if m:
                tocall = m.group(1)
                self._reply_to[fromId] = tocall
                message = m.group(3).strip()
                self._send_aprs_message(self._id_to_call_signs[fromId], tocall, message)
                return
            elif fromId in self._reply_to:
                self._send_aprs_message(
                    self._id_to_call_signs[fromId],
                    self._reply_to[fromId],
                    message_string,
                )
                return
            else:
                self._send_mesh_message(
                    fromId,
                    "Please prefix your message with the dest callsign. E.g., 'WLNK-1: hello'",
                )
                return

        # At this point the message was not handled yet. Announce yourself
        if should_announce:
            self._send_mesh_message(
                fromId,
                "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.",
            )

    def _process_aprs_packet(self, packet):
        if packet.get("format") == "message":
            fromcall = packet.get("from", "N0CALL").strip().upper()
            tocall = packet.get("addresse", "").strip().upper()

            # Is this an ack?
            if packet.get("response") == "ack":
                logger.debug(
                    f"Received ACK to {tocall}'s message #" + packet.get("msgNo", "")
                )
                return

            # Is this a registration beacon?
            if tocall == REGISTRATION_BEACON:
                mesh_id = packet.get("message_text", "").lower().strip()
                if re.search(r"^![a-f0-9]{8}$", mesh_id):
                    if mesh_id == MESH_TOMBSTONE:
                        mesh_id = None
                    if fromcall == APRS_TOMBSTONE:
                        fromcall = None

                    logger.info(
                        f"Observed registration beacon: {mesh_id}: {fromcall}",
                    )
                    self._id_to_call_signs.add_registration(mesh_id, fromcall, False)
                else:
                    # Not necessarily and error. Could be from a future version
                    logger.debug(
                        f"Unknown registration beacon: {packet.get('raw')}",
                    )
                return

            # Ack all remaining messages (which aren't themselves acks, and aren't beacons)
            self._send_aprs_ack(tocall, fromcall, packet.get("msgNo", ""))

            # Message was sent to the gateway itself. Respond with station information.
            if tocall == self._gateway_call_sign:
                self._send_aprs_message(
                    tocall,
                    fromcall,
                    f"Gateway ID: {self._gateway_id}, Uptime: {self._uptime()}, Version: {__version__}",
                )
                return

            # Figure out where the packet is going
            toId = None
            for k in self._id_to_call_signs:
                if tocall == self._id_to_call_signs[k].strip().upper():
                    toId = k
                    break
            if toId is None:
                logger.error(f"Unkown recipient: {tocall}")
                return

            # Forward the message
            message = packet.get("message_text")
            if message is not None:
                self._reply_to[toId] = fromcall
                self._send_mesh_message(toId, fromcall + ": " + message)

    def _send_aprs_message(self, fromcall, tocall, message):
        message_chunks = self._chunk_message(message, self._max_aprs_message_length)

        while len(tocall) < 9:
            tocall += " "

        for chunk in message_chunks:
            packet = (
                fromcall
                + ">"
                + APRS_SOFTWARE_ID
                + ",WIDE1-1,qAR,"
                + self._gateway_call_sign
                + "::"
                + tocall
                + ":"
                + chunk.strip()
                + "{"
                + str(random.randint(0, 999))
            )
            logger.debug("Sending to APRS: " + packet)
            self._aprs_client.send(packet)

    def _send_aprs_ack(self, fromcall, tocall, messageId):
        while len(tocall) < 9:
            tocall += " "
        packet = (
            fromcall
            + ">"
            + APRS_SOFTWARE_ID
            + ",WIDE1-1,qAR,"
            + self._gateway_call_sign
            + "::"
            + tocall
            + ":ack"
            + messageId
        )
        logger.debug("Sending to APRS: " + packet)
        self._aprs_client.send(packet)

    def _aprs_lat(self, lat):
        aprs_lat_ns = "N" if lat >= 0 else "S"
        lat = abs(lat)
        aprs_lat_deg = int(lat)
        aprs_lat_min = float((lat - aprs_lat_deg) * 60)
        return f"%02d%05.2f%s" % (aprs_lat_deg, aprs_lat_min, aprs_lat_ns)

    def _aprs_lon(self, lon):
        aprs_lon_ew = "E" if lon >= 0 else "W"
        lon = abs(lon)
        aprs_lon_deg = abs(int(lon))
        aprs_lon_min = float((lon - aprs_lon_deg) * 60)
        return f"%03d%05.2f%s" % (aprs_lon_deg, aprs_lon_min, aprs_lon_ew)

    def _send_aprs_position(self, fromcall, lat, lon, t, message):
        message = self._truncate_message(message, MAX_APRS_POSITION_MESSAGE_LENGTH)

        aprs_lat = self._aprs_lat(lat)
        aprs_lon = self._aprs_lon(lon)

        aprs_msg = None
        if t is None:
            # No timestamp
            aprs_msg = "=" + aprs_lat + "/" + aprs_lon + ">" + message
        else:
            aprs_ts = datetime.utcfromtimestamp(t).strftime("%d%H%M")
            if len(aprs_ts) == 5:
                aprs_ts = "0" + aprs_ts + "z"
            else:
                aprs_ts = aprs_ts + "z"
            aprs_msg = "@" + aprs_ts + aprs_lat + "/" + aprs_lon + ">" + message

        packet = (
            fromcall
            + ">"
            + APRS_SOFTWARE_ID
            + ",WIDE1-1,qAR,"
            + self._gateway_call_sign
            + ":"
            + aprs_msg
        )
        logger.debug(f"Sending to APRS: {packet}")
        self._aprs_client.send(packet)

    def _send_aprs_gateway_beacon(self, lat, lon, icon, message):
        aprs_lat = self._aprs_lat(lat)
        aprs_lon = self._aprs_lon(lon)
        aprs_msg = "!" + aprs_lat + icon[0] + aprs_lon + icon[1] + message
        packet = (
            self._gateway_call_sign + ">" + APRS_SOFTWARE_ID + ",TCPIP*:" + aprs_msg
        )
        logger.debug(f"Beaconing to APRS: {packet}")
        self._aprs_client.send(packet)

    def _send_mesh_message(self, destid, message):
        logger.info(f"Sending to '{destid}': {message}")
        self._interface.sendText(
            text=message, destinationId=destid, wantAck=True, wantResponse=False
        )

    def _spotted(self, node_id):
        """
        Checks if the node is registered, and newly spotted -- in which
        case we need to update the APRS filters, and also greet the user.
        In this case, it returns true. Otherwise, false.
        """

        # We spotted them, but they aren't registered
        if node_id not in self._id_to_call_signs:
            return False

        call_sign = self._id_to_call_signs[node_id]

        if call_sign in self._filtered_call_signs:
            return False

        # Ok it's new, update the filters
        self._filtered_call_signs.append(call_sign)
        self._aprs_client.set_filter("g/" + "/".join(self._filtered_call_signs))
        return True

    def _uptime(self):
        if self._start_time is None:
            return "None"

        seconds = int(time.time() - self._start_time)

        if seconds < 1:
            return "0s"

        parts = []
        for unit, div in TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)
            if amount > 0:
                parts.append("{}{}".format(amount, unit))
            if len(parts) >= 3:  # Don't get overly precise
                break

        return ", ".join(parts)

    def _truncate_message(self, message, max_bytes):
        m_len = len(message.encode("utf-8"))

        # Nothing to do
        if m_len <= max_bytes:
            return message

        # Warn about the message being too long
        warnings.warn(
            f"Message of length {m_len} bytes exceeds the protocol maximum of {max_bytes} bytes."
        )

        # Trim first by characters to get close, then remove one character at a time
        strlen = max_bytes
        message = message[0:strlen]
        while len(message.encode("utf-8")) > max_bytes:
            # Chop a character
            strlen -= 1
            message = message[0:strlen]
        return message

    def _chunk_message(self, message, max_bytes):
        chunks = list()

        # We want to break on spaces
        tokens = re.split(r"(\s+)", message)
        if len(tokens) == 0:
            return chunks

        buffer = tokens.pop(0)  # Always include at least one token
        while len(tokens) > 0:
            token = tokens.pop(0)
            if len((buffer + token).encode("utf-8")) > max_bytes:
                chunks.append(buffer)
                buffer = token
            else:
                buffer += token
        if len(buffer) > 0:
            chunks.append(buffer)
            buffer = ""

        return chunks
