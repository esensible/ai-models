"""Flat perforated speaker plate with RAISED letters for a 2-colour print.

No rim. Prints face-UP: black body first, then a pause at z=PLATE_T to swap
filament, then the raised letters in the accent colour. Letters sit on solid
plate (dots held off them) so they're crisp and don't bridge over holes.

  ./cad/run.sh cad/models/speaker_plate.py --diameter 130 --line1 Fuck --line2 Yeah
"""
import argparse, math, os
from build123d import *

ap = argparse.ArgumentParser()
ap.add_argument("--diameter", type=float, default=130.0)
ap.add_argument("--line1", default="Fuck")
ap.add_argument("--line2", default="Yeah")
ap.add_argument("--font", default="cad/fonts/PatrickHand-Regular.ttf")
ap.add_argument("--plate", type=float, default=3.0, help="plate thickness (mm)")
ap.add_argument("--letter", type=float, default=0.6, help="raised letter height (mm)")
ap.add_argument("--shift2", type=float, default=8.0, help="move line2 left (mm)")
ap.add_argument("--clear", type=float, default=2.2, help="keep dots this far off the strokes (mm)")
ap.add_argument("--tag", default="plate")
args = ap.parse_args()

D = args.diameter; R = D / 2.0
PLATE_T = args.plate; LH = args.letter
RIM = 5.0; R_HOLES = R - RIM
HOLE_D = 4.8; HOLE_R = HOLE_D / 2.0
FONT = os.path.abspath(args.font)

# ---- size the two lines as large as they fit ----
TARGET_W = 1.62 * R_HOLES
GAP = 4.0
TARGET_LINE_H = (1.55 * R_HOLES - GAP) / 2.0

def measure(txt, size):
    with BuildSketch() as s:
        Text(txt, font_size=size, font_path=FONT, align=(Align.CENTER, Align.CENTER))
    bb = s.sketch.bounding_box()
    return bb.size.X, bb.size.Y

BASE = 40.0
fs = 1e9
for line in (args.line1, args.line2):
    w, h = measure(line, BASE)
    fs = min(fs, BASE * TARGET_W / w, BASE * TARGET_LINE_H / h)
w1, h1 = measure(args.line1, fs)
w2, h2 = measure(args.line2, fs)
y1 = (max(h1, h2) + GAP) / 2.0
y2 = -(max(h1, h2) + GAP) / 2.0

# ---- text sketch (reads from +Z top -> NO mirror; printed face-up) ----
with BuildSketch() as txt:
    with Locations((0, y1)):
        Text(args.line1, font_size=fs, font_path=FONT, align=(Align.CENTER, Align.CENTER))
    with Locations((-args.shift2, y2)):
        Text(args.line2, font_size=fs, font_path=FONT, align=(Align.CENTER, Align.CENTER))
text_sk = txt.sketch

# ---- mask: keep holes off the letter strokes (so letters sit on solid plate) ----
import numpy as np
with BuildPart() as _maskp:
    with BuildSketch():
        add(text_sk)
    extrude(amount=0.5)
verts, tris = _maskp.part.tessellate(0.4)
TRI = np.array([[v.X, v.Y] for v in verts])[np.array(tris)]

def on_text(x, y):
    m = args.clear
    offs = [(0, 0), (m, 0), (-m, 0), (0, m), (0, -m),
            (m*.7, m*.7), (-m*.7, m*.7), (m*.7, -m*.7), (-m*.7, -m*.7)]
    P = np.array([[x+dx, y+dy] for dx, dy in offs])
    a, b, c = TRI[:, 0], TRI[:, 1], TRI[:, 2]
    def sgn(p, q, r):
        return (p[:, None, 0]-r[None, :, 0])*(q[None, :, 1]-r[None, :, 1]) - \
               (q[None, :, 0]-r[None, :, 0])*(p[:, None, 1]-r[None, :, 1])
    d1, d2, d3 = sgn(P, a, b), sgn(P, b, c), sgn(P, c, a)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0); pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    return bool((~(neg & pos)).any())

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
        if not on_text(x, y):
            pts.append((x, y))
    return pts

pts = spiral_points()

# ---- build: flat plate, holes, raised letters on +Z ----
with BuildPart() as part:
    Cylinder(radius=R, height=PLATE_T)                       # z = -PLATE_T/2 .. +PLATE_T/2
    BATCH = 60
    for i in range(0, len(pts), BATCH):
        with BuildSketch(Plane.XY.offset(PLATE_T / 2 + 0.5)):
            with Locations(*[Location((x, y)) for (x, y) in pts[i:i + BATCH]]):
                Circle(HOLE_R)
        extrude(amount=-(PLATE_T + 2.0), mode=Mode.SUBTRACT)
    with BuildSketch(Plane.XY.offset(PLATE_T / 2)):          # top (show) face
        add(text_sk)
    extrude(amount=LH, mode=Mode.ADD)                        # raised letters

p = part.part
bb = p.bounding_box()
print(f"text='{args.line1} {args.line2}' fs={fs:.1f}mm holes={len(pts)}")
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm  plate={PLATE_T}mm letters+{LH}mm")
print(f"COLOR-CHANGE Z = {PLATE_T:.2f} mm (pause here, swap to accent colour)")

out = os.path.join(os.path.dirname(__file__), "..", "out")
stl = os.path.join(out, f"speaker_{args.tag}.stl")
export_stl(p, stl, tolerance=0.08, angular_tolerance=0.5)
print(f"wrote {os.path.relpath(stl)}")
