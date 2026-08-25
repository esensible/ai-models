"""4x4x3 Gridfinity tray for 22 threading dies (4-5-4-5-4) with embossed labels.

Layout:
- Dies symmetric in the cavity (no y-shift): 5mm gap on every edge.
- Rows 1–4 labels: embossed on the floor in the gap above each die, with
  LABEL_DIE_MARGIN clearance between the die's top edge and the label.
- Row 5 (top) labels: embossed on the back interior wall instead of the floor,
  freeing the floor area immediately above the top row.
"""

from build123d import (
    Axis,
    Cylinder,
    FontStyle,
    Location,
    Part,
    Text,
    Vector,
    extrude,
)

from bin import BASE_H, FLOOR, GAP, GRID, UNIT_H, WALL, gridfinity_bin

DIE_DIAMETER = 27.0
DIE_HEIGHT = 10.0

# Material thickness left under each die pocket (lifts the pocket up from the
# bin's exterior bottom face)
POCKET_FLOOR_THICKNESS = 1.0

# Clearance from die top to the upper bin's foot when stacked. Bin height
# H is computed so this is exact, which means H is not an integer multiple
# of the 7mm Gridfinity unit — two of these still stack with each other,
# but the bin won't share a height grid with stock Gridfinity bins.
DIE_TO_UPPER_CLEARANCE = 2.0

X_UNITS = 4
Y_UNITS = 4

LABEL_FONT = "Arial"
LABEL_FONT_SIZE = 5.5
LABEL_LINE_GAP = 0.5
LABEL_EMBOSS_HEIGHT = 1.0
LABEL_DIE_MARGIN = 1.0

