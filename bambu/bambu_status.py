#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""
Bambu Lab (P1S) LAN status reader — run with uv.

    uv run bambu/bambu_status.py --host <printer-lan-ip> --code <access-code> --serial <serial>

Env vars also work: BAMBU_HOST, BAMBU_CODE, BAMBU_SERIAL.

Secrets live on the printer screen (LAN-only, never leaves your network):
    - Access code: Settings (gear) -> WLAN -> "Access Code" (8 digits)
    - Serial:      Settings -> Device  (or the sticker on the unit)
"""
import argparse
import json
import os
import ssl
import sys
import time

import paho.mqtt.client as mqtt


def summarize(p: dict) -> str:
    if not p:
        return ""
    g = p.get
    rows = [
        ("Nozzle", f"{g('nozzle_temper')}°C / {g('nozzle_target_temper')}°C", "nozzle_temper"),
        ("Bed", f"{g('bed_temper')}°C / {g('bed_target_temper')}°C", "bed_temper"),
        ("Chamber", f"{g('chamber_temper')}°C", "chamber_temper"),
        ("State", g("gcode_state"), "gcode_state"),
        ("Progress", f"{g('mc_percent')}%  (layer {g('layer_num')}/{g('total_layer_num')})", "mc_percent"),
        ("ETA", f"{g('mc_remaining_time')} min", "mc_remaining_time"),
        ("File", g("gcode_file"), "gcode_file"),
        ("WiFi", g("wifi_signal"), "wifi_signal"),
    ]
    return "\n".join(f"  {label:9} {val}" for label, val, key in rows if p.get(key) not in (None, ""))


def main() -> int:
    ap = argparse.ArgumentParser(description="Read Bambu P1S status over LAN MQTT.")
    ap.add_argument("--host", default=os.environ.get("BAMBU_HOST"))
    ap.add_argument("--port", type=int, default=8883)
    ap.add_argument("--code", default=os.environ.get("BAMBU_CODE"), help="8-digit LAN access code")
    ap.add_argument("--serial", default=os.environ.get("BAMBU_SERIAL"), help="printer serial")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--watch", action="store_true", help="keep streaming updates until Ctrl-C")
    ap.add_argument("--raw", action="store_true", help="dump raw JSON")
    args = ap.parse_args()

    if not args.host or not args.code or not args.serial:
        print("ERROR: need --host (BAMBU_HOST), --code (access code) and --serial. See file header.", file=sys.stderr)
        return 2

    state = {"print": {}}
    report_topic = f"device/{args.serial}/report"
    request_topic = f"device/{args.serial}/request"

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"Connect failed: {reason_code} (wrong access code?)", file=sys.stderr)
            return
        print("Connected + authenticated. ✓")
        client.subscribe(report_topic)
        client.publish(request_topic, json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))
        print(f"Subscribed to {report_topic}, requested full status...\n")

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            return
        if args.raw:
            print(json.dumps(data, indent=2))
        if "print" in data:
            state["print"].update(data["print"])
        out = summarize(state["print"])
        if out:
            if not args.raw:
                print("\033[2J\033[H", end="")
            print(f"=== Bambu P1S @ {args.host} ===")
            print(out)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu")
    client.username_pw_set("bblp", args.code)
    client.tls_set(cert_reqs=ssl.CERT_NONE)   # printer uses a self-signed cert
    client.tls_insecure_set(True)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.host, args.port, keepalive=30)
    except OSError as e:
        print(f"Could not reach {args.host}:{args.port} — {e}", file=sys.stderr)
        return 1

    client.loop_start()
    try:
        if args.watch:
            while True:
                time.sleep(0.5)
        else:
            time.sleep(args.timeout)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

    if not state["print"]:
        print("Connected but no status arrived. Printer asleep, or wrong serial?", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
