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
    DATABASE_FILE,
    OVERRIDES_FILE,
    PRECOMPILED_FILE,
)

TEST_PRECOMPILED_FILE = "test_" + PRECOMPILED_FILE
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")


def test_initialize_registry():
    db_file = os.path.join(data_dir, DATABASE_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(precompiled_file)

    # Initialize the registry
    registry = CallSignRegistry(data_dir)

    # Make sure the files now exist
    assert os.path.isfile(db_file)
    assert os.path.isfile(precompiled_file)

    # Check that we can parse the precompiled file
    with open(precompiled_file, "rt") as fh:
        precompiled_data = json.loads(fh.read())

    # Load the database, and run a simple query
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM VersionInfo;")
    rows = cursor.fetchall()
    assert len(rows) == 1
    conn.close()


def test_inserts_and_updates():
    db_file = os.path.join(data_dir, DATABASE_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(precompiled_file)

    # Initialize the registry
    registry = CallSignRegistry(data_dir)
    # Use only the database
    registry._overrides = {}
    registry._precompiled = {}
    registry._rebuild()

    # Make sure we are starting empty
    assert len(registry) == 0
    assert _to_dict(registry) == {}

    # Add a registration 5 times, checking after each
    for i in range(1, 6):
        call_sign = f"N0CALL-{i}"
        registry.add_registration("!00000000", call_sign, True)
        assert len(registry) == 1
        assert _to_dict(registry) == {"!00000000": call_sign}
    registry.add_registration("!00000000", "N0CALL-1", True)

    # Now update the device IDs
    for i in range(1, 6):
        device_id = f"!0000000{i}"
        registry.add_registration(device_id, "N0CALL-1", True)
        assert len(registry) == 1
        assert _to_dict(registry) == {device_id: "N0CALL-1"}
    registry.add_registration("!00000000", "N0CALL-1", True)

    # Wait a second, then do the same for beacons
    time.sleep(1.1)
    for i in range(6, 11):
        call_sign = f"N0CALL-{i}"
        registry.add_registration("!00000000", call_sign, False)
        assert len(registry) == 1
        assert _to_dict(registry) == {"!00000000": call_sign}
    registry.add_registration("!00000000", "N0CALL-1", False)

    for i in range(1, 6):
        device_id = f"!0000000{i}"
        registry.add_registration(device_id, "N0CALL-1", False)
        assert len(registry) == 1
        assert _to_dict(registry) == {device_id: "N0CALL-1"}
    registry.add_registration("!00000000", "N0CALL-1", False)

    # Add a bunch more registrations
    registry.add_registration("!00000002", "N0CALL-2", True)
    registry.add_registration("!00000003", "N0CALL-3", True)
    registry.add_registration("!00000004", "N0CALL-4", True)
    registry.add_registration("!00000005", "N0CALL-5", False)
    registry.add_registration("!00000006", "N0CALL-6", False)
    registry.add_registration("!00000007", "N0CALL-7", False)
    assert _to_dict(registry) == {
        "!00000000": "N0CALL-1",
        "!00000002": "N0CALL-2",
        "!00000003": "N0CALL-3",
        "!00000004": "N0CALL-4",
        "!00000005": "N0CALL-5",
        "!00000006": "N0CALL-6",
        "!00000007": "N0CALL-7",
    }


def test_precompiled():
    db_file = os.path.join(data_dir, DATABASE_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)
    test_precompiled_file = os.path.join(data_dir, TEST_PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(precompiled_file)

    # Copy the test precompiled_registry
    shutil.copyfile(test_precompiled_file, precompiled_file)

    # Initialize the registry
    registry = CallSignRegistry(data_dir)

    # Now check that it looks right
    assert _to_dict(registry) == {
        "!00000001": "N0CALL-1",
        "!00000002": "N0CALL-2",
    }

    # And call signs are updated correctly
    registry.add_registration("!00000001", "N0CALL-3", True)
    assert _to_dict(registry) == {
        "!00000001": "N0CALL-3",
        "!00000002": "N0CALL-2",
    }

    registry.add_registration("!00000002", "N0CALL-4", False)
    assert _to_dict(registry) == {
        "!00000001": "N0CALL-3",
        "!00000002": "N0CALL-4",
    }

    # Reset
    registry.add_registration("!00000001", "N0CALL-1", True)
    registry.add_registration("!00000002", "N0CALL-2", False)
    assert _to_dict(registry) == {
        "!00000001": "N0CALL-1",
        "!00000002": "N0CALL-2",
    }

    # And ids are updated correctly
    registry.add_registration("!00000003", "N0CALL-1", True)
    assert _to_dict(registry) == {
        "!00000003": "N0CALL-1",
        "!00000002": "N0CALL-2",
    }

    registry.add_registration("!00000004", "N0CALL-2", False)
    assert _to_dict(registry) == {
        "!00000003": "N0CALL-1",
        "!00000004": "N0CALL-2",
    }


def _to_dict(registry):
    """
    Helper function to convert the registry into a dictionary
    """
    d = dict()
    for k in registry:
        d[k] = registry[k]
    return d


##########################
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_initialize_registry()
    test_inserts_and_updates()
    test_precompiled()