# 22 metric thread sizes in reading order (top-left → bottom-right).
THREADS = [
    (2.0, 0.40), (3.0, 0.50), (4.0, 0.70), (5.0, 0.80),
    (6.0, 0.75), (6.0, 1.00), (7.0, 0.75), (7.0, 1.00), (8.0, 0.75),
    (8.0, 1.00), (8.0, 1.25), (9.0, 0.75), (9.0, 1.00),
    (9.0, 1.25), (10.0, 0.75), (10.0, 1.00), (10.0, 1.25), (10.0, 1.50),
    (11.0, 0.75), (11.0, 1.00), (11.0, 1.25), (11.0, 1.50),
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
    """Embossed label on the floor at (cx, cy, cz) — text reads from above."""
    line1, line2, dy1, dy2 = _two_line_sketches(diameter, pitch)
    line1_3d = extrude(line1, amount=LABEL_EMBOSS_HEIGHT)
    line2_3d = extrude(line2, amount=LABEL_EMBOSS_HEIGHT)
    return (
        line1_3d.moved(Location(Vector(cx, cy + dy1, cz)))
        + line2_3d.moved(Location(Vector(cx, cy + dy2, cz)))
    )


def _label_back_wall(diameter: float, pitch: float, cx: float, cy_wall: float, cz: float) -> Part:
    """Embossed label on the +y interior wall — text reads from inside the bin (looking +y)."""
    line1, line2, dy1, dy2 = _two_line_sketches(diameter, pitch)
    line1_3d = extrude(line1, amount=LABEL_EMBOSS_HEIGHT).rotate(Axis.X, 90)
    line2_3d = extrude(line2, amount=LABEL_EMBOSS_HEIGHT).rotate(Axis.X, 90)
    return (
        line1_3d.moved(Location(Vector(cx, cy_wall, cz + dy1)))
        + line2_3d.moved(Location(Vector(cx, cy_wall, cz + dy2)))
    )


floor_top = BASE_H + FLOOR                              # 5.95
DIE_RECESS_DEPTH = floor_top - POCKET_FLOOR_THICKNESS   # 4.95 (depth of recess)
DIE_PROTRUSION = DIE_HEIGHT - DIE_RECESS_DEPTH          # 5.05 (above floor)
DIE_TOP_Z = floor_top + DIE_PROTRUSION                  # 11.0
_Z_OFFSET_FOR_REST = DIE_TOP_Z + DIE_TO_UPPER_CLEARANCE # 13.0
_TARGET_H = _Z_OFFSET_FOR_REST + BASE_H                  # 17.75
Z_UNITS = _TARGET_H / UNIT_H                              # ~2.536


def die_tray() -> Part:
    bin_part = gridfinity_bin(X_UNITS, Y_UNITS, Z_UNITS, solid=False)

    cavity_w = GRID * X_UNITS - GAP - 2 * WALL
    cavity_d = GRID * Y_UNITS - GAP - 2 * WALL
    g = (cavity_w - 5 * DIE_DIAMETER) / 6
    pitch = DIE_DIAMETER + g
    half_w = cavity_w / 2
    half_d = cavity_d / 2

    row5_xs = [-half_w + g + DIE_DIAMETER / 2 + i * pitch for i in range(5)]
    row4_xs = [(row5_xs[i] + row5_xs[i + 1]) / 2 for i in range(4)]

    ys = [-half_d + g + DIE_DIAMETER / 2 + i * pitch for i in range(5)]
    rows_xs = [row4_xs, row5_xs, row4_xs, row5_xs, row4_xs]

    pocket_z_centre = (floor_top + POCKET_FLOOR_THICKNESS) / 2
    H = _TARGET_H

    # Cut die pockets
    for row_idx in range(5):
        for x in rows_xs[row_idx]:
            cyl = Cylinder(
                radius=DIE_DIAMETER / 2,
                height=DIE_RECESS_DEPTH,
            ).locate(Location(Vector(x, ys[row_idx], pocket_z_centre)))
            bin_part = bin_part - cyl

    # Use the largest label height for consistent floor-label placement
    sample = _two_line_sketches(10.0, 1.25)
    sample_h = sample[0].bounding_box().size.Y + LABEL_LINE_GAP + sample[1].bounding_box().size.Y

    # Wall labels for top row sit midway up the back wall
    wall_z_centre = (floor_top + (H - WALL)) / 2
    wall_y = half_d  # y of inner cavity surface on the +y side

    threads_iter = iter(THREADS)
    for row_idx in [4, 3, 2, 1, 0]:  # top → bottom (reading order)
        y_die = ys[row_idx]
        if row_idx == 4:
            for x in sorted(rows_xs[row_idx]):
                d, p = next(threads_iter)
                bin_part = bin_part + _label_back_wall(d, p, x, wall_y, wall_z_centre)
        else:
            label_cy = y_die + DIE_DIAMETER / 2 + LABEL_DIE_MARGIN + sample_h / 2
            for x in sorted(rows_xs[row_idx]):
                d, p = next(threads_iter)
                bin_part = bin_part + _label_floor(d, p, x, label_cy, floor_top)

    return bin_part


if __name__ == "__main__":
    import os

    from build123d import Mesher, export_step, export_stl

    from bin import OUT

    p = die_tray()
    bb = p.bounding_box().size
    W = GRID * X_UNITS - GAP
    D = GRID * Y_UNITS - GAP
    print(f"die tray: vol={p.volume:.1f}mm³  bbox=({bb.X:.1f}, {bb.Y:.1f}, {bb.Z:.1f})")
    # Footprint must equal the grid footprint exactly — any excess means a
    # label/feature poked through a wall (see gridfinity cavity-clipping rule).
    assert abs(bb.X - W) < 0.05 and abs(bb.Y - D) < 0.05, \
        f"footprint {bb.X:.2f}x{bb.Y:.2f} != {W:.2f}x{D:.2f}"
    assert abs(bb.Z - _TARGET_H) < 0.05, f"height {bb.Z:.2f} != {_TARGET_H:.2f}"

    export_stl(p, os.path.join(OUT, "gridfinity_die_tray.stl"))
    export_step(p, os.path.join(OUT, "gridfinity_die_tray.step"))
    m = Mesher()
    m.add_shape(p)
    m.write(os.path.join(OUT, "gridfinity_die_tray.3mf"))
    print(f"exported gridfinity_die_tray.stl/.step/.3mf -> {os.path.normpath(OUT)}")
