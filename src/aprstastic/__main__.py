import logging
import yaml
import os
import sys
from ._gateway import Gateway

logging.basicConfig(level=logging.INFO)

# Try to find the config file
config_path = None
if os.path.isfile("config.yml"):
    config_path = "config.yml"
else:
    path = os.path.expanduser("~")
    path = os.path.join(path, ".config", "aprstastic", "config.yml")
    if os.path.isfile(path):
        config_path = path
    else:
        print(
            "Config file not found. Save the following to 'config.yml', and edit appropriately:\n"
            "=================================================================================="
        )
        print(
            """
gateway:
  call_sign: N0CALL         # Radio call sign of the gateway itself (analogy, iGate's call sign)
  aprsis_passcode: 12345    # APRS-IS passcode. Search Google for how to get this
  meshtastic_interface:     # Only serial devices are supported right now
    type: serial
    #device: /dev/ttyACM0   # Name of the serial device if more than one

licensed_operators: # Mapping of Meshtastic device IDs to call signs
  "!12345678": NOCALL-1
#  "!87654321": NOCALL-2
#  "!12121212": NOCALL-3
"""
        )
        sys.exit(1)

with open(config_path, "r") as file:
    config = yaml.safe_load(file)

gateway = Gateway(config)
gateway.run()
