import os
import yaml
import logging
from ._config_const import DEFAULT_CONFIG_CONTENT

logger = logging.getLogger("aprstastic")

CONFIG_FILE_NAME = "aprstastic.yaml"
LOGS_SUBDIR = "logs"
DATA_SUBDIR = "data"
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".config", "aprstastic")
DEFAULT_CALL_SIGN = "N0CALL"


class ConfigError(Exception):
    pass


def init_config():
    """
    Return a valid gateway configuration, or raise an error.
    This method performs the following steps:

        1. Find the config.yaml file. If unsuccessful, create a sample, and exit.
        2. Validate the configuration.
        3. Determine the data directory -- creating it if it does not exist.
        4. Determine the logging directory -- creating it if it does not exits.
    """

    # Find the config file
    config_path = None
    if os.path.isfile(CONFIG_FILE_NAME):
        config_path = CONFIG_FILE_NAME
    else:
        path = os.path.join(DEFAULT_DATA_DIR, CONFIG_FILE_NAME)
        if os.path.isfile(path):
            config_path = path
        else:
            os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
            with open(os.path.join(DEFAULT_DATA_DIR, CONFIG_FILE_NAME), "wt") as fh:
                fh.write(DEFAULT_CONFIG_CONTENT.rstrip() + "\n")
            raise ConfigError(
                f"ERROR: No '{CONFIG_FILE_NAME}' file was found.\nA sample configuration was written to '{path}'\nBE SURE TO EDIT THIS FILE BEFORE PROCEEDING.\nAt the very least, edit the 'call_sign' and 'aprsis_passcode' values!"
            )

    # Load the config file
    config = None
    logger.debug(f"config file: {config_path}")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Validate
    # TODO

    # Make sure the call sign was at least changed
    call_sign = config.get("call_sign")
    if call_sign == DEFAULT_CALL_SIGN:
        raise ConfigError(
            f"ERROR: '{config_path}' appears to be the sample config.\nBE SURE TO EDIT THIS FILE BEFORE PROCEEDING.\nAt the very least, edit the 'call_sign' and 'aprsis_passcode' values!"
        )

    # Try to get the data directory
    data_dir = config.get("data_dir")
    if data_dir is None or data_dir.strip() == "":
        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(config_path)), DATA_SUBDIR
        )
    elif not os.path.isabs(data_dir):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(config_path)), data_dir)

    logger.debug(f"data directory: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)
    config["data_dir"] = data_dir

    # Try to get the logging directory
    logs_dir = config.get("logs_dir")
    if logs_dir is None or logs_dir.strip() == "":
        logs_dir = os.path.join(
            os.path.dirname(os.path.abspath(config_path)), LOGS_SUBDIR
        )
    elif not os.path.isabs(logs_dir):
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(config_path)), logs_dir)

    logger.debug(f"logs directory: {logs_dir}")
    os.makedirs(logs_dir, exist_ok=True)
    config["logs_dir"] = logs_dir

    # TODO: Fixme
    # Wrap the config in a structure that is backwards compatible
    return {"gateway": config, "licensed_operators": {}}
