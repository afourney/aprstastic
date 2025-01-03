# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging
import yaml
import os
import sys
import traceback
from logging.handlers import TimedRotatingFileHandler
from ._config import init_config, ConfigError
from ._gateway import Gateway

# Set up logging
################
LOG_FORMAT = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
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
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
stream_handler.addFilter(LocalDebugFilter())
logging.root.addHandler(stream_handler)
logging.captureWarnings(True)

# Load the configuration
config = None
try:
    config = init_config()
except ConfigError as e:
    sys.stderr.write(str(e).rstrip() + "\n")
    sys.exit(1)

# Configure file logs
logs_dir = config.get("logs_dir")
if logs_dir is not None:
    log_file = os.path.join(logs_dir, "aprstastic.log")
    logger.debug(f"Writing logs to: {log_file}")
    file_handler = TimedRotatingFileHandler(
        log_file, when="d", interval=1, backupCount=7
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.addFilter(LocalDebugFilter())
    logging.root.addHandler(file_handler)

# Start the gateway. Log any errors, and exit cleanly
try:
    gateway = Gateway(config)
    gateway.run()
except:
    logger.error(traceback.format_exc())
    raise
finally:
    logging.shutdown()
