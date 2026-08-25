# Dual-CANBoard enclosure: base + lid (build123d). All values from spec.py.
#   - PCBs on 5mm bosses with 45-degree conical flares to the floor
#   - AT04-12P PanelMate on EACH long wall (opposite), AT04-4P on the -x wall:
#     flanges recess POCKET deep into the wall inner faces (location), and
#     self-tap screws pass from outside through CONN_SCREW_CLEAR holes into
#     the connectors' own bosses
#   - lid: flat plate + registration skirt inside the walls (LIP_CLEAR fit),
#     M3 screws into heat-set inserts in wall pads at the long-wall ends
from build123d import *
import spec as S

def box(x1, y1, z1, x2, y2, z2):
    return Pos((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2) * \
        Box(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))

# ---- base -------------------------------------------------------------------
outer = Pos((S.EX1 + S.EX2) / 2, (S.EY1 + S.EY2) / 2, S.EZ1) * \
    extrude(RectangleRounded(S.EX2 - S.EX1, S.EY2 - S.EY1, 3.0), S.TOP - S.EZ1)
base = outer - box(S.IX1, S.IY1, S.FLOOR, S.IX2, S.IY2, S.TOP + 1)

add = []
for x, y in S.PCB_BOSSES:   # boss + 45-degree flare cone to the floor
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.BOSS_D / 2), S.BOSS_H))
    add.append(Pos(x, y, S.FLOOR) *
               Cone(S.BOSS_D / 2 + S.BOSS_H, S.BOSS_D / 2, S.BOSS_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)))
for x, y in S.INSERTS:      # lid-insert pads on the wall inner faces
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.BOSS_PAD_D / 2), S.INT_H))
base += add

cut = []
f12w = S.C12_FLANGE[0] + 2 * S.POCKET_CLEAR
f12h = S.C12_FLANGE[1] + 2 * S.POCKET_CLEAR
z1, z2 = S.CONN_Z - f12h / 2, S.CONN_Z + f12h / 2
cw, ch, _ = S.C12_CUT
for wall_y, sgn in ((S.IY1, -1), (S.IY2, 1)):
    cut.append(box(S.CTR_X - f12w / 2, wall_y, z1,          # flange pocket
                   S.CTR_X + f12w / 2, wall_y + sgn * S.POCKET, z2))
    cut.append(box(S.CTR_X - cw / 2, wall_y - sgn * 1, S.CONN_Z - ch / 2,
                   S.CTR_X + cw / 2, wall_y + sgn * (S.WALL_T + 1), S.CONN_Z + ch / 2))
    for dx in (-S.C12_SCREW_PITCH / 2, S.C12_SCREW_PITCH / 2):
        cut.append(Pos(S.CTR_X + dx, wall_y + sgn * S.WALL_T / 2, S.CONN_Z) *
                   Rot(90, 0, 0) * Cylinder(S.CONN_SCREW_CLEAR / 2, S.WALL_T + 4))
f4w = S.C4_FLANGE[0] + 2 * S.POCKET_CLEAR
f4h = S.C4_FLANGE[1] + 2 * S.POCKET_CLEAR
cut.append(box(S.IX1 - S.POCKET, S.CTR_Y - f4w / 2, S.CONN_Z - f4h / 2,
               S.IX1, S.CTR_Y + f4w / 2, S.CONN_Z + f4h / 2))
cut.append(Pos(S.IX1 - S.WALL_T / 2, S.CTR_Y, S.CONN_Z) *
           Rot(0, 90, 0) * Cylinder(S.C4_CUT_DIA / 2, S.WALL_T + 4))
for dy in (-S.C4_SCREW_PITCH / 2, S.C4_SCREW_PITCH / 2):
    cut.append(Pos(S.IX1 - S.WALL_T / 2, S.CTR_Y + dy, S.CONN_Z) *
               Rot(0, 90, 0) * Cylinder(S.CONN_SCREW_CLEAR / 2, S.WALL_T + 4))
for x, y in S.PCB_BOSSES:   # M3 thread-forming pilots, 6.5 deep from boss top
    cut.append(Pos(x, y, S.FLOOR + S.BOSS_H - 6.5) *
               extrude(Circle(S.PCB_SCREW_PILOT / 2), 7.0))
for x, y in S.INSERTS:      # heat-set insert holes from the wall top
    cut.append(Pos(x, y, S.TOP - S.INSERT_DEPTH) *
               extrude(Circle(S.INSERT_HOLE / 2), S.INSERT_DEPTH + 1))
base -= cut

# ---- lid --------------------------------------------------------------------
lid = Pos((S.EX1 + S.EX2) / 2, (S.EY1 + S.EY2) / 2, S.TOP) * \
    extrude(RectangleRounded(S.EX2 - S.EX1, S.EY2 - S.EY1, 3.0), S.LID_T)
sx, sy = S.IX2 - S.IX1 - 2 * S.LIP_CLEAR, S.IY2 - S.IY1 - 2 * S.LIP_CLEAR
skirt = Pos((S.IX1 + S.IX2) / 2, (S.IY1 + S.IY2) / 2, S.TOP - S.LIP_H) * \
    (extrude(Rectangle(sx, sy), S.LIP_H) -
     extrude(Rectangle(sx - 2 * S.LIP_T, sy - 2 * S.LIP_T), S.LIP_H + 1))
skirt -= [Pos(x, y, S.TOP - S.LIP_H - 0.5) *
          extrude(Circle(S.BOSS_PAD_D / 2 + S.LIP_CLEAR + S.LIP_T), S.LIP_H + 1)
          for x, y in S.INSERTS]
lid += skirt
lc = []
for x, y in S.INSERTS:
    lc.append(Pos(x, y, S.TOP - 1) * extrude(Circle(S.LID_SCREW_CLEAR / 2), S.LID_T + 2))
    lc.append(Pos(x, y, S.TOP + S.LID_T - S.LID_CBORE[1]) *
              extrude(Circle(S.LID_CBORE[0] / 2), S.LID_CBORE[1] + 1))
lid -= lc

# ---- verify + export --------------------------------------------------------
for name, part in (('canbox_base', base), ('canbox_lid', lid)):
    bb = part.bounding_box()
    print(f'{name}: ({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f}) -> '
          f'({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})  vol {part.volume/1000:.1f} cm3  '
          f'solids {len(part.solids())}')
    assert len(part.solids()) == 1, f'{name} not a single solid'
    export_stl(part, f'{S.OUT}/{name}.stl')
    export_step(part, f'{S.OUT}/{name}.step')

for label, off in (('board A', 0.0), ('board B', S.B_OFF)):
    board = Pos(off + S.BOARD / 2, S.BOARD / 2, S.PCB_T / 2) * \
        extrude(RectangleRounded(S.BOARD, S.BOARD, S.BOARD_R), S.PCB_T / 2, both=True)
    i = base.intersect(board)
    v = sum(s.volume for s in i.solids()) if i else 0
    print(f'{label} vs base intersection (want 0): {v:.4f}')
    assert v < 1e-6
