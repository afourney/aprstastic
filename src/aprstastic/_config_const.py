DEFAULT_CONFIG_CONTENT = """# 
# APRSTASTIC CONFIGURATION FILE (version: 1)
# Be sure to at least modify 'call_sign' and 'aprsis_passcode'.
#


# Radio call sign of the gateway itself (analogy, iGate's call sign)
call_sign: N0CALL 


# APRS-IS passcode. Search Google for how to get this
aprsis_passcode: 12345 


# Only serial devices are supported right now. 
# If 'device' is null (or commented out), an attempt will be made to 
# detected it automatically.
meshtastic_interface: 
   type: serial
#  device: /dev/ttyACM0


# Beacon new registrations to APRS-IS to facilitate discovery
beacon_registrations: true 


# Where should logs be stored?
# If null, (or commented out), store logs in the `logs` dir, sibling to this file. 
#log_dir: null


# Where should data be stored?
# If null, (or commented out), store data in the `data` dir, sibling to this file. 
#data_dir: null
"""
