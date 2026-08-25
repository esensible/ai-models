"""4x4 Gridfinity tray for 12 large threading dies (3 rows of 4) with embossed labels.

Layout:
- 3 rows of 4 dies each, regular grid (no row offset).
- 40mm dies pack tightly in x (~0.74mm gaps); y has ~10.9mm gaps between rows
  to accommodate labels.
- Rows 0–1 labels: embossed on the floor in the gap above each die.
- Row 2 (top) labels: embossed on the back interior wall.

Like the M3–M10 tray, this bin's height is sized for exactly DIE_TO_UPPER_CLEARANCE
above the dies when stacked, so it is NOT an integer multiple of the 7mm
Gridfinity unit.
"""

from build123d import (
    Axis,
    Box,
    Cylinder,
    FontStyle,
    Location,
    Part,
    Text,
    Vector,
    extrude,
)

from bin import BASE_H, GAP, GRID, UNIT_H, WALL, gridfinity_bin

DIE_DIAMETER = 40.0
DIE_HEIGHT = 14.0

# Recess depth is set explicitly (rather than derived from floor thickness as
# in the smaller die tray): with these 14mm-tall dies an 8mm recess is wanted,
# which requires raising this bin's floor above the canonical 1.2mm.
DIE_RECESS_DEPTH = 8.0

POCKET_FLOOR_THICKNESS = 1.0
DIE_TO_UPPER_CLEARANCE = 2.0

X_UNITS = 4
Y_UNITS = 4

LABEL_FONT = "Arial"
LABEL_FONT_SIZE = 6.1
LABEL_LINE_GAP = 0.5
LABEL_EMBOSS_HEIGHT = 1.0
LABEL_DIE_MARGIN = 1.0

# Rectangular slot cut along each row's centre, removing the thin material
# between adjacent recesses. Spans from leftmost to rightmost die centre in x
# (the outer half of each end die is still recessed by its own cylinder, and
# the small slivers between the end dies and the cavity walls stay intact).
# 20mm in y fits inside the 40mm die radius so the slot stays within the row.
ROW_SLOT_WIDTH = 20.0

# 12 metric thread sizes in reading order (top-left → bottom-right).
THREADS = [
    (12.0, 0.75), (12.0, 1.00), (12.0, 1.25), (12.0, 1.50),
    (12.0, 1.75), (14.0, 1.00), (14.0, 1.25), (14.0, 1.50),
    (14.0, 2.00), (16.0, 1.00), (16.0, 1.50), (16.0, 2.00),
]


def _two_line_sketches(diameter: float, pitch: float):
    line1 = Text(f"M{diameter:g}", font_size=LABEL_FONT_SIZE, font=LABEL_FONT, font_style=FontStyle.BOLD)
    line2 = Text(f"{pitch:.2f}", font_size=LABEL_FONT_SIZE, font=LABEL_FONT, font_style=FontStyle.BOLD)
    h1 = line1.bounding_box().size.Y
    h2 = line2.bounding_box().size.Y
    h_total = h1 + LABEL_LINE_GAP + h2
    dy1 = h_total / 2 - h1 / 2
    dy2 = -h_total / 2 + h2 / 2
    return line1, line2, dy1, dy2


def _label_floor(diameter: float, pitch: float, cx: float, cy: float, cz: float) -> Part:
    line1, line2, dy1, dy2 = _two_line_sketches(diameter, pitch)
    line1_3d = extrude(line1, amount=LABEL_EMBOSS_HEIGHT)
    line2_3d = extrude(line2, amount=LABEL_EMBOSS_HEIGHT)
    return (
        line1_3d.moved(Location(Vector(cx, cy + dy1, cz)))
        + line2_3d.moved(Location(Vector(cx, cy + dy2, cz)))
    )


def _label_back_wall(diameter: float, pitch: float, cx: float, cy_wall: float, cz: float) -> Part:
    line1, line2, dy1, dy2 = _two_line_sketches(diameter, pitch)
    line1_3d = extrude(line1, amount=LABEL_EMBOSS_HEIGHT).rotate(Axis.X, 90)
    line2_3d = extrude(line2, amount=LABEL_EMBOSS_HEIGHT).rotate(Axis.X, 90)
    return (
        line1_3d.moved(Location(Vector(cx, cy_wall, cz + dy1)))
        + line2_3d.moved(Location(Vector(cx, cy_wall, cz + dy2)))
    )


