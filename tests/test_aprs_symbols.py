# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import json
import time
import shutil

from aprstastic._aprs_symbols import get_symbol_code, APRS_SYMBOLS, APRS_OVERLAYS


def test_symbol_codes():
    # A few sanity spot checks
    assert get_symbol_code(None) == None
    assert get_symbol_code("MV") == "/>"
    assert get_symbol_code("HS") == "/["
    assert get_symbol_code("OG") == "\\&"
    assert get_symbol_code("OGM") == "M&"
    assert get_symbol_code("HSM") == "/["  # Not an overlay
    assert get_symbol_code("ZZ") is None  # Not present
    assert get_symbol_code("OGMM") is None  # Too long
    assert get_symbol_code("O") is None  # Too short
    assert get_symbol_code("OG$") == "\\&"  # Invlaid overlay

    # Check all symbols
    for icon in APRS_SYMBOLS:
        entry = APRS_SYMBOLS[icon]
        assert get_symbol_code(icon) == entry["symbol"]

        # Check correct handling of overlays
        for o in APRS_OVERLAYS:
            if "overlay" in entry:
                assert get_symbol_code(icon + o) == o + entry["symbol"][1:]
            else:
                assert get_symbol_code(icon + o) == entry["symbol"]


##########################
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    test_symbol_codes()
