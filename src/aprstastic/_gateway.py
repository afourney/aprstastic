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
import serial.tools.list_ports
import meshtastic.stream_interface
import meshtastic.serial_interface
from datetime import datetime
from meshtastic.util import message_to_json

from queue import Queue, Empty
from ._aprs_client import APRSClient

MQTT_TOPIC = "meshtastic.receive"

class Gateway(object):

    def __init__(self, config):
        self._config = config
        self._id_to_call_signs = config.get("licensed_operators")

        self._gateway_id = None
        self._gateway_call_sign = None

        self._interface = None
        self._mesh_rx_queue = Queue()

        self._aprs_client = None

        self._reply_to = {}
        self._spotted = {}
       

    def run(self):
        
        # Connect to the Meshtastic device
        device = self._config.get("gateway", {}).get("meshtastic_interface", {}).get("device")
        self._interface = self._get_interface(device)
        if self._interface is None:
            raise ValueError("No meshtastic device detected or specified.")
        def on_recv(packet):
            self._mesh_rx_queue.put(packet)
        pubsub.pub.subscribe(on_recv, MQTT_TOPIC)
        node_info = self._interface.getMyNodeInfo()
        self._gateway_id = node_info.get("user", {}).get("id")
        logging.info(f"Gateway device id: {self._gateway_id}")

        self._gateway_call_sign = self._config.get("gateway", {}).get("call_sign", "").upper().strip()
        aprsis_passcode = self._config.get("gateway", {}).get("aprsis_passcode")

        filters = [ c for c in self._id_to_call_signs.values() ]
        filters.append(self._gateway_call_sign) # Add ourself back in
        filters = "g/" + "/".join(filters)

        self._aprs_client = APRSClient(self._gateway_call_sign, aprsis_passcode, filters)

        while True:

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


    def _get_interface(self, device = None) -> meshtastic.stream_interface.StreamInterface:
        if device is None:
            ports = list(serial.tools.list_ports.comports())
            if len(ports) == 1:
                device = ports[0].device
        if device is not None:
            dev = meshtastic.serial_interface.SerialInterface(device)
            logging.info(f"Connected to: {device}")
            return dev
        else:
            return None


    def _process_meshtastic_packet(self, packet):
        fromId = packet.get("fromId", None)
        toId = packet.get("toId", None)
        portnum = packet.get("decoded", {}).get("portnum")
        logging.info(f"{fromId} -> {toId}: {portnum}")

        if portnum == "POSITION_APP":

            if fromId not in self._id_to_call_signs:
                return

            position = packet.get("decoded", {}).get("position")
            self._send_aprs_position(
                self._id_to_call_signs[fromId],
                position.get("latitude"),
                position.get("longitude"),
                position.get("time"),
                "aprstastic: " + fromId
            )

        if portnum == "TEXT_MESSAGE_APP":
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')

            if toId == "^all" and message_string.lower().strip().startswith("aprs?"):
                self._send_mesh_message(fromId, "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.")
                self._spotted[fromId] = True
                return

            if toId != self._gateway_id:
                # Not for me
                return

            self._spotted[fromId] = True

            if message_string.strip() == "?":
                # TODO
                self._send_mesh_message(fromId, "See https://github.com/afourney/aprstastic for more.")
                return

            if fromId not in self._id_to_call_signs:
                self._send_mesh_message(fromId, "Unknown device. Please register your call sign with the gateway owner.")
                return

            m = re.search(r"^([A-Za-z0-9]+(\-[A-Za-z0-9]+)?):(.*)$", message_string)
            if m:
                tocall = m.group(1)
                self._reply_to[fromId] = tocall
                message = m.group(3).strip()
                self._send_aprs_message(self._id_to_call_signs[fromId], tocall, message)
                return
            elif fromId in self._reply_to:
                self._send_aprs_message(self._id_to_call_signs[fromId], self._reply_to[fromId], message_string)
                return
            else:
                self._send_mesh_message(fromId, "Please prefix your message with a the dest callsign. E.g., 'WLNK-1: hello'")
                return

        # At this point the message was not handled yet. Announce yourself
        if fromId in self._id_to_call_signs and fromId not in self._spotted:
            self._send_mesh_message(fromId, "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.")
            self._spotted[fromId] = True

    def _process_aprs_packet(self, packet):
        if packet.get("format") == "message":
            fromcall = packet.get("from", "N0CALL").strip().upper()
            tocall = packet.get("addresse", "").strip().upper()

            # Is this an ack? 
            if packet.get("response") == "ack":
                logging.info(f"Received ACK to {tocall}'s message #" + packet.get("msgNo", "")) 
                return

            # Ack all messages
            self._send_aprs_ack(tocall, fromcall, packet.get("msgNo", "")) 

            # Message was sent to the gateway itself. Print it. Do nothing else.
            if tocall == self._gateway_call_sign:
                logging.info(f"Received APRS message addressed to the gateway ({self._gateway_call_sign}): {packet['raw']}")
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
        packet = fromcall + ">APRS,WIDE1-1,qAR," + self._gateway_call_sign + "::" + tocall + ":" + message.strip() + "{" + str(random.randint(0,999))
        logging.info("Sending APRS: " + packet)
        self._aprs_client.send(packet)


    def _send_aprs_ack(self, fromcall, tocall, messageId):
        while len(tocall) < 9:
            tocall += " "
        self._aprs_client.send(fromcall + ">APRS,WIDE1-1,qAR," + self._gateway_call_sign + "::" + tocall + ":ack" + messageId)

    def _send_aprs_position(self, fromcall, lat, lon, t, message):
        aprs_lat_ns   = "N" if lat >= 0 else "S"
        lat = abs(lat)
        aprs_lat_deg  = int(lat)
        aprs_lat_min  = float((lat - aprs_lat_deg) * 60)
        aprs_lat = f"%02d%02.2f%s" % (aprs_lat_deg, aprs_lat_min, aprs_lat_ns)

        aprs_lon_ns   = "E" if lon >= 0 else "W"
        lon = abs(lon)
        aprs_lon_deg  = abs(int(lon))
        aprs_lon_min  = float((lon - aprs_lon_deg) * 60)
        aprs_lon = f"%03d%05.2f%s" % (aprs_lon_deg, aprs_lon_min, aprs_lon_ns)

        aprs_ts = datetime.utcfromtimestamp(t).strftime('%d%H%M')
        if len(aprs_ts) == 5:
            aprs_ts = "0" + aprs_ts + "z"
        else:
            aprs_ts = aprs_ts + "z"

        aprs_msg = "@" + aprs_ts + aprs_lat + "/" + aprs_lon + ">" + message
        logging.info(f"Sending to APRS: {aprs_msg}")
        self._aprs_client.send(fromcall + ">APRS,WIDE1-1,qAR," + self._gateway_call_sign + ":"+aprs_msg)


    def _send_mesh_message(self, destid, message):
        logging.info(f"Sending to '{destid}': {message}")
        self._interface.sendText(
            text=message,
            destinationId=destid,
            wantAck=True,
            wantResponse=False
        )
