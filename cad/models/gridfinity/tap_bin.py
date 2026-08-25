"""Tap holder bins — pair of side-by-side bins, combined footprint 6×5.

Holds 35 unique threaded taps loaded from tap_sizes.csv (next to this file).

CSV provenance: the original /workspace/tap-sizes.csv did not survive the
migration from github.com/esensible/gridfinity (it lived outside that repo).
The bundled tap_sizes.csv is RECONSTRUCTED from tap_bins.py's GROUPS table +
tap_length() (34 taps) plus M18x1.5, whose presence this file's own comments
attest (SINGLE_LINE_OVERRIDES, STANDARD_PITCHES note) — its 100mm length is an
ESTIMATE. If the original CSV resurfaces, replace the file and re-run.

Layout:
- Sort by (size, pitch).
- Sizes ≤ 5 (M2-M5) horizontal in bin A's leftmost X strip with single-line
  floor labels to their LEFT (e.g. "M2x0.4").
- Sizes 6..11 vertical in row 1 (top), with two-line labels DEBOSSED on the
  +Y interior wall.
- Sizes 12..18 vertical in row 2 (bottom), with two-line floor labels below
  each tap.

The cavity floor sits at z = top_z (top tangent of all taps). Each trough
descends BELOW the floor as a cylindrical pocket — the floor's top surface
spans the top edge of every holder.
"""

import csv
import math
import os

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    FontStyle,
    Location,
    Part,
    Text,
    Vector,
    export_step,
    extrude,
)

from bin import BASE_H, GAP, GRID, UNIT_H, WALL, gridfinity_bin

CSV_PATH = os.path.join(os.path.dirname(__file__), "tap_sizes.csv")

TAP_CLEAR = 1.0
POCKET_FLOOR = 0.4
TAP_TO_UPPER = 2.0

TOP_PAD = 0.5
BOT_PAD = 0.5
MIDDLE_CLEARANCE = 2.0

LABEL_FONT = "Arial"
LABEL_FONT_SIZE = 4.0
LABEL_LINE_GAP = 1.0
LABEL_EMBOSS = 1.0
LABEL_MARGIN = 1.5
LABEL_OVERLAP_SLACK = 0.2

# Per-tap single-line override. Two-line is the default; (d, p) listed here
# becomes a single-line label like "M8x1" or "M18x1.5". Used when a two-line
# label would push the trough into a horizontal singleton's territory.
SINGLE_LINE_OVERRIDES = {(8, 1.0), (18, 1.5)}

# Standard-pitch highlight rings.
RING_WIDTH = 0.6        # radial thickness of the ring
RING_LABEL_PAD = 0.5    # clearance from label corners to inner ring edge
RING_LABEL_GAP = 0.5    # padding around neighbour labels when breaking ring
RING_RECESS_GAP = 0.3   # padding around recess footprints when breaking ring

# ISO metric coarse pitches present in the CSV. M18 coarse is 2.5 but the
# CSV only has M18×1.5 (fine), so M18 gets no highlight.
STANDARD_PITCHES = {
    6: 1.0, 7: 1.0, 8: 1.25, 9: 1.25,
    10: 1.5, 11: 1.5, 12: 1.75,
    14: 2.0, 16: 2.0,
}

ROW_SLOT_DEPTH = 10.0
ROW_SLOT_WIDTH = 30.0
SLOT_X_INSET = 2.0

Y_UNITS = 5
COMBINED_X_UNITS = 6

HORIZONTAL_MAX_SIZE = 5
ROW2_MIN_SIZE = 12

H_LEFT_PAD = 1.5
H_LABEL_TO_TAP = 1.0
H_INTER_GAP = 1.0


def load_taps():
    taps = []
    with open(CSV_PATH) as f:
        for row in csv.DictReader(f):
            taps.append((int(row["Size"]), float(row["Pitch"]), float(row["Length"])))
    taps.sort(key=lambda t: (t[0], t[1]))
    return taps


def trough_radius(d): return d / 2 + TAP_CLEAR
def trough_width(d): return d + 2 * TAP_CLEAR
def trough_length_(length): return length + 2 * TAP_CLEAR


def _trough_axis_z(d, top_z):
    """Cylinder axis Z so a tap rests with its top tangent at top_z."""
    return top_z - d / 2 + 1


