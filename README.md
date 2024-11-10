# aprstastic

[![PyPI - Version](https://img.shields.io/pypi/v/aprstastic.svg)](https://pypi.org/project/aprstastic)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aprstastic.svg)](https://pypi.org/project/aprstastic)

---

> [!WARNING]
> Legal operation of this software requires an amateur radio license and a valid call sign.

> [!NOTE]
> Star this repo to follow our progress! This code is under active development, and contributions are both welcomed and appreciated. See [CONTRIBUTING.md](https://github.com/afourney/aprstastic/blob/main/CONTRIBUTING.md) for details.

## New!

:fire: 2-minute [YouTube demo](https://www.youtube.com/watch?v=qUvpZUwl-cY)

:fire: Over-the-air discovery and registration now supported. See image below.

:fire: Call sign registrations are now (optionally) beaconed to [MESHID-01](https://aprs.fi/?c=message&call=MESHID-01) to facilitate a global roaming profile.

## Introduction

`aprstastic` is a bidirectional Meshtastic APRS gateway for Meshtastic users **with amateur radio licenses**. It runs on stock Meshtastic devices (LongFast, 915MHz, etc.), allowing you to participate and extend the public network, while using pre-registered associations between Meshtastic device IDs and amateur radio call signs to _bidirectionally_ gate APRS packets in a way that is compliant with FCC regulations. To this end, operation requires at least two Meshtastic devices: one to serve as the gateway, and the others are the clients. The following image demonstrates how operators can register with the gateway (and the broader global network, if registration beaconing is enabled):

![Example aprstastic registration flow. Start by sending 'aprs?' to any public channel. Wait for a direct message. Reply with !register CALLSIGN-SSID.](https://github.com/afourney/aprstastic/blob/main/imgs/flow.png "Example aprstastic registration flow.")

In this scenario, direct messages to the gateway will be forwarded to APRS with the "from" call sign `KK7CMT-8`. Likewise, APRS messages addressed to `KK7CMT-8` will be routed to the originating/registered Meshtastic device via direct message. If registration beaconing is enabled, registration will also trigger a one-time APRS broadcast of the device-id to call sign mapping, allowing all other participating `aprstastic` gateways to learn the association. This enables devices to roam between participating gateways.

These interactions are demonstrated in the following YouTube video [https://www.youtube.com/watch?v=qUvpZUwl-cY](https://www.youtube.com/watch?v=qUvpZUwl-cY)

Each gateway mimics an iGate, and can support multiple Meshtastic users, as long as their call signs and devices are pre-registered.

## Special Commands

Various special commands can be issued by sending direct Meshtastic messages to the gateway. The following commands are currently supported.

**Register a device:**

Use the following command to register a Meshtastic device to a call sign, replacing `<YOUR_CALLSIGN>` appropriately:

```
!register <YOUR_CALLSIGN>
```

e.g.,

```
!register N0CALL-1
```

**Unregister a device:**

Use the following command to unregister a Meshtastic device AND call sign.

```
!unregister
```

**Print version information:**

Use the following command to print the gateway's info and version.

```
!version
```

## Installation, Configuration, and Running

```console
pip install aprstastic
```

```console
python -m aprstastic
```

The first time aprstastic runs, it will create a sample `aprstastic.yaml` file. **Edit the sample**, then run it again.

```console
nano ~/.config/aprstastic/aprstastic.yaml
python -m aprstastic
```

## Addressing APRS messages

How does the gateway know the addressee ("to" address) of APRS packets when all Meshtastic messages are addressed to the gateway device?

To address this, we adopt the "CALLSIGN: " convention. Messages should start with the addressee's call sign, followed by a colon. **If this is omitted, then the call sign of the addressee is taken to be that of the previous message (i.e., to respond to the previously received message).**

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

## Compliance

aprstastic only allows messages to transit if they are found in the client device-to-callsign mapping, and are thus attributable to a licensed operator. Random messages published on channels like LongFast, or from other devices do not qualify. All messages are unencrypted before they leave Meshtastic, so all APRS traffic is clear text.

## A Note for APRS-IS Admins

Instances of the aprstastic gateway identify themselves to the APRS-IS level 2 servers with the software version number `APZMAG`. In accordance to the [Protocol Reference](http://www.aprs.org/doc/APRS101.PDF), `APZ` designates an experimental application in development. In this case, `MAG` is short for 'Meshtastic-APRS Gateway'.

## License

`aprstastic` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
