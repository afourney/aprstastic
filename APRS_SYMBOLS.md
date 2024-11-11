# APRS Symbols

When registering a call sign with the Gateway, it is often desirable to also
set the symbol that will represent the device on various applications and maps
(e.g., [APRS.fi](https://https://aprs.fi/).

Each symbol is represented by a 2- or 3-letter code, as outlined in the tables below.

If the symbol is simple, it will use a two letter code, as listed in the [first table](#simple-symbols).
For example, `HS` will map to `Human`. You can set this symbol when registering
(or re-registering) with the gateway. E.g.,

```
!register <call sign> <symbol>
```

```
!register N0CALL-1 HS
```

You can also set various composite overlay symbols with a 3-letter code, as per the
[second table](#overlay-symbols) below. In this case, the first two letters define the symbol, and the
third letter defines the overlay (must be A-Z or 0-9). For example 'OGM' represents
a gateway station (diamond) with the letter M overlaid.

```
!register <call sign> <symbol_and_overlay>
```

```
!register N0CALL-1 OGM
```

## Simple Symbols

| code | description                            |
| ---- | -------------------------------------- |
| A8   | 802.11 WiFi or other network node      |
| A9   | Gas station                            |
| AB   | Blowing snow                           |
| AC   | Coast Guard                            |
| AD   | Drizzling rain                         |
| AE   | Smoke, Chimney                         |
| AF   | Freezing rain                          |
| AG   | Snow shower                            |
| AH   | Haze                                   |
| AI   | Rain shower                            |
| AJ   | Lightning                              |
| AK   | Kenwood HT                             |
| AL   | Lighthouse                             |
| AN   | Navigation buoy                        |
| AO   | Rocket                                 |
| AP   | Parking                                |
| AQ   | Earthquake                             |
| AR   | Restaurant                             |
| AS   | Satellite                              |
| AT   | Thunderstorm                           |
| AU   | Sunny                                  |
| AV   | VORTAC, Navigational aid               |
| AX   | Pharmacy                               |
| BB   | Police station                         |
| BD   | Digipeater                             |
| BE   | Telephone                              |
| BF   | DX cluster                             |
| BG   | HF gateway                             |
| BH   | Small aircraft                         |
| BI   | Mobile satellite station               |
| BJ   | Wheelchair, handicapped                |
| BK   | Snowmobile                             |
| BL   | Red Cross                              |
| BM   | Boy Scouts                             |
| BN   | House                                  |
| BO   | Red X                                  |
| BP   | Red dot                                |
| DS   | Wall Cloud                             |
| DX   | Rain                                   |
| HS   | Human                                  |
| HT   | DF triangle                            |
| HU   | Mailbox, post office                   |
| HV   | Large aircraft                         |
| HW   | Weather station                        |
| HX   | Satellite dish antenna                 |
| LA   | Ambulance                              |
| LB   | Bicycle                                |
| LC   | Incident command post                  |
| LD   | Fire station                           |
| LE   | Horse, equestrian                      |
| LF   | Fire truck                             |
| LG   | Glider                                 |
| LH   | Hospital                               |
| LI   | IOTA, islands on the air               |
| LJ   | Jeep                                   |
| LK   | Truck                                  |
| LL   | Laptop                                 |
| LM   | Mic-E repeater                         |
| LN   | Node, black bulls-eye                  |
| LO   | Emergency operations center            |
| LP   | Dog                                    |
| LQ   | Grid square, 2 by 2                    |
| LR   | Repeater tower                         |
| LS   | Ship, power boat                       |
| LT   | Truck stop                             |
| LU   | Semi-trailer truck, 18-wheeler         |
| LV   | Van                                    |
| LW   | Water station                          |
| LX   | X / Unix                               |
| LY   | House, yagi antenna                    |
| LZ   | Shelter                                |
| MR   | Fire                                   |
| MS   | Campground, tent                       |
| MT   | Motorcycle                             |
| MU   | Railroad engine                        |
| MV   | Car                                    |
| MW   | File server                            |
| MX   | Hurricane predicted path               |
| NR   | Hail                                   |
| NS   | Park, picnic area                      |
| NT   | Advisory, single red flag              |
| NW   | Info kiosk                             |
| NX   | Hurricane, Tropical storm              |
| OB   | Emergency                              |
| OE   | Bank or ATM                            |
| OH   | Crash / incident site                  |
| OI   | Cloudy                                 |
| OJ   | Firenet MEO, MODIS Earth Observation   |
| OK   | Snow                                   |
| OL   | Church                                 |
| OM   | Girl Scouts                            |
| ON   | House, HF antenna                      |
| OO   | Ambiguous, question mark inside circle |
| OP   | Waypoint destination                   |
| P0   | Numbered circle: 0                     |
| P1   | Numbered circle: 1                     |
| P2   | Numbered circle: 2                     |
| P3   | Numbered circle: 3                     |
| P4   | Numbered circle: 4                     |
| P5   | Numbered circle: 5                     |
| P6   | Numbered circle: 6                     |
| P7   | Numbered circle: 7                     |
| P8   | Numbered circle: 8                     |
| P9   | Numbered circle: 9                     |
| PA   | Aid station                            |
| PB   | BBS                                    |
| PC   | Canoe                                  |
| PE   | Eyeball                                |
| PF   | Farm vehicle, tractor                  |
| PG   | Grid square, 3 by 3                    |
| PH   | Hotel                                  |
| PI   | TCP/IP network station                 |
| PK   | School                                 |
| PL   | PC user                                |
| PM   | Mac apple                              |
| PN   | NTS station                            |
| PO   | Balloon                                |
| PP   | Police car                             |
| PR   | Recreational vehicle                   |
| PS   | Space Shuttle                          |
| PT   | SSTV                                   |
| PU   | Bus                                    |
| PV   | ATV, Amateur Television                |
| PW   | Weather service site                   |
| PX   | Helicopter                             |
| PY   | Sailboat                               |
| PZ   | Windows flag                           |
| Q1   | Fog                                    |
| SB   | Blowing dust, sand                     |
| SD   | DX spot                                |
| SE   | Sleet                                  |
| SF   | Funnel cloud                           |
| SG   | Gale, two red flags                    |
| SH   | Store                                  |
| SJ   | Work zone, excavating machine          |
| SK   | SUV, ATV                               |
| SM   | Value sign, 3 digit display            |
| SO   | Small circle                           |
| SP   | Partly cloudy                          |
| SR   | Restrooms                              |
| ST   | Tornado                                |
| SW   | Flooding                               |
| SY   | Skywarn                                |
| SZ   | Shelter                                |

## Overlay Symbols

Replace the underscore '\_' with the desired overlay (must be A-Z, or 0-9).

| code | description                       |
| ---- | --------------------------------- |
| A0\_ | Circle, IRLP / Echolink/WIRES     |
| AA\_ | White box                         |
| AW\_ | NWS site                          |
| DV\_ | Aircraft                          |
| DW\_ | Weather site                      |
| NV\_ | Red car                           |
| OD\_ | Digipeater, green star            |
| OG\_ | Gateway station                   |
| SA\_ | Red diamond                       |
| SC\_ | CD triangle, RACES, CERTS, SATERN |
| SI\_ | Black box, point of interest      |
| SN\_ | Red triangle                      |
| SS\_ | Ship, boat                        |
| SU\_ | Truck                             |
| SV\_ | Van                               |
