# Dual-CANBoard enclosure assembly (build123d). All values from spec.py.
# Connector solids are the VENDOR STEP models from Amphenol Tuchel Industrial
# (amphenol-industrial.de product pages, direct .stp downloads):
#   c3d-at04-12pa-pm11-01-000.stp / c3d-at04-4p-pm11-01-000.stp
# Their local frames (measured by section scan): x = flange long axis
# (centered), z = flange tall axis, y = mating axis with the nose toward -y;
# flange front face at y = tip + nose length. We remap to our convention:
# z=0 at the flange front face (pocket-floor contact plane), nose toward +z.
from build123d import *
import copy
import os
import spec as S

VENDOR = os.environ.get('AMPHENOL_DIR', os.path.expanduser('~/vendor-cad'))

def vendor(n):
    p = os.path.join(VENDOR, n)
    assert os.path.exists(p), (
        f'{p} missing: download from amphenol-industrial.de product pages '
        f'(AT04-12PA-PM11 / AT04-4P-PM11, direct .stp links) into AMPHENOL_DIR')
    return p

def conn12():
    step = import_step(vendor('AT04-12PA-PM11.stp'))
    tip_y = step.bounding_box().min.Y                    # mating tip (4.70)
    return Rot(-90, 0, 0) * Pos(0, -(tip_y + S.C12_NOSE), 0) * step

def conn4():
    step = import_step(vendor('AT04-4P-PM11.stp'))
    bb = step.bounding_box()
    z_ctr = (bb.min.Z + bb.max.Z) / 2                    # flange z center (-1.0)
    return Rot(-90, 0, 0) * Pos(0, -(bb.min.Y + S.C4_NOSE), -z_ctr) * step

# place: flange front face against the pocket floor, nose pointing outward
conn_s = Pos(S.CTR_X, S.IY1 - S.POCKET, S.CONN_Z) * Rot(90, 0, 0) * conn12()
conn_n = Pos(S.CTR_X, S.IY2 + S.POCKET, S.CONN_Z) * Rot(-90, 0, 0) * conn12()
conn_w = Pos(S.IX1 - S.POCKET, S.CTR_Y, S.CONN_Z) * Rot(0, -90, 0) * \
    Rot(0, 0, 90) * conn4()                         # -x wall, nose -x

pcba = import_step(S.canboard('Export/V2/CANBoard_V2.step'))
board_A = Pos(*S.KICAD_ORG, 0) * copy.copy(pcba)
board_B = Pos(S.KICAD_ORG[0] + S.B_OFF, S.KICAD_ORG[1], 0) * copy.copy(pcba)
base = import_step(f'{S.OUT}/canbox_base.step')
lid = import_step(f'{S.OUT}/canbox_lid.step')

parts = [('base', base), ('lid', lid), ('board_A', board_A), ('board_B', board_B),
         ('conn12_south', conn_s), ('conn12_north', conn_n), ('conn4_west', conn_w)]
for name, p in parts:
    p.label = name
    bb = p.bounding_box()
    print(f'{name:14s} solids {len(p.solids()):3d}  '
          f'({bb.min.X:7.2f},{bb.min.Y:7.2f},{bb.min.Z:6.2f}) -> '
          f'({bb.max.X:7.2f},{bb.max.Y:7.2f},{bb.max.Z:6.2f})')

def clash_pieces(a, b):
    out = []
    for sa in a.solids():
        for sb in b.solids():
            i = sa.intersect(sb)
            if i: out += list(i.solids())
    return out

# The vendor models include the silicone facial gasket proud of each flange
# front face (measured: 1.0 on the 12P, 1.3 on the 4P). Fully-seated placement
# (conservative for interior clearances) therefore shows exactly that gasket
# sheet interpenetrating the pocket floor -- the physical crush zone. Allow it
# there, nowhere else.
GASKET_BAND = 1.35
def in_gasket_zone(piece, axis, floor, sign):
    b = piece.bounding_box()
    lo = (b.min.X, b.min.Y, b.min.Z)[axis]
    hi = (b.max.X, b.max.Y, b.max.Z)[axis]
    zone = sorted([floor, floor + sign * GASKET_BAND])
    return zone[0] - 0.01 <= lo and hi <= zone[1] + 0.01

checks = [('conn12_south vs board_A', conn_s, board_A, None),
          ('conn12_south vs board_B', conn_s, board_B, None),
          ('conn12_north vs board_A', conn_n, board_A, None),
          ('conn12_north vs board_B', conn_n, board_B, None),
          ('conn4_west vs board_A', conn_w, board_A, None),
          ('conn12_south vs base', conn_s, base, (1, S.IY1 - S.POCKET, -1)),
          ('conn12_north vs base', conn_n, base, (1, S.IY2 + S.POCKET, 1)),
          ('conn4_west vs base', conn_w, base, (0, S.IX1 - S.POCKET, -1)),
          ('lid vs base', lid, base, None),
          ('lid vs conn12_south', lid, conn_s, None),
          ('conn4 vs conn12_south', conn_w, conn_s, None)]
for label, a, b, gasket in checks:
    pieces = clash_pieces(a, b)
    if gasket:
        bad = [p for p in pieces if not in_gasket_zone(p, *gasket)]
        gv = sum(p.volume for p in pieces) - sum(p.volume for p in bad)
        v = sum(p.volume for p in bad)
        print(f'{label:28s} gasket-crush {gv:7.1f}  other (want 0): {v:.4f}')
    else:
        v = sum(p.volume for p in pieces)
        print(f'{label:28s} intersection (want 0): {v:.4f}')
    assert v < 1e-6, label

asm = Compound(children=[p for _, p in parts], label='canbox')
export_step(asm, f'{S.OUT}/canbox_assembly.step')
try:   # printable parts only: imported meshes (boards, vendor connectors)
    m = Mesher()   # fail lib3mf validation
    for name, p in parts:
        if name in ('base', 'lid'):
            m.add_shape(p, part_number=name)
    m.write(f'{S.OUT}/canbox_printables.3mf')
    print('3MF written')
except Exception as e:
    print('3MF export failed (STEP still valid):', e)
print('STEP written')
