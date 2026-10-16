#!/usr/bin/env python3
"""Pre-print support/bridge audit for a sliced Orca gcode file.

Orca's "this object needs supports" warning is GUI-only -- the CLI emits
NOTHING (verified 2026-09-01), so a headless pipeline must derive the risk
itself from what the slicer bakes into the gcode:

  - ; FEATURE: Bridge        extrusions over air
  - ; FEATURE: Overhang wall steep wall segments
  - ; enable_support =       whether supports were generated

This tool reports, per layer height: bridge count, the LONGEST single
bridge line (the number that predicts sag/failure), and total bridged path;
plus overhang-wall totals and the support flag. Exit code 1 if any single
bridge line exceeds --max-bridge (default 20mm, user threshold 2026-09-01)
and supports are off, so wrapper scripts can gate on it.

  audit_gcode.py plate_1.gcode [--max-bridge 20]
"""
import argparse
import math
import re
import sys

Z_RE = re.compile(r"^; Z_HEIGHT: ([\d.]+)")
FEAT_RE = re.compile(r"^; FEATURE: (.+)")
MOVE_RE = re.compile(r"^G[01] ")
WORD_RE = re.compile(r"([XYE])(-?\d*\.?\d+)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gcode")
    ap.add_argument("--max-bridge", type=float, default=20.0,
                    help="longest acceptable single bridge line without supports")
    a = ap.parse_args()

    support = None
    z = 0.0
    feat = ""
    x = y = None
    bridges = {}     # z -> [count, max_line, total_len]
    overhang = {}    # z -> total_len
    with open(a.gcode, errors="replace") as fh:
        for line in fh:
            m = Z_RE.match(line)
            if m:
                z = float(m.group(1))
                continue
            m = FEAT_RE.match(line)
            if m:
                feat = m.group(1).strip()
                continue
            if line.startswith("; enable_support ="):
                support = line.split("=")[1].strip() == "1"
                continue
            if not MOVE_RE.match(line):
                continue
            words = dict(WORD_RE.findall(line))
            nx = float(words["X"]) if "X" in words else x
            ny = float(words["Y"]) if "Y" in words else y
            if x is not None and nx is not None and "E" in words and \
                    float(words["E"]) > 0:
                seg = math.hypot(nx - x, ny - y)
                if feat == "Bridge":
                    b = bridges.setdefault(z, [0, 0.0, 0.0])
                    b[0] += 1
                    b[1] = max(b[1], seg)
                    b[2] += seg
                elif feat.startswith("Overhang"):
                    overhang[z] = overhang.get(z, 0.0) + seg
            x, y = nx, ny

    print(f"supports enabled: {support}")
    worst = 0.0
    for zz in sorted(bridges):
        c, mx, tot = bridges[zz]
        worst = max(worst, mx)
        print(f"bridges @ z {zz:6.2f}: {c:4d} lines, longest {mx:6.1f}mm, "
              f"total {tot:7.0f}mm")
    for zz in sorted(overhang):
        print(f"overhang walls @ z {zz:6.2f}: total {overhang[zz]:.0f}mm")
    if not bridges:
        print("no bridge features")
    print(f"longest single bridge line: {worst:.1f}mm "
          f"(threshold {a.max_bridge}mm)")
    if worst > a.max_bridge and not support:
        print("VERDICT: bridges exceed threshold and supports are OFF -- "
              "flag to the user before printing")
        return 1
    print("VERDICT: within threshold (or supports enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
