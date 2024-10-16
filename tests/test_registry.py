# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import json
import sqlite3
from aprstastic._registry import (
    CallSignRegistry,
    DATABASE_FILE,
    OVERRIDES_FILE,
    PRECOMPILED_FILE,
)

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
