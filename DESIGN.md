# Design Document
### Really, more of scratchpad of ideas right now

### Position Reports
Most APRS traffic consists of position beaconing. Meshtastic devices are well-suited to this. While the `aprstastic` Gateway currently operates via direct messages, it could watch for Meshtastic beacons on channels (e.g, `LongFast`), and gate them to APRS if their originator is in the `licensed_operator` list, and their call sign is known. Certainly some Meshtastic channels are intentionally private -- and even if public -- not all operators will desire this forwarding. Consider configuration options such as a setting in the licensed\_operator record (e.g., ``"!abc12345" = (call_sign="NOCALL", gate_positions=False)``). The Gateway configuration file could also include options for what channels to listen to, and we might opt to ignore channels with non-default keys.

### Weather Reports
Some Meshtastic devices have environment sensors. These have direct analogs on APRS and can be gated following a similar protocol to the above-mentioned position reports.

### Central Registry
A limitation of the current design is that the `licensed_operator` list is part of the configuration, and must be set and updated by all gateway administrators. If there was a central registry maintaining this mapping, then gateways could subscribe or download it, allowing for roaming. This could be as simple as a Google Forms sheet, or perhaps submitting PRs to a GitHub repo. It's possible APRS-IS could even be used for this, if there was a standard format of announcing your Meshtastic device.

### Discovery
Related to the above, how does one know if there is a gateway operating in range of their radio? I propose two options:
- Operators could send a query message to a channel (e.g., "aprs?" on LongFast), to which Gateways would reply
- If operators are already in the `licensed_operator` list, the gateway might send a direct message introducing itself the first time the Gateway observes *any* message from the device (telemetry or otherwise), and then perhaps once a day afterward, until receiving *any* direct text message from the device (e.g., "stop", or even any APRS-destined message)
