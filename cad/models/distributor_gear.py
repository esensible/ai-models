"""Helical involute gear — replacement for a vintage distributor's nylon gear.

Involute tooth proportions (measured from the original part):
  - Module m = OD/(Z+2) = 1.075 (21.5/20), standard addendum
  - Pressure angle 20° → base radius = pitch_R · cos(20°) = 9.092
  - Addendum = m = 1.07 mm (tip above pitch circle)
  - Root (blank) diameter measured at 16.5 mm → dedendum 1.42 mm, whole depth
    2.50 mm. The root is specified DIRECTLY (--root-dia), not from the standard
    1.25 m dedendum, since the measured part's root is a touch deeper.

Tooth profile in each transverse section: spline-fitted involute from base
circle to OD, capped with an arc at the tip; below the base circle, a radial
line drops to the root circle, where an arc connects to the next tooth. The
section is rotated along Z to sweep the helix (piecewise-ruled loft).

Bore Ø7 mm with a 2.7 mm wide keyway at +X. Face width 11 mm. Exports STEP
(precise CAD) + STL (print/preview) to cad/out/. All dimensions are parametric:

  ./cad/run.sh cad/models/distributor_gear.py
  ./cad/run.sh cad/models/distributor_gear.py --teeth 18 --helix 22.5 --hand left \\
       --od 21.5 --root-dia 16.5 --bore 7 --keyway-w 2.7 --face-width 11
"""

import argparse
import math
import os

from build123d import (
    Axis,
    Box,
    BuildLine,
    BuildSketch,
    Cylinder,
    Line,
    Location,
    Spline,
    ThreePointArc,
    Vector,
    export_step,
    export_stl,
    fillet,
    loft,
    make_face,
)

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--od", type=float, default=21.5, help="outside (tip) diameter, mm")
ap.add_argument("--root-dia", type=float, default=16.5,
                help="root (blank) diameter — the cylinder the teeth sit on, mm. "
                     "Overrides the dedendum-derived root; set <=0 to derive it instead.")
ap.add_argument("--bore", type=float, default=7.0, help="bore diameter, mm")
ap.add_argument("--teeth", type=int, default=18, help="number of teeth Z")
ap.add_argument("--helix", type=float, default=22.5, help="helix angle, deg")
ap.add_argument("--hand", choices=("left", "right"), default="left", help="helix hand")
ap.add_argument("--pressure-angle", type=float, default=20.0, help="pressure angle, deg")
ap.add_argument("--keyway-w", type=float, default=2.7, help="keyway width, mm")
ap.add_argument("--keyway-h", type=float, default=1.0, help="keyway depth (radial), mm")
ap.add_argument("--face-width", type=float, default=11.0, help="gear face width, mm")
ap.add_argument("--addendum-factor", type=float, default=1.0, help="addendum / module")
ap.add_argument("--dedendum-factor", type=float, default=1.25, help="dedendum / module")
ap.add_argument("--samples", type=int, default=9, help="involute spline pts per flank")
ap.add_argument("--sections", type=int, default=9, help="loft sections along the helix")
ap.add_argument("--tag", default="distributor_gear", help="output file basename")
args = ap.parse_args()

OD = args.od
ID = args.bore
Z_TEETH = args.teeth
HELIX_ANGLE_DEG = args.helix
HELIX_DIRECTION = -1 if args.hand == "left" else 1   # -1 left-hand, +1 right-hand
KEYWAY_W = args.keyway_w
KEYWAY_H = args.keyway_h
FACE_WIDTH = args.face_width
PRESSURE_ANGLE_DEG = args.pressure_angle
ADDENDUM_FACTOR = args.addendum_factor
DEDENDUM_FACTOR = args.dedendum_factor
INVOLUTE_SAMPLES = args.samples
LOFT_SECTIONS = args.sections

OR = OD / 2
IR = ID / 2
MODULE = OD / (Z_TEETH + 2)
PITCH_R = MODULE * Z_TEETH / 2
BASE_R = PITCH_R * math.cos(math.radians(PRESSURE_ANGLE_DEG))
ADDENDUM = ADDENDUM_FACTOR * MODULE
# Root: take the measured blank/root diameter directly when given, else derive it
# from the standard dedendum. (A measured part may have a non-standard root depth.)
if args.root_dia > 0:
    ROOT_R = args.root_dia / 2
else:
    ROOT_R = PITCH_R - DEDENDUM_FACTOR * MODULE
DEDENDUM = PITCH_R - ROOT_R          # actual dedendum (below pitch circle)
WHOLE_DEPTH = ADDENDUM + DEDENDUM

EPS = 1e-3


def _involute_point(theta):
    return (BASE_R * (math.cos(theta) + theta * math.sin(theta)),
            BASE_R * (math.sin(theta) - theta * math.cos(theta)))


def _flank_pts(base_angle, theta_max, mirror=False):
    pts = []
    for k in range(INVOLUTE_SAMPLES):
        theta = k * theta_max / (INVOLUTE_SAMPLES - 1)
        x, y = _involute_point(theta)
        if mirror:
            y = -y
        ca, sa = math.cos(base_angle), math.sin(base_angle)
        pts.append(Vector(x * ca - y * sa, x * sa + y * ca))
    return pts


