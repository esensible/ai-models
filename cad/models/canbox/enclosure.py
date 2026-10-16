# Single-CANBoard enclosure v8: base + lid (build123d). All values from spec.py.
# The body is WAISTED (sides need not be straight -- user): a wide HEAD band
# at the +y wall carries the 12P flange, tapering to a NECK sized by the 4P
# flange. External M6 mounting tabs off the neck walls at TAB_Y put the holes
# at exactly the fixed 87.5 chassis pitch, clocked 90 deg to the connectors.
# Everything is generated from ONE interior plan outline:
#   interior plan -> +WALL_T offset = exterior; -REBATE_CLEAR offset = lid plug
#   - PCB on 5mm bosses with 45-degree conical flares
#   - flanges surface-mount against the inner wall faces (no recess)
#   - generous interior fillets: plan corners CAVITY_R, floor FLOOR_FILLET
#   - tabs: full-width slab + rounded end (R = tab half-width, tangent to the
#     gusset outer faces), gussets blend into the tab via a tangent arc
#   - lid: thickened plate, rebated edges (solid plug, REBATE_CLEAR tolerance),
#     plug relieved over the 4P flange top and around the insert pads; "CAN"
#     recessed into the lid top (lid prints top-face-down); M3 + inserts
from build123d import *
import spec as S

def box(x1, y1, z1, x2, y2, z2):
    return Pos((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2) * \
        Box(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))

def rounded(face, r):
    for radius in (r, r / 2, r / 4):
        try:
            return fillet(face.vertices(), radius)
        except Exception:
            continue
    raise RuntimeError('plan fillet failed at all radii')

# ---- plan outlines ----------------------------------------------------------
iplan = rounded(Polygon(
    (S.IX1, S.IY1), (S.IX2, S.IY1),                    # neck, -y end
    (S.IX2, S.NECK_Y2), (S.HX2, S.HEAD_Y1),            # taper +x side
    (S.HX2, S.IY2), (S.HX1, S.IY2),                    # head, +y wall
    (S.HX1, S.HEAD_Y1), (S.IX1, S.NECK_Y2),            # taper -x side
    align=None), S.CAVITY_R)
eplan = offset(iplan, S.WALL_T)
pplan = offset(iplan, -S.REBATE_CLEAR)                 # lid plug outline

# ---- base -------------------------------------------------------------------
outer = Pos(0, 0, S.EZ1) * extrude(eplan, S.TOP - S.EZ1)
tool = Pos(0, 0, S.FLOOR) * extrude(iplan, S.TOP - S.FLOOR + 1)
tool = fillet(tool.edges().group_by(Axis.Z)[0], S.FLOOR_FILLET)
base = outer - tool

add = []
for x, y in S.PCB_BOSSES:
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.BOSS_D / 2), S.BOSS_H))
    add.append(Pos(x, y, S.FLOOR) *
               Cone(S.BOSS_D / 2 + S.BOSS_H, S.BOSS_D / 2, S.BOSS_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)))
for x, y in S.INSERTS:
    add.append(Pos(x, y, S.FLOOR) * extrude(Circle(S.BOSS_PAD_D / 2), S.INT_H))
# v8 mounting tabs off the neck walls: full-width slab out to the hole +
# rounded end (tangent to the gusset outer faces), blended gussets
for hx, hy in S.MOUNT_HOLES:
    sgn = -1 if hx < S.CTR_X else 1
    wall = S.EX1 if sgn < 0 else S.EX2
    # one stadium profile: straight flanks at +-TAB_W/2, semicircular end cap
    # R = TAB_W/2 centred on the hole -- cap tangent to the flanks (and so to
    # the gusset outer faces), no slab/circle seams
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
    # soften the ear standalone (the merged solid refuses): round its outer
    # perimeter edges, keep the wall-contact zone sharp so the union fuses
    away = (lambda b: b.max.X > wall + 0.1) if sgn > 0 else \
           (lambda b: b.min.X < wall - 0.1)
    ear = fillet([e for e in ear.edges() if away(e.bounding_box())], 0.5)
    add.append(ear)
    # gusset: straight brace from the wall top tangent into a fillet foot
    # that lands tangent on the tab top at the hole axis (a single tangent
    # arc over this run/height is geometrically impossible -- it would bulge
    # through the wall; the 'blended' fins it produced were slivers, caught
    # by material probes 2026-08-27)
    import math
    x0, gf, gh = -0.5, S.TAB_REACH, S.GUSSET_H
    rf = S.GUSSET_FOOT_R
    A = (x0, gh)                      # brace top, on the wall
    C = (gf, rf)                      # foot fillet centre (tangent to tab top)
    u = (A[0] - C[0], A[1] - C[1])
    d2 = u[0] * u[0] + u[1] * u[1]
    L = math.sqrt(d2 - rf * rf)
    # tangent point on the upper-left of the foot circle
    T = (C[0] + rf * rf / d2 * u[0] - rf * L / d2 * u[1],
         C[1] + rf * rf / d2 * u[1] + rf * L / d2 * u[0])
    a_t = math.atan2(T[1] - C[1], T[0] - C[0])
    a_f = -math.pi / 2
    a_m = a_t + ((a_f - a_t + math.pi) % (2 * math.pi) - math.pi) / 2
    M = (C[0] + rf * math.cos(a_m), C[1] + rf * math.sin(a_m))
    g2d = make_face([
        Polyline((sgn * gf, 0), (sgn * x0, 0), (sgn * x0, gh), (sgn * T[0], T[1])),
        ThreePointArc((sgn * T[0], T[1]), (sgn * M[0], M[1]), (sgn * gf, 0)),
    ])
    tri = 0.5 * (gf - x0) * gh
    assert 0.35 * tri < g2d.area < 0.95 * tri, \
        f'gusset area {g2d.area:.1f} vs triangle {tri:.1f} -- bad profile'
    g = extrude(g2d, S.GUSSET_T, dir=(0, 0, 1))
    for gy in (hy - S.GUSSET_GAP / 2 - S.GUSSET_T / 2,
               hy + S.GUSSET_GAP / 2 + S.GUSSET_T / 2):
        add.append(Pos(wall, gy + S.GUSSET_T / 2, S.EZ1 + S.TAB_T) * Rot(90, 0, 0) * g)
