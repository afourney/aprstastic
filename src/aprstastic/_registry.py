# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import sqlite3
import logging
import json
import shutil
import time
import requests
import traceback
import os

from packaging.version import Version
from .__about__ import __version__

logger = logging.getLogger("aprstastic")

DATABASE_FILE = "registrations.db"

# The precompiled registrations and overrides are not updated directly, and so are loaded from flat files
OVERRIDES_FILE = "registration_overrides.json"
PRECOMPILED_FILE = "precompiled_registrations.json"

COL_DEVICE_ID = 0
COL_CALL_SIGN = 1
COL_SETTINGS = 2
COL_TIMESTAMP = 3


class CallSignRegistry(object):
    """
    There are three potential sources of registration data:
        - local (via direct Meshtastic messages to this device)
        - beaconed (observing registration beacons to APRS)
        - precompiled (a precompiled database, downloaded from the web, to seed things)

    There is also a system-level registration which is meant to override everything if needed.

    The records are then merged, by date (with system-level overrides having the final word).
    This class manages this process
    """

    def __init__(self, data_dir):
        super().__init__()
        self._data_dir = data_dir

        self._db_conn = self._open_db(os.path.join(data_dir, DATABASE_FILE))
        self._precompiled = self._load_precompiled(
            os.path.join(data_dir, PRECOMPILED_FILE)
        )
        self._overrides = self._load_overrides(os.path.join(data_dir, OVERRIDES_FILE))
        self._merged = dict()

        self._rebuild()

    def _open_db(self, db_path):
        """
        Return a sqlite database connection to the registration database, initilizing the database if needed.
        """
        create_db = not os.path.isfile(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if create_db:
            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS VersionInfo (
    db_version INTEGER,
    package_version TEXT
)
"""
            )

            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS LocalRegistrations (
    device_id TEXT UNIQUE,
    call_sign TEXT UNIQUE,
    settings_json TEXT,
    timestamp INTEGER
)
"""
            )

            cursor.execute(
                """
CREATE TABLE IF NOT EXISTS BeaconedRegistrations (
    device_id TEXT UNIQUE,
    call_sign TEXT UNIQUE,
    settings_json TEXT,
    timestamp INTEGER
)
"""
            )

            cursor.execute(
                "INSERT INTO VersionInfo (db_version, package_version) VALUES (?, ?);",
                (1, __version__),
            )

            # Commit the changes
            conn.commit()
            logger.debug(f"initialized database: {db_path}")

        cursor.close()
        return conn

    def add_registration(self, device_id, call_sign, icon, is_local):
        cursor = self._db_conn.cursor()

        # Make sure that device or call_sign is non None
        if device_id is None and call_sign is None:
            raise ValueError(
                "At least one of 'device_id' or 'call_sign' must be non-None."
            )

        # Delete prior rows
        del_query = "DELETE FROM %s WHERE device_id = ? OR call_sign = ?;" % (
            "LocalRegistrations" if is_local else "BeaconedRegistrations",
        )
        cursor.execute(del_query, (device_id, call_sign))

        # Insert the new record
        insert_query = (
            "INSERT INTO %s (device_id, call_sign, settings_json, timestamp) VALUES (?, ?, ?, ?);"
            % ("LocalRegistrations" if is_local else "BeaconedRegistrations",)
        )
        cursor.execute(insert_query, (device_id, call_sign, icon, int(time.time())))

        self._db_conn.commit()
        cursor.close()

        self._rebuild()

    def _rebuild(self):
        """
        Updates (by rebuilding), the in-memory copy of the merged database, replaying actions in time order.
        """
        cursor = self._db_conn.cursor()

        # Append all the operations together
        operations = [t for t in self._precompiled]
        operations.extend([t for t in self._overrides])

        cursor.execute(
            "SELECT device_id, call_sign, settings_json, timestamp FROM BeaconedRegistrations;"
        )
        rows = cursor.fetchall()
        for row in rows:
            operations.append(
                (
                    row[COL_DEVICE_ID],
                    row[COL_CALL_SIGN],
                    row[COL_SETTINGS],
                    row[COL_TIMESTAMP],
                )
            )

        cursor.execute(
            "SELECT device_id, call_sign, settings_json, timestamp FROM LocalRegistrations;"
        )
        rows = cursor.fetchall()
        for row in rows:
            operations.append(
                (
                    row[COL_DEVICE_ID],
                    row[COL_CALL_SIGN],
                    row[COL_SETTINGS],
                    row[COL_TIMESTAMP],
                )
            )

        # Sort by date, ascending
        operations.sort(key=lambda x: x[COL_TIMESTAMP])

        self._merged = dict()
        for op in operations:
            d_id = op[COL_DEVICE_ID]
            icon = op[COL_SETTINGS]
            cs = op[COL_CALL_SIGN]
            cs_key = self._get_device_id(self._merged, cs)

            # Delete the prior value(s)
            if d_id is not None and d_id in self._merged:
                del self._merged[d_id]
            if cs_key is not None and cs_key in self._merged:
                del self._merged[cs_key]

            # If either the device id or call sign are None, then continue
            # (this is a tombstone)
            if d_id is None or cs is None:
                continue

            # Update
            self._merged[d_id] = {"call_sign": cs, "icon": icon}

        cursor.close()

    def _load_overrides(self, file_path):
        """
        Return a copy of the registration overrides, which is loaded into memory.
        """

        if not os.path.isfile(file_path):
            # No file, no overrides
            return {}

        # Load the existing copy
        override_data = None
        with open(file_path, "rt") as fh:
            override_data = json.loads(fh.read())

        # get a date in the distant future
        future = time.time() + 3600 * 24 * 365 * 1000

        # Return tuples in the expected format
        tuples = override_data.get("tuples")
        for t in tuples:
            t[COL_TIMESTAMP] = future
        return tuples

    def _load_precompiled(self, file_path):
        """
        Return a copy of the precompiled registrations, which are loaded into memory.
        """

        # Doesn't exist, so copy the version that shipped with this app
        if not os.path.isfile(file_path):
            packaged_database = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "res", PRECOMPILED_FILE
            )
            logger.debug(
                f"Copying packaged version of the precompiled database: {packaged_database}"
            )
            shutil.copyfile(packaged_database, file_path)

        # Load the existing copy
        precompiled_data = None
        with open(file_path, "rt") as fh:
            precompiled_data = json.loads(fh.read())
        cached_timestamp = precompiled_data.get("download_timestamp", 0)
        now = time.time()

        # It's older than a day, so download a new one
        if now - cached_timestamp > 3600 * 24:
            logger.debug("Downloading precompiled database.")
            try:
                response = requests.get(precompiled_data.get("url"))
                response.raise_for_status()
                new_data = json.loads(response.text)

                # Check for compatibility
                min_version = new_data.get("min_package_version", "0.0.1a1")
                if Version(__version__) < Version(min_version):
                    logger.error(
                        f"Remote precompiled database requires at least aprstastic version '{min_version}'. Please upgrade."
                    )
                elif "tuples" not in new_data:
                    logger.error(
                        f"Remote precompiled database is incompatible. Please upgrade."
                    )
                else:
                    precompiled_data = new_data
                    precompiled_data["download_timestamp"] = now
                    precompiled_data["reported_timestamp"] = min(
                        now, precompiled_data["reported_timestamp"]
                    )

                    # Save it
                    with open(file_path, "wt") as fh:
                        fh.write(json.dumps(precompiled_data, indent=4))
                        logger.debug("New precompiled database saved to disk.")
            except:
                logger.error(traceback.format_exc())

        # Return tuples in the expected format
        tuples = precompiled_data.get("tuples")
        for t in tuples:
            t[COL_TIMESTAMP] = min(now, t[COL_TIMESTAMP])
        return tuples

    def _get_device_id(self, d, call_sign):
        """
        Return the first device id that maps to the given call sign
        """
        for k in d:
            if d[k]["call_sign"] == call_sign:
                return k
        return None

    # Emulate a dictionary
    def __getitem__(self, key):
        return self._merged[key]

    def __len__(self):
        return len(self._merged)

    def keys(self):
        return self._merged.keys()

    def values(self):
        return self._merged.values()

    def items(self):
        return self._merged.items()

    def __contains__(self, item):
        return item in self._merged

    def __iter__(self):
        return iter(self._merged)
