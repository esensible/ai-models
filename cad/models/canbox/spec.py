"""Single source of truth for the dual-CANBoard enclosure ("canbox").

Provenance tags (same scheme as dual_pdm):
  [GROUND TRUTH] our design decisions everything derives from
  [DATUM]        coordinate-frame definition
  [MEASURED]     lifted from an artifact -- each names its exact source
  [STANDARD]     external standards, not ours to choose
  [CHOSEN]       values we defined; each states what constrains it
  [DERIVED]      computed here; no new information

=== GROUND TRUTH ===============================================================
Two CANBoard V2 PCBs (corygrant/CANBoard), side by side in one plane, 5.0mm
edge gap. Connectors: 2x Amphenol Sine AT04-12PA-PM11 (one per long wall,
OPPOSITE walls), 1x AT04-4P-PM11 on an adjacent (short) wall between them.
Form factor: lowest profile achievable -- the height floor is set by the
4-pin's 37.0-tall flange, not the boards.

=== DATUM ======================================================================
z = 0 at the PCB undersides (user rule). x-y origin at board A's lower-left
corner, +x toward board B, +y toward the +Y 12-pin wall. Boards sit on 5.0
bosses, so the enclosure floor top is z = -BOSS_H.
"""

# === GROUND TRUTH =============================================================
GAP = 5.0             # [GROUND TRUTH] board edge-to-edge separation (x)

# === MEASURED: CANBoard V2 -- corygrant/CANBoard repo ========================
# CANBoard/CANBoard.kicad_pcb unless stated
BOARD = 40.0          # [MEASURED] Edge.Cuts: square outline 118..158 x 63..103
BOARD_R = 3.1         # [MEASURED] Edge.Cuts corner arcs
PCB_T = 1.6           # [MEASURED] nominal; Export/V2/CANBoard_V2.step confirms
HOLES_LOCAL = [(33.638, 3.178), (3.158, 36.833)]   # [MEASURED] M3 MountingHole
                      #   footprints, kicad (151.638,99.822)/(121.158,66.167)
HOLE_DIA = 3.2        # [MEASURED] M3 clearance in the PCB
PARTS_TOP = 3.38      # [MEASURED] CANBoard_V2.step: tallest populated part
                      #   above PCB underside (headers NOT populated)
KICAD_ORG = (-118.0, 103.0)   # [DERIVED] datum position of the KiCad STEP
                              #   origin (x=-outline min, y=+outline max)

# === MEASURED: Amphenol Sine datasheets ======================================
# AT04-12PX-PMXX drawing rev A4 (amphenol-sine.com/pdf/datasheet/AT04-12PA-PM11.pdf)
C12_FLANGE = (75.7, 34.0)     # [MEASURED] flange outline (long x tall)
C12_CUT = (45.5, 25.5, 5.0)   # [MEASURED] mounting-plate cutout w x h x corner R
C12_SCREW_PITCH = 61.0        # [MEASURED] 2x screw holes, plate drill 5.6
C12_NOSE = 16.7               # [MEASURED] flange front to mating surface
C12_BEHIND = 29.1             # [MEASURED] depth behind flange (rear body)
# AT04-4P-PM1X drawing rev A1 (amphenol-sine.com/pdf/datasheet/AT04-4P-PM11.pdf)
C4_FLANGE = (55.5, 37.0)      # [MEASURED] flange outline (long x tall)
C4_CUT_DIA = 28.0             # [MEASURED] round mounting-plate cutout
C4_SCREW_PITCH = 40.5         # [MEASURED] 2x screw holes, plate drill 5.6
C4_NOSE = 17.4                # [MEASURED] flange front to mating surface
C4_BEHIND = 28.6              # [MEASURED] depth behind flange
CONN_SCREW_CLEAR = 5.6        # [MEASURED] both drawings: plate hole for the
                              #   ST4.8 / #10 self-tap screws that thread into
                              #   the connectors' own 4.0 dia x 16.4 deep bosses

# === STANDARD =================================================================
INSERT_HOLE = 4.0     # [STANDARD] M3 heat-set insert (OD ~4.6) pilot hole
INSERT_DEPTH = 6.5    # [STANDARD] M3 x 5.7 insert + slack
LID_SCREW_CLEAR = 3.4 # [STANDARD] M3 clearance in the lid
LID_CBORE = (6.4, 3.2)        # [STANDARD] M3 SHCS head 5.5x3 recess dia/depth
PCB_SCREW_PILOT = 2.5 # [STANDARD] pilot for M3 thread-forming plastic screws

# === CHOSEN ===================================================================
BOSS_H = 5.0          # [GROUND TRUTH] PCB standoff height (user-specified)
BOSS_D = 7.0          # [CHOSEN] PCB boss diameter: >= screw head + seat
WALL_T = 4.5          # [CHOSEN] wall: flange pocket 1.5 leaves a 3.0 panel;
                      #   full 4.5 at the screw ears carries connector torque
