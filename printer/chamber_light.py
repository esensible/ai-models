#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Toggle the P1S chamber light over LAN MQTT (system.ledctrl).

    ./printer/light.sh on|off        # or:
    BAMBU_HOST=.. BAMBU_CODE=.. BAMBU_SERIAL=.. uv run printer/chamber_light.py off

The light is NOT controllable via gcode; it needs this MQTT system command.
"""
import json
import os
import ssl
import sys
import time

import paho.mqtt.client as mqtt

host = os.environ.get("BAMBU_HOST")
code = os.environ.get("BAMBU_CODE")
serial = os.environ.get("BAMBU_SERIAL")
mode = sys.argv[1] if len(sys.argv) > 1 else "on"
if not host or not code or not serial or mode not in ("on", "off"):
    sys.exit("usage: chamber_light.py on|off  (needs BAMBU_HOST/CODE/SERIAL)")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="light-ctl")
c.username_pw_set("bblp", code)
c.tls_set(cert_reqs=ssl.CERT_NONE)
c.tls_insecure_set(True)
c.connect(host, 8883, keepalive=30)
c.loop_start()
time.sleep(1)
payload = {"system": {"sequence_id": "0", "command": "ledctrl",
                      "led_node": "chamber_light", "led_mode": mode,
                      "led_on_time": 500, "led_off_time": 500,
                      "loop_times": 0, "interval_time": 0}}
c.publish(f"device/{serial}/request", json.dumps(payload))
time.sleep(1)
c.loop_stop()
c.disconnect()
print(f"chamber light -> {mode}")
