"""Gridfinity bin generator (no grid base, perimeter chamfer + simplified lip).

The bin's outer face is vertical at the full footprint W up to z = H. The
"lip" is a single 45° chamfer at the top-inner edge of the wall, sized to
WALL × WALL. WALL is chosen so the chamfer matches the canonical
mating-chamfer width (1.9 mm) AND leaves canonical lateral clearance
(2.15 - WALL = 0.25 mm/side) between the upper bin's base vertical face
and this bin's inner cavity wall.

Migrated from github.com/esensible/gridfinity @ a442056 (models printed
Apr 2026); verify_stack.py checks the lip/base mate. Run via ./cad/run.sh.
"""

import os

from build123d import (
    Part,
    Plane,
    RectangleRounded,
    extrude,
    loft,
)

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

GRID = 42.0
UNIT_H = 7.0
GAP = 0.5
OUTER_R = 3.75
WALL = 1.9
FLOOR = 1.2

BASE_LOWER_CH = 0.8
BASE_VERT = 1.8
BASE_UPPER_CH = 2.15
BASE_H = BASE_LOWER_CH + BASE_VERT + BASE_UPPER_CH  # 4.75

# Simplified lip: just a 45° chamfer at the top-inner edge of the wall.
# Size = WALL (the canonical lip's outer chamfer clipped to the wall thickness).


def _rect(z: float, w: float, d: float, r: float):
    return Plane.XY.offset(z) * RectangleRounded(w, d, r)


def gridfinity_bin(
    x_units: int,
    y_units: int,
    z_units: int,
    solid: bool = False,
    floor: float = FLOOR,
) -> Part:
    """Build a Gridfinity bin sized x_units * y_units * z_units.

    z_units must be >= 2 (a 1U bin can't fit both base profile and lip).

    Args:
        x_units, y_units: footprint in 42mm grid units.
        z_units: total external height in 7mm units.
        solid: True for a solid block below the lip pocket; False for a hollow
            bin with WALL-thick walls and `floor`-thick floor on the base profile.
        floor: floor thickness above the base profile (cavity bottom sits at
            BASE_H + floor). Defaults to the canonical FLOOR=1.2 mm.
    """
    if min(x_units, y_units) < 1 or z_units < 2:
        raise ValueError("x_units, y_units >= 1 and z_units >= 2")

    W = GRID * x_units - GAP
    D = GRID * y_units - GAP
    H = UNIT_H * z_units

    # Base profile (chamfer + vertical + chamfer foot at the bottom).
    base = loft(
        [
            _rect(0.0,                       W - 5.9, D - 5.9, max(0.4, OUTER_R - 2.95)),
            _rect(BASE_LOWER_CH,             W - 4.3, D - 4.3, max(0.4, OUTER_R - 2.15)),
            _rect(BASE_LOWER_CH + BASE_VERT, W - 4.3, D - 4.3, max(0.4, OUTER_R - 2.15)),
            _rect(BASE_H,                    W,       D,       OUTER_R),
        ],
        ruled=True,
    )

    # Body above the base profile: simple straight extrusion at full footprint
    # all the way to the top — no outer-edge chamfer.
    body_top = extrude(_rect(BASE_H, W, D, OUTER_R), amount=H - BASE_H)
    body = base + body_top

    # Cavity: a tapered pocket that creates the simplified lip chamfer at the
    # top-inner edge. For hollow bins, the pocket extends down as a vertical
    # inner cavity to the floor.
    inner_w, inner_d = W - 2 * WALL, D - 2 * WALL
    inner_r = max(0.4, OUTER_R - WALL)

    cavity_sections = []
    if not solid:
        cavity_sections.append((BASE_H + floor, inner_w, inner_d, inner_r))
    cavity_sections += [
        (H - WALL,    inner_w, inner_d, inner_r),  # bottom of top chamfer
        (H,           W,       D,       OUTER_R),  # top, opens at full footprint
        (H + 0.5,     W,       D,       OUTER_R),  # extend past top for clean cut
    ]
    cavity = loft([_rect(*s) for s in cavity_sections], ruled=True)

    return body - cavity
