#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Print one-shot Bambu readings as JSON: {"nozzle":x,"bed":y,"state":"IDLE"}.

Used to gate a pre-warm-then-print flow: with the hotend unpowered, the nozzle
sensor tracks chamber air temperature. Creds from BAMBU_* env.
"""
import json, os, ssl, sys, time
import paho.mqtt.client as mqtt

host = os.environ["BAMBU_HOST"]; code = os.environ["BAMBU_CODE"]; serial = os.environ["BAMBU_SERIAL"]
state = {}

def on_connect(c, u, f, rc, p=None):
    c.subscribe(f"device/{serial}/report")
    c.publish(f"device/{serial}/request", json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))

def on_message(c, u, msg):
    try:
        d = json.loads(msg.payload.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return
    if "print" in d:
        state.update(d["print"])

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="emily-nozzle")
c.username_pw_set("bblp", code)
c.tls_set(cert_reqs=ssl.CERT_NONE); c.tls_insecure_set(True)
c.on_connect = on_connect; c.on_message = on_message
c.connect(host, 8883, keepalive=30)
c.loop_start()
deadline = time.time() + 12
while time.time() < deadline and "nozzle_temper" not in state:
    time.sleep(0.3)
c.loop_stop(); c.disconnect()

if "nozzle_temper" not in state:
    sys.exit("no status")
print(json.dumps({
    "nozzle": state.get("nozzle_temper"),
    "bed": state.get("bed_temper"),
    "bed_target": state.get("bed_target_temper"),
    "state": state.get("gcode_state"),
}))
