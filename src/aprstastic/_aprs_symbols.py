# Symbol table adapted from: https://github.com/hessu/aprs-symbol-index
APRS_SYMBOLS = {
    "A0": {
        "symbol": "\\0",
        "description": "Circle, IRLP / Echolink/WIRES",
        "overlay": True,
    },
    "A8": {"symbol": "\\8", "description": "802.11 WiFi or other network node"},
    "A9": {"symbol": "\\9", "description": "Gas station"},
    "AA": {
        "symbol": "\\A",
        "description": "White box",
        "overlay": True,
    },
    "AB": {"symbol": "\\B", "description": "Blowing snow"},
    "AC": {"symbol": "\\C", "description": "Coast Guard"},
    "AD": {"symbol": "\\D", "description": "Drizzling rain"},
    "AE": {"symbol": "\\E", "description": "Smoke, Chimney"},
    "AF": {"symbol": "\\F", "description": "Freezing rain"},
    "AG": {"symbol": "\\G", "description": "Snow shower"},
    "AH": {"symbol": "\\H", "description": "Haze"},
    "AI": {"symbol": "\\I", "description": "Rain shower"},
    "AJ": {"symbol": "\\J", "description": "Lightning"},
    "AK": {"symbol": "\\K", "description": "Kenwood HT"},
    "AL": {"symbol": "\\L", "description": "Lighthouse"},
    "AN": {"symbol": "\\N", "description": "Navigation buoy"},
    "AO": {"symbol": "\\O", "description": "Rocket"},
    "AP": {"symbol": "\\P", "description": "Parking"},
    "AQ": {"symbol": "\\Q", "description": "Earthquake"},
    "AR": {"symbol": "\\R", "description": "Restaurant"},
    "AS": {"symbol": "\\S", "description": "Satellite"},
    "AT": {"symbol": "\\T", "description": "Thunderstorm"},
    "AU": {"symbol": "\\U", "description": "Sunny"},
    "AV": {"symbol": "\\V", "description": "VORTAC, Navigational aid"},
    "AW": {
        "symbol": "\\W",
        "description": "NWS site",
        "overlay": True,
    },
    "AX": {"symbol": "\\X", "description": "Pharmacy"},
    "BB": {"symbol": "/!", "description": "Police station"},
    "BD": {"symbol": "/#", "description": "Digipeater"},
    "BE": {"symbol": "/$", "description": "Telephone"},
    "BF": {"symbol": "/%", "description": "DX cluster"},
    "BG": {"symbol": "/&", "description": "HF gateway"},
    "BH": {"symbol": "/'", "description": "Small aircraft"},
    "BI": {"symbol": "/(", "description": "Mobile satellite station"},
    "BJ": {"symbol": "/)", "description": "Wheelchair, handicapped"},
    "BK": {"symbol": "/*", "description": "Snowmobile"},
    "BL": {"symbol": "/+", "description": "Red Cross"},
    "BM": {"symbol": "/,", "description": "Boy Scouts"},
    "BN": {"symbol": "/-", "description": "House"},
    "BO": {"symbol": "/.", "description": "Red X"},
    "BP": {"symbol": "//", "description": "Red dot"},
    "DS": {"symbol": "\\[", "description": "Wall Cloud"},
    "DV": {
        "symbol": "\\^",
        "description": "Aircraft",
        "overlay": True,
    },
    "DW": {
        "symbol": "\\_",
        "description": "Weather site",
        "overlay": True,
    },
    "DX": {"symbol": "\\`", "description": "Rain"},
    "HS": {"symbol": "/[", "description": "Human"},
    "HT": {"symbol": "/\\", "description": "DF triangle"},
    "HU": {"symbol": "/]", "description": "Mailbox, post office"},
    "HV": {"symbol": "/^", "description": "Large aircraft"},
    "HW": {"symbol": "/_", "description": "Weather station"},
    "HX": {"symbol": "/`", "description": "Satellite dish antenna"},
    "LA": {"symbol": "/a", "description": "Ambulance"},
    "LB": {"symbol": "/b", "description": "Bicycle"},
    "LC": {"symbol": "/c", "description": "Incident command post"},
    "LD": {"symbol": "/d", "description": "Fire station"},
    "LE": {"symbol": "/e", "description": "Horse, equestrian"},
    "LF": {"symbol": "/f", "description": "Fire truck"},
    "LG": {"symbol": "/g", "description": "Glider"},
    "LH": {"symbol": "/h", "description": "Hospital"},
    "LI": {"symbol": "/i", "description": "IOTA, islands on the air"},
    "LJ": {"symbol": "/j", "description": "Jeep"},
    "LK": {"symbol": "/k", "description": "Truck"},
    "LL": {"symbol": "/l", "description": "Laptop"},
    "LM": {"symbol": "/m", "description": "Mic-E repeater"},
    "LN": {"symbol": "/n", "description": "Node, black bulls-eye"},
    "LO": {"symbol": "/o", "description": "Emergency operations center"},
    "LP": {"symbol": "/p", "description": "Dog"},
    "LQ": {"symbol": "/q", "description": "Grid square, 2 by 2"},
    "LR": {"symbol": "/r", "description": "Repeater tower"},
    "LS": {"symbol": "/s", "description": "Ship, power boat"},
    "LT": {"symbol": "/t", "description": "Truck stop"},
    "LU": {"symbol": "/u", "description": "Semi-trailer truck, 18-wheeler"},
    "LV": {"symbol": "/v", "description": "Van"},
    "LW": {"symbol": "/w", "description": "Water station"},
    "LX": {"symbol": "/x", "description": "X / Unix"},
    "LY": {"symbol": "/y", "description": "House, yagi antenna"},
    "LZ": {"symbol": "/z", "description": "Shelter"},
    "MR": {"symbol": "/:", "description": "Fire"},
    "MS": {"symbol": "/;", "description": "Campground, tent"},
    "MT": {"symbol": "/<", "description": "Motorcycle"},
    "MU": {"symbol": "/=", "description": "Railroad engine"},
    "MV": {"symbol": "/>", "description": "Car"},
    "MW": {"symbol": "/?", "description": "File server"},
    "MX": {"symbol": "/@", "description": "Hurricane predicted path"},
    "NR": {"symbol": "\\:", "description": "Hail"},
    "NS": {"symbol": "\\;", "description": "Park, picnic area"},
    "NT": {"symbol": "\\<", "description": "Advisory, single red flag"},
    "NV": {
        "symbol": "\\>",
        "description": "Red car",
        "overlay": True,
    },
    "NW": {"symbol": "\\?", "description": "Info kiosk"},
    "NX": {"symbol": "\\@", "description": "Hurricane, Tropical storm"},
    "OB": {"symbol": "\\!", "description": "Emergency"},
    "OD": {
        "symbol": "\\#",
        "description": "Digipeater, green star",
        "overlay": True,
    },
    "OE": {"symbol": "\\$", "description": "Bank or ATM"},
    "OG": {
        "symbol": "\\&",
        "description": "Gateway station",
        "overlay": True,
    },
    "OH": {"symbol": "\\'", "description": "Crash / incident site"},
    "OI": {"symbol": "\\(", "description": "Cloudy"},
    "OJ": {"symbol": "\\)", "description": "Firenet MEO, MODIS Earth Observation"},
    "OK": {"symbol": "\\*", "description": "Snow"},
    "OL": {"symbol": "\\+", "description": "Church"},
    "OM": {"symbol": "\\,", "description": "Girl Scouts"},
    "ON": {"symbol": "\\-", "description": "House, HF antenna"},
    "OO": {"symbol": "\\.", "description": "Ambiguous, question mark inside circle"},
    "OP": {"symbol": "\\/", "description": "Waypoint destination"},
    "P0": {"symbol": "/0", "description": "Numbered circle: 0"},
    "P1": {"symbol": "/1", "description": "Numbered circle: 1"},
    "P2": {"symbol": "/2", "description": "Numbered circle: 2"},
    "P3": {"symbol": "/3", "description": "Numbered circle: 3"},
    "P4": {"symbol": "/4", "description": "Numbered circle: 4"},
    "P5": {"symbol": "/5", "description": "Numbered circle: 5"},
    "P6": {"symbol": "/6", "description": "Numbered circle: 6"},
    "P7": {"symbol": "/7", "description": "Numbered circle: 7"},
    "P8": {"symbol": "/8", "description": "Numbered circle: 8"},
    "P9": {"symbol": "/9", "description": "Numbered circle: 9"},
    "PA": {"symbol": "/A", "description": "Aid station"},
    "PB": {"symbol": "/B", "description": "BBS"},
    "PC": {"symbol": "/C", "description": "Canoe"},
    "PE": {"symbol": "/E", "description": "Eyeball"},
    "PF": {"symbol": "/F", "description": "Farm vehicle, tractor"},
    "PG": {"symbol": "/G", "description": "Grid square, 3 by 3"},
    "PH": {"symbol": "/H", "description": "Hotel"},
    "PI": {"symbol": "/I", "description": "TCP/IP network station"},
    "PK": {"symbol": "/K", "description": "School"},
    "PL": {"symbol": "/L", "description": "PC user"},
    "PM": {"symbol": "/M", "description": "Mac apple"},
    "PN": {"symbol": "/N", "description": "NTS station"},
    "PO": {"symbol": "/O", "description": "Balloon"},
    "PP": {"symbol": "/P", "description": "Police car"},
    "PR": {"symbol": "/R", "description": "Recreational vehicle"},
    "PS": {"symbol": "/S", "description": "Space Shuttle"},
    "PT": {"symbol": "/T", "description": "SSTV"},
    "PU": {"symbol": "/U", "description": "Bus"},
    "PV": {"symbol": "/V", "description": "ATV, Amateur Television"},
    "PW": {"symbol": "/W", "description": "Weather service site"},
    "PX": {"symbol": "/X", "description": "Helicopter"},
    "PY": {"symbol": "/Y", "description": "Sailboat"},
    "PZ": {"symbol": "/Z", "description": "Windows flag"},
    "Q1": {"symbol": "\\{", "description": "Fog"},
    "SA": {
        "symbol": "\\a",
        "description": "Red diamond",
        "overlay": True,
    },
    "SB": {"symbol": "\\b", "description": "Blowing dust, sand"},
    "SC": {
        "symbol": "\\c",
        "description": "CD triangle, RACES, CERTS, SATERN",
        "overlay": True,
    },
    "SD": {"symbol": "\\d", "description": "DX spot"},
    "SE": {"symbol": "\\e", "description": "Sleet"},
    "SF": {"symbol": "\\f", "description": "Funnel cloud"},
    "SG": {"symbol": "\\g", "description": "Gale, two red flags"},
    "SH": {"symbol": "\\h", "description": "Store"},
    "SI": {
        "symbol": "\\i",
        "description": "Black box, point of interest",
        "overlay": True,
    },
    "SJ": {"symbol": "\\j", "description": "Work zone, excavating machine"},
    "SK": {"symbol": "\\k", "description": "SUV, ATV"},
    "SM": {"symbol": "\\m", "description": "Value sign, 3 digit display"},
    "SN": {
        "symbol": "\\n",
        "description": "Red triangle",
        "overlay": True,
    },
    "SO": {"symbol": "\\o", "description": "Small circle"},
    "SP": {"symbol": "\\p", "description": "Partly cloudy"},
    "SR": {"symbol": "\\r", "description": "Restrooms"},
    "SS": {
        "symbol": "\\s",
        "description": "Ship, boat",
        "overlay": True,
    },
    "ST": {"symbol": "\\t", "description": "Tornado"},
    "SU": {
        "symbol": "\\u",
        "description": "Truck",
        "overlay": True,
    },
    "SV": {
        "symbol": "\\v",
        "description": "Van",
        "overlay": True,
    },
    "SW": {"symbol": "\\w", "description": "Flooding"},
    "SY": {"symbol": "\\y", "description": "Skywarn"},
    "SZ": {"symbol": "\\z", "description": "Shelter"},
}


APRS_OVERLAYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_symbol_code(icon: str | None) -> str | None:
    "Convert a tocall-formatted icon to a symbol table and symbol code, pair."

    if icon is None:
        return None

    assert icon is not None

    icon = icon.upper().strip()
    overlay = None

    if len(icon) < 2 or len(icon) > 3:
        return None

    if len(icon) == 3:
        overlay = icon[2]
        icon = icon[0:2]

    if icon not in APRS_SYMBOLS:
        return None

    # Invalid overlay
    if overlay is not None and overlay not in APRS_OVERLAYS:
        overlay = None

    result = APRS_SYMBOLS[icon]["symbol"]
    if overlay is not None and APRS_SYMBOLS[icon].get("overlay") == True:
        result = overlay + result[1:]

    assert len(result) == 2
    return result
