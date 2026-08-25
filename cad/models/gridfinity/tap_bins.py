"""Tap holder bins. Layout via rectpack (MaxRects-BAF) with isolated troughs.

Each tap has its own half-cylinder trough cut into the floor:
- 1mm clearance around the tap (sides, ends, bottom)
- 1mm wall between two end-to-end taps within a pair
- 1mm wall between adjacent pair-cols within a super-block
- 1mm pad around each super-block (so different-diameter groups are isolated)

Super-blocks (one per diameter) are packed into 5×5 cavities by rectpack.
Heights are set by the largest tap in each bin:
    Bin with M16: H = 23.75
    Bin with M11 max: H = 18.75
Stack: 23.75 + 18.75 − 4.75 = 37.75 mm.
"""

from build123d import (
    Axis,
    Cylinder,
    Location,
    Vector,
    export_step,
    extrude,
)
from rectpack import (
    MaxRectsBaf,
    PackingBin,
    PackingMode,
    newPacker,
)

from bin import BASE_H, GAP, GRID, UNIT_H, WALL, gridfinity_bin

TAP_CLEAR = 1.0
PAIR_WALL = 1.0
COL_SEP = 1.0
SUPER_PAD = 1.0
POCKET_FLOOR = 1.0
TAP_TO_UPPER = 2.0

# (diameter, [pitches]) — one entry per diameter group, each pitch is a pair
GROUPS = [
    (16, [1.00, 1.50, 2.00]),
    (14, [1.00, 1.25, 1.50, 2.00]),
    (12, [0.75, 1.00, 1.25, 1.50, 1.75]),
    (11, [0.75, 1.00, 1.25, 1.50]),
    (10, [0.75, 1.00, 1.25, 1.50]),
    (9, [0.75, 1.00, 1.25]),
    (8, [0.75, 1.00, 1.25]),
    (7, [0.75, 1.00]),
    (6, [0.75, 1.00]),
    (5, [0.80]),
    (4, [0.70]),
    (3, [0.50]),
    (2, [0.40]),
]
GROUPS_DICT = dict(GROUPS)


def tap_length(d):
    if d <= 7: return 65.0
    if d == 8: return 69.0
    if d == 9: return 73.0
    if d == 10: return 76.0
    if d == 11: return 80.0
    if d == 12: return 83.0
    if d == 14: return 85.0
    if d == 16: return 95.0
    raise ValueError(d)


def trough_radius(d):
    return d / 2 + TAP_CLEAR


def trough_width(d):
    return d + 2 * TAP_CLEAR


def trough_length(d):
    return tap_length(d) + 2 * TAP_CLEAR


def super_dims(d, n_pairs):
    """Super-block (W, L) with 1mm pad on every side."""
    inner_w = n_pairs * trough_width(d) + (n_pairs - 1) * COL_SEP
    inner_l = 2 * trough_length(d) + PAIR_WALL
    return (inner_w + 2 * SUPER_PAD, inner_l + 2 * SUPER_PAD)


def make_trough_cyl(d, length, axis_y=True):
    R = trough_radius(d)
    c = Cylinder(radius=R, height=length)
    if axis_y:
        c = c.rotate(Axis.X, 90)
    else:
        c = c.rotate(Axis.Y, 90)
    return c


def run_packer(cavity_w, cavity_d, n_bins=3):
    """Returns placements: list of dicts with bin_idx, x, y, w, h, rotated, d, n_pairs."""
    packer = newPacker(
        mode=PackingMode.Offline,
        bin_algo=PackingBin.BFF,
        pack_algo=MaxRectsBaf,
        rotation=True,
    )
    for _ in range(n_bins):
        packer.add_bin(cavity_w, cavity_d)
    for d, pitches in GROUPS:
        w, l = super_dims(d, len(pitches))
        packer.add_rect(w, l, d)
    packer.pack()

    placements = []
    for bin_idx, bin_ in enumerate(packer):
        for r in bin_:
            d = r.rid
            n = len(GROUPS_DICT[d])
            orig_w, orig_l = super_dims(d, n)
            rotated = (r.width, r.height) != (orig_w, orig_l)
            placements.append({
                "bin_idx": bin_idx,
                "x": float(r.x),
                "y": float(r.y),
                "w": float(r.width),
                "h": float(r.height),
                "rotated": rotated,
                "d": d,
                "n": n,
            })
    n_packed = len(placements)
    n_total = len(GROUPS)
    if n_packed != n_total:
        raise RuntimeError(f"only packed {n_packed}/{n_total} super-blocks")
    return placements


