# Left/right dual-dingoPDM enclosures (build123d), v4: stock single cases
# adapted to the NO-intermediate-plate stack (boards on one 0.5 pad directly
# on the 204 heatsink). Replaces the old merged/bridged enclosure entirely.
#
# Per side, from the stock V7.5 Case.step (own-centre frame, z = datum):
#   1. remove the 3.175 skirt: cut everything below HS_TOP (-0.5) -- the wall
#      bottoms then sit flush on the heatsink. In this board-anchored frame
#      every wall feature (USB opening) STAYS board-aligned, which realises
#      the user's "move the USB hole up 3.175" as seen from the case bottom.
#   2. restore the tab thickness: extrude the ear footprints (sectioned at
#      z=1, screw holes included) to span -0.5..LOBE_TOP+3.175 -- original
#      8.475 total, so the stock M6x14 engagement is unchanged.
#   3. truncate the JOIN-side ears at the assembly centreline (45.805 from
#      the case's own centre = (PITCH - 0) / 2).
#   4. mounting holes at the join: ONE per y-position, centred exactly ON the
#      cut plane -- each case carries a clean half-hole; the two halves butt
#      into a full round hole shared by a single screw.
from build123d import *
import copy
import spec as S

BIG = 400
EAR_TOP = S.LOBE_TOP + 3.175           # 7.975: stock seat + the removed
                                       #   intermediate-plate thickness
CUT_LOCAL = S.PITCH / 2                # 45.805: assembly centreline in the
                                       #   case's own frame
JOINT_TOL = 0.4                        # total clearance at the butted tab
                                       #   ends (0.2 per side, user spec)

stock = import_step(S.dingopdm('Export/V7.5/Case/Case.step'))

# Ear columns: extrude the z=1 cross-section (ears + screw holes + the
# corner material that spans the case's ~3mm 45-degree corner chamfers),
# restricted to the ear/corner ZONES, then subtract a prism of the case's
# own z=10 outline (shrunk 0.2 for wall overlap). The subtraction guarantees
# NOTHING lands inboard of the walls/chamfers -- the board space stays
# untouched -- while the corner triangles beyond the chamfer faces survive.
# (A perimeter-wide rim is deliberately avoided: wall features like the USB
# opening vary with z, and extruding their z=1 shape corrupts them.)
_sec1 = section(stock.solids()[0], Plane.XY.offset(1.0))
_sec10 = section(stock.solids()[0], Plane.XY.offset(10.0))
_body = make_face(_sec10.faces()[0].outer_wire())
_full = Pos(0, 0, S.HS_TOP) * extrude(_sec1.faces()[0], EAR_TOP - S.HS_TOP)
_zones = []
for sx in (-1, 1):
    _zones.append(Pos(sx * (S.WALL_OUT - 0.2 + BIG / 2), 0, 0) * Box(BIG, BIG, BIG))
    for sy in (-1, 1):
        _zones.append(Pos(sx * (36.9 + 25), sy * (48.2 + 25), 0) * Box(50, 50, BIG))
_col = None
for z in _zones:
    piece = _full.intersect(z)
    if piece and piece.solids():
        _col = piece if _col is None else _col + piece
_col -= Pos(0, 0, S.HS_TOP - 1) * extrude(offset(_body, -0.2), EAR_TOP - S.HS_TOP + 2)

def make_side(sgn):
    """sgn=+1: truncate the +x ears (LEFT case); sgn=-1: the -x ears (RIGHT)."""
    c = copy.copy(stock)
    # 1. skirt off
    c -= Pos(0, 0, S.HS_TOP - BIG / 2) * Box(BIG, BIG, BIG)
    # 2. full-thickness ear columns (chamfer-spanning triangles included; the
    #    footprint already overlaps 0.2 into the walls)
    c += copy.copy(_col)
    # 3. truncate the join-side ears 0.2 short of the centreline (0.4 total
    #    joint tolerance across the two cases -- user spec)
    c -= Pos(sgn * (CUT_LOCAL - JOINT_TOL / 2 + BIG / 2), 0, 0) * Box(BIG, BIG, BIG)
    # 4. shared mounting holes: cut on the TRUE centreline (concentric with
    #    the tapped heatsink holes) -- each case carries slightly less than a
    #    half-hole because of the joint tolerance. These cuts also swallow
    #    the remnant arcs of the stock inner holes.
    for sy in (-S.CASE_SCREW_DY, S.CASE_SCREW_DY):
        c -= Pos(sgn * CUT_LOCAL, sy, EAR_TOP / 2) * \
            Cylinder(S.CASE_SCREW_HOLE / 2, EAR_TOP + 22)
    return c

