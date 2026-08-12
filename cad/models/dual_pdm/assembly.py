# Full dual-dingoPDM assembly for clearance checking (build123d).
# Datum frame: board A lower-left PCB corner, z=0 at PCB bottom.
# Components are separately named so Fusion/Orca can show/hide them.
# The heatsink is the RAW BLANK (no holes/pockets/rebates modeled).
from build123d import *

import os
S = os.path.join(os.path.dirname(__file__), '..', '..', 'out')   # products of
                                                                 # templates.py + enclosure.py
DINGOPDM = os.environ.get('DINGOPDM_DIR', os.path.expanduser('~/dingoPDM'))
PCBA = os.path.join(DINGOPDM, 'Export/V7.5/DingoPDM_V7_5.step')
assert os.path.exists(PCBA), \
    'clone https://github.com/corygrant/dingoPDM and set DINGOPDM_DIR to it'

HS_X1, HS_Y1, HS_X2, HS_Y2 = -12.0, 4.0, 166.78, 91.25
HS_TOP, HS_THICK = -0.5, 12.0    # top at pad plane; thickness = your stock

pcba_full = import_step(PCBA)
# keep the PCB + every clearance-relevant part (sizable, or reaching above z=4);
# drops hundreds of tiny passives that only bloat the file
kept = [s for s in pcba_full.solids()
        if s.volume > 50 or s.bounding_box().max.Z > 4]
print(f'PCBA solids kept: {len(kept)} of {len(pcba_full.solids())}')
import copy
pcba = Compound(children=[s for s in kept])
board_A = Pos(37.846, 61.976, 0) * copy.copy(pcba)   # PCBA frame -> datum frame
board_B = Pos(37.846 + 82.39, 61.976, 0) * copy.copy(pcba)
heatsink = Pos((HS_X1 + HS_X2) / 2, (HS_Y1 + HS_Y2) / 2, HS_TOP - HS_THICK / 2) * \
    Box(HS_X2 - HS_X1, HS_Y2 - HS_Y1, HS_THICK)
enclosure = import_step(f'{S}/case_dual_mod.step')
t1 = Pos(0, 0, HS_TOP) * import_step(f'{S}/template1_drill_guide.step')
t2 = Pos(0, 0, HS_TOP) * import_step(f'{S}/template2_router_reliefs.step')
t3 = Pos(0, 0, HS_TOP) * import_step(f'{S}/template3_skirt_rebate.step')

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
export_step(asm, f'{S}/dual_pdm_assembly.step')
print('STEP written')

try:
    m = Mesher()
    for name, p in parts:
        m.add_shape(p, part_number=name)
    m.write(f'{S}/dual_pdm_assembly.3mf')
    print('3MF written')
except Exception as e:
    print('3MF export failed (STEP still valid):', e)
