#!/usr/bin/env python3
"""Shift a single-material sliced job to print ON an already-printed raft.

Companion to splice_raft.py for the restart case: the raft (material A) is
already on the bed, firmly attached; only the part (material B, loaded) is to
be printed. The part is sliced normally at z=0 with its placement matching the
raft, then this tool lifts every layer move by the raft height, leaving the
machine start gcode (homing at the exposed steel strip behind the bed, purge
line at the bed front — both clear of a back-placed raft) untouched.

MUST be printed with bed leveling DISABLED (print_job.py --no-bed-leveling):
a G29 pass would probe the raft surface and corrupt the mesh. The printer
then reuses its last saved mesh — valid if the raft's own job leveled this
same plate.

  shift_over_raft.py IN.gcode OUT.gcode --raft-h 1.2 [--max-bed 70]

Checks: part layer-1 plane lands one layer height above the raft top; no
M140/M190 anywhere exceeds --max-bed (the raft must not be re-melted); the
start gcode's only bed-contact XY (Z-home, wipe, purge line) are outside the
raft's y-range is NOT verified here — that is a property of the stock P1S
start gcode, reviewed 2026-08-27.
"""
import argparse
import re
import sys

from splice_raft import LAYER1, _ZH, shift_z

_BED = re.compile(r"^M1(40|90) +S(\d+\.?\d*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("out")
    ap.add_argument("--raft-h", type=float, required=True)
    ap.add_argument("--max-bed", type=float, default=70.0)
    a = ap.parse_args()

    with open(a.infile) as f:
        lines = f.read().splitlines()

    hot = [(i + 1, l) for i, l in enumerate(lines)
           if (m := _BED.match(l.strip())) and float(m.group(2)) > a.max_bed]
    if hot:
        for n, l in hot[:5]:
            print(f"  line {n}: {l}", file=sys.stderr)
        sys.exit(f"bed temp above {a.max_bed}C found ({len(hot)} lines) — "
                 f"slice with BED_TEMP={a.max_bed:.0f} so the raft is not re-melted")

    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(LAYER1))
    except StopIteration:
        sys.exit("no CHANGE_LAYER marker — is this a sliced Orca gcode?")

    body = [shift_z(l, a.raft_h) for l in lines[start:]]
    merged = lines[:start] + [
        f"; ===== shift_over_raft: all layers +{a.raft_h} (existing raft) =====",
    ] + body

    first_layer_z = next((float(_ZH.match(l).group(1)) for l in body
                          if _ZH.match(l)), None)
    print(f"wrote {a.out}: {len(merged)} lines  shifted from line {start + 1}  "
          f"layer1-Z={first_layer_z}")
    if first_layer_z is None or not (a.raft_h < first_layer_z <= a.raft_h + 0.45):
        sys.exit(f"layer-1 plane {first_layer_z} not just above raft top {a.raft_h}")

    with open(a.out, "w") as f:
        f.write("\n".join(merged) + "\n")


if __name__ == "__main__":
    main()