floor_top = POCKET_FLOOR_THICKNESS + DIE_RECESS_DEPTH   # 9.0
LOCAL_FLOOR = floor_top - BASE_H                        # 4.25 (passed to bin)
DIE_PROTRUSION = DIE_HEIGHT - DIE_RECESS_DEPTH          # 6.0
DIE_TOP_Z = floor_top + DIE_PROTRUSION                  # 15.0 (= POCKET_FLOOR + DIE_HEIGHT)
_Z_OFFSET_FOR_REST = DIE_TOP_Z + DIE_TO_UPPER_CLEARANCE # 17.0
_TARGET_H = _Z_OFFSET_FOR_REST + BASE_H                  # 21.75
Z_UNITS = _TARGET_H / UNIT_H                              # ~3.107


def large_die_tray() -> Part:
    bin_part = gridfinity_bin(X_UNITS, Y_UNITS, Z_UNITS, solid=False, floor=LOCAL_FLOOR)

    cavity_w = GRID * X_UNITS - GAP - 2 * WALL
    cavity_d = GRID * Y_UNITS - GAP - 2 * WALL

    gx = (cavity_w - 4 * DIE_DIAMETER) / 5
    pitch_x = DIE_DIAMETER + gx
    half_w = cavity_w / 2
    xs = [-half_w + gx + DIE_DIAMETER / 2 + i * pitch_x for i in range(4)]

    gy = (cavity_d - 3 * DIE_DIAMETER) / 4
    pitch_y = DIE_DIAMETER + gy
    half_d = cavity_d / 2
    ys = [-half_d + gy + DIE_DIAMETER / 2 + i * pitch_y for i in range(3)]

    pocket_z_centre = (floor_top + POCKET_FLOOR_THICKNESS) / 2
    H = _TARGET_H

    for y in ys:
        for x in xs:
            cyl = Cylinder(
                radius=DIE_DIAMETER / 2,
                height=DIE_RECESS_DEPTH,
            ).locate(Location(Vector(x, y, pocket_z_centre)))
            bin_part = bin_part - cyl
        slot_length = xs[-1] - xs[0]
        slot = Box(slot_length, ROW_SLOT_WIDTH, DIE_RECESS_DEPTH).locate(
            Location(Vector(0, y, pocket_z_centre))
        )
        bin_part = bin_part - slot

    sample = _two_line_sketches(24.0, 3.0)
    sample_h = sample[0].bounding_box().size.Y + LABEL_LINE_GAP + sample[1].bounding_box().size.Y

    wall_z_centre = (floor_top + (H - WALL)) / 2
    wall_y = half_d

    threads_iter = iter(THREADS)
    for row_idx in [2, 1, 0]:  # top → bottom (reading order)
        y_die = ys[row_idx]
        if row_idx == 2:
            for x in sorted(xs):
                d, p = next(threads_iter)
                bin_part = bin_part + _label_back_wall(d, p, x, wall_y, wall_z_centre)
        else:
            label_cy = y_die + DIE_DIAMETER / 2 + LABEL_DIE_MARGIN + sample_h / 2
            for x in sorted(xs):
                d, p = next(threads_iter)
                bin_part = bin_part + _label_floor(d, p, x, label_cy, floor_top)

    return bin_part


if __name__ == "__main__":
    import os

    from build123d import Mesher, export_step, export_stl

    from bin import OUT

    p = large_die_tray()
    bb = p.bounding_box().size
    W = GRID * X_UNITS - GAP
    D = GRID * Y_UNITS - GAP
    print(f"large die tray: vol={p.volume:.1f}mm³  bbox=({bb.X:.1f}, {bb.Y:.1f}, {bb.Z:.1f})")
    assert abs(bb.X - W) < 0.05 and abs(bb.Y - D) < 0.05, \
        f"footprint {bb.X:.2f}x{bb.Y:.2f} != {W:.2f}x{D:.2f}"
    assert abs(bb.Z - _TARGET_H) < 0.05, f"height {bb.Z:.2f} != {_TARGET_H:.2f}"

    export_stl(p, os.path.join(OUT, "gridfinity_large_die_tray.stl"))
    export_step(p, os.path.join(OUT, "gridfinity_large_die_tray.step"))
    m = Mesher()
    m.add_shape(p)
    m.write(os.path.join(OUT, "gridfinity_large_die_tray.3mf"))
    print(f"exported gridfinity_large_die_tray.stl/.step/.3mf -> {os.path.normpath(OUT)}")