base += add

cut = []
# 12P on the +y (head) wall: nose cutout + screws through the full wall
cw, ch, _ = S.C12_CUT
cut.append(box(S.CTR_X - cw / 2, S.IY2 - 1, S.CONN_Z - ch / 2,
               S.CTR_X + cw / 2, S.IY2 + S.WALL_T + 1, S.CONN_Z + ch / 2))
for dx in (-S.C12_SCREW_PITCH / 2, S.C12_SCREW_PITCH / 2):
    cut.append(Pos(S.CTR_X + dx, S.IY2 + S.WALL_T / 2, S.CONN_Z) *
               Rot(90, 0, 0) * Cylinder(S.CONN_SCREW_CLEAR / 2, S.WALL_T + 4))
# single 4P on the -y (neck) wall
for cx in S.C4_X:
    cut.append(Pos(cx, S.IY1 - S.WALL_T / 2, S.CONN_Z) *
               Rot(90, 0, 0) * Cylinder(S.C4_CUT_DIA / 2, S.WALL_T + 4))
    for dx in (-S.C4_SCREW_PITCH / 2, S.C4_SCREW_PITCH / 2):
        cut.append(Pos(cx + dx, S.IY1 - S.WALL_T / 2, S.CONN_Z) *
                   Rot(90, 0, 0) * Cylinder(S.CONN_SCREW_CLEAR / 2, S.WALL_T + 4))
# PCB screw pilots, lid inserts, tab holes
for x, y in S.PCB_BOSSES:
    cut.append(Pos(x, y, S.FLOOR + S.BOSS_H - 6.5) *
               extrude(Circle(S.PCB_SCREW_PILOT / 2), 7.0))
for x, y in S.INSERTS:
    cut.append(Pos(x, y, S.TOP - S.INSERT_DEPTH) *
               extrude(Circle(S.INSERT_HOLE / 2), S.INSERT_DEPTH + 1))
for hx, hy in S.MOUNT_HOLES:
    cut.append(Pos(hx, hy, S.EZ1 + S.TAB_T / 2) *
               Cylinder(S.MOUNT_SCREW_CLEAR / 2, S.TAB_T + 2))
base -= cut

# ---- lid --------------------------------------------------------------------
lid = Pos(0, 0, S.TOP) * extrude(eplan, S.LID_T)
lid += Pos(0, 0, S.TOP - S.REBATE_D) * extrude(pplan, S.REBATE_D)
# relieve the plug around the insert pads and over the 4P flange top (the
# 12P tops out below the plug and needs no relief)
lid -= [Pos(x, y, S.TOP - S.REBATE_D - 0.5) *
        extrude(Circle(S.BOSS_PAD_D / 2 + S.REBATE_CLEAR), S.REBATE_D + 0.5)
        for x, y in S.INSERTS]
f4w = S.C4_FLANGE[0] + 2 * S.POCKET_CLEAR
lid -= [box(cx - f4w / 2 - 1, S.IY1 - 1, S.TOP - S.REBATE_D - 0.5,
            cx + f4w / 2 + 1, S.IY1 + 4.0, S.TOP - S.REBATE_D + 1.2)
        for cx in S.C4_X]
