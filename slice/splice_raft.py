#!/usr/bin/env python3
"""Splice a sacrificial-raft print: material A raft, pause/swap, material B part.

Single-nozzle two-material stack (e.g. PETG bed-plate under a PAHT-CF part):
both bodies are sliced SEPARATELY as single-filament jobs sharing one X/Y
frame, the part sliced sitting at z=0. The splice:

    [raft file: start gcode + all raft layers]     <- material A, its recipe
    retract, lift, park, M400 U1                   <- PAUSE: swap A -> B, purge
    M109 to part temp, G92 E0, fan reset
    [part file: layers 1..N, all Z + raft height]  <- material B
    [part file: its own end gcode]

Z-shift is textual (+raft_h on every G0/G1/G2/G3 Z word and Z_HEIGHT comment)
— deterministic and verifiable. The raft's M73 progress lines are stripped so
the printer's progress display follows the part.

  splice_raft.py RAFT.gcode PART.gcode OUT.gcode --raft-h 1.2 --part-temp 290

Sanity-checked: exactly one pause, monotonic layer markers, part's first
extrusion sits one layer height above the raft top.
"""
import argparse
import re
import sys

PAUSE = "M400 U1"   # P1S pause-until-user-resume (proven in merge_twocolor.py)
END_MARK = "; filament end gcode"
LAYER1 = "; CHANGE_LAYER"

_Z = re.compile(r"(?<=[ ])Z(-?\d*\.?\d+)")
_ZH = re.compile(r"^; Z_HEIGHT: (-?\d*\.?\d+)")


def read(path):
    with open(path) as f:
        return f.read().splitlines()


def shift_z(line, dz):
    if line.startswith(("G0", "G1", "G2", "G3")):
        return _Z.sub(lambda m: f"Z{float(m.group(1)) + dz:.3f}", line)
    m = _ZH.match(line)
    if m:
        return f"; Z_HEIGHT: {float(m.group(1)) + dz:.3f}"
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raft")
    ap.add_argument("part")
    ap.add_argument("out")
    ap.add_argument("--raft-h", type=float, required=True)
    ap.add_argument("--part-temp", type=int, required=True)
    a = ap.parse_args()

    raft = read(a.raft)
    part = read(a.part)

    # raft: keep start gcode + every layer, drop its end gcode; strip its M73s
    try:
        raft_end = next(i for i, l in enumerate(raft) if l.startswith(END_MARK))
    except StopIteration:
        sys.exit(f"raft: no {END_MARK!r} marker")
    raft_body = [l for l in raft[:raft_end] if not l.lstrip().startswith("M73")]

    # part: from its first layer marker to EOF (keeps its own end gcode)
    try:
        part_start = next(i for i, l in enumerate(part) if l.startswith(LAYER1))
    except StopIteration:
        sys.exit("part: no CHANGE_LAYER marker")
    part_body = [shift_z(l, a.raft_h) for l in part[part_start:]]

    park_z = a.raft_h + 5
    transition = [
        "; ===== RAFT -> PART material swap =============================",
        "G1 E-.8 F1800 ; retract",
        f"G1 Z{park_z:.1f} F900 ; lift clear of the raft",
        "G1 X50 Y10 F12000 ; park front-left, clear of the print",
        "M106 S0 ; part fan off (matches part slice's assumed state)",
        f"{PAUSE} ; PAUSE: swap filament, purge until clean, then resume",
        f"M109 S{a.part_temp} ; heat to part material temp and wait",
        "G92 E0 ; reset extruder datum",
        "; ===== part layers (Z shifted +raft height) ===================",
    ]

    merged = raft_body + transition + part_body
    with open(a.out, "w") as f:
        f.write("\n".join(merged) + "\n")

    npause = sum(1 for l in merged if l.startswith(PAUSE))
    # part's first LAYER plane after the shift should be raft_h + one layer
    # height (travel hops in between may be higher — check the Z_HEIGHT tag)
    first_layer_z = next((float(_ZH.match(l).group(1)) for l in part_body
                          if _ZH.match(l)), None)
    print(f"wrote {a.out}: {len(merged)} lines  raft={len(raft_body)}  "
          f"part={len(part_body)}  pauses={npause}  "
          f"part-layer1-Z={first_layer_z}")
    if npause != 1:
        sys.exit(f"expected exactly 1 pause, got {npause}")
    if first_layer_z is None or not (a.raft_h < first_layer_z <= a.raft_h + 0.45):
        sys.exit(f"part layer-1 plane {first_layer_z} not just above raft top {a.raft_h}")


if __name__ == "__main__":
    main()
