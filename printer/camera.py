#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Grab a single JPEG frame from a Bambu P1S chamber camera (LAN only).

The P1 series exposes the camera as a TLS socket on :6000. You send an 80-byte
auth packet (header + 'bblp' + access code, each padded to 32B), then the printer
streams frames: a 16-byte header whose first uint32 is the JPEG length, followed
by that many bytes of JPEG.

  uv run bambu/camera.py out.jpg     # via BAMBU_HOST / BAMBU_CODE env

Importable: grab(host, code, out) -> bytes_written.
"""
import os, socket, ssl, struct, sys


def grab(host, code, out):
    auth = bytearray()
    auth += struct.pack("<IIII", 0x40, 0x3000, 0, 0)
    auth += b"bblp".ljust(32, b"\x00")
    auth += code.encode("ascii").ljust(32, b"\x00")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, 6000), timeout=10) as sk:
        with ctx.wrap_socket(sk, server_hostname=host) as ss:
            ss.write(auth)
            hdr = b""
            while len(hdr) < 16:
                chunk = ss.recv(16 - len(hdr))
                if not chunk:
                    raise RuntimeError("no data (bad access code?)")
                hdr += chunk
            size = struct.unpack("<I", hdr[0:4])[0]
            if not (0 < size < 5_000_000):
                raise RuntimeError(f"implausible frame size {size}")
            img = b""
            while len(img) < size:
                chunk = ss.recv(min(8192, size - len(img)))
                if not chunk:
                    break
                img += chunk

    if not (img[:2] == b"\xff\xd8" and img[-2:] == b"\xff\xd9"):
        print(f"WARN: frame not a clean JPEG (len={len(img)}, "
              f"start={img[:2].hex()}, end={img[-2:].hex()})", file=sys.stderr)
    with open(out, "wb") as fh:
        fh.write(img)
    return len(img)


if __name__ == "__main__":
    host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE")
    out = sys.argv[1] if len(sys.argv) > 1 else "chamber.jpg"
    if not (host and code):
        sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE")
    n = grab(host, code, out)
    print(f"saved {n} bytes -> {out}")
