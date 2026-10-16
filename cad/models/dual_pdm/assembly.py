# Full dual-dingoPDM assembly (build123d), v4: LEFT + RIGHT adapted cases
# (skirtless, thick ears, butted at the centreline with shared screw holes)
# on the 204 heatsink, no intermediate plate. All values from spec.py.
from build123d import *
import copy
import spec as S

pcba_full = import_step(S.dingopdm('Export/V7.5/DingoPDM_V7_5.step'))
kept = [s for s in pcba_full.solids()
        if s.volume > 50 or s.bounding_box().max.Z > 4]
print(f'PCBA solids kept: {len(kept)} of {len(pcba_full.solids())}')
pcba = Compound(children=[s for s in kept])
board_A = Pos(*S.KICAD_ORG, 0) * copy.copy(pcba)
board_B = Pos(S.KICAD_ORG[0] + S.B_OFF, S.KICAD_ORG[1], 0) * copy.copy(pcba)

case_L = import_step(f'{S.OUT}/dual_pdm_case_left.step')
case_R = import_step(f'{S.OUT}/dual_pdm_case_right.step')

HS_X1 = S.CTR_A[0] - S.CASE_TAB_TIP
heatsink = Pos(HS_X1 + S.HS_LEN / 2, S.CTR_A[1], S.HS_TOP - S.HS_THICK_NOM / 2) * \
    Box(S.HS_LEN, 2 * S.CASE_HALF_L, S.HS_THICK_NOM)

parts = [('heatsink_blank', heatsink), ('board_A', board_A), ('board_B', board_B),
         ('case_left', case_L), ('case_right', case_R)]
for name, p in parts:
    p.label = name
    b = p.bounding_box()
    print(f'{name:15s} solids {len(p.solids()):4d}  '
          f'({b.min.X:7.2f},{b.min.Y:7.2f},{b.min.Z:7.2f}) -> '
          f'({b.max.X:7.2f},{b.max.Y:7.2f},{b.max.Z:7.2f})')

def clash(a, b, label):
    v = 0
    for sa in a.solids():
        for sb in b.solids():
            i = sa.intersect(sb)
            if i:
                v += sum(s.volume for s in i.solids())
    print(f'{label}: intersection (want 0): {v:.4f}')
    assert v < 1e-6, label

clash(case_L, case_R, 'case_left vs case_right')
clash(board_A, case_L, 'board_A vs case_left')
clash(board_B, case_R, 'board_B vs case_right')
# cases rest ON the heatsink plane, never into it
for name, c in (('left', case_L), ('right', case_R)):
    assert c.bounding_box().min.Z >= S.HS_TOP - 0.01, f'case_{name} into the heatsink'

asm = Compound(children=[p for _, p in parts], label='dual_dingoPDM')
export_step(asm, f'{S.OUT}/dual_pdm_assembly.step')
print('STEP written')

import zipfile
with zipfile.ZipFile(f'{S.OUT}/dual_pdm_assembly_step.zip', 'w',
                     zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(f'{S.OUT}/dual_pdm_assembly.step', 'dual_pdm_assembly.step')
print('zip written')