POCKET = 1.5          # [CHOSEN] flange recess depth into the wall inner face
POCKET_CLEAR = 0.25   # [CHOSEN] flange-to-pocket clearance per side (locate)
BASE_T = 2.6          # [CHOSEN] floor thickness under the boss field
LID_T = 3.0           # [CHOSEN] lid plate thickness
LIP_H = 2.5           # [CHOSEN] lid registration skirt drop below the plate
LIP_T = 2.0           # [CHOSEN] skirt thickness
LIP_CLEAR = 0.15      # [CHOSEN] skirt-to-wall-inner-face fit clearance
SIDE_CLEAR_E = 4.5    # [CHOSEN] board B edge to +x wall inner face
SIDE_CLEAR_W = 11.0   # [CHOSEN] board A edge to -x (4P) wall inner face:
                      #   sized so the 4P rear structures clear the 12P rear
                      #   structures (vendor STEPs kiss at 9.0; 11.0 gives
                      #   ~1.4 at the closest features, verified empirically
                      #   in assembly.py); the extra space is the wiring bay
WIRE_BAY = 11.0       # [CHOSEN] board edge to wall inner face, y direction:
                      #   wiring room; also makes the short wall long enough
                      #   for the 4P flange (55.5 + margins)
CONN_Z = 17.25        # [CHOSEN] connector centerline above PCB underside.
                      #   Floor: the 12P rear bodies (25.5 tall, 27.6 deep)
                      #   overhang the boards -- their underside CONN_Z-12.75
                      #   must clear the tallest board part (3.38 measured)
                      #   by >= 1.0
BOSS_PAD_D = 8.0      # [CHOSEN] lid-insert wall pads: fit within the 12P
                      #   flange end margins (8.65 each end of the long walls)
INT_H = 43.5          # [CHOSEN] interior height, floor top to wall top:
                      #   CONN_Z + half the 4P pocket + 1.5 top margin;
                      #   the connector stack is THE height driver

# === DERIVED ==================================================================
PITCH = BOARD + GAP                        # 45.0 board-origin pitch (x)
B_OFF = PITCH
# interior box, datum frame:
IX1, IX2 = -SIDE_CLEAR_W, 2 * BOARD + GAP + SIDE_CLEAR_E   # -11.0 .. 89.5
IY1, IY2 = -WIRE_BAY, BOARD + WIRE_BAY                   # -11.0 .. 51.0
FLOOR = -BOSS_H                            # -5.0 floor top
TOP = FLOOR + INT_H                        # +36.5 wall top / lid underside
# exterior:
EX1, EX2 = IX1 - WALL_T, IX2 + WALL_T
EY1, EY2 = IY1 - WALL_T, IY2 + WALL_T
EZ1, EZ2 = FLOOR - BASE_T, TOP + LID_T     # -7.6 .. 39.5 overall
CTR_X = (2 * BOARD + GAP) / 2              # 42.5: 12P connectors centered over
                                           #   the BOARD field (not the interior,
                                           #   which is wider on the 4P side)
CTR_Y = (IY1 + IY2) / 2                    # 20.0: 4P centered on its wall
# PCB bosses (board holes, both boards):
PCB_BOSSES = [(x, y) for off in (0, B_OFF) for x, y in
              [(h[0] + off, h[1]) for h in HOLES_LOCAL]]
# lid insert pads: long-wall end margins, clear of the 12P flange pockets
PAD_XS = [IX1 + 4.4, IX2 - 4.4]
INSERTS = [(x, y) for x in PAD_XS for y in (IY1, IY2)]   # pad centers ON the
                                                         # wall inner faces
C12_HALF = C12_FLANGE[0] / 2 + POCKET_CLEAR
for pad_end in (IX1, IX2):   # 12P pockets must clear the lid-insert pads
    assert abs(CTR_X - pad_end) - C12_HALF > BOSS_PAD_D / 2 + 0.4, \
        '12P pocket hits lid-insert pads'
# coarse pre-check only -- the authoritative clearance check runs the vendor
# STEP geometries against each other in assembly.py
assert (IX1 - POCKET + C4_BEHIND) <= (CTR_X - (C12_CUT[0] - 0.2) / 2) - 3.5, \
    '4P rear body too close to the 12P rear bodies'
assert (IY2 - IY1) - (C4_FLANGE[0] + 2 * POCKET_CLEAR) > 4, '4P flange vs wall'
assert FLOOR + INT_H - (CONN_Z + C4_FLANGE[1] / 2 + POCKET_CLEAR) >= 1.5, \
    '4P pocket too close to the wall top'
assert CONN_Z - C12_CUT[1] / 2 >= PARTS_TOP + 1.0, \
    '12P rear body clashes board components'

import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
CANBOARD = os.environ.get('CANBOARD_DIR', os.path.expanduser('~/CANBoard'))

def canboard(rel):
    p = os.path.join(CANBOARD, rel)
    assert os.path.exists(p), \
        f'{p} missing: clone github.com/corygrant/CANBoard, set CANBOARD_DIR'
    return p

os.makedirs(OUT, exist_ok=True)
