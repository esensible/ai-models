# Slim CANBoard enclosure: base + lid (build123d). All values from spec.py.
# Minimal: bare board on low bosses, one plain cable hole per end wall,
# stadium mounting tabs at the fixed 87.5 chassis pitch, rebated lid with
# countersunk M3s into heat-set inserts, everything rounded.
from build123d import *
import spec as S

def box(x1, y1, z1, x2, y2, z2):
    return Pos((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2) * \
        Box(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))

iplan = RectangleRounded(S.IX2 - S.IX1, S.IY2 - S.IY1, S.CAVITY_R)
iplan = Pos((S.IX1 + S.IX2) / 2, (S.IY1 + S.IY2) / 2) * iplan
eplan = offset(iplan, S.WALL_T)

# ---- base (lower clamshell: floor to the parting line + registration lip) ---
base = Pos(0, 0, S.EZ1) * extrude(eplan, S.PART_Z - S.EZ1)
# round the bottom perimeter NOW, while the shell is a simple prism (the
# finished solid refuses whole-part fillets)
base = fillet(base.edges().group_by(Axis.Z)[0], 1.0)
tool = Pos(0, 0, S.FLOOR) * extrude(iplan, S.PART_Z - S.FLOOR + 1)
tool = fillet(tool.edges().group_by(Axis.Z)[0], 2.0)   # floor-wall blend
base -= tool

add = []
# registration lip: the inner LIP_T of the wall continues up past the split
add.append(Pos(0, 0, S.PART_Z) * extrude(offset(iplan, S.LIP_T) - iplan, S.LIP_H))
for x, y in S.PCB_BOSSES:
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.BOSS_D / 2), S.BOSS_H))
    add.append(Pos(x, y, S.FLOOR) *
               Cone(S.BOSS_D / 2 + S.BOSS_H, S.BOSS_D / 2, S.BOSS_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)))
for x, y in S.INSERTS:   # freestanding insert columns rise to just under the lid
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.PAD_R), S.TOP - S.FLOOR - 0.5))
# stadium tabs on the +-x walls, tangent semicircular ends at the holes
for hx, hy in S.MOUNT_HOLES:
    sgn = -1 if hx < S.CTR_X else 1
    wall = S.EX1 if sgn < 0 else S.EX2
    w0 = wall - sgn * 0.5
    ear2d = make_face([
        Polyline((w0, hy - S.TAB_W / 2), (hx, hy - S.TAB_W / 2)),
        ThreePointArc((hx, hy - S.TAB_W / 2),
                      (hx + sgn * S.TAB_END_R, hy),
                      (hx, hy + S.TAB_W / 2)),
        Polyline((hx, hy + S.TAB_W / 2), (w0, hy + S.TAB_W / 2)),
        Polyline((w0, hy + S.TAB_W / 2), (w0, hy - S.TAB_W / 2)),
    ])
    ear = Pos(0, 0, S.EZ1) * extrude(ear2d, S.TAB_T, dir=(0, 0, 1))
    away = (lambda b: b.max.X > wall + 0.1) if sgn > 0 else \
           (lambda b: b.min.X < wall - 0.1)
    ear = fillet([e for e in ear.edges() if away(e.bounding_box())], S.SOFT_R)
    add.append(ear)
    # gussets: straight brace from the wall, tangent fillet foot onto the tab
    # (same construction as the big canbox; explicit tangent math)
    import math
    x0, gf, gh = -0.5, S.TAB_REACH, S.GUSSET_H
    rf = 4.0
    A = (x0, gh)
    C = (gf, rf)
    u = (A[0] - C[0], A[1] - C[1])
    d2 = u[0] * u[0] + u[1] * u[1]
    L = math.sqrt(d2 - rf * rf)
    T = (C[0] + rf * rf / d2 * u[0] - rf * L / d2 * u[1],
         C[1] + rf * rf / d2 * u[1] + rf * L / d2 * u[0])
    a_t = math.atan2(T[1] - C[1], T[0] - C[0])
    a_m = a_t + ((-math.pi / 2 - a_t + math.pi) % (2 * math.pi) - math.pi) / 2
    Mp = (C[0] + rf * math.cos(a_m), C[1] + rf * math.sin(a_m))
    g2d = make_face([
        Polyline((sgn * gf, 0), (sgn * x0, 0), (sgn * x0, gh), (sgn * T[0], T[1])),
        ThreePointArc((sgn * T[0], T[1]), (sgn * Mp[0], Mp[1]), (sgn * gf, 0)),
    ])
    tri = 0.5 * (gf - x0) * gh
    assert 0.35 * tri < g2d.area < 0.98 * tri, \
        f'gusset area {g2d.area:.1f} vs triangle {tri:.1f} -- bad profile'
    g = extrude(g2d, S.GUSSET_T, dir=(0, 0, 1))
    for gy in (hy - S.GUSSET_GAP / 2 - S.GUSSET_T / 2,
               hy + S.GUSSET_GAP / 2 + S.GUSSET_T / 2):
        add.append(Pos(wall, gy + S.GUSSET_T / 2, S.EZ1 + S.TAB_T) * Rot(90, 0, 0) * g)
