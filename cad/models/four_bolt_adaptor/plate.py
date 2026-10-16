# Adaptor plate between two 4-bolt fixtures (build123d).
# All values come from spec.py (single source of truth); importing spec runs
# the measurement-closure and hole-collision verifications.
from build123d import *
import math
import spec as S

pts = list(S.ALL_HOLES_PLATE.values())

# ---- outline: convex hull of the 8 hole centres, offset outward -------------
def hull(points):
    pts = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (
                (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])

OUTLINE_OFF = S.HOLE_DIA / 2 + S.EDGE_MARGIN     # 9: hole edge + margin
hull_face = make_face(Polyline(*hull(pts), close=True))
plate_face = offset(hull_face, OUTLINE_OFF, kind=Kind.ARC)
plate = extrude(plate_face, S.THICKNESS)

# ---- holes ------------------------------------------------------------------
cut = [Pos(*S.A_BORE_CTR, S.THICKNESS / 2) *
       Cylinder(S.BORE_DIA / 2, S.THICKNESS + 2)]
for x, y in pts:
    cut.append(Pos(x, y, S.THICKNESS / 2) * Cylinder(S.HOLE_DIA / 2, S.THICKNESS + 2))

# ---- screw recesses (v6) -----------------------------------------------------
# A-quad: 90 deg conical countersinks from the A face (z=0) for M5 flat heads.
# The cutter cone extends 1mm past the face on the same 45 deg slope.
def _csk(quad):
    ext = 1.0
    r_mouth = S.CSK_DIA / 2 + ext
    r_tip = S.HOLE_DIA / 2
    h = S.CSK_DEPTH + ext
    for k in ("TL", "TR", "BL", "BR"):
        x, y = quad[k]
        cut.append(Pos(x, y, -ext + h / 2) * Cone(r_mouth, r_tip, h))

# B-quad: HEX pockets from the B face (z=THICKNESS) capturing M5 hex
# nuts/heads (8 A/F) against rotation. Flats face +/-y (orientation is
# arbitrary for capture; fixed for repeatability). RegularPolygon's radius
# is the circumradius = across-corners/2.
def _rebate(quad):
    hex_face = RegularPolygon(S.POCKET_ACROSS_CORNERS / 2, 6, major_radius=True)
    for k in ("TL", "TR", "BL", "BR"):
        x, y = quad[k]
        cut.append(Pos(x, y, S.THICKNESS - S.REBATE_DEPTH) *
                   extrude(hex_face, S.REBATE_DEPTH + 1))

if S.RECESS_A:
    _csk(S.A_QUAD)
if S.RECESS_B:
    _rebate(S.B_HOLES_PLATE)

# ---- face marking: which side mates with fixture B (reads correctly from +z)
cut.append(Pos(22, -9, S.THICKNESS - 0.6) *
           extrude(Text("B SIDE", font_size=6), 0.6))
plate -= cut

# ---- verify + export --------------------------------------------------------
# Below any recess (z=1.0 < THICKNESS-CB_DEPTH) the section is always the clean
# through pattern: bore + 8 holes = 9 wires. The recess-level count is reported
# but not asserted (the accepted A-TR/B-TR breach merges two features there).
bb = plate.bounding_box()
print(f"plate: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {plate.volume/1000:.1f} cm3")
# M5 geometry (TR centres 7.40, BR 9.36; hole r 2.75, cone r(z)=5.3-z to
# z=2.55, rebate r 5.1 over z 1.5-4): the BR corner never merges. TR merges
# in every band EXCEPT a thin window around z~1 where cone+hole = 7.05 < 7.40:
#   z=0.4  A cones + B holes, TR merged      -> 8
#   z=1.0  A cones + B holes, all separate   -> 9
#   z=2.0  A cones + B rebates, TR merged    -> 8
#   z=3.3  A holes + B rebates, TR merged    -> 8  (below the face engraving)
for z, nexp in ((0.4, 8), (1.0, 9), (2.0, 8), (3.3, 8)):
    sec = section(plate.solids()[0], Plane.XY.offset(z))
    inner = [w for f in sec.faces() for w in f.inner_wires()]
    print(f"  features at z{z:.2f}: {len(inner)} (expect {nexp})")
    assert len(inner) == nexp, f"feature count mismatch at z={z}"
for (fx, name), (x, y) in S.ALL_HOLES_PLATE.items():
    d = math.dist((x, y), S.A_BORE_CTR) - S.HOLE_DIA / 2 - S.BORE_DIA / 2
    assert d >= 2.0, f"{fx}-{name} cuts into the bore (wall {d:.2f})"
export_stl(plate, f"{S.OUT}/four_bolt_adaptor.stl")
export_step(plate, f"{S.OUT}/four_bolt_adaptor.step")
print("exported four_bolt_adaptor.stl/.step")
