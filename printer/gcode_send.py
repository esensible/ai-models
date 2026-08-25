#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Send raw G-code line(s) to a Bambu P1S over LAN MQTT (gcode_line command).

  uv run bambu/gcode_send.py "G91" "G1 Z-5 F600" "G90"

Each arg is one G-code line. LAN only; creds from BAMBU_* env.
NOTE: on the P1S the bed moves in Z. LOWER Z = bed UP (toward nozzle/camera),
HIGHER Z = bed DOWN. Move in small steps with eyes on the camera.
"""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt

host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
if not (host and code and serial):
    sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL")
if len(sys.argv) < 2:
    sys.exit("usage: gcode_send.py 'G-code line' ['line2' ...]")

param = "\n".join(sys.argv[1:]) + "\n"
cmd = {"print": {"command": "gcode_line", "param": param, "sequence_id": "0"}}

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu-gcode")
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
print("sent:\n" + param)