def trough_cut_vert(d, length, top_z, cx, cy):
    """Stadium-section cut for a vertical (Y-axis) tap trough.

    Lower half is a half-cylinder (radius d/2+1); upper half is a vertical
    rectangular column of the same width (d+2) extending past top_z. This
    keeps the floor opening at full diameter so the tap can drop straight in.
    """
    r = trough_radius(d)
    axis_z = _trough_axis_z(d, top_z)
    cyl = Cylinder(radius=r, height=length).rotate(Axis.X, 90).moved(
        Location(Vector(cx, cy, axis_z))
    )
    box_h = top_z + 2 - axis_z
    box = Box(2 * r, length, box_h).moved(
        Location(Vector(cx, cy, axis_z + box_h / 2))
    )
    return cyl + box


def trough_cut_horiz(d, length, top_z, cx, cy):
    """Stadium-section cut for a horizontal (X-axis) tap trough."""
    r = trough_radius(d)
    axis_z = _trough_axis_z(d, top_z)
    cyl = Cylinder(radius=r, height=length).rotate(Axis.Y, 90).moved(
        Location(Vector(cx, cy, axis_z))
    )
    box_h = top_z + 2 - axis_z
    box = Box(length, 2 * r, box_h).moved(
        Location(Vector(cx, cy, axis_z + box_h / 2))
    )
    return cyl + box


def label_two_line(d, p, font_size=LABEL_FONT_SIZE, line_gap=LABEL_LINE_GAP):
    l1 = Text(f"M{d:g}", font_size=font_size, font=LABEL_FONT, font_style=FontStyle.BOLD)
    l2 = Text(f"{p:.2f}", font_size=font_size, font=LABEL_FONT, font_style=FontStyle.BOLD)
    bb1, bb2 = l1.bounding_box(), l2.bounding_box()
    h = bb1.size.Y + line_gap + bb2.size.Y
    w = max(bb1.size.X, bb2.size.X)
    return ((l1, h / 2 - bb1.size.Y / 2), (l2, -h / 2 + bb2.size.Y / 2)), w, h


def _pitch_short(p):
    """Minimal-decimal pitch string: 1.0→'1', 0.4→'0.4', 1.25→'1.25'."""
    if p == int(p):
        return str(int(p))
    return f"{p:g}"


def label_single_line(d, p, font_size=LABEL_FONT_SIZE, drop_zero=False):
    """Single-line label e.g. 'M2x0.4', 'M8x1', 'M18x1.5'."""
    pstr = _pitch_short(p)
    if drop_zero and pstr.startswith("0"):
        pstr = pstr[1:]
    text = Text(f"M{d:g}x{pstr}", font_size=font_size, font=LABEL_FONT,
                font_style=FontStyle.BOLD)
    bb = text.bounding_box().size
    return text, bb.X, bb.Y


def label_format(d, p):
    return "single" if (int(d), p) in SINGLE_LINE_OVERRIDES else "two"


def label_dims(d, p):
    """Return (format, label_w, label_h) for the chosen format."""
    if label_format(d, p) == "single":
        _, lw, lh = label_single_line(d, p)
        return "single", lw, lh
    _, lw, lh = label_two_line(d, p)
    return "two", lw, lh


def emboss_floor_two_line(d, p, cx, cy, cz):
    (l1, l2), _, _ = label_two_line(d, p)
    out = None
    for line, dy in (l1, l2):
        e = extrude(line, amount=LABEL_EMBOSS).moved(Location(Vector(cx, cy + dy, cz)))
        out = e if out is None else out + e
    return out


def emboss_floor_single_line(text_sketch, cx, cy, cz):
    return extrude(text_sketch, amount=LABEL_EMBOSS).moved(Location(Vector(cx, cy, cz)))


def emboss_floor_label(tp, top_z):
    """Emboss the per-tap floor label (single or two-line) at tp['label_y']."""
    if tp["fmt"] == "single":
        text, _, _ = label_single_line(tp["d"], tp["p"])
        return emboss_floor_single_line(text, tp["x"], tp["label_y"], top_z)
    return emboss_floor_two_line(tp["d"], tp["p"], tp["x"], tp["label_y"], top_z)


def is_standard_pitch(d, p):
    return STANDARD_PITCHES.get(int(d)) == p


def _ring_dims(label_w, label_h):
    half_diag = math.hypot(label_w, label_h) / 2
    inner_r = half_diag + RING_LABEL_PAD
    return inner_r, inner_r + RING_WIDTH


