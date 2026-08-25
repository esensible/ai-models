#!/usr/bin/env python3
"""Translate a binary STL into P1S plate coordinates (use with ARRANGE=0).

Plate frame: front-left origin, X/Y in 0..256, Y+ = toward the BACK
(away from the door). zmin always lands on 0.

  place_stl.py in.stl out.stl --center X Y        # bbox centre at (X, Y)
  place_stl.py in.stl out.stl --back-ymax Y       # X-centred, bbox ymax at Y
                                                  # (leave room for the brim:
                                                  #  Y <= 256 - brim - ~3)
"""
import argparse
import struct
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--center", nargs=2, type=float, metavar=("X", "Y"))
    g.add_argument("--back-ymax", type=float, metavar="Y")
    args = ap.parse_args()

    with open(args.src, "rb") as fh:
        data = bytearray(fh.read())
    if data[:5] == b"solid" and b"facet" in data[:200]:
        sys.exit("ASCII STL not supported (export binary)")
    (ntri,) = struct.unpack_from("<I", data, 80)
    if 84 + ntri * 50 != len(data):
        sys.exit("not a plain binary STL")

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for i in range(ntri):
        base = 84 + i * 50 + 12          # skip the normal vector
        for v in range(3):
            x, y, z = struct.unpack_from("<3f", data, base + v * 12)
            for k, c in enumerate((x, y, z)):
                lo[k] = min(lo[k], c)
                hi[k] = max(hi[k], c)

    if args.center:
        dx = args.center[0] - (lo[0] + hi[0]) / 2
        dy = args.center[1] - (lo[1] + hi[1]) / 2
    else:
        dx = 128.0 - (lo[0] + hi[0]) / 2
        dy = args.back_ymax - hi[1]
    dz = -lo[2]

    for i in range(ntri):
        base = 84 + i * 50 + 12
        for v in range(3):
            x, y, z = struct.unpack_from("<3f", data, base + v * 12)
            struct.pack_into("<3f", data, base + v * 12, x + dx, y + dy, z + dz)
    with open(args.dst, "wb") as fh:
        fh.write(data)

    print(f"bbox {hi[0]-lo[0]:.2f} x {hi[1]-lo[1]:.2f} x {hi[2]-lo[2]:.2f}  "
          f"placed x {lo[0]+dx:.2f}..{hi[0]+dx:.2f}  y {lo[1]+dy:.2f}..{hi[1]+dy:.2f}  "
          f"z 0..{hi[2]-lo[2]:.2f} -> {args.dst}")


if __name__ == "__main__":
    main()
