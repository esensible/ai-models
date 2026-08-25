#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Resume a paused print on a Bambu P1S over LAN MQTT (e.g. after a filament swap).

  uv run bambu/resume_print.py

Creds from BAMBU_* env. Only meaningful when the printer is in a PAUSE state.
"""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt

host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
if not (host and code and serial):
    sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL")

cmd = {"print": {"command": "resume", "param": "", "sequence_id": "0"}}

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu-resume")
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
print("RESUME command sent.")
