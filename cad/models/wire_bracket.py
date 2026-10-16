# Wire-saddle bracket (build123d): 80 x 10 x 5 bar; the central 50mm of the
# TOP face's two long edges get generous fillets (insulated wiring rests
# there), tapering over a short transition back to square edges at the ends;
# two M5 clearance holes 40mm apart.
#
# The tapered fillet is built by subtraction: the 2D "corner minus quarter
# disc" removal profile is self-similar in the radius, so the transition is
# a loft between a full-size and a near-zero-scale copy -- same topology,
# no variable-radius fillet needed (OCC has none).
#
# Frame: origin at bar centre in x/y, z=0 bottom face, z=T top (wire) face.
from build123d import *
import math

L, W, T = 60.0, 10.0, 5.0     # [GROUND TRUTH user, rev 2026-09-08] 66->60
                              #   (v1 at 66/55 printed fine; dims corrected
                              #   after the flat-battery caliper episode)
FILLET_R = 2.0                # [CHOSEN] "generous" on a 5 thick bar: rounds
                              #   most of the edge, keeps 1mm of side wall
WIRE_ZONE = 35.0              # [GROUND TRUTH user, rev 2026-09-08] 40->35:
                              #   shortened so the transition (ends at
                              #   +-22.5) clears the hole edges (+-22.75)
TRANS = 5.0                   # [CHOSEN] fillet-to-square transition length
HOLE_D = 4.5                  # [GROUND TRUTH user, rev 2026-09-08] 4->4.5
HOLE_PITCH = 50.0             # [GROUND TRUTH user, rev 2026-09-08] 55->50:
                              #   holes land CONCENTRIC with the end arcs
                              #   (both at +-25)
R_MIN = 0.02                  # near-zero radius at the transition's outboard end

def corner_cut_face(r, sy):
    """Removal profile at one top corner (sy=+1: +y edge), in the YZ plane:
    the r x r corner square minus the quarter disc -- what a radius-r fillet
    removes. Self-similar in r."""
    y_edge = sy * W / 2
    pts = [(y_edge - sy * r, T), (y_edge, T), (y_edge, T - r)]
    line = Polyline(*pts)
    arc = RadiusArc(pts[2], pts[0], -r if sy > 0 else r)
    return make_face(Plane.YZ * (line + arc))

cuts = []
for sy in (-1, 1):
    mid = extrude(Pos(-WIRE_ZONE / 2, 0, 0) * corner_cut_face(FILLET_R, sy),
                  WIRE_ZONE, dir=(1, 0, 0))
    cuts.append(mid)
    for sx in (-1, 1):
        inner = Pos(sx * WIRE_ZONE / 2, 0, 0) * corner_cut_face(FILLET_R, sy)
        outer = Pos(sx * (WIRE_ZONE / 2 + TRANS), 0, 0) * \
            corner_cut_face(R_MIN, sy)
        cuts.append(loft([inner, outer]))

# plan outline: stadium -- fully radiused ends (r = W/2)
bar = extrude(SlotOverall(L, W), T)
part = bar
for c in cuts:
    part -= c
for sx in (-1, 1):
    part -= Pos(sx * HOLE_PITCH / 2, 0, T / 2) * Cylinder(HOLE_D / 2, T + 2)

# ---- verify + export --------------------------------------------------------
bb = part.bounding_box()
print(f"wire_bracket: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {part.volume / 1000:.2f} cm3  solids {len(part.solids())}")
assert len(part.solids()) == 1

def top_width_at(x):
    """Material width at the very top of the bar (z just under T), local to x."""
    slab = Pos(x, 0, T - 0.01) * Box(1.0, W + 2, 0.02)
    piece = part.intersect(slab)
    solids = piece.solids() if hasattr(piece, "solids") else piece
    ys = [v for s in solids for v in
          (s.bounding_box().min.Y, s.bounding_box().max.Y)]
    return max(ys) - min(ys)

w_mid = top_width_at(0)
# with L=60 there is no straight square section left (transition ends at the
# end-arc centre), so "square edges at the ends" is checked by comparing the
# TOP width against the MID-HEIGHT width at the same x in the end arc: equal
# widths = no fillet there
X_END = L / 2 - 3.0
def mid_width_at(x):
    slab = Pos(x, 0, T / 2) * Box(1.0, W + 2, 0.02)
    piece = part.intersect(slab)
    solids = piece.solids() if hasattr(piece, "solids") else piece
    ys = [v for s in solids for v in
          (s.bounding_box().min.Y, s.bounding_box().max.Y)]
    return max(ys) - min(ys)
w_end = top_width_at(X_END)
w_end_mid = mid_width_at(X_END)
print(f"  top width mid {w_mid:.2f} (fillets, expect ~{W - 2 * FILLET_R + 0.6:.1f}..{W - 2 * FILLET_R + 1.2:.1f}); "
      f"end arc at x={X_END:.1f}: top {w_end:.2f} vs mid-height {w_end_mid:.2f}")
assert abs(w_end - w_end_mid) < 0.05, "end edges must be square (no fillet)"
assert w_mid < W - 2 * (FILLET_R - 0.6), "middle must be filleted"
# holes present and clear
sec = section(part.solids()[0], Plane.XY.offset(T / 2))
holes = [w for f in sec.faces() for w in f.inner_wires()]
assert len(holes) == 2, f"expected 2 holes, found {len(holes)}"
for w in holes:
    wb = w.bounding_box()
    assert abs((wb.max.X - wb.min.X) - HOLE_D) < 0.05
print(f"  2x Ø{HOLE_D} holes at ±{HOLE_PITCH / 2} confirmed")
# end-region sanity: holes fully clear of the wire zone INCLUDING its
# transitions (user 2026-09-08), and enough wall to the end arc
assert HOLE_PITCH / 2 - HOLE_D / 2 > WIRE_ZONE / 2 + TRANS, \
    "hole encroaches on the wire-zone transition"
_arc_ctr = L / 2 - W / 2
_wall = W / 2 - abs(HOLE_PITCH / 2 - _arc_ctr) - HOLE_D / 2
assert _wall >= 2.0, f"hole to end-arc wall {_wall:.2f} < 2"
print(f"  hole clear of full-fillet zone; min wall to end arc {_wall:.2f}mm")

export_stl(part, "cad/out/wire_bracket.stl")
export_step(part, "cad/out/wire_bracket.step")
print("exported wire_bracket.stl/.step")
