import aprslib
from aprslib.parsing import parse
import pubsub
import time
import sys
import json
import time
import logging
import random
import threading
import re
import os
import serial.tools.list_ports
import meshtastic.stream_interface
import meshtastic.serial_interface
from datetime import datetime
from meshtastic.util import message_to_json

from queue import Queue, Empty
from .__about__ import __version__
from ._aprs_client import APRSClient
from ._registry import CallSignRegistry

logger = logging.getLogger("aprstastic")

from aprslib.parsing import parse

APRS_SOFTWARE_ID = "APZMAG"  # Experimental Meshtastic-APRS Gateway
MQTT_TOPIC = "meshtastic.receive"
REGISTRATION_BEACON = "MESHID-01"
GATEWAY_BEACON_INTERVAL = 3600  # Station beacons once an hour


class Gateway(object):
    def __init__(self, config):
        self._config = config

        self._gateway_id = None
        self._gateway_call_sign = None

        self._interface = None
        self._mesh_rx_queue = Queue()

        self._aprs_client = None

        self._reply_to = {}
        self._filtered_call_signs = []
        self._beacon_registrations = False

        self._next_beacon_time = 0

        self._id_to_call_signs = CallSignRegistry(
            config.get("gateway", {}).get("data_dir")
        )

    def run(self):
        # Connect to the Meshtastic device
        device = (
            self._config.get("gateway", {})
            .get("meshtastic_interface", {})
            .get("device")
        )

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
        self._gateway_call_sign = (
            self._config.get("gateway", {}).get("call_sign", "").upper().strip()
        )
        self._filtered_call_signs.append(self._gateway_call_sign)

        # The registraion beacon
        self._beacon_registrations = self._config.get("gateway", {}).get(
            "beacon_registrations", True
        )
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
        aprsis_passcode = self._config.get("gateway", {}).get("aprsis_passcode")
        self._aprs_client = APRSClient(
            self._gateway_call_sign,
            aprsis_passcode,
            "g/" + "/".join(self._filtered_call_signs),
        )

        logger.debug("Pausing for 2 seconds...")
        time.sleep(2.0)
        logger.debug("Starting main loop.")

        gateway_beacon = self._config.get("gateway", {}).get("gateway_beacon", {})

        while True:
            # Beacon the gateway position
            now = time.time()
            if now > self._next_beacon_time and gateway_beacon.get("enabled"):
                # If the latitude and longitude are not set in the config, then read it from the radio
                gate_lat = gateway_beacon.get("latitude")
                gate_lon = gateway_beacon.get("longitude")
                if gate_lat is None or gate_lon is None:
                    gate_position = self._interface.getMyNodeInfo().get("position", {})
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

            # Read a meshastic packet
            mesh_packet = None
            try:
                mesh_packet = self._mesh_rx_queue.get(block=False)
            except Empty:
                pass

            if mesh_packet is not None:
                self._process_meshtastic_packet(mesh_packet)

            # Read an APRS packet
            aprs_packet = self._aprs_client.recv()
            if aprs_packet is not None:
                self._process_aprs_packet(aprs_packet)

            # Yield
            time.sleep(0.001)

    def _get_interface(
        self, device=None
    ) -> meshtastic.stream_interface.StreamInterface:
        if device is None:
            ports = list(serial.tools.list_ports.comports())
            if len(ports) == 1:
                device = ports[0].device
        if device is not None:
            dev = meshtastic.serial_interface.SerialInterface(device)
            logger.info(f"Connected to: {device}")
            return dev
        else:
            return None

    def _process_meshtastic_packet(self, packet):
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
                # It seems to send in the opposite order? LIFO?
                self._send_mesh_message(
                    fromId,
                    "Send and receive APRS messages by registering your call sign. HAM license required.\n\nReply with:\n!register [CALLSIGN]-[SSID]\nE.g.,\n!register N0CALL-1\n\nSee https://github.com/afourney/aprstastic for more.",
                )
                return

            if message_string.strip() == "!id" or message_string.strip() == "!version":
                # Let clients query the gateway call sign and version number
                self._send_mesh_message(
                    fromId,
                    f"Gateway call sign: {self._gateway_call_sign}, Version: {__version__}",
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
                    logger.info(
                        f"Observed registration beacon: {mesh_id}: {fromcall}",
                    )
                    self._id_to_call_signs.add_registration(mesh_id, fromcall, False)
                else:
                    logger.error(
                        f"Invalid registration beacon: {packet.get('raw')}",
                    )
                return

            # Ack all remaining messages (which aren't themselves acks, and aren't beacons)
            self._send_aprs_ack(tocall, fromcall, packet.get("msgNo", ""))

            # Message was sent to the gateway itself. Print it. Do nothing else.
            if tocall == self._gateway_call_sign:
                logger.info(
                    f"Received APRS message addressed to the gateway ({self._gateway_call_sign}): {packet['raw']}"
                )
                return

            # Figure out where the packet is going
            toId = None
            for k in self._id_to_call_signs:
                if tocall == self._id_to_call_signs[k].strip().upper():
                    toId = k
                    break
            if toId is None:
                loggin.error(f"Unkown recipient: {tocall}")
                return

            # Forward the message
            message = packet.get("message_text")
            if message is not None:
                self._reply_to[toId] = fromcall
                self._send_mesh_message(toId, fromcall + ": " + message)

    def _send_aprs_message(self, fromcall, tocall, message):
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
            + ":"
            + message.strip()
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
        aprs_lat = self._aprs_lat(lat)
        aprs_lon = self._aprs_lon(lon)

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
