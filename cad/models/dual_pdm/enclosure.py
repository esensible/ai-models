# Single-print dual dingoPDM enclosure (build123d).
# All values from spec.py. Construction, per the agreed design:
#   1. place two stock cases relative to the boards (ground truth)
#   2. boolean off each half's join-side wall + tabs
#   3. extrude the full cut profile (walls + roof + skirts) across the gap
#   4. solid divider wall between the halves, clear of both PCBs, bottom
#      DIV_CLEAR above the heatsink plane (skirts stay stock height and
#      define seating; the divider carries the tolerance)
#   5. enclosed recessed M6 SHCS through the divider into the heatsink
#   6. shallow roof reliefs under the bus bars (bars bolt onto the RedCube
#      block tops, which protrude through the roof windows)
from build123d import *
import copy
import spec as S

BIG = 400
stock = import_step(S.dingopdm('Export/V7.5/Case/Case.step'))
A = Pos(S.CTR_A[0], S.CTR_A[1], 0) * stock
B = Pos(S.CTR_B[0], S.CTR_B[1], 0) * copy.copy(stock)
cut_a = S.CTR_A[0] + S.CUT_LOCAL
cut_b = S.CTR_B[0] - S.CUT_LOCAL
assert S.CUT_LOCAL <= S.WALL_OUT - S.WALL_T - S.CUT_MARGIN

# 1+2. remove join-side wall + tabs from each half
A_cut = A - Pos(cut_a + BIG / 2, S.CTR_A[1], 0) * Box(BIG, BIG, BIG)
B_cut = B - Pos(cut_b - BIG / 2, S.CTR_A[1], 0) * Box(BIG, BIG, BIG)

# 3. bridge: extrude A's cut profile across to B's cut plane
prof = section(A.solids()[0], Plane.YZ.offset(cut_a))
bridge = extrude(prof, cut_b - cut_a)
bb = bridge.bounding_box()
assert abs(bb.min.X - cut_a) < 0.01 and abs(bb.max.X - cut_b) < 0.01, \
    f'bridge extruded wrong way: {bb.min.X:.2f}..{bb.max.X:.2f}'

# 4. divider wall, PCB_CLEAR from each board edge, DIV_CLEAR above heatsink
d1, d2 = S.BOARD_W + S.PCB_CLEAR, S.BOARD_W + S.GAP - S.PCB_CLEAR
db, dt = S.HS_TOP + S.DIV_CLEAR, S.ROOF_BOT + 0.8
divider = Pos((d1 + d2) / 2, S.CTR_A[1], (db + dt) / 2) * \
    Box(d2 - d1, 2 * S.CASE_HALF_L - 2.5, dt - db)
boss = Pos(*S.JOINT_SCREW, (S.BOSS_BOT + dt) / 2) * Cylinder(S.BOSS_R, dt - S.BOSS_BOT)

enclosure = A_cut + B_cut + bridge + divider + boss

# 5. enclosed screw recess (through the roof) + hole; 6. bus-bar roof reliefs
cut = [Pos(*S.JOINT_SCREW, (S.SEAT_Z + 21) / 2) * Cylinder(S.RECESS_D / 2, 21 - S.SEAT_Z),
       Pos(*S.JOINT_SCREW, (S.SEAT_Z - 6) / 2 + 0.025) * Cylinder(S.JOINT_HOLE / 2, S.SEAT_Z + 6.05)]
RELIEFS = [(S.STUDS_P[0][1], S.BAR_W_P, S.STUDS_P[0][0] - S.BAR_END, S.STUDS_P[1][0] + S.BAR_END),
           (S.STUDS_N[0][1], S.BAR_W_N, S.STUDS_N[0][0] - S.BAR_END, S.STUDS_N[1][0] + S.BAR_END)]
for v, w, u1, u2 in RELIEFS:
    cut.append(Pos((u1 + u2) / 2, v, S.ROOF_TOP - S.BAR_RELIEF + 5) * Box(u2 - u1, w, 10))
enclosure -= cut

bb = enclosure.bounding_box()
print(f'enclosure: bbox ({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f}) -> '
      f'({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})  vol {enclosure.volume/1000:.1f} cm3  '
      f'solids {len(enclosure.solids())}')
assert len(enclosure.solids()) == 1, 'enclosure must be a single solid'
for name, x0 in (('board A', 0.0), ('board B', S.B_OFF)):
    board = Pos(x0 + S.CTR_A[0], S.CTR_A[1], S.PCB_T / 2) * \
        Box(S.BOARD_W, S.BOARD_L, S.PCB_T)
    i = enclosure.intersect(board)
    v = sum(s.volume for s in i.solids()) if i else 0
    print(f'{name} intersection volume (want 0): {v:.4f}')
    assert v == 0, f'enclosure intersects {name}'

export_stl(enclosure, f'{S.OUT}/case_dual_mod.stl')
export_step(enclosure, f'{S.OUT}/case_dual_mod.step')