base += add

cut = []
# one plain cable hole per end wall
for wy in (S.IY1 - S.WALL_T / 2, S.IY2 + S.WALL_T / 2):
    cut.append(Pos(S.CTR_X, wy, S.CABLE_Z) *
               Rot(90, 0, 0) * Cylinder(S.CABLE_D / 2, S.WALL_T + 4))
for x, y in S.PCB_BOSSES:
    cut.append(Pos(x, y, S.FLOOR + S.BOSS_H - 5.0) *
               extrude(Circle(S.PCB_SCREW_PILOT / 2), 5.5))
for x, y in S.INSERTS:
    cut.append(Pos(x, y, S.TOP - S.INSERT_DEPTH) *
               extrude(Circle(S.INSERT_HOLE / 2), S.INSERT_DEPTH + 1))
for hx, hy in S.MOUNT_HOLES:
    cut.append(Pos(hx, hy, S.EZ1 + S.TAB_T / 2) *
               Cylinder(S.MOUNT_SCREW_CLEAR / 2, S.TAB_T + 2))
base -= cut

# ---- lid (upper clamshell: cap from the parting line to the top) ------------
lid = Pos(0, 0, S.PART_Z) * extrude(eplan, S.EZ2 - S.PART_Z)
lid = fillet(lid.edges().group_by(Axis.Z)[-1], S.TOP_R)   # smooth top edge
lid -= Pos(0, 0, S.PART_Z - 1) * extrude(iplan, S.TOP - S.PART_Z + 1)
# groove for the base's registration lip, LIP_CLEAR all around
groove = offset(iplan, S.LIP_T + S.LIP_CLEAR) - offset(iplan, -S.LIP_CLEAR)
lid -= Pos(0, 0, S.PART_Z - 0.5) * extrude(groove, S.LIP_H + 0.3 + 0.5)
lc = []
for x, y in S.INSERTS:
    lc.append(Pos(x, y, S.TOP - 1) *
              extrude(Circle(S.LID_SCREW_CLEAR / 2), S.LID_T + S.TOP_R + 2))
    # countersink for DIN 7991 flat head, flush with the lid top
    csk_h = (S.CSK_HEAD_D - S.LID_SCREW_CLEAR) / 2
    lc.append(Pos(x, y, S.EZ2 - csk_h) *
              Cone(S.LID_SCREW_CLEAR / 2, S.CSK_HEAD_D / 2, csk_h,
                   align=(Align.CENTER, Align.CENTER, Align.MIN)))
    lc.append(Pos(x, y, S.EZ2 - 0.01) * extrude(Circle(S.CSK_HEAD_D / 2), 2))
# the cable holes: full cylinders cut from the CAP too -- each wall ends up
# with matching semicircular cradles that open with the lid
for wy in (S.IY1 - S.WALL_T / 2, S.IY2 + S.WALL_T / 2):
    lc.append(Pos(S.CTR_X, wy, S.CABLE_Z) *
              Rot(90, 0, 0) * Cylinder(S.CABLE_D / 2, S.WALL_T + 4))
# recessed two-line text on the lid top (prints face-down: crisp first-layer
# voids). Chalkboard-style font, whole block rotated LID_TEXT_ROT CCW.
import os
_font = os.path.join(os.path.expanduser('~'), S.LID_TEXT_FONT)
for i, line in enumerate(S.LID_TEXT):
    txt = Text(line, font_size=S.LID_TEXT_H, font_path=_font)
    ly = (len(S.LID_TEXT) - 1) * 8.0 - i * 16.0
    lc.append(Pos(S.CTR_X, S.CTR_Y, S.EZ2 - S.LID_TEXT_D) *
              Rot(0, 0, S.LID_TEXT_ROT) * Pos(0, ly, 0) *
              extrude(txt, S.LID_TEXT_D + 1))