def make_floor_ring(cx, cy, cz, label_w, label_h):
    inner_r, outer_r = _ring_dims(label_w, label_h)
    ring_2d = Circle(outer_r) - Circle(inner_r)
    return extrude(ring_2d, amount=LABEL_EMBOSS).moved(
        Location(Vector(cx, cy, cz))
    )


def select_visible_x(positions, direction="ltr"):
    iter_order = list(positions) if direction == "ltr" else list(reversed(positions))
    out = []
    last_right = float("-inf")
    last_left = float("+inf")
    for tp in iter_order:
        lw = tp["label_w"]
        left = tp["x"] - lw / 2
        right = tp["x"] + lw / 2
        if direction == "ltr":
            include = left >= last_right + LABEL_OVERLAP_SLACK
            if include:
                last_right = right
        else:
            include = right <= last_left - LABEL_OVERLAP_SLACK
            if include:
                last_left = left
        out.append({**tp, "include": include})
    if direction == "rtl":
        out.reverse()
    return out


def plan_layout():
    """Pick row composition + bin split given the loaded CSV."""
    taps = load_taps()
    horiz = [t for t in taps if t[0] <= HORIZONTAL_MAX_SIZE]
    row1 = [t for t in taps if HORIZONTAL_MAX_SIZE < t[0] < ROW2_MIN_SIZE]
    row2 = [t for t in taps if t[0] >= ROW2_MIN_SIZE]

    max_d_pair = max(t[0] for t in taps)

    combined_external = COMBINED_X_UNITS * GRID - 2 * GAP
    combined_cavity = combined_external - 4 * WALL  # 243.4

    sum_w_row2 = sum(trough_width(d) for d, _, _ in row2)
    n2 = len(row2)
    n_gaps_row2 = n2 + 2
    row2_gap = (combined_cavity - sum_w_row2) / n_gaps_row2

    best = None
    for split2 in range(2, n2 - 1):
        sum_A = sum(trough_width(d) for d, _, _ in row2[:split2])
        sum_B = sum_w_row2 - sum_A
        cav_A = sum_A + (split2 + 1) * row2_gap
        cav_B = sum_B + (n2 - split2 + 1) * row2_gap
        if cav_A < 100 or cav_B < 80:
            continue
        score = abs(cav_A - cav_B)
        if best is None or score < best["score"]:
            best = {"split2": split2, "cav_A": cav_A, "cav_B": cav_B, "score": score}
    if best is None:
        raise RuntimeError("no valid row 2 split")

    sum_w_row1 = sum(trough_width(d) for d, _, _ in row1)
    n1 = len(row1)
    best1 = None
    for split1 in range(1, n1):
        sum_A = sum(trough_width(d) for d, _, _ in row1[:split1])
        sum_B = sum_w_row1 - sum_A
        gap_A = (best["cav_A"] - sum_A) / (split1 + 1)
        gap_B = (best["cav_B"] - sum_B) / (n1 - split1 + 1)
        if gap_A < 1.0 or gap_B < 1.0:
            continue
        score = abs(gap_A - gap_B)
        if best1 is None or score < best1["score"]:
            best1 = {"split1": split1, "gap_A": gap_A, "gap_B": gap_B, "score": score}
    if best1 is None:
        raise RuntimeError("no valid row 1 split")

    ext_A = best["cav_A"] + 2 * WALL
    ext_B = best["cav_B"] + 2 * WALL
    x_a = (ext_A + GAP) / GRID
    x_b = (ext_B + GAP) / GRID

    return {
        "horiz": horiz,
        "row1_A": row1[:best1["split1"]],
        "row1_B": row1[best1["split1"]:],
        "row2_A": row2[:best["split2"]],
        "row2_B": row2[best["split2"]:],
        "max_d_pair": max_d_pair,
        "cav_A": best["cav_A"],
        "cav_B": best["cav_B"],
        "x_a": x_a,
        "x_b": x_b,
        "row2_gap": row2_gap,
        "row1_gap_A": best1["gap_A"],
        "row1_gap_B": best1["gap_B"],
    }


