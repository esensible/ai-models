# Single-print dual dingoPDM enclosure (build123d) -- rev 4.
# Datum frame: board A lower-left PCB corner, X right (join direction), Y up
# in plan (board long axis), Z up, z=0 at PCB bottom. Boards at 82.39 pitch.
#
# Key measured facts this build relies on:
#   - side wall: outer x 40.195, 3.0 thick; main roof: z 12.2 .. ~15.05
#   - RedCube blocks are 17.0 tall, topping out at z 15.23 THROUGH the roof
#     windows: the bus bars bolt on above the roof, so the divider needs no
#     corridors -- only a 1.0 shallow relief channel in the roof top per bar
#   - embossed '+' / '-' roof symbols sit in the bar paths (removed by reliefs)
from build123d import *

# ---- parameters -------------------------------------------------------------
PITCH = 82.39
A_POS, B_POS = 36.195, 118.585   # board centers (datum u)
CUT_LOCAL = 36.5                 # cut plane, case-local |x|: inside the wall
                                 #   inner face (37.2) and within flat roof
PCB_CLEAR = 0.5                  # divider clearance to each PCB edge
HS_TOP = -0.5                    # heatsink top plane (PCB bottom - 0.5 pad)
DIV_CLEAR = 0.3                  # divider bottom sits this far above the
                                 #   heatsink top: seating is defined by the
                                 #   stock-height skirts (rebate depth 3.175
                                 #   exactly); the un-rebated divider gets the
                                 #   tolerance so it can never hold the case up
ROOF_BOT = 12.2                  # measured roof underside
SCREWS_V = [60.0]                # single joint screw, between the DT connectors
BOSS_R = 6.5
BOSS_BOT = 4.0
SEAT_Z = 4.8                     # screw seat (stock lobe height)
RECESS_R = 5.75                  # M6 SHCS head 10.0 + clearance
HOLE_R = 3.6
RELIEF_Z = 14.05                 # bar relief: roof shaved above this z
RELIEFS = [(34.798, 16.0, 4, 104),   # (v line, width, u start, u end): +12V
           (89.154, 13.5, -1, 98)]   # GND (width capped by back wall at v96.25)
import os
DINGOPDM = os.environ.get('DINGOPDM_DIR', os.path.expanduser('~/dingoPDM'))
CASE = os.path.join(DINGOPDM, 'Export/V7.5/Case/Case.step')
assert os.path.exists(CASE), \
    'clone https://github.com/corygrant/dingoPDM and set DINGOPDM_DIR to it'
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
os.makedirs(OUT, exist_ok=True)
BIG = 400

stock = import_step(CASE)
A = Pos(A_POS, 47.625, 0) * stock
B = Pos(B_POS, 47.625, 0) * stock
cut_a = A_POS + CUT_LOCAL        # 72.695
cut_b = B_POS - CUT_LOCAL        # 82.085

# 1. boolean off the join-side wall + tabs of each half
A_cut = A - Pos(cut_a + BIG / 2, 47.625, 0) * Box(BIG, BIG, BIG)
B_cut = B - Pos(cut_b - BIG / 2, 47.625, 0) * Box(BIG, BIG, BIG)

# 2. extrude the full cut profile (walls + roof + skirts) across the gap
prof = section(A.solids()[0], Plane.YZ.offset(cut_a))
bridge = extrude(prof, cut_b - cut_a)
bb = bridge.bounding_box()
assert abs(bb.min.X - cut_a) < 0.01 and abs(bb.max.X - cut_b) < 0.01, \
    f'bridge extruded wrong way: {bb.min.X:.2f}..{bb.max.X:.2f}'

# 3. divider wall: side wall to side wall, heatsink top up into the roof
d1, d2 = 72.39 + PCB_CLEAR, 82.39 - PCB_CLEAR
db = HS_TOP + DIV_CLEAR
divider = Pos((d1 + d2) / 2, 47.625, (db + ROOF_BOT + 0.8) / 2) * \
    Box(d2 - d1, 103.25 - 2.5, ROOF_BOT + 0.8 - db)
bosses = [Pos(77.39, v, (BOSS_BOT + ROOF_BOT + 0.8) / 2) *
          Cylinder(BOSS_R, ROOF_BOT + 0.8 - BOSS_BOT) for v in SCREWS_V]

enclosure = A_cut + B_cut + bridge + divider + bosses

# 4. enclosed screw recesses (through the roof) + holes; bar relief channels
cut = []
for v in SCREWS_V:
    cut.append(Pos(77.39, v, (SEAT_Z + 21) / 2) * Cylinder(RECESS_R, 21 - SEAT_Z))
    cut.append(Pos(77.39, v, (SEAT_Z - 6) / 2 + 0.025) * Cylinder(HOLE_R, SEAT_Z + 6.05))
for v, w, u1, u2 in RELIEFS:
    cut.append(Pos((u1 + u2) / 2, v, RELIEF_Z + 5) * Box(u2 - u1, w, 10))
enclosure -= cut

bb = enclosure.bounding_box()
print(f'enclosure: bbox ({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f}) -> '
      f'({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})  vol {enclosure.volume/1000:.1f} cm3  '
      f'solids {len(enclosure.solids())}')
for name, x0 in (('board A', 0.0), ('board B', 82.39)):
    board = Pos(x0 + 36.195, 47.625, 0.815) * Box(72.39, 95.25, 1.63)
    i = enclosure.intersect(board)
    v = sum(s.volume for s in i.solids()) if i else 0
    print(f'{name} intersection volume (want 0): {v:.4f}')

export_stl(enclosure, f'{OUT}/case_dual_mod.stl')
export_step(enclosure, f'{OUT}/case_dual_mod.step')
