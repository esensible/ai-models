# Heatsink machining templates for the dual-dingoPDM mount (build123d).
# All values come from spec.py (single source of truth). Board layout is
# ground truth; nothing here depends on the heatsink's dimensions -- cuts
# that reach a heatsink edge simply run off it, wherever that edge is.
from build123d import *
import spec as S

# ---- template 1: drill guide ------------------------------------------------
M = 10  # body margin beyond the outermost screw lines (full bores everywhere)
bx1, by1 = S.SX1 - M, S.SY1 - M
bx2, by2 = S.SX2 + M, S.SY2 + M
t1 = Pos((bx1 + bx2) / 2, (by1 + by2) / 2, S.TEMPLATE_THICKNESS / 2) * \
    Box(bx2 - bx1, by2 - by1, S.TEMPLATE_THICKNESS)

def bores(points, dia, cone_extra=0.6):
    for u, v in points:
        yield Pos(u, v, S.TEMPLATE_THICKNESS / 2) * Cylinder(dia / 2, S.TEMPLATE_THICKNESS + 2)
        yield Pos(u, v, S.TEMPLATE_THICKNESS - 0.3) * Cone(dia / 2, dia / 2 + cone_extra, 0.6)

def label(txt, x, y):
    try:
        return Pos(x, y, S.TEMPLATE_THICKNESS - 0.6) * extrude(Text(txt, font_size=5), 0.6)
    except Exception:
        return None

cut = list(bores(S.M3_HOLES + S.CORNER_DRILLS, S.BORE_M3))
cut += bores(S.CASE_SCREWS + [S.JOINT_SCREW], S.BORE_M6, 0.8)
cut += bores(S.MOUNT_HOLES, S.BORE_MOUNT, 0.8)
for u, v in S.CORNER_DRILLS:   # double-ring marker = blind, relief depth only
    ring = Pos(u, v) * (Circle(3.5) - Circle(2.7))
    cut.append(Pos(0, 0, S.TEMPLATE_THICKNESS - 0.6) * extrude(ring, 0.6))
lbl = label(f'T1: M3 @{S.BORE_M3:.1f} thru+tap / ringed=BLIND {S.RELIEF_DEPTH:.0f}mm'
            f' / M6 @{S.BORE_M6:.1f} thru+tap / mount @{S.BORE_MOUNT:.1f} thru NO TAP', 20, 58)
if lbl: cut.append(lbl)
t1 -= cut

# ---- template 2: pin-relief router template ---------------------------------
# Openings = pocket + OFFSET per side; the bushing rides inside them. Registers
# on 4 M3 screws into the freshly tapped board holes (counterbored heads).
def opening(p):
    o = [p[0] - S.OFFSET, p[1] - S.OFFSET, p[2] + S.OFFSET, p[3] + S.OFFSET]
    assert min(o[2] - o[0], o[3] - o[1]) >= S.BUSH, 'bushing cannot enter opening'
    return o

T2_FIX = [S.M3_HOLES_LOCAL[1], S.M3_HOLES_LOCAL[3],
          (S.M3_HOLES_LOCAL[1][0] + S.B_OFF, S.M3_HOLES_LOCAL[1][1]),
          (S.M3_HOLES_LOCAL[3][0] + S.B_OFF, S.M3_HOLES_LOCAL[3][1])]
# M3 SHCS counterbore (head 5.5 x 3.0): as deep as the template allows while
# keeping a 1.5 floor under the head; head sits sub-flush whenever possible
CB_D = 6.4
CB_DEPTH = min(4.5, S.TEMPLATE_THICKNESS - 1.5)

ops = [opening(p) for p in S.RELIEF_POCKETS]
ox1 = min(o[0] for o in ops) - S.OFFSET - 8
oy1 = min(o[1] for o in ops) - S.OFFSET - 8
ox2 = max(o[2] for o in ops) + S.OFFSET + 8
oy2 = max(o[3] for o in ops) + S.OFFSET + 8
t2 = Pos((ox1 + ox2) / 2, (oy1 + oy2) / 2, S.TEMPLATE_THICKNESS / 2) * \
    Box(ox2 - ox1, oy2 - oy1, S.TEMPLATE_THICKNESS)