def compute_bin_layout(plan, side):
    cav_w = plan["cav_A"] if side == "A" else plan["cav_B"]
    cav_d = GRID * Y_UNITS - GAP - 2 * WALL

    max_d_pair = plan["max_d_pair"]
    floor_top = trough_radius(max_d_pair) + POCKET_FLOOR
    top_z = floor_top + (max_d_pair / 2 - 1)
    H = top_z + TAP_TO_UPPER + BASE_H
    z_units = H / UNIT_H
    # Inverted floor: cavity floor sits AT top_z. Below the floor is solid
    # material that the troughs cut into.
    local_floor = top_z - BASE_H

    row1 = plan["row1_A"] if side == "A" else plan["row1_B"]
    row2 = plan["row2_A"] if side == "A" else plan["row2_B"]
    horiz = plan["horiz"] if side == "A" else []
    row1_gap = plan["row1_gap_A"] if side == "A" else plan["row1_gap_B"]
    row2_gap = plan["row2_gap"]

    half_d = cav_d / 2
    # Row 1: troughs hugged near +Y wall; per-tap trough_top_y so single-line
    # taps have shorter label band and sit higher (closer to wall).
    # Row 2: troughs hugged against -Y wall; labels sit ABOVE each trough.
    y_bot_row_bottoms = -half_d + BOT_PAD

    def row1_positions(taps_list, gap):
        cur_x = -cav_w / 2 + gap
        out = []
        for d, p, length in taps_list:
            tw = trough_width(d)
            tl = trough_length_(length)
            cx = cur_x + tw / 2
            fmt, lw, lh = label_dims(d, p)
            trough_top_y = half_d - TOP_PAD - LABEL_MARGIN - lh
            cy = trough_top_y - tl / 2
            label_y = trough_top_y + LABEL_MARGIN + lh / 2
            out.append({"d": d, "p": p, "x": cx, "y": cy, "w": tw, "tl": tl,
                        "label_y": label_y, "label_w": lw, "label_h": lh,
                        "fmt": fmt})
            cur_x += tw + gap
        return out

    def row2_positions(taps_list, gap):
        cur_x = -cav_w / 2 + gap
        out = []
        for d, p, length in taps_list:
            tw = trough_width(d)
            tl = trough_length_(length)
            cx = cur_x + tw / 2
            fmt, lw, lh = label_dims(d, p)
            cy = y_bot_row_bottoms + tl / 2
            label_y = cy + tl / 2 + LABEL_MARGIN + lh / 2
            out.append({"d": d, "p": p, "x": cx, "y": cy, "w": tw, "tl": tl,
                        "label_y": label_y, "label_w": lw, "label_h": lh,
                        "fmt": fmt})
            cur_x += tw + gap
        return out

    row1_pos = row1_positions(row1, row1_gap)
    row2_pos = row2_positions(row2, row2_gap)

    horiz_pos = []
    if horiz:
        max_lw = max(label_single_line(d, p)[1] for d, p, _ in horiz)
        h_tap_left = -cav_w / 2 + H_LEFT_PAD + max_lw + H_LABEL_TO_TAP

        max_h_len = max(trough_length_(length) for _, _, length in horiz)
        x_lo = h_tap_left
        x_hi = h_tap_left + max_h_len

        def overlapping(positions_list, x_lo, x_hi):
            return [tp for tp in positions_list
                    if (tp["x"] - tp["w"] / 2 < x_hi) and (tp["x"] + tp["w"] / 2 > x_lo)]

        r1_in_range = overlapping(row1_pos, x_lo, x_hi)
        r2_in_range = overlapping(row2_pos, x_lo, x_hi)
        # Row 1: trough -Y end (label is ABOVE trough so doesn't reach middle).
        if r1_in_range:
            row1_lowest_bot = min(tp["y"] - tp["tl"] / 2 for tp in r1_in_range)
        else:
            row1_lowest_bot = half_d
        # Row 2: label top (label rises ABOVE trough into middle).
        if r2_in_range:
            row2_highest_top = max(tp["label_y"] + tp["label_h"] / 2
                                    for tp in r2_in_range)
        else:
            row2_highest_top = y_bot_row_bottoms

        safe_y_min = row2_highest_top + MIDDLE_CLEARANCE
        safe_y_max = row1_lowest_bot - MIDDLE_CLEARANCE
        h_stack_h = sum(trough_width(d) for d, _, _ in horiz) + (len(horiz) - 1) * H_INTER_GAP
        slack = (safe_y_max - safe_y_min) - h_stack_h
        print(f"  horizontal stack: avail={safe_y_max-safe_y_min:.2f}mm "
              f"stack={h_stack_h:.2f}mm slack={slack:.2f}mm")
        if slack < 0:
            print(f"  WARNING bin {side} horizontal stack overflows by {-slack:.2f}mm")

        cur_y = (safe_y_min + safe_y_max) / 2 + h_stack_h / 2
        label_x = -cav_w / 2 + H_LEFT_PAD + max_lw / 2
        for d, p, length in horiz:
            tw = trough_width(d)
            tl = trough_length_(length)
            cy = cur_y - tw / 2
            cx = h_tap_left + tl / 2
            horiz_pos.append({"d": d, "p": p, "x": cx, "y": cy, "w": tw, "tl": tl,
                              "label_x": label_x})
            cur_y -= tw + H_INTER_GAP

    return {
        "cav_w": cav_w, "cav_d": cav_d,
        "floor_top": floor_top, "top_z": top_z,
        "H": H, "z_units": z_units, "local_floor": local_floor,
        "y_bot_row_bottoms": y_bot_row_bottoms,
        "row1": row1_pos, "row2": row2_pos, "horiz": horiz_pos,
        "max_d_pair": max_d_pair,
    }


