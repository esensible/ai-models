# Full dual-dingoPDM assembly for clearance checking (build123d).
# All values from spec.py. Components separately named for Fusion/Orca
# show/hide. The heatsink is a RAW BLANK at the minimum outline (the case
# screw lines) -- display only, nothing derives from it.
from build123d import *
import copy
import spec as S

pcba_full = import_step(S.dingopdm('Export/V7.5/DingoPDM_V7_5.step'))
# keep the PCB + every clearance-relevant part (sizable, or reaching above
# z=4); drops hundreds of tiny passives that only bloat the file
kept = [s for s in pcba_full.solids()
        if s.volume > 50 or s.bounding_box().max.Z > 4]
print(f'PCBA solids kept: {len(kept)} of {len(pcba_full.solids())}')
pcba = Compound(children=[s for s in kept])
board_A = Pos(*S.KICAD_ORG, 0) * copy.copy(pcba)
board_B = Pos(S.KICAD_ORG[0] + S.B_OFF, S.KICAD_ORG[1], 0) * copy.copy(pcba)
heatsink = Pos((S.SX1 + S.SX2) / 2, (S.SY1 + S.SY2) / 2,
               S.HS_TOP - S.HS_THICK_NOM / 2) * \
    Box(S.SX2 - S.SX1, S.SY2 - S.SY1, S.HS_THICK_NOM)
enclosure = import_step(f'{S.OUT}/case_dual_mod.step')
t1 = Pos(0, 0, S.HS_TOP) * import_step(f'{S.OUT}/template1_drill_guide.step')
t2 = Pos(0, 0, S.HS_TOP) * import_step(f'{S.OUT}/template2_router_reliefs.step')
t3 = Pos(0, 0, S.HS_TOP) * import_step(f'{S.OUT}/template3_skirt_rebate.step')

parts = [('heatsink_blank', heatsink), ('board_A', board_A), ('board_B', board_B),
         ('enclosure', enclosure), ('template1_drill', t1),
         ('template2_reliefs', t2), ('template3_rebate', t3)]
for name, p in parts:
    p.label = name
    bb = p.bounding_box()
    print(f'{name:18s} solids {len(p.solids()):4d}  '
          f'({bb.min.X:7.2f},{bb.min.Y:7.2f},{bb.min.Z:7.2f}) -> '
          f'({bb.max.X:7.2f},{bb.max.Y:7.2f},{bb.max.Z:7.2f})')

asm = Compound(children=[p for _, p in parts], label='dual_dingoPDM')
export_step(asm, f'{S.OUT}/dual_pdm_assembly.step')
print('STEP written')

import zipfile
with zipfile.ZipFile(f'{S.OUT}/dual_pdm_assembly_step.zip', 'w',
                     zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(f'{S.OUT}/dual_pdm_assembly.step', 'dual_pdm_assembly.step')

try:   # boards-free 3MF for Orca (the PCBA meshes fail 3MF validation)
    m = Mesher()
    for name, p in parts:
        if name.startswith('board'):
            continue
        m.add_shape(p, part_number=name)
    m.write(f'{S.OUT}/dual_pdm_assembly_no_boards.3mf')
    print('3MF written')
except Exception as e:
    print('3MF export failed (STEP still valid):', e)
