"""Round speaker cover with large recessed text on the face.

Spiral (phyllotaxis) perforation field + two lines of text RECESSED into the
show face (which prints face-down). Holes are cleared from behind the letters
so the text reads cleanly. Text auto-sized as large as fits.

  ./cad/run.sh cad/models/speaker_cover_text.py --diameter 130 \
       --line1 "Fuck" --line2 "Yeah" --font cad/fonts/PatrickHand-Regular.ttf
"""
import argparse
import math
import os

from build123d import *

ap = argparse.ArgumentParser()
ap.add_argument("--diameter", type=float, default=130.0)
ap.add_argument("--line1", default="Fuck")
ap.add_argument("--line2", default="Yeah")
ap.add_argument("--font", default="cad/fonts/PatrickHand-Regular.ttf")
ap.add_argument("--depth", type=float, default=1.2, help="text recess depth")
ap.add_argument("--tag", default="text")
ap.add_argument("--no-holes", action="store_true", help="skip perforations (debug the text alone)")
ap.add_argument("--recess", action="store_true", help="shallow engraving instead of the default clean cut-through")
ap.add_argument("--perf-text", action="store_true",
                help="two-colour PERFORATED text: letters are accent colour on the first layer only, "
                     "but the spiral holes pass through them too (text = colour, not a solid plug). "
                     "Exports face body (main STL) + font body (--inlay-out). Use --depth 0.2.")
ap.add_argument("--shift2", type=float, default=0.0, help="move line2 left (mm) in the final view")
ap.add_argument("--clear", type=float, default=0.0,
                help="keep perforations this many mm off the letter strokes (so an engraving reads); 0 = holes through text")
ap.add_argument("--inlay-out", default=None,
                help="also export a thin dark-text inlay STL for preview rendering")
args = ap.parse_args()

D = args.diameter
R = D / 2.0
T_FACE = 2.2
RIM_W = 3.5
RIM_H = 8.0
MARGIN = 6.0
R_HOLES = R - MARGIN
HOLE_D = 4.8
HOLE_R = HOLE_D / 2.0
FONT = os.path.abspath(args.font)
DEPTH = args.depth

# ---- size the two text lines as large as they fit ----
TARGET_W = 1.62 * R_HOLES          # max line width
GAP = 4.0
TARGET_LINE_H = (1.55 * R_HOLES - GAP) / 2.0

def measure(txt, size):
    with BuildSketch() as s:
        Text(txt, font_size=size, font_path=FONT,
             align=(Align.CENTER, Align.CENTER))
    bb = s.sketch.bounding_box()
    return bb.size.X, bb.size.Y

BASE = 40.0
fs = 1e9
for line in (args.line1, args.line2):
    w, h = measure(line, BASE)
    fs = min(fs, BASE * TARGET_W / w, BASE * TARGET_LINE_H / h)

# final line metrics + vertical placement (line1 on top)
w1, h1 = measure(args.line1, fs)
w2, h2 = measure(args.line2, fs)
# line1 drawn above centre so that after the Y-mirror it reads on top
y1 = (max(h1, h2) + GAP) / 2.0
y2 = -(max(h1, h2) + GAP) / 2.0

# ---- text sketch (built first; reused for the mask and the recess tool) ----
with BuildSketch() as txt:
    with Locations((0, y1)):
        Text(args.line1, font_size=fs, font_path=FONT,
             align=(Align.CENTER, Align.CENTER))
    with Locations((args.shift2, y2)):   # +shift2 in sketch -> moves LEFT after the YZ mirror
        Text(args.line2, font_size=fs, font_path=FONT,
             align=(Align.CENTER, Align.CENTER))
# mirror LEFT-RIGHT (about YZ) so the text reads correctly from the -Z show face
mirrored = txt.sketch.mirror(Plane.YZ)

# ---- optional: keep holes off the letter strokes so an engraving reads ----
# Tessellate the text to 2D triangles and skip any hole whose centre (or a point
# `clear` mm away, in 8 directions) lands on a stroke.
_tri_xy = None
if args.clear > 0:
    import numpy as _np
    with BuildPart() as _maskp:
        with BuildSketch():
            add(mirrored)
        extrude(amount=0.5)
    verts, tris = _maskp.part.tessellate(0.4)
    P = _np.array([[v.X, v.Y] for v in verts])
    _tri_xy = P[_np.array(tris)]            # (K,3,2)

