# aprstastic

[![PyPI - Version](https://img.shields.io/pypi/v/aprstastic.svg)](https://pypi.org/project/aprstastic)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aprstastic.svg)](https://pypi.org/project/aprstastic)

-----

> [!WARNING]
> Legal operation of this software requires an amateur radio license and a valid call sign. 

> [!IMPORTANT]
> This is a minimum viable example of the concept of an APRS to Meshtastic gateway. The code is of poor quality, and not up to any standard, but it serves to prove the possibility. Star this repo for future updates -- I plan to build this concept out appropriately to a stable turnkey appliance.

## New!
:fire: 2-minute [YouTube demo](https://www.youtube.com/watch?v=qUvpZUwl-cY)
:fire: Send 'aprs?' on any public Meshtastic channel (e.g., LongFast), to query if a gateway is available in your area!
:fire: Design doc and future plans: [DESIGN.md](https://github.com/afourney/aprstastic/blob/main/DESIGN.md)

## Introduction
Here is a proof of concept of a Meshtastic to APRS gateway for Meshtastic users **with amateur radio licenses**. It runs on stock Meshtastic (915MHz, not HAM band or mode), but uses a pre-registered association between Meshtastic device MAC addresses and amateur radio callsign+SSID to keep things properly attributed and compliant with FCC regulations. To this end, operation requires at least two meshtastic devices: one to serve as the gateway, and the others are the clients. Each client is registered in the `config.yaml` as seen in the following example:

```yaml
licensed_operators:
  "!12345678": NOCALL-1
  "!87654321": NOCALL-2
  "!12121212": NOCALL-3
```

In this scenario, APRS messages addressed to the call sign `NOCALL-1` will be routed to the Meshtastic device `!12345678` (short name `5678`) via a Meshtastic direct message.

Likewise, if `!12345678` sends a private message to the gateway, it will be forwarded to APRS with the "from" call sign `NOCALL-1`. But, there is one wrinkle: How does the gateway know the addressee ("to" address) of this new APRS packet?

To address this, we adopt the "CALLSIGN: " convention. Messages should start with the addressee's call sign, followed by a colon. If this is omitted, then the call sign of the addressee is taken to be that of the previous message (i.e., to respond to the previously received message).

As an example, from Meshtastic you could interact with the Winlink gateway (WLNK-1) as follows:

```
WLNK-1: ?
```

The reply from Winlink would be:

```
NOCALL-1: SP, SMS, L, R#, K#, Y#, F#, P, G, A, I, PR, B (? + cmd for more)
```

You could then simply enter:

```
L
```

and it would assume a reply to `WLNK-1`, producing the following response:
   

```
NOCALL-1: 10/11/2024 23:52:30 No messages.
```

These interactions are demonstrated in the following YouTube video [https://www.youtube.com/watch?v=qUvpZUwl-cY](https://www.youtube.com/watch?v=qUvpZUwl-cY)

Each gateway mimics an iGate, and can support multiple Meshtastic users, as long as their call signs and devices are pre-registered.

## Compliance
aprstastic only allows messages to transit if they are found in the client device-to-callsign mapping, and are thus attributable to a licensed operator. Random messages published on channels like LongFast, or from other devices do not qualify. All messages are unencrypted before they leave Meshtastic, so all APRS traffic is clear text.


## Future Plans
The clear weakness of this gateway is the need to register devices in order for the call sign mapping to work. If every node administrator needs to manage this list, then the system will not scale (and maybe this is fine to control traffic). However, one compelling possibility is to create a central registry where, call signs can be registered to nodes, and the gateways could then subscribe to this list. This would allow a degree of roaming without much need for coordination.

Additional future plans include support for Meshtastic position beacons, and weather reports (both of which have analogs in APRS).

For more details see [DESIGN.md](https://github.com/afourney/aprstastic/blob/main/DESIGN.md)


## Installation

```console
pip install aprstastic
```

## Configuration
Copy `sample_config.yml` to `config.yml` and edit appropriately. Here is a sample:

```yml
gateway:
  call_sign: N0CALL           # Radio call sign of the gateway itself (analogy, iGate's call sign) 
  aprsis_passcode: 12345      # APRS-IS passcode. Search Google for how to get this
  meshtastic_interface:       # Only serial devices are supported right now
    type: serial
    device: /dev/ttyACM1      # Name of the serial device if more than one

licensed_operators:           # Mapping of Meshtastic device IDs to call signs
  "!12345678": NOCALL-1
  "!87654321": NOCALL-2
  "!12121212": NOCALL-3

```

## Running 
Execute the following command at the console.

```shell
python -m aprstastic
```

## License

`aprstastic` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
