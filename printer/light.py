#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Turn the Bambu P1S chamber light on/off over LAN MQTT.

  uv run bambu/light.py off
  uv run bambu/light.py on

Creds from BAMBU_* env. The chamber light is a `system/ledctrl` command, not gcode.
"""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt

mode = (sys.argv[1].lower() if len(sys.argv) > 1 else "off")
if mode not in ("on", "off"):
    sys.exit("usage: light.py on|off")

host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
if not (host and code and serial):
    sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL")

cmd = {"system": {"sequence_id": "0", "command": "ledctrl", "led_node": "chamber_light",
                  "led_mode": mode, "led_on_time": 500, "led_off_time": 500,
                  "loop_times": 0, "interval_time": 0}}

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu-light")
c.username_pw_set("bblp", code)
c.tls_set(cert_reqs=ssl.CERT_NONE)
c.tls_insecure_set(True)
c.connect(host, 8883, keepalive=30)
c.loop_start()
time.sleep(1)
info = c.publish(f"device/{serial}/request", json.dumps(cmd))
info.wait_for_publish(10)
time.sleep(2)
c.loop_stop(); c.disconnect()
print(f"chamber light -> {mode}")