# "CAN" recessed into the lid top, over the 4P (lid prints top-face-down)
txt = Text("CAN", font_size=S.CAN_TEXT_H, font_style=FontStyle.BOLD)
tb = txt.bounding_box().size
lid -= Pos(S.C4_X[-1], S.IY1 + 4 + tb.Y / 2, S.TOP + S.LID_T - S.CAN_TEXT_D) * \
    extrude(txt, S.CAN_TEXT_D + 1)
lc = []
for x, y in S.INSERTS:
    lc.append(Pos(x, y, S.TOP - 1) * extrude(Circle(S.LID_SCREW_CLEAR / 2), S.LID_T + 2))
    lc.append(Pos(x, y, S.TOP + S.LID_T - S.LID_CBORE[1]) *
              extrude(Circle(S.LID_CBORE[0] / 2), S.LID_CBORE[1] + 1))
lid -= lc

# ---- global edge softening: 0.5 fillet, zone by zone ------------------------
# The waisted plan's offset arcs leave tangent seams that make OCC refuse (or
# on some mixed subsets, segfault) a whole-part 0.5 fillet. Zone-granularity
# attempts fail CLEANLY (probed 2026-08-27), so soften applies each zone
# sequentially and skips zones OCC refuses -- those are the lid-seat parting
# rims, which are better left crisp anyway.
SOFT_R = 0.5

tb_can = ((S.C4_X[-1] - 25, S.IY1 + 1), (S.C4_X[-1] + 25, S.IY1 + 30))
def in_text(e):
    b = e.bounding_box()
    return (b.min.Z > S.TOP + S.LID_T - S.CAN_TEXT_D - 0.05 and
            tb_can[0][0] < b.min.X and b.max.X < tb_can[1][0] and
            tb_can[0][1] < b.min.Y and b.max.Y < tb_can[1][1])

def soften(part, name, zones, exclude=lambda e: False):
    done, skipped = 0, []
    for zname, zpred in zones:
        es = [e for e in part.edges()
              if e.length > 1.2 and not exclude(e) and zpred(e.bounding_box())]
        if not es:
            continue
        for r in (SOFT_R, 0.3, 0.2):
            try:
                part = fillet(es, r)
                done += len(es)
                if r != SOFT_R:
                    print(f'  {name}/{zname}: took r={r}')
                break
            except Exception:
                continue
        else:
            skipped.append(f'{zname}({len(es)})')
    print(f'{name} softened: {done} edges' +
          (f'; zones skipped: {", ".join(skipped)}' if skipped else ''))
    return part

def in_tab_region(b):
    return (b.min.Y > S.TAB_Y - S.TAB_W / 2 - 2 and
            b.max.Y < S.TAB_Y + S.TAB_W / 2 + 2 and
            (b.min.X < S.EX1 + 0.2 or b.max.X > S.EX2 - 0.2))

# tab ears are pre-rounded before the union (see the tab loop); the merged
# tab region refuses post-fillets, so it is excluded here
base = soften(base, 'base', [
    ('bottom', lambda b: b.max.Z < S.FLOOR + 0.1 and not in_tab_region(b)),
    ('top', lambda b: b.min.Z > S.TOP - 0.01),
    ('mid', lambda b: not in_tab_region(b) and
                      S.FLOOR + 0.1 <= b.max.Z and b.min.Z <= S.TOP - 0.01),
])
lid = soften(lid, 'lid', [
    ('top', lambda b: b.min.Z > S.TOP + S.LID_T - 0.01),
    ('bottom', lambda b: b.max.Z < S.TOP - S.REBATE_D + 0.01),
    ('mid', lambda b: S.TOP - S.REBATE_D + 0.01 <= b.max.Z and
                      b.min.Z <= S.TOP + S.LID_T - 0.01),
], exclude=in_text)

# ---- verify + export --------------------------------------------------------
for name, part in (('canbox_base', base), ('canbox_lid', lid)):
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
# base-level section: 2 tab holes + the 2 PCB screw pilots = 4 inner wires
sec = section(base.solids()[0], Plane.XY.offset(S.FLOOR - 1.0))
holes = [w for f in sec.faces() for w in f.inner_wires()]
print(f'features at base level: {len(holes)} (expect 4: 2 tab holes + 2 pilots)')
assert len(holes) == 4, 'base-level feature count wrong'
# connector-wall outer skins: each wall has its nose cut + 2 screw holes
for label, y, want in (('-y wall skin', S.EY1 + 1.0, 3), ('+y wall skin', S.EY2 - 1.0, 3)):
    sec = section(base.solids()[0], Plane(origin=(0, y, 0), z_dir=(0, 1, 0)))
    n = len([w for f in sec.faces() for w in f.inner_wires()])
    print(f'{label}: {n} holes (expect {want})')
    assert n == want, f'{label} hole count wrong'
print(f'mount holes: {S.MOUNT_HOLES}  pitch {S.MOUNT_PITCH} '
      f'(external tabs off the neck, M6, reach {S.TAB_REACH:.2f})')
