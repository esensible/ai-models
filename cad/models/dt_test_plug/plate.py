# One plate: 1x DT 4-way test plug + 2x DT 12-way, laid out for a single print.
#
# Built from the exported STEPs rather than re-deriving the plugs, so the
# geometry printed is exactly the geometry plug.py verified. Run plug.py first.
#
# ORIENTATION -- the plugs print REAR FACE DOWN (flipped 180 about X).
# As modelled, the nose runs z 0..NOSE_L at the smaller (fit-clearance) outline
# and the rear lip runs NOSE_L..BODY_L at REAR_LIP larger. Printed that way up,
# the lip is a 1.9mm unsupported ledge standing out all the way round at z=12.
# Flipped, the widest section (the lip) is on the plate and every later step
# goes INWARD -- no overhang anywhere, and the bed contact roughly doubles.
# The pin-1 chamfer ends up on the first layer as a 45deg cone opening down,
# which prints clean.
from build123d import *
import os
import spec as S

GAP = 14.0          # [CHOSEN] clear space between parts. Deliberately LESS
                    #   than 2*BRIM_W so the brims overlap into one contiguous
                    #   first layer (see the assert below).
BRIM_W = 20.0       # [GROUND TRUTH user 2026-09-18] brim width the plate is
                    #   laid out for. Must match the BRIM= passed to slice.sh.
BED = 256.0         # P1S

# ORDER: the 4-way goes BETWEEN the two 12-ways (user 2026-09-18). On the
# first attempt it sat on the end and was the only part to let go -- it has
# the smallest footprint (20.4 x 19.4 vs 40.4 x 21.0) carrying the same 26mm
# of height. Between the two big parts its brim fuses to both of theirs, so
# it is anchored by the whole plate rather than by its own contact patch.
ORDER = ["dt_test_plug_12", "dt_test_plug_4", "dt_test_plug_12"]


def load_flipped(name):
    """Import a plug STEP, turn it rear-face down, and sit it on z=0."""
    part = import_step(os.path.join(S.OUT, f"{name}.step"))
    part = Rot(180, 0, 0) * part
    bb = part.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * part


def assert_no_overhang(part, name, steps=26):
    """Footprint must never GROW with height -- that is what an overhang is.

    This is the whole reason for the flip, so it is checked rather than
    asserted in a comment. Compares each layer's section bounding box with the
    one below; a widening box means material is starting in mid-air.
    """
    bb = part.bounding_box()
    prev = None
    worst = 0.0
    for i in range(1, steps):
        z = bb.min.Z + (bb.max.Z - bb.min.Z) * i / steps
        sec = section(part, Plane.XY.offset(z))
        if not sec.faces():
            continue
        b = sec.bounding_box()
        if prev is not None:
            grow = max(b.size.X - prev.size.X, b.size.Y - prev.size.Y) / 2
            worst = max(worst, grow)
        prev = b
    assert worst <= 0.05, (
        f"{name}: footprint grows by {worst:.2f}mm going up -- that is an "
        f"unsupported ledge; check the orientation")
    return worst


protos = {}
for name in dict.fromkeys(ORDER):
    proto = load_flipped(name)
    grow = assert_no_overhang(proto, name)
    bb = proto.bounding_box()
    print(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}"
          f"   max footprint growth {grow:.3f}mm (0 = no overhang)")
    protos[name] = proto

parts = []
placed = []
x = 0.0
seen = {}
for name in ORDER:
    proto = protos[name]
    bb = proto.bounding_box()
    seen[name] = seen.get(name, 0) + 1
    parts.append(Pos(x + bb.size.X / 2, 0, 0) * proto)
    placed.append((f"{name}#{seen[name]}", x, x + bb.size.X, bb.size.Y))
    x += bb.size.X + GAP

span_x = x - GAP
plate = parts[0]
for p in parts[1:]:
    plate += p
bb = plate.bounding_box()
plate = Pos(-bb.center().X, -bb.center().Y, 0) * plate

bb = plate.bounding_box()
print(f"\nplate: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}"
      f"   {len(plate.solids())} solids   vol {plate.volume / 1000:.2f} cm3")
assert len(plate.solids()) == len(parts), (
    f"{len(plate.solids())} solids from {len(parts)} parts -- they overlap")
assert bb.size.X < BED - 20 and bb.size.Y < BED - 20, (
    f"plate footprint {bb.size.X:.1f} x {bb.size.Y:.1f} leaves no room for "
    f"a brim on a {BED}mm bed")

# every pair must clear GAP, or brims will merge and the parts fuse
sol = plate.solids()
for i in range(len(sol)):
    for j in range(i + 1, len(sol)):
        a, b = sol[i].bounding_box(), sol[j].bounding_box()
        dx = max(0.0, max(a.min.X - b.max.X, b.min.X - a.max.X))
        dy = max(0.0, max(a.min.Y - b.max.Y, b.min.Y - a.max.Y))
        d = max(dx, dy)
        assert d >= GAP - 0.01, f"parts {i} and {j} are only {d:.2f}mm apart"
print(f"  all pairs >= {GAP}mm apart; contact area on the plate:")
for nm, x0, x1, sy in placed:
    print(f"    {nm:<20s} {x1 - x0:5.2f} x {sy:5.2f} footprint")

# The brims MUST merge into one contiguous first layer (user 2026-09-18). Two
# brims of BRIM_W each close a GAP when 2*BRIM_W > GAP; anything less leaves
# separate islands and the small part is on its own again -- which is how the
# 4-way came loose the first time.
overlap = 2 * BRIM_W - GAP
assert overlap > 4.0, (
    f"a {BRIM_W}mm brim across a {GAP}mm gap overlaps by only "
    f"{overlap:.1f}mm -- the first layer will not be contiguous")
print(f"  brims: {BRIM_W}mm each side of a {GAP}mm gap -> {overlap:.0f}mm of "
      f"overlap between neighbours (contiguous first layer)")
print(f"  first layer incl. brim: {bb.size.X + 2 * BRIM_W:.1f} x "
      f"{bb.size.Y + 2 * BRIM_W:.1f}mm")
assert bb.size.X + 2 * BRIM_W < BED - 10 and bb.size.Y + 2 * BRIM_W < BED - 10, (
    "plate plus brim does not fit the bed")

export_stl(plate, f"{S.OUT}/dt_test_plug_plate.stl")
print(f"\n  exported dt_test_plug_plate.stl")
