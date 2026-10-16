# Single-CANBoard enclosure assembly v2 (build123d). All values from spec.py.
# Connector solids are the VENDOR STEP models from Amphenol Tuchel Industrial
# (amphenol-industrial.de product pages, direct .stp downloads):
#   AT04-12PA-PM11.stp / AT04-4P-PM11.stp
# Their local frames (measured by section scan): x = flange long axis
# (centered), z = flange tall axis, y = mating axis with the nose toward -y;
# flange front face at y = tip + nose length. conn12()/conn4() remap to:
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

# place: flange front face against its pocket floor, nose pointing outward.
# v2: 12P on the +y wall (nose +y), two 4P side by side on the -y wall (nose -y)
conn_12 = Pos(S.CTR_X, S.IY2 + S.POCKET, S.CONN_Z) * Rot(-90, 0, 0) * conn12()
conn_4 = [Pos(cx, S.IY1 - S.POCKET, S.CONN_Z) * Rot(90, 0, 0) * copy.copy(conn4())
          for cx in S.C4_X]

pcba = import_step(S.canboard('Export/V2/CANBoard_V2.step'))
board = Pos(*S.KICAD_ORG, 0) * pcba
bb = board.bounding_box()
assert abs(bb.min.X) < 0.5 and abs(bb.min.Y) < 0.5 and \
    abs(bb.max.X - S.BOARD) < 0.5 and abs(bb.max.Y - S.BOARD) < 0.5, \
    f'board not at datum: ({bb.min.X:.2f},{bb.min.Y:.2f})..({bb.max.X:.2f},{bb.max.Y:.2f})'
base = import_step(f'{S.OUT}/canbox_base.step')
lid = import_step(f'{S.OUT}/canbox_lid.step')

parts = [('base', base), ('lid', lid), ('board', board),
         ('conn12_north', conn_12)] + \
        [(f'conn4_south_{i + 1}', c) for i, c in enumerate(conn_4)]
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

checks = [('conn12 vs board', conn_12, board, None),
          ('conn12 vs base', conn_12, base, (1, S.IY2 + S.POCKET, 1)),
          ('board vs base', board, base, None),
          ('lid vs base', lid, base, None),
          ('lid vs conn12', lid, conn_12, None)]
for i, c in enumerate(conn_4, 1):
    checks += [(f'conn4_{i} vs board', c, board, None),
               (f'conn4_{i} vs base', c, base, (1, S.IY1 - S.POCKET, -1)),
               (f'lid vs conn4_{i}', lid, c, None),
               (f'conn12 vs conn4_{i}', conn_12, c, None)]
for a, b in zip(conn_4, conn_4[1:]):
    checks.append(('conn4 vs conn4', a, b, None))
for label, a, b, gasket in checks:
    pieces = clash_pieces(a, b)
    if gasket:
        bad = [p for p in pieces if not in_gasket_zone(p, *gasket)]
        gv = sum(p.volume for p in pieces) - sum(p.volume for p in bad)
        v = sum(p.volume for p in bad)
        print(f'{label:24s} gasket-crush {gv:7.1f}  other (want 0): {v:.4f}')
    else:
        v = sum(p.volume for p in pieces)
        print(f'{label:24s} intersection (want 0): {v:.4f}')
    assert v < 1e-6, label

asm = Compound(children=[p for _, p in parts], label='canbox')
export_step(asm, f'{S.OUT}/canbox_assembly.step')
try:   # printable parts only: imported meshes (board, vendor connectors)
    m = Mesher()   # fail lib3mf validation
    for name, p in parts:
        if name in ('base', 'lid'):
            m.add_shape(p, part_number=name)
    m.write(f'{S.OUT}/canbox_printables.3mf')
    print('3MF written')
except Exception as e:
    print('3MF export failed (STEP still valid):', e)
print('STEP written')
