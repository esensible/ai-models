#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Grab one JPEG frame from a Bambu P1S chamber camera (LAN, port 6000).

Bambu's P1-series camera is a proprietary TLS stream, not RTSP:
  1. TLS connect to <host>:6000
  2. send an 80-byte auth packet (16-byte header + 32-byte user + 32-byte access code)
  3. read frames: 16-byte header whose first 4 bytes (LE) = JPEG byte length, then the JPEG

Usage:
    uv run bambu/bambu_camera.py --out bambu/snapshot.jpg
Creds default to env (BAMBU_HOST / BAMBU_CODE), so run.sh-style sourcing works.
"""
import argparse
import os
import socket
import ssl
import struct
import sys


def build_auth(username: str, access_code: str) -> bytes:
    d = bytearray()
    d += struct.pack("<I", 0x40)
    d += struct.pack("<I", 0x3000)
    d += struct.pack("<I", 0)
    d += struct.pack("<I", 0)
    d += username.encode("ascii")[:32].ljust(32, b"\x00")
    d += access_code.encode("ascii")[:32].ljust(32, b"\x00")
    return bytes(d)


def recvall(sock, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("BAMBU_HOST"))
    ap.add_argument("--port", type=int, default=6000)
    ap.add_argument("--code", default=os.environ.get("BAMBU_CODE"))
    ap.add_argument("--out", default="bambu/snapshot.jpg")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()
    if not args.host or not args.code:
        print("ERROR: need --host (or BAMBU_HOST) and --code (or BAMBU_CODE).", file=sys.stderr)
        return 2

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Connecting to camera {args.host}:{args.port} (TLS)...")
    raw = socket.create_connection((args.host, args.port), timeout=args.timeout)
    sock = ctx.wrap_socket(raw, server_hostname=args.host)
    sock.settimeout(args.timeout)
    sock.sendall(build_auth("bblp", args.code))

    header = recvall(sock, 16)
    if len(header) != 16:
        print(f"Bad/short header ({len(header)} bytes) — auth rejected?", file=sys.stderr)
        return 1
    payload_size = int.from_bytes(header[0:4], "little")
    if not (0 < payload_size < 5_000_000):
        print(f"Implausible frame size {payload_size} — protocol mismatch?", file=sys.stderr)
        return 1
    img = recvall(sock, payload_size)
    sock.close()

    if img[:2] != b"\xff\xd8" or img[-2:] != b"\xff\xd9":
        print(f"Got {len(img)} bytes but not a clean JPEG (start={img[:2].hex()} end={img[-2:].hex()})",
              file=sys.stderr)
        # still write it for inspection
    with open(args.out, "wb") as f:
        f.write(img)
    print(f"Saved {len(img)} bytes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
