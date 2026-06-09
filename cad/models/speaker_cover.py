"""Round speaker cover / grille — parametric.

Flat perforated face (prints face-DOWN for a clean surface) + a rim on the back
that sits over the driver. Two perforation styles:

  --pattern spiral   phyllotaxis "sunflower" spiral of holes (golden angle) [cool]
  --pattern hex      classic staggered (hex-packed) round holes

  --diameter 130     outer diameter in mm (default 130 = 13 cm)

Acoustics: targets ~45-50% open area (pro grilles run 50-65%); holes ~4.8-5mm.
"""
import argparse
import math
import os

from build123d import *

ap = argparse.ArgumentParser()
ap.add_argument("--pattern", choices=["spiral", "hex"], default="spiral")
ap.add_argument("--diameter", type=float, default=130.0)
args = ap.parse_args()

# ---- parameters ----
D = args.diameter            # outer diameter
R = D / 2.0
T_FACE = 2.2                 # flat face thickness (printed face-down)
RIM_W = 3.5                  # rim wall thickness
RIM_H = 8.0                  # rim height (depth of the cover)
MARGIN = 6.0                 # solid ring from edge inward before holes start
R_HOLES = R - MARGIN         # holes live within this radius

HOLE_D = 4.8 if args.pattern == "spiral" else 5.0
HOLE_R = HOLE_D / 2.0

# ---- hole centre points ----
def spiral_points():
    # Vogel's model: r = c*sqrt(n), theta = n * golden_angle
    golden = math.radians(137.508)
    # choose spacing so nearest-neighbour gap leaves a printable wall
    target_nn = HOLE_D + 1.4          # centre-to-centre of nearest neighbours
    c = target_nn / 1.905             # NN spacing ~= 1.905*c for Vogel spiral
    n_max = int((R_HOLES / c) ** 2) + 1
    pts = []
    for n in range(n_max):
        r = c * math.sqrt(n + 0.5)
        if r > R_HOLES:
            continue
        th = n * golden
        pts.append((r * math.cos(th), r * math.sin(th)))
    return pts

def hex_points():
    pitch = HOLE_D + 1.8              # centre-to-centre
    dy = pitch * math.sqrt(3) / 2.0
    pts = []
    j = 0
    y = -R_HOLES
    while y <= R_HOLES:
        offset = (pitch / 2.0) if (j % 2) else 0.0
        x = -R_HOLES + offset
        while x <= R_HOLES:
            if math.hypot(x, y) <= R_HOLES:
                pts.append((x, y))
            x += pitch
        y += dy
        j += 1
    return pts

pts = spiral_points() if args.pattern == "spiral" else hex_points()

# ---- build ----
with BuildPart() as cover:
    # flat face: spans z in [-T_FACE/2, +T_FACE/2]
    Cylinder(radius=R, height=T_FACE)
    # rim on the BACK (the +z side; the -z face is the clean printed face)
    with Locations((0, 0, T_FACE / 2 + RIM_H / 2)):
        Cylinder(radius=R, height=RIM_H)
        Cylinder(radius=R - RIM_W, height=RIM_H, mode=Mode.SUBTRACT)
    # perforate the face: sketch all holes just above the face, cut fully through
    with BuildSketch(Plane.XY.offset(T_FACE / 2 + 0.5)):   # z = +1.6, above face top
        with Locations(*[Location((x, y)) for (x, y) in pts]):
            Circle(HOLE_R)
    extrude(amount=-(T_FACE + 2.0), mode=Mode.SUBTRACT)     # down to z = -2.6, clears face

part = cover.part

# ---- report ----
open_area = len(pts) * math.pi * HOLE_R ** 2
face_area = math.pi * R ** 2
print(f"pattern={args.pattern}  D={D:.0f}mm  holes={len(pts)}  hole_d={HOLE_D}mm")
print(f"open_area={open_area/face_area*100:.1f}%  (of full face)")
bb = part.bounding_box()
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm  volume={part.volume/1000:.1f} cm^3")

out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
stl = os.path.join(out, f"speaker_cover_{args.pattern}.stl")
export_stl(part, stl, tolerance=0.08, angular_tolerance=0.5)
print(f"wrote {os.path.relpath(stl)}")
