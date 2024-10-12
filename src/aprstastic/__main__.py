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
import yaml
import serial.tools.list_ports
import meshtastic.stream_interface
import meshtastic.serial_interface
from meshtastic.util import message_to_json

logging.basicConfig(level=logging.INFO) # level=10

MQTT_TOPIC = "meshtastic.receive"

# Globals -- ick
my_id = None
inerface = None
aprs = None
id_to_call_signs = {}
reply_to = {}
spotted = {}

def onReceive(packet, interface):
    fromId = packet.get("fromId", None)
    toId = packet.get("toId", None)
    portnum = packet.get("decoded", {}).get("portnum")
    logging.debug(f"{fromId} -> {toId}: {portnum}")

    if portnum == "TEXT_MESSAGE_APP":
        if "decoded" not in packet:
            # Can't read it
            return

        message_bytes = packet['decoded']['payload']
        message_string = message_bytes.decode('utf-8')

        if toId == "^all" and message_string.lower().strip().startswith("aprs?"):
            send_mesh_message(fromId, "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.")
            spotted[fromId] = True
            return

        if toId != my_id:
            # Not for me
            return

        spotted[fromId] = True

        if message_string.strip() == "?":
            # TODO
            send_mesh_message(fromId, "See https://github.com/afourney/aprstastic for more.")
            return

        if fromId not in id_to_call_signs:
            send_mesh_message(fromId, "Unknown device. Please register your call sign with the gateway owner.")
            return

        m = re.search(r"^([A-Za-z0-9]+(\-[A-Za-z0-9]+)?):(.*)$", message_string)
        if m:
            tocall = m.group(1)
            reply_to[fromId] = tocall
            message = m.group(3).strip()
            send_aprs_message(id_to_call_signs[fromId], tocall, message)
            return
        elif fromId in reply_to:
            send_aprs_message(id_to_call_signs[fromId], reply_to[fromId], message_string)
            return
        else:
            send_mesh_message(fromId, "Please prefix your message with a the dest callsign. E.g., 'WNLK-1: hello'")
            return

    # At this point the message was not handled yet. Announce yourself
    if fromId in id_to_call_signs and fromId not in spotted:
        send_mesh_message(fromId, "APRS-tastic Gateway available here. Welcome. Reply '?' for more info.")
        spotted[fromId] = True

def callback(packet):
    if packet.get("format") == "message":
        fromcall = packet.get("from", "N0CALL")
        toId = None
        for k in id_to_call_signs:
            if packet.get("addresse", "").upper() == id_to_call_signs[k].upper():
                toId = k
                break
        if toId is None:
            print(f"Unkown recipient: " + packet.get("addresse", ""))
            return
        message = packet.get("message_text")
        if message is not None:
            reply_to[toId] = fromcall
            send_mesh_message(toId, fromcall + ": " + message)
            send_aprs_ack(packet.get("addresse", ""), fromcall, packet.get("msgNo", "")) 


def get_interface(device = None) -> meshtastic.stream_interface.StreamInterface:
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


def send_aprs_message(fromcall, tocall, message):
    while len(tocall) < 9:
        tocall += " "
    aprs.sendall(fromcall + ">APRS,WIDE1-1,qAR,TESTCAL::" + tocall + ":" + message.strip() + "{" + str(random.randint(0,999)))


def send_aprs_ack(fromcall, tocall, messageId):
    while len(tocall) < 9:
        tocall += " "
    aprs.sendall(fromcall + ">APRS,WIDE1-1,qAR,TESTCAL::" + tocall + ":ack" + messageId)


def send_mesh_message(destid, message):
    logging.info(f"Sending to '{destid}': {message}")
    interface.sendText(
        text=message,
        destinationId=destid,
        wantAck=True,
        wantResponse=False
    )


def rx_loop():
    while True:
        aprs.consumer(callback, raw=False, blocking=True)
        time.sleep(0) # yield


def main():
    global my_id
    global interface
    global aprs
    global id_to_call_signs

    # Function to read a YAML file and return its content
    with open("config.yml", 'r') as file:
        config = yaml.safe_load(file)

    id_to_call_signs = config.get("licensed_operators")
    gateway_call_sign = config.get("gateway", {}).get("call_sign")
    aprsis_passcode = config.get("gateway", {}).get("aprsis_passcode")
    device = config.get("gateway", {}).get("meshtastic_interface", {}).get("device")

    interface = get_interface(device)
    if interface is None:
        sys.exit("No meshtastic device detected or specified.")

    pubsub.pub.subscribe(onReceive, MQTT_TOPIC)
    node_info = interface.getMyNodeInfo()
    my_id = node_info.get("user", {}).get("id")
    logging.debug(f"Gateway device id: {my_id}")

    # a valid passcode for the callsign is required in order to send
    aprs = aprslib.IS(gateway_call_sign, passwd=aprsis_passcode, port=14580)
    aprs.set_filter("g/" + "/".join(id_to_call_signs.values()))
    aprs.connect()
    rx_thread = threading.Thread(target=rx_loop)
    rx_thread.start()

    while True:
        time.sleep(1)

main()

