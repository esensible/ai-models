#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Stop (cancel) the current print on a Bambu P1S over LAN MQTT.

  uv run bambu/stop_print.py --confirm

Irreversible: ends the running print. Requires --confirm. Creds from BAMBU_* env.
"""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt

if "--confirm" not in sys.argv:
    sys.exit("refusing to stop without --confirm")

host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
if not (host and code and serial):
    sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL")

cmd = {"print": {"command": "stop", "param": "", "sequence_id": "0"}}

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu-stop")
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
print("STOP command sent.")
