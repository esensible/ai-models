# 3D-printed templates for the dual-dingoPDM heatsink (build123d) -- rev 3.
# GROUND TRUTH: the board layout (two boards at 82.39 pitch) and the enclosure
# derived from it. No template feature depends on the heatsink's dimensions;
# cuts that reach a heatsink edge simply run off it, wherever that edge is.
# Frame: datum = board A lower-left PCB corner, X right, Y up (top view), Z up.
# Heatsink (combined baseplate): rect (-12, 4)-(166.78, 91.25) plus an R8 tab
# at the south joint screw (77.39, 4.005) hanging to v=-4. Case-seat rebates
# 3.2 deep x 11 wide run along the west and east edges (routed, template 2).
from build123d import *

# ---- parameters -------------------------------------------------------------
THICK = 10.0            # template thickness
CUTTER = 6.0            # router cutter diameter
BUSH = 15.0             # trimmer guide bush OD
BUSH_PROTRUSION = 8.0
TAP_DRILL_M3 = 2.5
TAP_DRILL_M6 = 5.0
GUIDE_CLEAR = 0.1
PRINT_COMP = 0.2        # FDM hole shrink compensation
FIX_DIA = 3.2           # template-2 hold-downs (M3 into tapped board holes)
CBORE_DIA = 6.4
CBORE_DEPTH = 4.5
PITCH = 82.39
ENGRAVE = 0.6
# (case-skirt seat rebates along the west/east edges are handled separately,
#  not by these templates)

OFFSET = (BUSH - CUTTER) / 2
OPEN_R = CUTTER / 2 + OFFSET
BORE3 = TAP_DRILL_M3 + GUIDE_CLEAR + PRINT_COMP
BORE6 = TAP_DRILL_M6 + GUIDE_CLEAR + PRINT_COMP
assert BUSH_PROTRUSION < THICK

# ---- fixed geometry (ALL board-layout-derived; no heatsink assumptions) -----
# Outer case-screw lines = the enclosure's corner boss centers: board centers
# +-48.195 in u, +-43.625 in v. The heatsink must be sized to reach these; the
# templates do not care what size it actually is.
SX1, SY1, SX2, SY2 = -12.0, 4.005, 166.78, 91.245
HOLES_A = [(4.826, 40.386), (64.516, 40.386), (16.764, 83.566), (64.516, 83.566)]
HOLES_M3 = HOLES_A + [(u + PITCH, v) for u, v in HOLES_A]
# blind dog-bone drills at every relief-pocket corner pin (the 6mm cutter's
# r3 corners encroach the corner pins by ~0.3): 4 per RedCube block
CORNER_DRILLS = [(su + off + du, sv + dv)
                 for su, sv in ((13.208, 34.798), (7.366, 89.154))
                 for off in (0, PITCH) for du in (-3.81, 3.81) for dv in (-3.81, 3.81)]
HOLES_M6 = [(SX1, SY1), (SX1, SY2), (SX2, SY1), (SX2, SY2),
            (77.39, 60.0)]                      # 4 outer case + 1 joint screw
MOUNT_DRILL = 8.0                               # stock baseplate mounting hole,
                                                #   un-threaded, drill through
MOUNT_HOLES = [(SX1, 47.625), (SX2, 47.625)]    # end midpoints, between the
                                                #   enclosure lobes, outside its
                                                #   walls (stock: on the edge)
FIX = [(64.516, 40.386), (64.516, 83.566),
       (64.516 + PITCH, 40.386), (64.516 + PITCH, 83.566)]

# All reliefs share one style: pin field (+-3.81 rows, pin r0.7) + 0.5 margin
# -> 10 wide, centered on the part. Closed pockets everywhere: if the heatsink
# happens to end inside one, the cut simply runs off its edge.
def pockets(off):
    return [(13.208 + off - 5.0, 29.79, 13.208 + off + 5.0, 39.81),      # +12V RedCube
            (37.846 + off - 12.9, 55.626, 37.846 + off + 12.9, 68.326),  # DT pins
            (7.366 + off - 5.0, 84.154, 7.366 + off + 5.0, 94.154)]      # GND RedCube
POCKETS = pockets(0) + pockets(PITCH)

def opening(p):
    u1, v1, u2, v2 = p
    o = [u1 - OFFSET, v1 - OFFSET, u2 + OFFSET, v2 + OFFSET]
    assert min(o[2] - o[0], o[3] - o[1]) >= BUSH
    return o

def label(txt, x, y):
    try:
        return Pos(x, y, THICK - ENGRAVE) * extrude(Text(txt, font_size=5), ENGRAVE)
    except Exception:
        return None

import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
os.makedirs(OUT, exist_ok=True)

# ---- template 1: drill guide ------------------------------------------------
M = 10  # body margin beyond the outermost screw lines (full bores at all guides)
bx1, by1, bx2, by2 = SX1 - M, SY1 - M, SX2 + M, SY2 + M
t1 = Pos((bx1 + bx2) / 2, (by1 + by2) / 2, THICK / 2) * Box(bx2 - bx1, by2 - by1, THICK)

cut = []
for u, v in HOLES_M3 + CORNER_DRILLS:
    cut.append(Pos(u, v, THICK / 2) * Cylinder(BORE3 / 2, THICK + 2))
    cut.append(Pos(u, v, THICK - 0.3) * Cone(BORE3 / 2, BORE3 / 2 + 0.6, 0.6))
for u, v in HOLES_M6:
    cut.append(Pos(u, v, THICK / 2) * Cylinder(BORE6 / 2, THICK + 2))
    cut.append(Pos(u, v, THICK - 0.3) * Cone(BORE6 / 2, BORE6 / 2 + 0.8, 0.6))
