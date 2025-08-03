# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import json
import sqlite3
import time
import shutil
from aprstastic._registry import (
    CallSignRegistry,
)
from aprstastic.__about__ import __version__


def main(data_dir):
    # Initialize the registry
    registry = CallSignRegistry(data_dir)
    result = {
        "version": 1,
        "package_version": __version__,
        "download_timestamp": time.time(),
        "reported_timestamp": time.time(),
        "url": "https://raw.githubusercontent.com/afourney/aprstastic/refs/heads/main/src/aprstastic/res/precompiled_registrations.json",
        "tuples": [],
    }

    for k in registry:
        # Convert the registry entry to a tuple
        record = [
            k,
            registry[k]["call_sign"],
            registry[k]["icon"],
            registry[k]["timestamp"],
        ]

        result["tuples"].append(record)

    print(json.dumps(result, indent=4))


##########################
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    main(os.path.join(os.path.dirname(__file__), "dump_data"))
