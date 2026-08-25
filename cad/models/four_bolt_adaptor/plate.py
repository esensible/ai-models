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

# ---- A-hole recesses (v2): cut from the A mating face (z=0) -----------------
# User-accepted: the A-TR recess breaches B-TR's hole (bolt clash understood;
# hardware will be adapted at that corner).
for k in ("TL", "TR", "BL", "BR"):
    x, y = S.A_QUAD[k]
    z_ctr = (S.CB_DEPTH / 2 - 0.5) if S.CB_SIDE_A else (S.THICKNESS - S.CB_DEPTH / 2 + 0.5)
    cut.append(Pos(x, y, z_ctr) * Cylinder(S.CB_DIA / 2, S.CB_DEPTH + 1))

# ---- face marking: which side mates with fixture B (reads correctly from +z)
cut.append(Pos(22, -9, S.THICKNESS - 0.6) *
           extrude(Text("B SIDE", font_size=6), 0.6))
plate -= cut

# ---- verify + export --------------------------------------------------------
# Recess side carries: bore + 4 B holes + 4 recesses, with the A-TR recess
# merged into B-TR's hole (accepted breach) = 8 wires. Plain side: bore + 8
# holes = 9 wires. v2: recesses at the BOTTOM (A face), so z=2.5 is the
# recessed section and z=7.5 the plain one.
bb = plate.bounding_box()
print(f"plate: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {plate.volume/1000:.1f} cm3")
_zexp = ((2.5, 8), (7.5, 9)) if S.CB_SIDE_A else ((2.5, 9), (7.5, 8))
for z, nexp in _zexp:
    sec = section(plate.solids()[0], Plane.XY.offset(z))
    inner = [w for f in sec.faces() for w in f.inner_wires()]
    print(f"  inner wires z{z}: {len(inner)} (expect {nexp})")
    assert len(inner) == nexp, f"feature count mismatch at z={z}"
for (fx, name), (x, y) in S.ALL_HOLES_PLATE.items():
    d = math.dist((x, y), S.A_BORE_CTR) - S.HOLE_DIA / 2 - S.BORE_DIA / 2
    assert d >= 2.0, f"{fx}-{name} cuts into the bore (wall {d:.2f})"
export_stl(plate, f"{S.OUT}/four_bolt_adaptor.stl")
export_step(plate, f"{S.OUT}/four_bolt_adaptor.step")
print("exported four_bolt_adaptor.stl/.step")
