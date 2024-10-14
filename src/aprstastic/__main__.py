import logging
import yaml
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from ._gateway import Gateway

# Set up logging
################
logger = logging.getLogger("aprstastic")
logging.root.setLevel(logging.DEBUG)


class LocalDebugFilter(logging.Filter):
    """
    Only show debug messages if they are from arpstastic
    """

    def filter(self, record):
        if record.name == "aprstastic":
            return True
        else:
            return record.levelno > logging.DEBUG


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
stream_handler.addFilter(LocalDebugFilter())
logging.root.addHandler(stream_handler)


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
  call_sign: N0CALL            # Update this! Radio call sign of the gateway itself (analogy, iGate's call sign)
  aprsis_passcode: 12345       # Update this! APRS-IS passcode. Search Google for how to get this
  meshtastic_interface:        # Only serial devices are supported right now
    type: serial
    #device: /dev/ttyACM0      # Update this if needed. Name of the serial device if more than one
  #logdir: /var/log/aprstastic # Where should logs be stored?
  beacon_registrations: true   # Beacon new registrations to APRS-IS to facilitate discovery 

licensed_operators: # Mapping of Meshtastic device IDs to call signs
  "!12345678": NOCALL-1
#  "!87654321": NOCALL-2
#  "!12121212": NOCALL-3
"""
        )
        sys.exit(1)

logger.debug(f"Config file: {config_path}")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# If a log directory was set, then set up a rolling log
logdir = config.get("gateway", {}).get("logdir", "").strip()
if logdir != "":
    logfile = os.path.join(logdir, "aprstastic.log")
    logger.debug(f"Writing logs to: {logfile}")
    file_handler = TimedRotatingFileHandler(
        logfile, when="d", interval=1, backupCount=7
    )
    file_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    file_handler.addFilter(LocalDebugFilter())
    logging.root.addHandler(file_handler)

# Start the gateway
gateway = Gateway(config)
gateway.run()