def build_bin(plan, side, x_units):
    L = compute_bin_layout(plan, side)
    top_z = L["top_z"]

    # Inverted floor: the bin's cavity floor is at top_z. Trough cylinders
    # cut DOWN into the solid material below — no per-tap plinths.
    bin_part = gridfinity_bin(x_units, Y_UNITS, L["z_units"], solid=False,
                              floor=L["local_floor"])

    for tp in L["row1"] + L["row2"]:
        bin_part = bin_part - trough_cut_vert(tp["d"], tp["tl"], top_z,
                                               tp["x"], tp["y"])
    for tp in L["horiz"]:
        bin_part = bin_part - trough_cut_horiz(tp["d"], tp["tl"], top_z,
                                                tp["x"], tp["y"])

    half_d = L["cav_d"] / 2

    # Slots — fixed 10mm depth below the floor surface, centered along the
    # row's max-trough Y.
    for row_key, near_pos_y in (("row1", True), ("row2", False)):
        positions_list = L[row_key]
        if not positions_list:
            continue
        leftmost = min(tp["x"] - tp["w"] / 2 for tp in positions_list)
        rightmost = max(tp["x"] + tp["w"] / 2 for tp in positions_list)
        slot_x_len = (rightmost - leftmost) - 2 * SLOT_X_INSET
        slot_x_centre = (leftmost + rightmost) / 2
        # Use the longest tap's center Y for the slot.
        long_tp = max(positions_list, key=lambda tp: tp["tl"])
        slot_y_centre = long_tp["y"]
        slot_z_centre = top_z - ROW_SLOT_DEPTH / 2
        slot = Box(slot_x_len, ROW_SLOT_WIDTH, ROW_SLOT_DEPTH).moved(
            Location(Vector(slot_x_centre, slot_y_centre, slot_z_centre))
        )
        bin_part = bin_part - slot

    # Per-tap floor labels for both rows (above each trough, varying Y).
    row1_lbl = select_visible_x(L["row1"], direction="ltr")
    for tp in row1_lbl:
        if tp["include"]:
            bin_part = bin_part + emboss_floor_label(tp, top_z)

    row2_lbl = select_visible_x(L["row2"], direction="ltr")
    for tp in row2_lbl:
        if tp["include"]:
            bin_part = bin_part + emboss_floor_label(tp, top_z)

    # Horizontals: single-line floor labels to the LEFT of each tap.
    horiz_label_dims = []
    for tp in L["horiz"]:
        text, lw, lh = label_single_line(tp["d"], tp["p"])
        horiz_label_dims.append((tp["label_x"], tp["y"], lw, lh))
        bin_part = bin_part + emboss_floor_single_line(text, tp["label_x"],
                                                        tp["y"], top_z)

    # Standard-pitch highlight rings — both rows, on the floor.
    floor_h = LABEL_EMBOSS + 0.4
    floor_z_centre = top_z + floor_h / 2 - 0.2

    def _floor_recess_cutter(tp, vertical):
        tw = trough_width(tp["d"])
        sx = tw + 2 * RING_RECESS_GAP if vertical else tp["tl"] + 2 * RING_RECESS_GAP
        sy = tp["tl"] + 2 * RING_RECESS_GAP if vertical else tw + 2 * RING_RECESS_GAP
        return Box(sx, sy, floor_h).moved(
            Location(Vector(tp["x"], tp["y"], floor_z_centre))
        )

    def _floor_label_cutter(lx, ly, lw, lh):
        return Box(lw + 2 * RING_LABEL_GAP, lh + 2 * RING_LABEL_GAP, floor_h).moved(
            Location(Vector(lx, ly, floor_z_centre))
        )

    floor_cutters = []
    for tp in L["row1"] + L["row2"]:
        floor_cutters.append(_floor_recess_cutter(tp, vertical=True))
    for tp in L["horiz"]:
        floor_cutters.append(_floor_recess_cutter(tp, vertical=False))

    for tp in row1_lbl + row2_lbl:
        if not tp["include"]:
            continue
        floor_cutters.append(_floor_label_cutter(tp["x"], tp["label_y"],
                                                  tp["label_w"], tp["label_h"]))
    for lx, ly, lw, lh in horiz_label_dims:
        floor_cutters.append(_floor_label_cutter(lx, ly, lw, lh))

    # Clip anything beyond the cavity inner walls (rings around labels close
    # to a wall would otherwise add material past the bin's outer surface).
    big = 200.0
    cav_w = L["cav_w"]
    for sign in (+1, -1):
        floor_cutters.append(Box(2 * cav_w + 2 * big, big, floor_h).moved(
            Location(Vector(0, sign * (half_d + big / 2), floor_z_centre))
        ))
        floor_cutters.append(Box(big, 2 * half_d + 2 * big, floor_h).moved(
            Location(Vector(sign * (cav_w / 2 + big / 2), 0, floor_z_centre))
        ))

    for tp in row1_lbl + row2_lbl:
        if not tp["include"] or not is_standard_pitch(tp["d"], tp["p"]):
            continue
        ring = make_floor_ring(tp["x"], tp["label_y"], top_z,
                                tp["label_w"], tp["label_h"])
        for c in floor_cutters:
            ring = ring - c
        bin_part = bin_part + ring

    return bin_part, L, row1_lbl, row2_lbl


