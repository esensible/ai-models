#!/usr/bin/env python3
"""Insert a per-layer bed-temp ramp into sliced Bambu gcode.

Slicers only support two bed temps (first layer + rest), so ramps are a
post-processing job: slice with the bed pinned at the first-layer temp for the
WHOLE print, then run this to insert M140 steps after successive layer-change
markers, starting at layer 2.

  inject_bed_ramp.py in.gcode out.gcode 85,80,75,70

Safety: refuses if the body (after layer 1) already contains M140 lines that
would fight the ramp (the end-gcode bed-off M140 S0 is allowed), and asserts
every step actually got placed. Repack the result with repack_gcode_3mf.py —
the printer validates the gcode against its md5 sidecar.
"""
import re
import sys

LAYER = re.compile(r"^; layer num/total_layer_count: (\d+)[/,]")


def main():
    src, dst = sys.argv[1], sys.argv[2]
    steps = [int(s) for s in sys.argv[3].split(",")]
    ramp = {i + 2: t for i, t in enumerate(steps)}   # first step at layer 2

    out = []
    layer = 0
    inserted = {}
    conflicts = []
    with open(src, errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            m = LAYER.match(line)
            out.append(line)
            if m:
                layer = int(m.group(1))
                if layer in ramp and layer not in inserted:
                    out.append(f"M140 S{ramp[layer]} ; bed ramp step (injected)\n")
                    inserted[layer] = True
                continue
            if layer >= 2 and line.startswith("M140") and "injected" not in line \
                    and not re.match(r"M140\s+S0\b", line):
                conflicts.append((i, line.strip()))

    if conflicts:
        sys.exit(f"refusing: existing M140 after layer 1 would fight the ramp: {conflicts[:5]}")
    if sorted(inserted) != sorted(ramp):
        sys.exit(f"missed ramp layers: placed {sorted(inserted)} of {sorted(ramp)} "
                 f"(print has fewer layers than the ramp?)")

    with open(dst, "w") as fh:
        fh.writelines(out)
    print(f"injected bed ramp {ramp} -> {dst}")


if __name__ == "__main__":
    main()
