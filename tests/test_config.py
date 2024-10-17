# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import json
import time
import shutil

from aprstastic._config import (
    ConfigError,
    init_config,
    CONFIG_FILE_NAME,
    LOGS_SUBDIR,
    DATA_SUBDIR,
    DEFAULT_CALL_SIGN,
)


TEST_CONFIG_FILE_NAME_1 = "test_aprstastic_1.yaml"
TEST_CONFIG_FILE_NAME_2 = "test_aprstastic_2.yaml"
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

# Monkey patch the default directory
import aprstastic._config

aprstastic._config.DEFAULT_DATA_DIR = config_dir

logs_dir = os.path.join(config_dir, LOGS_SUBDIR)
data_dir = os.path.join(config_dir, DATA_SUBDIR)


def test_initialize_config():
    config_file = os.path.join(config_dir, CONFIG_FILE_NAME)

    # Start fresh
    if os.path.isfile(config_file):
        os.unlink(config_file)

    assert not os.path.isfile(config_file)

    cwd = os.path.abspath(os.getcwd())
    error_msg = None
    try:
        os.chdir(config_dir)

        # Initialize the config
        config = init_config()

    except ConfigError as e:
        error_msg = str(e)
    finally:
        os.chdir(cwd)

    # Make sure the sample config exists now
    assert os.path.isfile(config_file)
    # assert os.path.isdir(logs_dir)
    # assert os.path.isdir(data_dir)

    # Make sure the correct error was thrown
    assert "A sample configuration was written" in error_msg

    # Try loading it again, and check that the correct error was thrown the second time
    try:
        os.chdir(config_dir)
        config = init_config()
    except ConfigError as e:
        error_msg = str(e)
    finally:
        os.chdir(cwd)
    assert "appears to be the sample config" in error_msg


def test_load_config():
    config_file = os.path.join(config_dir, CONFIG_FILE_NAME)
    test_config_file_1 = os.path.join(config_dir, TEST_CONFIG_FILE_NAME_1)
    test_config_file_2 = os.path.join(config_dir, TEST_CONFIG_FILE_NAME_2)

    mylogs_dir = os.path.join(config_dir, "mylogs")
    mydata_dir = os.path.join(config_dir, "mydata")

    # Install our test config #1
    shutil.copyfile(test_config_file_1, config_file)

    # Load the config
    cwd = os.path.abspath(os.getcwd())
    error_msg = None
    try:
        os.chdir(config_dir)
        config = init_config()
    finally:
        os.chdir(cwd)

    # Check that it looks right
    assert config == json.loads(
        """
{
    "gateway": {
        "call_sign": "N0CALL-1",
        "aprsis_passcode": 12345,
        "meshtastic_interface": {
            "type": "serial"
        },
        "beacon_registrations": true,
        "data_dir": "%s",
        "logs_dir": "%s"
    },
    "licensed_operators": {}
}
"""
        % (data_dir, logs_dir)
    )

    # Install our test config #2
    shutil.copyfile(test_config_file_2, config_file)

    # Load the config
    cwd = os.path.abspath(os.getcwd())
    error_msg = None
    try:
        os.chdir(config_dir)
        config = init_config()
    finally:
        os.chdir(cwd)

    # Check that it looks right
    assert config == json.loads(
        """
{
    "gateway": {
        "call_sign": "N0CALL-2",
        "aprsis_passcode": 12345,
        "meshtastic_interface": {
            "type": "serial"
        },
        "beacon_registrations": false,
        "data_dir": "%s",
        "logs_dir": "%s"
    },
    "licensed_operators": {}
}
"""
        % (mydata_dir, mylogs_dir)
    )


##########################
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_initialize_config()
    test_load_config()