if __name__ == "__main__":
    from build123d import Mesher

    plan = plan_layout()
    print("=== plan ===")
    print(f"horizontals (bin A): {[(d, p) for d, p, _ in plan['horiz']]}")
    print(f"row1 A: {len(plan['row1_A'])} taps  B: {len(plan['row1_B'])} taps")
    print(f"row2 A: {len(plan['row2_A'])} taps  B: {len(plan['row2_B'])} taps")
    print(f"cavity widths: A={plan['cav_A']:.2f}  B={plan['cav_B']:.2f}")
    print(f"x_units: A={plan['x_a']:.4f}  B={plan['x_b']:.4f}  sum={plan['x_a']+plan['x_b']:.4f}")
    print(f"row1 gap: A={plan['row1_gap_A']:.2f}  B={plan['row1_gap_B']:.2f}")
    print(f"row2 gap (uniform): {plan['row2_gap']:.2f}")

    for side in ("A", "B"):
        x_units = plan["x_a"] if side == "A" else plan["x_b"]
        print(f"\n=== bin {side} ({x_units:.3f}×{Y_UNITS}) ===")
        bin_part, L, r1, r2 = build_bin(plan, side, x_units)
        bb = bin_part.bounding_box().size
        print(f"H={L['H']:.2f}  z_units={L['z_units']:.3f}  TOP_Z={L['top_z']:.2f}")
        print(f"bbox={bb.X:.2f}×{bb.Y:.2f}×{bb.Z:.2f}  vol={bin_part.volume:.0f}mm³")
        print(f"row 1: {len(L['row1'])} taps; row 2: {len(L['row2'])}; horiz: {len(L['horiz'])}")
        n_r1_kept = sum(1 for tp in r1 if tp["include"])
        n_r2_kept = sum(1 for tp in r2 if tp["include"])
        print(f"row 1 wall labels: {n_r1_kept}/{len(r1)} kept")
        skipped = [f"M{tp['d']:g}×{tp['p']:.2f}" for tp in r1 if not tp["include"]]
        if skipped:
            print(f"  skipped: {', '.join(skipped)}")
        print(f"row 2 floor labels: {n_r2_kept}/{len(r2)} kept")
        skipped = [f"M{tp['d']:g}×{tp['p']:.2f}" for tp in r2 if not tp["include"]]
        if skipped:
            print(f"  skipped: {', '.join(skipped)}")

        from bin import OUT

        name = f"gridfinity_tap_bin_{side.lower()}"
        export_step(bin_part, os.path.join(OUT, f"{name}.step"))
        print(f"wrote {name}.step")
        try:
            m = Mesher()
            m.add_shape(bin_part)
            m.write(os.path.join(OUT, f"{name}.3mf"))
            print(f"wrote {name}.3mf")
        except Exception as e:
            print(f"3MF export failed ({type(e).__name__}: {e}); STEP is fine")