def gear_profile_2d():
    inv_alpha = math.tan(math.radians(PRESSURE_ANGLE_DEG)) - math.radians(PRESSURE_ANGLE_DEG)
    tooth_half_base = math.pi / (2 * Z_TEETH) + inv_alpha
    theta_max = math.sqrt((OR / BASE_R) ** 2 - 1)

    inv_x, inv_y = _involute_point(theta_max)
    inv_offset = math.atan2(inv_y, inv_x)

    pitch = 2 * math.pi / Z_TEETH

    with BuildSketch() as sk:
        with BuildLine():
            for i in range(Z_TEETH):
                center = i * pitch
                leading_base = center - tooth_half_base
                trailing_base = center + tooth_half_base
                ang_lead_tip = leading_base + inv_offset
                ang_trail_tip = trailing_base - inv_offset
                next_lead_base = (i + 1) * pitch - tooth_half_base

                # Leading flank (involute spline from base circle to OD)
                Spline(*_flank_pts(leading_base, theta_max, mirror=False))

                # Tip arc on OD
                ang_mid_tip = (ang_lead_tip + ang_trail_tip) / 2
                ThreePointArc(
                    (OR * math.cos(ang_lead_tip), OR * math.sin(ang_lead_tip)),
                    (OR * math.cos(ang_mid_tip), OR * math.sin(ang_mid_tip)),
                    (OR * math.cos(ang_trail_tip), OR * math.sin(ang_trail_tip)),
                )

                # Trailing flank (mirrored involute, OD back to base circle)
                trail = list(reversed(_flank_pts(trailing_base, theta_max, mirror=True)))
                Spline(*trail)

                # Radial drop from base circle to root circle (below base)
                Line(
                    (BASE_R * math.cos(trailing_base), BASE_R * math.sin(trailing_base)),
                    (ROOT_R * math.cos(trailing_base), ROOT_R * math.sin(trailing_base)),
                )

                # Root arc to next tooth
                ang_mid_root = (trailing_base + next_lead_base) / 2
                ThreePointArc(
                    (ROOT_R * math.cos(trailing_base), ROOT_R * math.sin(trailing_base)),
                    (ROOT_R * math.cos(ang_mid_root), ROOT_R * math.sin(ang_mid_root)),
                    (ROOT_R * math.cos(next_lead_base), ROOT_R * math.sin(next_lead_base)),
                )

                # Radial rise from root back up to base for next tooth's flank
                Line(
                    (ROOT_R * math.cos(next_lead_base), ROOT_R * math.sin(next_lead_base)),
                    (BASE_R * math.cos(next_lead_base), BASE_R * math.sin(next_lead_base)),
                )
        make_face()
    return sk.sketch.faces()[0]


def _ep(edge, t):
    """Endpoint of an edge (t=0 start, t=1 end) as a Vector. build123d uses the
    `@` operator for position-at-parameter — there is no .start_point()/.end_point()."""
    return edge @ t


def is_horizontal_edge_at(z, edge):
    pts = [_ep(edge, 0), _ep(edge, 1)]
    return all(abs(p.Z - z) < EPS for p in pts)


def is_vertical_edge(edge):
    p1, p2 = _ep(edge, 0), _ep(edge, 1)
    return abs(p1.X - p2.X) < EPS and abs(p1.Y - p2.Y) < EPS


def near_keyway(edge):
    p = _ep(edge, 0)
    return p.X > IR - 0.1 and abs(p.Y) < KEYWAY_W / 2 + 0.1


def build_gear():
    face_2d = gear_profile_2d()
    twist_total_rad = (HELIX_DIRECTION * FACE_WIDTH
                       * math.tan(math.radians(HELIX_ANGLE_DEG)) / PITCH_R)
    twist_total_deg = math.degrees(twist_total_rad)
    print(f"Module: {MODULE:.4f}, Pitch R: {PITCH_R:.3f}, "
          f"Base R: {BASE_R:.3f}, Root R: {ROOT_R:.3f}")
    print(f"Addendum: {ADDENDUM:.2f}, Dedendum: {DEDENDUM:.2f}, "
          f"Whole depth: {WHOLE_DEPTH:.2f} mm")
    print(f"Helix twist over face: {twist_total_deg:+.2f}° (hand = {args.hand})")

    sections = []
    for k in range(LOFT_SECTIONS):
        t = k / (LOFT_SECTIONS - 1)
        z = t * FACE_WIDTH
        twist = t * twist_total_deg
        sec = face_2d.rotate(Axis.Z, twist).moved(Location(Vector(0, 0, z)))
        sections.append(sec)

    gear_helical = loft(sections, ruled=True)

    hole = Cylinder(IR, FACE_WIDTH + 2).moved(Location(Vector(0, 0, FACE_WIDTH / 2)))
    keyway = Box(KEYWAY_H + 0.1, KEYWAY_W, FACE_WIDTH + 2).moved(
        Location(Vector(IR + KEYWAY_H / 2 - 0.05, 0, FACE_WIDTH / 2))
    )
    gear = gear_helical - hole - keyway

    fillet_edges = [
        e for e in gear.edges()
        if is_horizontal_edge_at(0, e)
        or is_horizontal_edge_at(FACE_WIDTH, e)
        or (is_vertical_edge(e) and near_keyway(e))
    ]
    print(f"Filleting {len(fillet_edges)} edges of {len(gear.edges())} total")
    for r in (0.2, 0.15, 0.1, 0.05):
        try:
            gear = fillet(fillet_edges, radius=r)
            print(f"  fillet {r}mm OK")
            break
        except Exception:
            print(f"  fillet {r}mm failed; trying smaller")
    else:
        print("  no fillet applied")
    return gear


gear = build_gear()
bb = gear.bounding_box().size
print(f"vol={gear.volume:.1f}mm³ bbox={bb.X:.2f}×{bb.Y:.2f}×{bb.Z:.2f}")

out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
step = os.path.join(out, f"{args.tag}.step")
stl = os.path.join(out, f"{args.tag}.stl")
export_step(gear, step)
print(f"wrote {os.path.relpath(step)}")
export_stl(gear, stl, tolerance=0.05, angular_tolerance=0.3)
print(f"wrote {os.path.relpath(stl)}")