BORE8 = MOUNT_DRILL + GUIDE_CLEAR + PRINT_COMP
for u, v in MOUNT_HOLES:
    cut.append(Pos(u, v, THICK / 2) * Cylinder(BORE8 / 2, THICK + 2))
    cut.append(Pos(u, v, THICK - 0.3) * Cone(BORE8 / 2, BORE8 / 2 + 0.8, 0.6))
for u, v in CORNER_DRILLS:   # double-ring marker = blind, pocket depth only
    ring = Pos(u, v) * (Circle(3.5) - Circle(2.7))
    cut.append(Pos(0, 0, THICK - ENGRAVE) * extrude(ring, ENGRAVE))
lbl = label(f'T1: M3 @{BORE3:.1f} thru+tap / ringed=BLIND 4mm / M6 @{BORE6:.1f} thru+tap '
            f'/ mount @{BORE8:.1f} thru NO TAP', 20, 58)
if lbl: cut.append(lbl)
t1 -= cut

# ---- template 2: router template --------------------------------------------
ops = [opening(p) for p in POCKETS]
ox1 = min(o[0] for o in ops) - OFFSET
oy1 = min(o[1] for o in ops) - OFFSET
ox2 = max(o[2] for o in ops) + OFFSET
oy2 = max(o[3] for o in ops) + OFFSET
B2 = 8
cx1, cy1, cx2, cy2 = ox1 - OFFSET - B2, oy1 - OFFSET - B2, ox2 + OFFSET + B2, oy2 + OFFSET + B2
t2 = Pos((cx1 + cx2) / 2, (cy1 + cy2) / 2, THICK / 2) * Box(cx2 - cx1, cy2 - cy1, THICK)

cut = []
for p in POCKETS:
    o1, o2, o3, o4 = opening(p)
    cut.append(Pos((o1 + o3) / 2, (o2 + o4) / 2, THICK / 2) *
               extrude(RectangleRounded(o3 - o1, o4 - o2, OPEN_R), THICK + 2, both=True))
for u, v in FIX:
    cut.append(Pos(u, v, THICK / 2) * Cylinder(FIX_DIA / 2, THICK + 2))
    cut.append(Pos(u, v, THICK - CBORE_DEPTH / 2 + 0.5) * Cylinder(CBORE_DIA / 2, CBORE_DEPTH + 1))
lbl = label(f'T2 {CUTTER:.0f}/{BUSH:.0f}: pin reliefs 3.5 deep', 30, 46)
if lbl: cut.append(lbl)
t2 -= cut

# ---- template 3: skirt rebate island ----------------------------------------
# Rectangular island screwed to the heatsink. The bush rides around the
# template's OUTER edge: cut inner boundary = template edge + OFFSET, so the
# template is inset OFFSET from the rebate inner walls. One guided perimeter
# pass cuts the critical inner wall + a CUTTER-wide floor band; clear the rest
# outward to the plate edges freehand at the same depth. Rebate depth = 3.175
# exactly (stock skirt height) -- seating is skirt-on-floor, no added height.
# ALL FOUR edges derived identically: template edge = skirt inner face
# + SKIRT_CLEAR + OFFSET. On a plate shorter than the enclosure the N/S
# passes run off its edges harmlessly; on a longer plate they cut the
# rebates those skirts would then need. (Walls measure 3.0 thick all round;
# skirt inner faces: u -1.0 / 155.78, v -1.0 / 96.25.)
SKIRT_CLEAR = 0.3                    # lateral clearance past the skirt inner face
WALL_OUT, WALL_T2 = 40.195, 3.0      # case side wall outer face / thickness
inset = WALL_T2 + SKIRT_CLEAR + OFFSET               # 7.8 from each wall OUTER face
tx1, ty1 = 36.195 - WALL_OUT + inset, -4.0 + inset   # (3.8, 3.8)
tx2, ty2 = 118.585 + WALL_OUT - inset, 99.25 - inset # (150.98, 91.45)
T3_FIX = [(64.516, 40.386), (64.516, 83.566), (87.216, 40.386), (99.154, 83.566)]
t3 = Pos((tx1 + tx2) / 2, (ty1 + ty2) / 2, THICK / 2) * \
    Box(tx2 - tx1, ty2 - ty1, THICK)
cut = []
for u, v in T3_FIX:
    cut.append(Pos(u, v, THICK / 2) * Cylinder(FIX_DIA / 2, THICK + 2))
    cut.append(Pos(u, v, THICK - CBORE_DEPTH / 2 + 0.5) * Cylinder(CBORE_DIA / 2, CBORE_DEPTH + 1))
lbl = label(f'T3 SKIRT REBATE {CUTTER:.0f}/{BUSH:.0f}: bush rides OUTER edge, '
            f'depth 3.175, clear outward to plate edges', 12, 60)
if lbl: cut.append(lbl)
lbl = label('all edges = skirt inner face +0.3 +4.5: walls at u -0.7/155.48, v -0.7/95.95', 12, 30)
if lbl: cut.append(lbl)
t3 -= cut

# ---- verify + export --------------------------------------------------------
for name, part, nexp in (('template1_drill_guide', t1, 31), ('template2_router_reliefs', t2, 10),
                         ('template3_skirt_rebate', t3, 4)):
    bb = part.bounding_box()
    sec = section(part, Plane.XY.offset(2))
    inner = [w for f in sec.faces() for w in f.inner_wires()]
    print(f'{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {part.volume/1000:.1f} cm3  '
          f'inner wires z2: {len(inner)} (expect {nexp})')
    export_stl(part, f'{OUT}/{name}.stl')
    export_step(part, f'{OUT}/{name}.step')
