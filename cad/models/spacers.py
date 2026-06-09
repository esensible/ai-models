"""Four cylindrical spacers, arranged on the plate in print orientation
(standing on their ends). ID 6, OD 15.

  2x plain:   15 mm long
  2x angled:  one end cut at 45 deg -> short side 7 mm, tall side 7+15 = 22 mm
"""
import os
from build123d import *

OD = 15.0
ID = 6.0
ro, ri = OD / 2, ID / 2
PLAIN_L = 15.0
SHORT = 7.0
TALL = SHORT + OD          # 45 deg across Ø15 -> +15 mm -> 22 mm

def plain():
    s = Cylinder(ro, PLAIN_L) - Cylinder(ri, PLAIN_L + 2)
    return s.translate((0, 0, PLAIN_L / 2))      # base on z=0

def angled():
    H = TALL + 2.0
    s = Cylinder(ro, H) - Cylinder(ri, H + 2)
    s = s.translate((0, 0, H / 2))               # base on z=0, axis +Z
    # cut at 45 deg: plane through (-ro,0,SHORT), normal (-1,0,1); keep lower part
    s = split(s, bisect_by=Plane(origin=(0, 0, SHORT + ro), z_dir=(-1, 0, 1)),
              keep=Keep.BOTTOM)
    return s

layout = [
    (plain(), (-20, -20)), (plain(), (-20, 20)),
    (angled(), (20, -20)), (angled(), (20, 20)),
]
parts = None
for solid, (x, y) in layout:
    m = solid.moved(Location((x, y, 0)))
    parts = m if parts is None else parts + m

bb = parts.bounding_box()
print(f"4 parts: plain L={PLAIN_L}  angled short={SHORT}/tall={TALL}  OD={OD} ID={ID}")
print(f"overall bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")

out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
stl = os.path.join(out, "spacers.stl")
export_stl(parts, stl, tolerance=0.05, angular_tolerance=0.3)
print(f"wrote {os.path.relpath(stl)}")