lid -= lc

# ---- soften -----------------------------------------------------------------
def soften(part, name, zones, exclude=lambda e: False):
    done, skipped = 0, []
    for zname, zpred in zones:
        es = [e for e in part.edges()
              if e.length > 1.2 and not exclude(e) and zpred(e.bounding_box())]
        if not es:
            continue
        for r in (S.SOFT_R, 0.3):
            try:
                part = fillet(es, r)
                done += len(es)
                break
            except Exception:
                continue
        else:
            skipped.append(f'{zname}({len(es)})')
    print(f'{name} softened: {done} edges' +
          (f'; zones skipped: {", ".join(skipped)}' if skipped else ''))
    return part

def in_tab(b):
    return (b.min.Y > S.CTR_Y - S.TAB_W / 2 - 2 and
            b.max.Y < S.CTR_Y + S.TAB_W / 2 + 2 and
            (b.min.X < S.EX1 + 0.2 or b.max.X > S.EX2 - 0.2))

base = soften(base, 'base', [
    ('bottom', lambda b: b.max.Z < S.FLOOR + 0.1 and not in_tab(b)),
    ('top', lambda b: b.min.Z > S.TOP - 0.01),
    ('mid', lambda b: not in_tab(b) and
                      S.FLOOR + 0.1 <= b.max.Z and b.min.Z <= S.TOP - 0.01),
])
def in_text(e):
    b = e.bounding_box()
    return (b.min.Z > S.EZ2 - S.LID_TEXT_D - 0.05 and
            abs((b.min.X + b.max.X) / 2 - S.CTR_X) < 25 and
            abs((b.min.Y + b.max.Y) / 2 - S.CTR_Y) < 20)

lid = soften(lid, 'lid', [
    ('top', lambda b: b.min.Z > S.TOP + 0.5),
    ('rest', lambda b: b.min.Z <= S.TOP + 0.5),
], exclude=in_text)

# ---- verify + export --------------------------------------------------------
for name, part in (('canbox_slim_base', base), ('canbox_slim_lid', lid)):
    bb = part.bounding_box()
    print(f'{name}: ({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f}) -> '
          f'({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})  vol {part.volume/1000:.1f} cm3  '
          f'solids {len(part.solids())}')
    assert len(part.solids()) == 1, f'{name} not a single solid'
    export_stl(part, f'{S.OUT}/{name}.stl')
    export_step(part, f'{S.OUT}/{name}.step')

board = Pos(S.BOARD / 2, S.BOARD / 2, S.PCB_T / 2) * \
    extrude(RectangleRounded(S.BOARD, S.BOARD, S.BOARD_R), S.PCB_T / 2, both=True)
i = base.intersect(board)
v = sum(s.volume for s in i.solids()) if i else 0
print(f'board vs base intersection (want 0): {v:.4f}')
assert v < 1e-6
# base-plate section: 2 mount holes + 2 pilots
sec = section(base.solids()[0], Plane.XY.offset(S.EZ1 + 1.0))
holes = [w for f in sec.faces() for w in f.inner_wires()]
print(f'features at base level: {len(holes)} (expect 4: 2 tab holes + 2 pilots)')
assert len(holes) == 4
# clamshell fit: assembled halves must not interpenetrate, and each end wall
# of the ASSEMBLY shows exactly one full cable hole (the two cradles meeting)
inter = base.intersect(lid)
vi = sum(s.volume for s in inter.solids()) if inter else 0
print(f'base vs lid interpenetration (want 0): {vi:.4f}')
assert vi < 1e-6
pair = base + lid   # fuse, so the two cradles close into one hole
for label, y in (('-y wall', S.EY1 + 1.0), ('+y wall', S.EY2 - 1.0)):
    sec = section(pair.solids()[0], Plane(origin=(0, y, 0), z_dir=(0, 1, 0)))
    n = len([w for f in sec.faces() for w in f.inner_wires()])
    print(f'{label} assembled skin: {n} holes (expect 1)')
    assert n == 1
print(f'mount pitch {S.MOUNT_PITCH} at {S.MOUNT_HOLES}; body '
      f'{S.EX2 - S.EX1:.1f} x {S.EY2 - S.EY1:.1f} x {S.EZ2 - S.EZ1:.1f}, '
      f'ear tip to tip {S.MOUNT_PITCH + 2 * S.TAB_END_R:.1f}')