def place_pairs(bin_part, sp, floor_top, cavity_w, cavity_d):
    """Cut all troughs for one super-block."""
    d = sp["d"]
    pitches = GROUPS_DICT[d]
    n = sp["n"]
    pw = trough_width(d)
    tl = trough_length(d)
    pair_inner_l = 2 * tl + PAIR_WALL
    inner_w = n * pw + (n - 1) * COL_SEP

    rotated = sp["rotated"]
    sx, sy, sw, sh = sp["x"], sp["y"], sp["w"], sp["h"]

    # Inner origin (after super-pad)
    if not rotated:
        # Cols along super's X (width sw), pairs along super's Y (length sh)
        inner_x0 = sx + SUPER_PAD
        inner_y0 = sy + SUPER_PAD
        inner_w_axis = "x"
        pair_axis = "y"
    else:
        # Cols along super's Y (height sh), pairs along super's X (width sw)
        inner_x0 = sx + SUPER_PAD
        inner_y0 = sy + SUPER_PAD
        inner_w_axis = "y"
        pair_axis = "x"

    pair_center_along_long = SUPER_PAD + pair_inner_l / 2

    for i in range(n):
        col_offset = i * (pw + COL_SEP) + pw / 2  # within inner area
        # Within the pair: tap 1 at -off, tap 2 at +off, where off = (tl+PAIR_WALL)/2
        tap_off = (tl + PAIR_WALL) / 2

        if not rotated:
            col_x = inner_x0 + col_offset
            pair_y = sy + pair_center_along_long
            tap1_y = pair_y - tap_off
            tap2_y = pair_y + tap_off
            t1 = (col_x, tap1_y)
            t2 = (col_x, tap2_y)
            axis_y = True
        else:
            col_y = inner_y0 + col_offset
            pair_x = sx + pair_center_along_long
            tap1_x = pair_x - tap_off
            tap2_x = pair_x + tap_off
            t1 = (tap1_x, col_y)
            t2 = (tap2_x, col_y)
            axis_y = False

        for (rx, ry) in [t1, t2]:
            cx = rx - cavity_w / 2
            cy = ry - cavity_d / 2
            cyl = make_trough_cyl(d, tl, axis_y=axis_y).moved(
                Location(Vector(cx, cy, floor_top))
            )
            bin_part = bin_part - cyl

    return bin_part


def build_bins():
    cavity_w = GRID * 5 - GAP - 2 * WALL
    cavity_d = cavity_w
    placements = run_packer(cavity_w, cavity_d)

    by_bin = {}
    for sp in placements:
        by_bin.setdefault(sp["bin_idx"], []).append(sp)

    bins = {}
    for bin_idx in sorted(by_bin):
        bps = by_bin[bin_idx]
        max_d = max(sp["d"] for sp in bps)
        floor_top = trough_radius(max_d) + POCKET_FLOOR
        # Tap rests on trough bottom; tap top sits (r-1) above floor surface
        tap_top_above_floor = max_d / 2 - 1
        H = floor_top + tap_top_above_floor + TAP_TO_UPPER + BASE_H
        z_units = H / UNIT_H
        local_floor = floor_top - BASE_H

        bin_part = gridfinity_bin(5, 5, z_units, solid=False, floor=local_floor)

        for sp in bps:
            bin_part = place_pairs(bin_part, sp, floor_top, cavity_w, cavity_d)

        bins[bin_idx] = {
            "part": bin_part,
            "H": H,
            "z_units": z_units,
            "max_d": max_d,
            "max_d_super_count": len(bps),
            "placements": bps,
        }

    return bins


if __name__ == "__main__":
    from build123d import Mesher

    bins = build_bins()
    for idx, info in sorted(bins.items()):
        part = info["part"]
        bb = part.bounding_box().size
        name = f"bin_{idx + 1}"
        print(f"\n=== {name} ===")
        print(f"max_d=M{info['max_d']}  H={info['H']:.2f}  z_units={info['z_units']:.3f}")
        print(f"bbox={bb.X:.2f}×{bb.Y:.2f}×{bb.Z:.2f}   vol={part.volume:.0f}mm³")
        print(f"super-blocks placed: {info['max_d_super_count']}")
        for sp in info["placements"]:
            r_str = " (rotated)" if sp["rotated"] else ""
            print(f"  M{sp['d']:>2} ({sp['n']} pairs)  @({sp['x']:.1f},{sp['y']:.1f}) "
                  f"{sp['w']:.1f}×{sp['h']:.1f}{r_str}")
        import os

        from bin import OUT

        m = Mesher()
        m.add_shape(part)
        m.write(os.path.join(OUT, f"gridfinity_tap_{name}.3mf"))
        export_step(part, os.path.join(OUT, f"gridfinity_tap_{name}.step"))
        print(f"wrote gridfinity_tap_{name}.3mf/.step")