cut = []
for o1, o2, o3, o4 in ops:
    cut.append(Pos((o1 + o3) / 2, (o2 + o4) / 2, S.TEMPLATE_THICKNESS / 2) *
               extrude(RectangleRounded(o3 - o1, o4 - o2, S.OPEN_R),
                       S.TEMPLATE_THICKNESS + 2, both=True))
for u, v in T2_FIX:
    cut.append(Pos(u, v, S.TEMPLATE_THICKNESS / 2) * Cylinder(3.2 / 2, S.TEMPLATE_THICKNESS + 2))
    cut.append(Pos(u, v, S.TEMPLATE_THICKNESS - CB_DEPTH / 2 + 0.5) * Cylinder(CB_D / 2, CB_DEPTH + 1))
lbl = label(f'T2 {S.CUTTER:.0f}/{S.BUSH:.0f}: pin reliefs {S.RELIEF_DEPTH} deep', 30, 46)
if lbl: cut.append(lbl)
t2 -= cut

# ---- template 3: skirt rebate island ----------------------------------------
# The bushing rides around the OUTER edge: cut wall = template edge + OFFSET.
# ALL FOUR edges derived identically: skirt inner face + SKIRT_CLEAR + OFFSET.
# Rebate depth = REBATE_DEPTH exactly (stock skirt height): seating is
# skirt-on-floor; the enclosure divider carries the height tolerance instead.
inset = S.WALL_T + S.SKIRT_CLEAR + S.OFFSET          # 7.8 from wall outer face
tx1 = S.CTR_A[0] - S.WALL_OUT + inset
tx2 = S.CTR_B[0] + S.WALL_OUT - inset
ty1 = S.CTR_A[1] - S.CASE_HALF_L + inset
ty2 = S.CTR_A[1] + S.CASE_HALF_L - inset
T3_FIX = [S.M3_HOLES_LOCAL[1], S.M3_HOLES_LOCAL[3],
          (S.M3_HOLES_LOCAL[0][0] + S.B_OFF, S.M3_HOLES_LOCAL[0][1]),
          (S.M3_HOLES_LOCAL[2][0] + S.B_OFF, S.M3_HOLES_LOCAL[2][1])]
t3 = Pos((tx1 + tx2) / 2, (ty1 + ty2) / 2, S.TEMPLATE_THICKNESS / 2) * \
    Box(tx2 - tx1, ty2 - ty1, S.TEMPLATE_THICKNESS)
cut = []
for u, v in T3_FIX:
    cut.append(Pos(u, v, S.TEMPLATE_THICKNESS / 2) * Cylinder(3.2 / 2, S.TEMPLATE_THICKNESS + 2))
    cut.append(Pos(u, v, S.TEMPLATE_THICKNESS - CB_DEPTH / 2 + 0.5) * Cylinder(CB_D / 2, CB_DEPTH + 1))
lbl = label(f'T3 SKIRT REBATE {S.CUTTER:.0f}/{S.BUSH:.0f}: bushing rides OUTER edge, '
            f'depth {S.REBATE_DEPTH}, clear outward past the heatsink edges', 12, 60)
if lbl: cut.append(lbl)
lbl = label(f'all edges = skirt inner face +{S.SKIRT_CLEAR} +{S.OFFSET}', 12, 30)
if lbl: cut.append(lbl)
t3 -= cut

# ---- verify + export --------------------------------------------------------
for name, part, nexp in (('template1_drill_guide', t1, 31),
                         ('template2_router_reliefs', t2, 10),
                         ('template3_skirt_rebate', t3, 4)):
    bb = part.bounding_box()
    sec = section(part.solids()[0], Plane.XY.offset(2))
    inner = [w for f in sec.faces() for w in f.inner_wires()]
    print(f'{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  '
          f'vol {part.volume/1000:.1f} cm3  inner wires z2: {len(inner)} (expect {nexp})')
    assert len(inner) == nexp, f'{name}: feature count mismatch'
    export_stl(part, f'{S.OUT}/{name}.stl')
    export_step(part, f'{S.OUT}/{name}.step')