left = Pos(S.CTR_A[0], S.CTR_A[1], 0) * make_side(+1)
right = Pos(S.CTR_B[0], S.CTR_B[1], 0) * make_side(-1)

# ---- verify + export --------------------------------------------------------
for name, part in (('dual_pdm_case_left', left), ('dual_pdm_case_right', right)):
    bb = part.bounding_box()
    print(f'{name}: ({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f}) -> '
          f'({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})  '
          f'vol {part.volume/1000:.1f} cm3  solids {len(part.solids())}')
    assert len(part.solids()) == 1, f'{name} not a single solid'
    assert abs(bb.min.Z - S.HS_TOP) < 0.01, f'{name} bottom not at the heatsink'
    export_stl(part, f'{S.OUT}/{name}.stl')
    export_step(part, f'{S.OUT}/{name}.step')

# the cases must meet with exactly JOINT_TOL of air between the tab ends
inter = left.intersect(right)
vi = sum(s.volume for s in inter.solids()) if inter else 0
print(f'left vs right interpenetration (want 0): {vi:.4f}')
assert vi < 1e-6

# close the joint gap artificially (shift right by JOINT_TOL): the faces
# must land coincident (still zero interpenetration) and the partial holes
# must close into full round holes on the centreline
JOIN_X = (S.CTR_A[0] + S.CTR_B[0]) / 2
right_closed = Pos(-JOINT_TOL, 0, 0) * copy.copy(right)
inter2 = left.intersect(right_closed)
vi2 = sum(s.volume for s in inter2.solids()) if inter2 else 0
print(f'gap-closed interpenetration (want 0, proves gap == {JOINT_TOL}): {vi2:.4f}')
assert vi2 < 1e-6
pair = left + right_closed
sec = section(pair.solids()[0], Plane.XY.offset(3.0))
join_holes = []
for f in sec.faces():
    for w in f.inner_wires():
        wb = w.bounding_box()
        cx = (wb.min.X + wb.max.X) / 2
        if abs(cx - JOIN_X) < 2.0 and 5 < (wb.max.X - wb.min.X) < 9:
            join_holes.append((cx, (wb.min.Y + wb.max.Y) / 2,
                               wb.max.X - wb.min.X))
# in the gap-closed test each side contributes (R - tol/2) of arc, so the
# union hole reads CASE_SCREW_HOLE - JOINT_TOL wide; in the real assembly
# the arcs sit concentric on the true centreline at full radius
print(f'shared join holes at z3: {join_holes} '
      f'(expect 2x, width {S.CASE_SCREW_HOLE - JOINT_TOL} in the gap-closed test)')
assert len(join_holes) == 2
for cx, cy, d in join_holes:
    assert abs(d - (S.CASE_SCREW_HOLE - JOINT_TOL)) < 0.1, 'join hole not clean'

# the USB opening must remain intact on both -y walls (board-aligned)
for name, part, ctr in (('left', left, S.CTR_A[0]), ('right', right, S.CTR_B[0])):
    sec = section(part.solids()[0],
                  Plane(origin=(0, S.CTR_A[1] - 50.5, 0), z_dir=(0, 1, 0)))
    ok = False
    for f in sec.faces():
        for w in f.inner_wires():
            wb = w.bounding_box()
            if wb.min.Z > 0 and wb.max.Z < 8.5 and (wb.max.X - wb.min.X) > 10:
                print(f'{name} USB opening: x {wb.min.X - ctr:.2f}..'
                      f'{wb.max.X - ctr:.2f} (local)  z {wb.min.Z:.2f}..{wb.max.Z:.2f}')
                ok = True
    assert ok, f'{name}: USB opening missing or clipped'
print(f'centreline JOIN_X = {JOIN_X}  ear span {2 * CUT_LOCAL:.2f} per pair, '
      f'ear thickness {EAR_TOP - S.HS_TOP:.3f} (= stock 8.475)')
