# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging
import yaml
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from ._config import init_config, ConfigError
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

# Load the configuration
config = None
try:
    config = init_config()
except ConfigError as e:
    sys.stderr.write(str(e).rstrip() + "\n")
    sys.exit(1)

# Configure file logs
logs_dir = config.get("gateway", {}).get("logs_dir")
if logs_dir is not None:
    log_file = os.path.join(logs_dir, "aprstastic.log")
    logger.debug(f"Writing logs to: {log_file}")
    file_handler = TimedRotatingFileHandler(
        log_file, when="d", interval=1, backupCount=7
    )
    file_handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    file_handler.addFilter(LocalDebugFilter())
    logging.root.addHandler(file_handler)

# cr = CallSignRegistry(config.get("gateway", {}).get("data_dir"))
# import json
# print(json.dumps(cr._merged, indent=4))
#
# print("cr['b_id_1729049990']: " + cr["b_id_1729049990"])
# print("len(cr): " + str(len(cr)))
# print("'b_id_1729049990' in cr: " + str('b_id_1729049990' in cr))
# print("'b_id_172904999x' in cr: " + str('b_id_172904999x' in cr))
# print("cr.keys(cr): " + str(cr.keys()))
# print("cr.values(cr): " + str(cr.values()))
# print("cr.items(cr): " + str(cr.items()))
#
# print()
# for k in cr:
#    print(f"Device ID: {k}, Call Sign: {cr[k]}")

# Start the gateway
gateway = Gateway(config)
gateway.run()