def _on_text(x, y):
    if _tri_xy is None:
        return False
    import numpy as _np
    m = args.clear
    offs = [(0, 0), (m, 0), (-m, 0), (0, m), (0, -m),
            (m * .7, m * .7), (-m * .7, m * .7), (m * .7, -m * .7), (-m * .7, -m * .7)]
    pts_t = _np.array([[x + dx, y + dy] for dx, dy in offs])     # (9,2)
    a, b, c = _tri_xy[:, 0], _tri_xy[:, 1], _tri_xy[:, 2]         # (K,2)
    def sgn(p, q, r):
        return (p[:, None, 0] - r[None, :, 0]) * (q[None, :, 1] - r[None, :, 1]) - \
               (q[None, :, 0] - r[None, :, 0]) * (p[:, None, 1] - r[None, :, 1])
    d1, d2, d3 = sgn(pts_t, a, b), sgn(pts_t, b, c), sgn(pts_t, c, a)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    inside = ~(neg & pos)                # (9,K)
    return bool(inside.any())

def spiral_points():
    golden = math.radians(137.508)
    c = (HOLE_D + 1.4) / 1.905
    n_max = int((R_HOLES / c) ** 2) + 1
    pts = []
    for n in range(n_max):
        r = c * math.sqrt(n + 0.5)
        if r > R_HOLES:
            continue
        th = n * golden
        x, y = r * math.cos(th), r * math.sin(th)
        if _on_text(x, y):
            continue
        pts.append((x, y))
    return pts

pts = spiral_points()

# ---- build the perforated cover (no text yet): face disc + rim, holes through everything ----
with BuildPart() as cover_perf:
    Cylinder(radius=R, height=T_FACE)
    with Locations((0, 0, T_FACE / 2 + RIM_H / 2)):
        Cylinder(radius=R, height=RIM_H)
        Cylinder(radius=R - RIM_W, height=RIM_H, mode=Mode.SUBTRACT)
    # perforations — the full spiral, including straight through the text, in batches
    if not args.no_holes:
        BATCH = 50
        for i in range(0, len(pts), BATCH):
            with BuildSketch(Plane.XY.offset(T_FACE / 2 + 0.5)):
                with Locations(*[Location((x, y)) for (x, y) in pts[i:i + BATCH]]):
                    Circle(HOLE_R)
            extrude(amount=-(T_FACE + 2.0), mode=Mode.SUBTRACT)

if args.perf_text:
    # PERFORATED two-colour text: the letters are NOT a solid plug. They are just the
    # accent colour on the FIRST LAYER, and the spiral holes run straight through them
    # like the rest of the face (so the cover stays acoustically open everywhere).
    # Build a one-layer-tall letter prism, INTERSECT it with the perforated cover to get
    # the accent body (perforated letters), then the face body is the rest. The two tile
    # perfectly and share every hole. Use --depth 0.2 (one layer).
    LAYER = DEPTH
    with BuildPart() as letter_prism:
        with BuildSketch(Plane.XY.offset(-T_FACE / 2)):   # on the show face (prints down)
            add(mirrored)
        extrude(amount=LAYER)
    font_body = cover_perf.part & letter_prism.part       # perforated accent letters, one layer
    part = cover_perf.part - font_body                    # face body (body colour) = the rest
    if args.inlay_out:
        export_stl(font_body, args.inlay_out, tolerance=0.08, angular_tolerance=0.5)
        print(f"wrote {os.path.relpath(args.inlay_out)}  (perforated font body, {LAYER}mm layer)")
else:
    # ---- default: recess/cut the SOLID text into the show face ----
    TXT_CUT = DEPTH if args.recess else (T_FACE + 2.0)    # default cut-through; --recess for shallow
    with BuildPart() as texttool:
        with BuildSketch(Plane.XY.offset(-T_FACE / 2)):
            add(mirrored)
        extrude(amount=TXT_CUT)
    part = cover_perf.part - texttool.part

print(f"text='{args.line1} {args.line2}'  font_size={fs:.1f}mm  holes={len(pts)}  perf_text={args.perf_text}")
print(f"line widths: {w1:.0f}/{w2:.0f}mm  line height ~{max(h1,h2):.0f}mm")
bb = part.bounding_box()
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm  volume={part.volume/1000:.1f} cm^3")

out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
stl = os.path.join(out, f"speaker_cover_{args.tag}.stl")
export_stl(part, stl, tolerance=0.08, angular_tolerance=0.5)
print(f"wrote {os.path.relpath(stl)}")

# font inlay body (SOLID-text recess mode only): letters extruded to fill the cavity
# flush. For --perf-text the font body is already exported above (perforated).
if args.inlay_out and not args.perf_text:
    with BuildPart() as inlay:
        with BuildSketch(Plane.XY.offset(-T_FACE / 2)):
            add(mirrored)
        extrude(amount=DEPTH)
    export_stl(inlay.part, args.inlay_out, tolerance=0.08, angular_tolerance=0.5)
    print(f"wrote {os.path.relpath(args.inlay_out)}")
