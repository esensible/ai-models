#!/usr/bin/env python
"""Stitch a two-colour, co-planar first-layer text print for a single-nozzle P1S.

The headless OrcaSlicer 2.3.2 CLI refuses multi-filament slicing on the P1S
(filament-to-nozzle "grouping" error). So we slice the two bodies SEPARATELY as
single-filament jobs and merge their G-code:

  * FONT  body  = the letters, 0.2 mm tall  -> printed FIRST, in the accent colour
  * FACE  body  = the cover with 0.2 mm letter cavities -> printed AFTER a swap

Both were sliced from STLs sharing one coordinate frame (same X/Y/Z origin), both
use relative extrusion (M83) and identical layer-1 setup, so the splice is:

    [face preamble + layer-1 setup]
    [font object block]                 <- letters, accent filament
    G1 E-.8 ; retract
    M400 U1 ; PAUSE  -> user swaps accent->body, resumes
    G92 E0
    [face object block + layers 2..N]   <- body filament

Result: one colour change, inside layer 1, letters then surround — exactly the
co-planar look a between-layer pause cannot give.

  ./cad/run.sh slice/merge_twocolor.py FACE.gcode FONT.gcode OUT.gcode [--plot P.png]
"""
import argparse
import re
import sys

PAUSE = "M400 U1"  # P1S machine_pause_gcode: pause + wait for user to resume


def read(path):
    with open(path) as f:
        return f.read().splitlines()


def find(lines, pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    return -1


def merge(face, font):
    # --- font object block: "; printing object fy" ... closing "M625" ---
    fs = find(font, lambda l: l.startswith("; printing object") and "fy_font" in l)
    if fs < 0:  # fall back: any printing-object marker
        fs = find(font, lambda l: l.startswith("; printing object"))
    fe = find(font, lambda l: l.strip() == "M625", fs)
    if fs < 0 or fe < 0:
        sys.exit("could not locate font object block")
    # Drop the font slice's OWN progress commands (M73 P../R../L..) — left in, they
    # corrupt the merged print's layer/percent/ETA readout (the printer adopts the
    # font's standalone progress). The face's own M73/M991 layer notifies stay intact.
    font_block = [l for l in font[fs:fe + 1] if not l.lstrip().startswith("M73")]

    # --- insertion point in FACE: just before its layer-1 object starts ---
    ins = find(face, lambda l: l.startswith("; printing object") and "speaker_cover" in l)
    if ins < 0:
        ins = find(face, lambda l: l.startswith("; printing object"))
    if ins < 0:
        sys.exit("could not locate face object start")

    inject = (
        ["; ===== TWO-COLOUR TEXT: accent letters printed first ====="]
        + font_block
        + [
            "; ===== colour change: swap accent -> body, then resume =====",
            "G1 E-.8 F1800 ; retract before pause",
            f"{PAUSE} ; PAUSE for manual filament swap (accent -> body)",
            "G92 E0 ; reset extruder datum after swap",
            "; ===== resume: surrounding face + remaining layers (body) =====",
        ]
    )
    return face[:ins] + inject + face[ins:], len(font_block)


# ---------- validation plot: layer 1, accent (pre-pause) vs body (post-pause) ----------
# numbers may lack a leading zero (e.g. "E.0375", "X-.8") -> digits optional before dot
_X = re.compile(r"X(-?\d*\.?\d+)")
_Y = re.compile(r"Y(-?\d*\.?\d+)")
_E = re.compile(r"E(-?\d*\.?\d+)")


def plot_layer1(lines, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    l0 = find(lines, lambda l: l.startswith("; CHANGE_LAYER"))
    l1end = find(lines, lambda l: l.startswith("; CHANGE_LAYER"), l0 + 1)
    if l1end < 0:
        l1end = len(lines)
    pause_i = find(lines, lambda l: l.startswith(PAUSE), l0, )

    px, py = None, None
    accent, body = [], []  # lists of (x0,y0,x1,y1)
    for i in range(l0, l1end):
        ln = lines[i]
        mx, my = _X.search(ln), _Y.search(ln)
        if ln.startswith("G1") and mx and my:
            x, y = float(mx.group(1)), float(my.group(1))
            me = _E.search(ln)
            extruding = me and float(me.group(1)) > 0
            if extruding and px is not None:
                (accent if i < pause_i else body).append((px, py, x, y))
            px, py = x, y
        elif ln.startswith("G1") and (_X.search(ln) or _Y.search(ln)):
            if mx:
                px = float(mx.group(1))
            if my:
                py = float(my.group(1))

    fig, ax = plt.subplots(figsize=(8, 8))
    for (x0, y0, x1, y1) in body:
        ax.plot([x0, x1], [y0, y1], color="#3a3d44", lw=0.5)
    for (x0, y0, x1, y1) in accent:
        ax.plot([x0, x1], [y0, y1], color="#e86026", lw=0.7)
    ax.set_aspect("equal")
    ax.set_title(f"Layer 1 toolpaths — accent letters: {len(accent)} segs (printed first)\n"
                 f"body face: {len(body)} segs (after swap)", fontsize=11)
    ax.set_facecolor("#0d0e12")
    fig.patch.set_facecolor("#0d0e12")
    ax.title.set_color("#dddddd")
    ax.tick_params(colors="#888888")
    fig.savefig(out_png, dpi=130, bbox_inches="tight")
    print(f"wrote {out_png}  (accent={len(accent)} body={len(body)} segs)")
    return len(accent), len(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("face")
    ap.add_argument("font")
    ap.add_argument("out")
    ap.add_argument("--plot")
    a = ap.parse_args()

    face, font = read(a.face), read(a.font)
    merged, nblock = merge(face, font)
    with open(a.out, "w") as f:
        f.write("\n".join(merged) + "\n")

    npause = sum(1 for l in merged if l.startswith(PAUSE))
    nlayers = sum(1 for l in merged if l.startswith("; CHANGE_LAYER"))
    print(f"wrote {a.out}: {len(merged)} lines, font block={nblock} lines, "
          f"pauses={npause}, layers={nlayers}")
    if npause != 1:
        print(f"WARNING: expected exactly 1 pause, got {npause}")
    if a.plot:
        plot_layer1(merged, a.plot)


if __name__ == "__main__":
    main()
