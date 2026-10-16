# DT benchtop test plugs (build123d), 4-way and 12-way.
#
# Built FROM the genuine TE/Deutsch DT06 plug models: we section the real
# plug in its constant-section region, take that outline as the body profile,
# and shrink it by the fit clearance. Cavity positions are read out of the
# same STEP, so body and contacts share one frame -- which matters, because
# the DT cavity grid is NOT centred in the body (the latch side is taller).
#
# Deliberately not reproduced: the latch catch, the wedgelock, the contact
# retention fingers, the seals. This is a bench fixture -- it must slide in
# and out by hand and just keep the contacts apart.
from build123d import *
import math
import os
import spec as S

VENDOR = os.environ.get("DT_CAD_DIR", "/root/vendor-cad")


def read_plug(stp, body_depth, cav_depth):
    """Return (body_profile_face, [(x, y), ...] cavity centres) from a DT06."""
    step = import_step(os.path.join(VENDOR, stp))
    top = step.bounding_box().max.Z

    sec = section(step, Plane(origin=(0, 0, top - body_depth), z_dir=(0, 0, 1)))
    face = max(sec.faces(), key=lambda f: f.area)
    prof = make_face(face.outer_wire())
    # The section face carries the donor's z. Bring it to z=0 or every later
    # feature is offset by that amount -- which silently left the front of the
    # plug with no bores at all (caught 2026-09-16).
    prof = Pos(0, 0, -prof.bounding_box().min.Z) * prof

    sec2 = section(step, Plane(origin=(0, 0, top - cav_depth), z_dir=(0, 0, 1)))
    voids = [w for f in sec2.faces() for w in f.inner_wires()]
    cav = []
    for w in voids:
        b = w.bounding_box()
        if b.size.X < 6.0:                      # skip the big seal bore
            cav.append(((b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2))
    pb = prof.bounding_box()
    print(f"    body {pb.size.X:.2f} x {pb.size.Y:.2f} "
          f"(y {pb.min.Y:+.2f}..{pb.max.Y:+.2f}), {len(cav)} cavities")
    return prof, sorted(cav, key=lambda c: (round(c[1], 1), c[0]))


def build(name, stp, body_depth, cav_depth, n_expect, pin1_corner):
    print(f"{name}:")
    prof, cav = read_plug(stp, body_depth, cav_depth)
    assert len(cav) == n_expect, f"found {len(cav)} cavities, expected {n_expect}"

    plan = offset(prof, -S.FIT_CLEAR, kind=Kind.ARC)
    part = extrude(plan, S.NOSE_L)
    part += Pos(0, 0, S.NOSE_L) * extrude(
        offset(plan, S.REAR_LIP, kind=Kind.ARC), S.BODY_L - S.NOSE_L)

    # Straight through-bores, front to back, no front neck: the user does not
    # want the contact retained (2026-09-16), only kept apart from its
    # neighbours as it flexes. A terminal can therefore pass clean through in
    # either direction.
    for x, y in cav:
        part -= Pos(x, y, -0.1) * Cylinder(
            S.CAV_D / 2, S.BODY_L + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    # --- pin-1 marker: a fat 45deg CHAMFER AROUND THE PIN 1 HOLE ------------
    # On the rear face, where terminals go in -- so the one you are looking
    # for is obvious while loading. It BREAKS INTO the nearest neighbouring
    # bore and that is intended: see PIN1_CHAMFER in spec.py. (Earlier
    # attempts put a dimple beside the hole, then a chamfer on the body
    # corner, then a deep shallow-angled funnel that stayed clear of the
    # neighbour -- the user rejected all three.)
    sx, sy = pin1_corner
    pin1 = max((c for c in cav if (c[0] > 0) == (sx > 0)
                and (c[1] > 0) == (sy > 0)), key=lambda c: abs(c[0]))
    r_out = S.CAV_D / 2 + S.PIN1_CHAMFER
    depth = S.PIN1_CHAMFER                      # 45deg: run == rise
    near = min(math.dist(pin1, c) for c in cav if c != pin1)
    breach = r_out - (near - S.CAV_D / 2)       # into the neighbour's wall
    print(f"  pin 1 at ({pin1[0]:+.3f},{pin1[1]:+.3f}); 45deg chamfer "
          f"Ø{S.CAV_D:.2f} -> Ø{2 * r_out:.2f} x {depth:.2f} deep; "
          f"breaks {breach:+.2f}mm into the neighbour {near:.2f} away")
    assert breach <= S.PIN1_BREACH_MAX, (
        f"the chamfer eats {breach:.2f}mm into the next bore -- past the "
        f"{S.PIN1_BREACH_MAX}mm allowed, the two cavities become one slot")

    before = part.volume
    part -= Pos(pin1[0], pin1[1], S.BODY_L - depth) * Cone(
        S.CAV_D / 2, r_out, depth + 0.001,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    removed = before - part.volume
    assert removed > 1.0, f"chamfer removed only {removed:.2f}mm3"

    # Prove the chamfer landed on the RIGHT hole, reached only the one
    # neighbour, and left every bore full-diameter below itself. A render
    # cannot show this: a chamfer that cuts air and one that cuts every hole
    # look identical at a glance (both happened, 2026-09-18).
    def wires_at(z):
        sec = section(part, Plane.XY.offset(z))
        return [w.bounding_box() for f in sec.faces() for w in f.inner_wires()]

    deep = wires_at(S.BODY_L - depth - 0.5)
    assert len(deep) == n_expect and all(
        abs(b.size.X - S.CAV_D) < 0.15 for b in deep), (
        f"below the chamfer the bores are not {n_expect} x Ø{S.CAV_D}: "
        f"{sorted(round(b.size.X, 2) for b in deep)}")

    mouth = wires_at(S.BODY_L - 0.05)
    assert len(mouth) == n_expect - 1, (
        f"{len(mouth)} openings at the rear face, expected {n_expect - 1} "
        f"(pin 1 merged with exactly one neighbour)")
    merged = [b for b in mouth
              if b.min.X - 0.01 <= pin1[0] <= b.max.X + 0.01
              and b.min.Y - 0.01 <= pin1[1] <= b.max.Y + 0.01]
    assert len(merged) == 1, "could not identify the pin-1 opening"
    others = [b for b in mouth if b is not merged[0]]
    assert all(abs(b.size.X - S.CAV_D) < 0.15 for b in others), (
        f"the chamfer reached a bore it should not have: "
        f"{sorted(round(b.size.X, 2) for b in others)}")
    print(f"    verified: pin-1 opening {merged[0].size.X:.2f} x "
          f"{merged[0].size.Y:.2f} at the face, the other "
          f"{len(others)} bores untouched at Ø{max(b.size.X for b in others):.2f}"
          f", all Ø{max(b.size.X for b in deep):.2f} below the chamfer "
          f"({removed:.0f}mm3 removed)")

    bb = part.bounding_box()
    print(f"  plug {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}  "
          f"vol {part.volume / 1000:.2f} cm3  solids {len(part.solids())}")
    assert len(part.solids()) == 1, "cavities broke the body apart"

    # closest pair of cavities sets the thinnest isolating wall
    worst = min(((a, b) for i, a in enumerate(cav) for b in cav[i + 1:]),
                key=lambda p: (p[0][0] - p[1][0]) ** 2 +
                              (p[0][1] - p[1][1]) ** 2)
    d = ((worst[0][0] - worst[1][0]) ** 2 +
         (worst[0][1] - worst[1][1]) ** 2) ** 0.5
    wall = d - S.CAV_D
    print(f"  closest cavity pair {d:.3f} apart -> {wall:.2f}mm wall")
    assert wall >= S.WALL_MIN, (
        f"only {wall:.2f}mm between the closest cavities -- below WALL_MIN")

    # every cavity must keep material to the outside too
    pb = plan.bounding_box()
    for x, y in cav:
        edge = min(pb.max.X - abs(x), pb.max.Y - y, y - pb.min.Y)
        assert edge - S.CAV_D / 2 > 0.6, (
            f"cavity at ({x:.2f},{y:.2f}) is {edge - S.CAV_D / 2:.2f}mm "
            f"from the outside wall")

    export_stl(part, f"{S.OUT}/{name}.stl")
    export_step(part, f"{S.OUT}/{name}.step")
    print(f"  exported {name}.stl/.step")


# body_depth: into the constant-section region, clear of the front seal ribs
# cav_depth : near the rear face, where the cavity mouths are open
build("dt_test_plug_4", "DT06-4S.stp", body_depth=10.0, cav_depth=30.5,
      n_expect=4, pin1_corner=S.PIN1_CORNER_4)
build("dt_test_plug_12", "DT06-12SA.stp", body_depth=14.0, cav_depth=29.0,
      n_expect=12, pin1_corner=S.PIN1_CORNER_12)
