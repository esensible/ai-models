"""20mm calibration cube."""
from build123d import *

S = 20.0  # edge length, mm

with BuildPart() as cube:
    Box(S, S, S)

part = cube.part
print(f"volume_mm3={part.volume:.1f}  (expected {S**3:.0f})")
bb = part.bounding_box()
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")

import os
out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
stl = os.path.join(out, "cube20.stl")
export_stl(part, stl)
print(f"wrote {os.path.relpath(stl)}")
