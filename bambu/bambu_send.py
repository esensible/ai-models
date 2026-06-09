#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Upload a file to the Bambu P1S over implicit FTPS (port 990), and (optionally)
trigger a LAN print of an already-sliced .gcode.3mf via MQTT.

    uv run bambu/bambu_send.py upload out/foo.gcode.3mf            # just upload
    uv run bambu/bambu_send.py list                                # list printer storage
    # printing is gated behind --confirm and a real sliced file (not done blindly):
    # uv run bambu/bambu_send.py print foo.gcode.3mf --confirm

Creds from env (BAMBU_HOST / BAMBU_CODE / BAMBU_SERIAL); run via the wrapper that
sources bambu/printer.env.
"""
import argparse
import ftplib
import os
import socket
import ssl
import sys


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """Bambu uses IMPLICIT FTPS on 990 (TLS from the first byte)."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


def connect(host, code):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = ImplicitFTP_TLS(context=ctx)
    ftp.connect(host, 990, timeout=15)
    ftp.login("bblp", code)
    ftp.prot_p()
    return ftp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["upload", "list", "delete", "print"])
    ap.add_argument("path", nargs="?", help="local file (upload) or remote name (list/delete/print)")
    ap.add_argument("--remote", help="remote filename (default: basename of local path)")
    ap.add_argument("--host", default=os.environ.get("BAMBU_HOST"))
    ap.add_argument("--code", default=os.environ.get("BAMBU_CODE"))
    ap.add_argument("--confirm", action="store_true", help="required to actually start a print")
    args = ap.parse_args()
    if not args.host or not args.code:
        print("ERROR: need BAMBU_HOST and BAMBU_CODE.", file=sys.stderr)
        return 2

    ftp = connect(args.host, args.code)
    try:
        if args.action == "list":
            print(f"--- {args.host} storage ---")
            ftp.retrlines("LIST")
        elif args.action == "upload":
            if not args.path or not os.path.isfile(args.path):
                print("ERROR: give an existing local file to upload.", file=sys.stderr)
                return 2
            remote = args.remote or os.path.basename(args.path)
            local_size = os.path.getsize(args.path)
            try:
                with open(args.path, "rb") as f:
                    ftp.storbinary(f"STOR {remote}", f)
            except (socket.timeout, ssl.SSLError, OSError) as e:
                # Bambu's FTPS server doesn't do a clean TLS shutdown on the data
                # channel — the transfer completes but teardown can time out. Verify by size.
                print(f"(note: noisy teardown ignored: {type(e).__name__})", file=sys.stderr)
            try:
                remote_size = ftp.size(remote)
            except Exception:
                remote_size = None
            ok = remote_size == local_size
            print(f"uploaded {args.path} -> {remote} "
                  f"({remote_size}/{local_size} bytes on printer) {'OK' if ok else '?? size mismatch'}")
        elif args.action == "delete":
            ftp.delete(args.path)
            print(f"deleted {args.path}")
        elif args.action == "print":
            # Deliberately NOT firing an MQTT print without a real sliced file + explicit confirm.
            print("print: not yet implemented — needs a sliced .gcode.3mf and the MQTT", file=sys.stderr)
            print("project_file command. Will wire once slicing is solved.", file=sys.stderr)
            return 3
    finally:
        try:
            ftp.quit()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
