# Slim CANBoard enclosure assembly (build123d): base + lid closed + the real
# CANBoard V2 PCBA, for review and clearance checking. All values from spec.py.
from build123d import *
import spec as S

base = import_step(f'{S.OUT}/canbox_slim_base.step')
lid = import_step(f'{S.OUT}/canbox_slim_lid.step')
pcba = import_step(S.canboard('Export/V2/CANBoard_V2.step'))
board = Pos(*S.KICAD_ORG, 0) * pcba
bb = board.bounding_box()
assert abs(bb.min.X) < 0.5 and abs(bb.min.Y) < 0.5 and \
    abs(bb.max.X - S.BOARD) < 0.5 and abs(bb.max.Y - S.BOARD) < 0.5, \
    f'board not at datum: ({bb.min.X:.2f},{bb.min.Y:.2f})..({bb.max.X:.2f},{bb.max.Y:.2f})'

parts = [('base', base), ('lid', lid), ('board', board)]
for name, p in parts:
    p.label = name
    b = p.bounding_box()
    print(f'{name:6s} solids {len(p.solids()):3d}  '
          f'({b.min.X:7.2f},{b.min.Y:7.2f},{b.min.Z:6.2f}) -> '
          f'({b.max.X:7.2f},{b.max.Y:7.2f},{b.max.Z:6.2f})')

def clash(a, b, label):
    v = 0
    for sa in a.solids():
        for sb in b.solids():
            i = sa.intersect(sb)
            if i:
                v += sum(s.volume for s in i.solids())
    print(f'{label}: intersection (want 0): {v:.4f}')
    assert v < 1e-6, label

clash(base, lid, 'base vs lid')
clash(board, base, 'board vs base')
clash(board, lid, 'board vs lid')

asm = Compound(children=[p for _, p in parts], label='canbox_slim')
export_step(asm, f'{S.OUT}/canbox_slim_assembly.step')
print('STEP written')
