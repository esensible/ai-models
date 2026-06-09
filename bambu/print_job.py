#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Send a sliced .gcode.3mf to a Bambu P1S over LAN and (optionally) start it.

LAN-only. Two phases, deliberately separable:
  upload   FTPS (implicit TLS, port 990, user 'bblp', pass = access code) -> SD root
  start    MQTT 'project_file' command referencing the uploaded file

  uv run bambu/print_job.py FILE.3mf            # upload + show status, DO NOT print
  uv run bambu/print_job.py FILE.3mf --print    # upload AND start the print
  uv run bambu/print_job.py --status            # dump filament/state and exit

Creds via env: BAMBU_HOST, BAMBU_CODE, BAMBU_SERIAL (loaded by bambu/run.sh).
"""
import argparse, ftplib, json, os, ssl, sys, time
import paho.mqtt.client as mqtt


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """ftplib speaks explicit FTPS; Bambu uses implicit TLS on :990."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value, server_hostname=self.host)
        self._sock = value

    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        # Bambu's FTPS server never replies to the TLS close_notify, so the
        # stock FTP_TLS.storbinary hangs on conn.unwrap() AFTER all data is sent.
        # Send the data, skip the unwrap, then read the server response.
        self.voidcmd("TYPE I")
        with self.transfercmd(cmd, rest) as conn:
            while True:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # deliberately NOT calling conn.unwrap()
        return self.voidresp()


def ftps_upload(host, code, local, remote):
    ctx = ssl._create_unverified_context()  # printer cert is self-signed
    ftp = ImplicitFTP_TLS(context=ctx)
    ftp.connect(host, 990, timeout=30)
    ftp.login("bblp", code)
    ftp.prot_p()
    size = os.path.getsize(local)
    with open(local, "rb") as fh:
        ftp.storbinary(f"STOR {remote}", fh)
    # verify it's there
    names = ftp.nlst()
    ftp.quit()
    return size, (remote in names or ("/" + remote) in names)


def mqtt_client(host, code):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bambu-send")
    c.username_pw_set("bblp", code)
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.connect(host, 8883, keepalive=30)
    return c


def get_status(host, code, serial, timeout=12):
    state = {}
    c = mqtt_client(host, code)

    def on_connect(cl, *_a, **_k):
        cl.subscribe(f"device/{serial}/report")
        cl.publish(f"device/{serial}/request",
                   json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))

    def on_message(cl, ud, msg):
        try:
            d = json.loads(msg.payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            return
        if "print" in d:
            state.update(d["print"])

    c.on_connect = on_connect
    c.on_message = on_message
    c.loop_start()
    time.sleep(timeout)
    c.loop_stop()
    c.disconnect()
    return state


def summarize_filament(p):
    out = []
    vt = p.get("vt_tray", {})
    if vt:
        out.append(f"external spool: type={vt.get('tray_type')!r} color=#{vt.get('tray_color')}")
    ams = p.get("ams", {})
    units = ams.get("ams", []) if isinstance(ams, dict) else []
    for u in units:
        for t in u.get("tray", []):
            if t.get("tray_type"):
                out.append(f"AMS[{u.get('id')}] tray{t.get('id')}: {t.get('tray_type')} #{t.get('tray_color')}")
    return out or ["(no filament info reported)"]


def start_print(host, code, serial, remote_3mf, name, use_ams=False, plate=1, bed="textured_plate"):
    cmd = {"print": {
        "command": "project_file",
        "param": f"Metadata/plate_{plate}.gcode",
        "url": f"file:///sdcard/{remote_3mf}",
        "subtask_name": name,
        "use_ams": use_ams,
        "timelapse": False,
        "bed_type": bed,
        "bed_leveling": True,
        "flow_cali": False,
        "vibration_cali": True,
        "layer_inspect": False,
        "task_id": "0", "subtask_id": "0", "project_id": "0", "profile_id": "0",
        "sequence_id": "0",
    }}
    c = mqtt_client(host, code)
    c.loop_start()
    time.sleep(1)
    info = c.publish(f"device/{serial}/request", json.dumps(cmd))
    info.wait_for_publish(10)
    time.sleep(2)
    c.loop_stop()
    c.disconnect()
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="local .gcode.3mf to send")
    ap.add_argument("--print", dest="do_print", action="store_true", help="start the print after upload")
    ap.add_argument("--status", action="store_true", help="just show printer filament/state")
    ap.add_argument("--remote", help="remote filename (default: basename of file)")
    ap.add_argument("--name", help="subtask name shown on printer")
    ap.add_argument("--use-ams", action="store_true")
    args = ap.parse_args()

    host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
    if not (host and code and serial):
        print("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL (via bambu/run.sh)", file=sys.stderr)
        return 2

    if args.status:
        p = get_status(host, code, serial)
        print(f"gcode_state: {p.get('gcode_state')}")
        print("filament:")
        for line in summarize_filament(p):
            print("  " + line)
        return 0

    if not args.file:
        print("ERROR: provide a .3mf file (or --status)", file=sys.stderr)
        return 2
    remote = args.remote or os.path.basename(args.file)
    name = args.name or os.path.splitext(remote)[0]

    print(f"[upload] {args.file} -> ftps://{host}:990/{remote}")
    size, ok = ftps_upload(host, code, args.file, remote)
    print(f"[upload] {size} bytes, present on printer: {ok}")
    if not ok:
        print("[upload] WARNING: file not confirmed in listing", file=sys.stderr)

    if not args.do_print:
        print("[done] uploaded only (no --print). Printer NOT started.")
        return 0

    print(f"[print] starting '{name}' from {remote} ...")
    cmd = start_print(host, code, serial, remote, name, use_ams=args.use_ams)
    print("[print] sent project_file command:")
    print(json.dumps(cmd, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
