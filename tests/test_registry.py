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

EMPTY_PRECOMPILED_FILE = "empty_" + PRECOMPILED_FILE
TEST_PRECOMPILED_FILE = "test_" + PRECOMPILED_FILE
TEST_OVERRIDES_FILE = "test_" + OVERRIDES_FILE
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
    overrides_file = os.path.join(data_dir, OVERRIDES_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(overrides_file):
        os.unlink(overrides_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(overrides_file)
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
        registry.add_registration("!00000000", call_sign, None, True)
        assert len(registry) == 1
        assert _to_dict(registry) == {
            "!00000000": {"call_sign": call_sign, "icon": None}
        }
    registry.add_registration("!00000000", "N0CALL-1", None, True)

    # Now update the device IDs
    for i in range(1, 6):
        device_id = f"!0000000{i}"
        registry.add_registration(device_id, "N0CALL-1", None, True)
        assert len(registry) == 1
        assert _to_dict(registry) == {
            device_id: {"call_sign": "N0CALL-1", "icon": None}
        }
    registry.add_registration("!00000000", "N0CALL-1", None, True)

    # Wait a second, then do the same for beacons
    time.sleep(1.1)
    for i in range(6, 11):
        call_sign = f"N0CALL-{i}"
        registry.add_registration("!00000000", call_sign, None, False)
        assert len(registry) == 1
        assert _to_dict(registry) == {
            "!00000000": {"call_sign": call_sign, "icon": None}
        }
    registry.add_registration("!00000000", "N0CALL-1", None, False)

    for i in range(1, 6):
        device_id = f"!0000000{i}"
        registry.add_registration(device_id, "N0CALL-1", None, False)
        assert len(registry) == 1
        assert _to_dict(registry) == {
            device_id: {"call_sign": "N0CALL-1", "icon": None}
        }
    registry.add_registration("!00000000", "N0CALL-1", None, False)

    # Add a bunch more registrations
    registry.add_registration("!00000002", "N0CALL-2", None, True)
    registry.add_registration("!00000003", "N0CALL-3", None, True)
    registry.add_registration("!00000004", "N0CALL-4", None, True)
    registry.add_registration("!00000005", "N0CALL-5", None, False)
    registry.add_registration("!00000006", "N0CALL-6", None, False)
    registry.add_registration("!00000007", "N0CALL-7", None, False)
    assert _to_dict(registry) == {
        "!00000000": {"call_sign": "N0CALL-1", "icon": None},
        "!00000002": {"call_sign": "N0CALL-2", "icon": None},
        "!00000003": {"call_sign": "N0CALL-3", "icon": None},
        "!00000004": {"call_sign": "N0CALL-4", "icon": None},
        "!00000005": {"call_sign": "N0CALL-5", "icon": None},
        "!00000006": {"call_sign": "N0CALL-6", "icon": None},
        "!00000007": {"call_sign": "N0CALL-7", "icon": None},
    }

    # Wait a second then nuke nearly everything
    time.sleep(1.1)
    registry.add_registration("!00000002", None, None, True)
    registry.add_registration(None, "N0CALL-2", None, True)

    registry.add_registration(None, "N0CALL-3", None, False)
    registry.add_registration(None, "N0CALL-4", None, True)

    registry.add_registration("!00000005", None, None, False)
    registry.add_registration(None, "N0CALL-5", None, False)

    registry.add_registration("!00000006", None, None, True)
    registry.add_registration("!00000007", None, None, False)

    assert _to_dict(registry) == {
        "!00000000": {"call_sign": "N0CALL-1", "icon": None},
    }

    # Make sure we throw a value error if we try to add None, None
    try:
        registry.add_registration(None, None, None, False)
        assert False
    except ValueError:
        pass


def test_precompiled():
    db_file = os.path.join(data_dir, DATABASE_FILE)
    overrides_file = os.path.join(data_dir, OVERRIDES_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)
    test_precompiled_file = os.path.join(data_dir, TEST_PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(overrides_file):
        os.unlink(overrides_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(overrides_file)
    assert not os.path.isfile(precompiled_file)

    # Copy the test precompiled_registry
    shutil.copyfile(test_precompiled_file, precompiled_file)

    # Initialize the registry
    registry = CallSignRegistry(data_dir)

    # Now check that it looks right
    assert _to_dict(registry) == {
        "!00000001": {"call_sign": "N0CALL-1", "icon": None},
        "!00000002": {"call_sign": "N0CALL-2", "icon": None},
    }

    # And call signs are updated correctly
    registry.add_registration("!00000001", "N0CALL-3", None, True)
    assert _to_dict(registry) == {
        "!00000001": {"call_sign": "N0CALL-3", "icon": None},
        "!00000002": {"call_sign": "N0CALL-2", "icon": None},
    }

    registry.add_registration("!00000002", "N0CALL-4", None, False)
    assert _to_dict(registry) == {
        "!00000001": {"call_sign": "N0CALL-3", "icon": None},
        "!00000002": {"call_sign": "N0CALL-4", "icon": None},
    }

    # Reset
    registry.add_registration("!00000001", "N0CALL-1", None, True)
    registry.add_registration("!00000002", "N0CALL-2", None, False)
    assert _to_dict(registry) == {
        "!00000001": {"call_sign": "N0CALL-1", "icon": None},
        "!00000002": {"call_sign": "N0CALL-2", "icon": None},
    }

    # And ids are updated correctly
    registry.add_registration("!00000003", "N0CALL-1", None, True)
    assert _to_dict(registry) == {
        "!00000003": {"call_sign": "N0CALL-1", "icon": None},
        "!00000002": {"call_sign": "N0CALL-2", "icon": None},
    }

    registry.add_registration("!00000004", "N0CALL-2", None, False)
    assert _to_dict(registry) == {
        "!00000003": {"call_sign": "N0CALL-1", "icon": None},
        "!00000004": {"call_sign": "N0CALL-2", "icon": None},
    }


def test_overrides():
    db_file = os.path.join(data_dir, DATABASE_FILE)
    overrides_file = os.path.join(data_dir, OVERRIDES_FILE)
    test_overrides_file = os.path.join(data_dir, TEST_OVERRIDES_FILE)
    precompiled_file = os.path.join(data_dir, PRECOMPILED_FILE)
    empty_precompiled_file = os.path.join(data_dir, EMPTY_PRECOMPILED_FILE)

    # Start fresh
    if os.path.isfile(db_file):
        os.unlink(db_file)
    if os.path.isfile(overrides_file):
        os.unlink(overrides_file)
    if os.path.isfile(precompiled_file):
        os.unlink(precompiled_file)

    assert not os.path.isfile(db_file)
    assert not os.path.isfile(overrides_file)
    assert not os.path.isfile(precompiled_file)

    # Copy the test precompiled_registry
    shutil.copyfile(test_overrides_file, overrides_file)
    shutil.copyfile(empty_precompiled_file, precompiled_file)

    # Initialize the registry
    registry = CallSignRegistry(data_dir)

    # Now check that it looks right
    assert _to_dict(registry) == {
        "!00000011": {"call_sign": "N0CALL-1", "icon": None},
        "!00000022": {"call_sign": "N0CALL-2", "icon": None},
    }

    # Proper things are being overridden
    registry.add_registration("!00000011", "N0CALL-6", None, True)
    registry.add_registration("!00000022", "N0CALL-6", None, False)
    registry.add_registration("!00000001", "N0CALL-1", None, True)
    registry.add_registration("!00000002", "N0CALL-2", None, False)
    assert _to_dict(registry) == {
        "!00000011": {"call_sign": "N0CALL-1", "icon": None},
        "!00000022": {"call_sign": "N0CALL-2", "icon": None},
    }

    # Deleted things stay deleted
    registry.add_registration("!00000033", "N0CALL-3", None, True)
    registry.add_registration("!00000033", "N0CALL-3", None, False)
    registry.add_registration("!00000044", "N0CALL-4", None, True)
    registry.add_registration("!00000044", "N0CALL-4", None, False)
    registry.add_registration("!00000055", "N0CALL-5", None, True)
    print(json.dumps(_to_dict(registry), indent=4))
    assert _to_dict(registry) == {
        "!00000011": {"call_sign": "N0CALL-1", "icon": None},
        "!00000022": {"call_sign": "N0CALL-2", "icon": None},
        "!00000055": {"call_sign": "N0CALL-5", "icon": None},
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
    test_overrides()
