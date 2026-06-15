"""Smoke-test part: rounded plate with two holes. Proves model -> STL/3MF export."""
from build123d import (
    BuildPart, BuildSketch, RectangleRounded, Circle, Locations,
    extrude, Mode, export_stl, Mesher,
)

LENGTH, WIDTH, THICK, HOLE_D = 40, 24, 4, 6

with BuildPart() as part:
    with BuildSketch():
        RectangleRounded(LENGTH, WIDTH, radius=4)
        with Locations((LENGTH / 2 - 8, 0), (-LENGTH / 2 + 8, 0)):
            Circle(HOLE_D / 2, mode=Mode.SUBTRACT)
    extrude(amount=THICK)

solid = part.part
export_stl(solid, "cad/out/test_plate.stl")

mesher = Mesher()
mesher.add_shape(solid)
mesher.write("cad/out/test_plate.3mf")

bb = solid.bounding_box()
print(f"volume_mm3={solid.volume:.1f}")
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print("wrote cad/out/test_plate.stl and cad/out/test_plate.3mf")
