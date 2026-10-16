"""Single source of truth for the CANBoard enclosure ("canbox") — v2, SINGLE board.

Provenance tags (same scheme as dual_pdm):
  [GROUND TRUTH] our design decisions everything derives from
  [DATUM]        coordinate-frame definition
  [MEASURED]     lifted from an artifact -- each names its exact source
  [STANDARD]     external standards, not ours to choose
  [CHOSEN]       values we defined; each states what constrains it
  [DERIVED]      computed here; no new information

=== GROUND TRUTH (v5, user 2026-08-27) =======================================
ONE CANBoard V2 PCB (corygrant/CANBoard). Connectors: 1x AT04-12PA-PM11 on the
+y wall, ONE AT04-4P-PM11 centred on the -y wall (v5: second 4P removed; box
narrowed in x -- now governed by the interior mount pitch -- and LENGTHENED
in y for cable clearance behind the connector rears); flanges surface-mount
against the inner wall faces -- NO recess pockets (v3).
Mounting (v8, user 2026-08-27): chassis holes FIXED -- 87.5 pitch, the hole
line clocked 90 deg to the connector axis (= along x), enclosure otherwise
AS SMALL AS POSSIBLE, and the sides need NOT be straight. So the body is
WAISTED: a wide HEAD band at the +y wall carries the 12P flange (vendor STEP
measured: body behind the flange is ~73 wide at 6mm depth, ~70 at 15mm,
collapsing to 31.6 past ~19mm -- so full width is only needed for HEAD_DEPTH
plus a TAPER_RUN), and the rest necks to what the 4P flange needs. External
M6 tabs (rounded ends tangent to the gusset outer faces, blended gussets)
sit off the NECK walls at TAB_Y, holes at exactly MOUNT_PITCH.
Lid (v4, user 2026-08-27): thickened plate with REBATED EDGES -- a solid
plug drops REBATE_D into the cavity opening with REBATE_CLEAR lateral
tolerance, the stepped rim seats on the wall tops (no thin registration
skirt). M3 screws into heat-set inserts; printed top-face-DOWN, so "CAN" is
RECESSED into the lid top (not raised), beside 4P #2. Generous fillets inside
the body (cavity corners + floor-wall junction).

=== DATUM ======================================================================
z = 0 at the PCB underside (user rule). x-y origin at the board's lower-left
corner, +y toward the 12-pin wall. Board sits on 5.0 bosses; floor top is
z = -BOSS_H.
"""

# === MEASURED: CANBoard V2 -- corygrant/CANBoard repo ========================
BOARD = 40.0          # [MEASURED] Edge.Cuts: square outline
BOARD_R = 3.1         # [MEASURED] corner arcs
PCB_T = 1.6           # [MEASURED] nominal; STEP confirms
HOLES_LOCAL = [(33.638, 3.178), (3.158, 36.833)]   # [MEASURED] M3 holes
HOLE_DIA = 3.2        # [MEASURED]
PARTS_TOP = 3.38      # [MEASURED] tallest part above PCB underside
KICAD_ORG = (-118.0, 103.0)   # [DERIVED] datum position of KiCad STEP origin

# === MEASURED: Amphenol Sine datasheets ======================================
C12_FLANGE = (75.7, 34.0)     # [MEASURED] AT04-12PA-PM11 flange w x h
C12_CUT = (45.5, 25.5, 5.0)   # [MEASURED] plate cutout w x h x corner R
C12_SCREW_PITCH = 61.0        # [MEASURED]
C12_NOSE = 16.7               # [MEASURED]
C12_BEHIND = 29.1             # [MEASURED]
C4_FLANGE = (55.5, 37.0)      # [MEASURED] AT04-4P-PM11 flange w x h
C4_CUT_DIA = 28.0             # [MEASURED]
C4_SCREW_PITCH = 40.5         # [MEASURED]
C4_NOSE = 17.4                # [MEASURED]
C4_BEHIND = 28.6              # [MEASURED]
CONN_SCREW_CLEAR = 5.6        # [MEASURED] plate holes for the self-tap screws

# === STANDARD =================================================================
INSERT_HOLE = 4.0     # [STANDARD] M3 heat-set insert pilot
INSERT_DEPTH = 6.5    # [STANDARD]
LID_SCREW_CLEAR = 3.4 # [STANDARD] M3 clearance
LID_CBORE = (6.4, 3.2)        # [STANDARD] M3 SHCS recess
PCB_SCREW_PILOT = 2.5 # [STANDARD] M3 thread-forming pilot
MOUNT_SCREW_CLEAR = 6.6       # [STANDARD] M6 clearance (v6: M6 SHCS mounts)
M6_SHCS_HEAD = (10.0, 6.0)    # [STANDARD] socket head cap screw dia x height

# === CHOSEN ===================================================================
BOSS_H = 5.0          # [GROUND TRUTH] PCB standoff height
BOSS_D = 7.0          # [CHOSEN]
WALL_T = 4.5          # [CHOSEN]
POCKET = 0.0          # [GROUND TRUTH] v3: flanges surface-mount on the inner
                      #   wall faces, no recess (was 1.5). Kept as a constant
                      #   so seat-plane expressions (wall face + POCKET)
                      #   degrade in place.
POCKET_CLEAR = 0.25   # [CHOSEN] lateral clearance used to space the 4P slots
BASE_T = 2.6          # [CHOSEN]
LID_T = 5.0           # [CHOSEN] v4: plate thickness above the wall top
                      #   (thickened from 3.0 to carry the edge rebate)
REBATE_D = 2.5        # [CHOSEN] v4: solid plug depth into the cavity opening
REBATE_CLEAR = 0.25   # [CHOSEN] v4: plug-to-cavity lateral tolerance per side
WIRE_BAY = 24.0       # [CHOSEN] v5: board edge to each connector wall inner
                      #   face (y both sides) -- sized so the internal cable
                      #   runs off the connector rears have straight-back room
                      #   (see CABLE_GAP assert). Rears overhang the board;
                      #   CONN_Z carries the vertical clearance
CABLE_GAP = 25.0      # [CHOSEN] v5: minimum clear span between the 12P and
                      #   4P rear bodies for the internal wire bends
END_MARGIN = 4.75     # [CHOSEN] head wall margin each side of the 12P flange
                      #   = CAVITY_R + 0.75 (at 4.0 the flange edge cleared
                      #   the plan corner fillet by only 0.24)
CONN_Z = 18.5         # [CHOSEN] connector centerline above PCB underside.
                      #   Floor: the 4P round rear bodies (dia 28) overhang the
                      #   board -- underside CONN_Z-14.0 must clear PARTS_TOP
                      #   by >= 1.0 (18.5-14.0 = 4.5 >= 4.38). 12P: 18.5-12.75
                      #   = 5.75, also clear
BOSS_PAD_D = 8.0      # [CHOSEN] lid-insert pads -- on the +-x (short) walls,
                      #   which carry no connectors in v2
INT_H = 43.75         # [CHOSEN] floor top to wall top: CONN_Z(+BOSS_H) + half
                      #   the 4P pocket + 1.5 top margin
MOUNT_PITCH = 87.5    # [GROUND TRUTH] chassis hole centres -- FIXED, cannot
                      #   be redrilled; hole line along x (90 deg to the
                      #   connector axis), user 2026-08-27
HEAD_DEPTH = 12.0     # [CHOSEN] v8: interior depth of the full-width head
                      #   band at the +y wall (12P shroud is 73.1 wide at 6mm
                      #   behind the flange -- measured from the vendor STEP)
TAPER_RUN = 10.0      # [CHOSEN] v8: head-to-neck taper length; at its end
                      #   (depth 22) the shroud is only 31.6 wide. Mid-taper
                      #   width vs shroud verified by the assembly clash check
NECK_MARGIN = 4.5     # [CHOSEN] v8: neck wall margin each side of the 4P
                      #   flange = CAVITY_R + 0.5, so the plan corner fillet
                      #   stays clear of the flange corners (clash-probed:
                      #   at 2.0 the r4 corner arc intruded 0.4 into the
                      #   flange footprint)
TAB_T = 5.0           # [CHOSEN] tab thickness at base level (M6 duty), head
                      #   seats directly on the tab
TAB_Y = 20.0          # [CHOSEN] v8: tab centreline y (mid-neck, clear of the
                      #   head taper and the lid-insert pads)
GUSSET_T = 3.0        # [CHOSEN] gusset thickness (y)
GUSSET_H = 15.0       # [CHOSEN] gusset height above the tab top
GUSSET_GAP = 18.0     # [CHOSEN] clear span between gusset inner faces --
                      #   room for the M6 head (10) + socket/key access
GUSSET_FOOT_R = 4.0   # [CHOSEN] fillet radius blending the brace into the
                      #   tab top at the foot
TAB_W = GUSSET_GAP + 2 * GUSSET_T   # [DERIVED] tab width spans the gussets
TAB_END_R = TAB_W / 2 # [DERIVED] rounded end radius = tab half-width: end
                      #   arc tangent to the gusset outer faces (user rule)
CAVITY_R = 4.0        # [CHOSEN] interior vertical corner fillet (v3)
FLOOR_FILLET = 3.0    # [CHOSEN] cavity floor-to-wall fillet (v3)
CAN_TEXT_H = 18.0     # [CHOSEN] "CAN" letter height, RECESSED 0.8 into the
                      #   lid top beside 4P #2 (lid prints top-face-down)
CAN_TEXT_D = 0.8      # [CHOSEN] recess depth

# === DERIVED ==================================================================
# waisted interior plan, datum frame (v8). Head band carries the 12P; neck
# carries everything else (4P flange governs its width):
CTR_X = BOARD / 2
HEAD_IHALF = (C12_FLANGE[0] + 2 * POCKET_CLEAR + 2 * END_MARGIN) / 2   # 42.35
NECK_IHALF = (C4_FLANGE[0] + 2 * POCKET_CLEAR + 2 * NECK_MARGIN) / 2   # 30.0
IY1, IY2 = -WIRE_BAY, BOARD + WIRE_BAY
HEAD_Y1 = IY2 - HEAD_DEPTH                 # full-width band bottom (52)
NECK_Y2 = HEAD_Y1 - TAPER_RUN              # neck top (42)
# neck inner faces double as the reference walls for inserts/lid features:
IX1, IX2 = CTR_X - NECK_IHALF, CTR_X + NECK_IHALF
HX1, HX2 = CTR_X - HEAD_IHALF, CTR_X + HEAD_IHALF
FLOOR = -BOSS_H
TOP = FLOOR + INT_H
EX1, EX2 = IX1 - WALL_T, IX2 + WALL_T      # NECK exterior faces
EY1, EY2 = IY1 - WALL_T, IY2 + WALL_T
EZ1, EZ2 = FLOOR - BASE_T, TOP + LID_T
CTR_Y = (IY1 + IY2) / 2
# single 4P centred on the -y wall (v5):
C4_SLOT = C4_FLANGE[0] + 2 * POCKET_CLEAR
C4_X = [CTR_X]
# mounting (v8): one external tab per NECK wall at TAB_Y, holes at the fixed
# chassis pitch:
MOUNT_HOLES = [(CTR_X - MOUNT_PITCH / 2, TAB_Y), (CTR_X + MOUNT_PITCH / 2, TAB_Y)]
TAB_REACH = MOUNT_PITCH / 2 - (NECK_IHALF + WALL_T)   # hole beyond neck wall
# PCB bosses (single board):
PCB_BOSSES = list(HOLES_LOCAL)
# lid-insert pads: two on the neck inner walls at the -y end, two on the
# head inner walls at the +y end:
INSERTS = [(IX1, IY1 + 8.0), (IX2, IY1 + 8.0),
           (HX1, IY2 - 8.0), (HX2, IY2 - 8.0)]

assert IX1 + NECK_MARGIN <= C4_X[0] - C4_SLOT / 2 and \
       C4_X[0] + C4_SLOT / 2 <= IX2 - NECK_MARGIN, '4P flange vs neck walls'
# v8 tab geometry:
assert TAB_REACH > 0, 'tab holes inside the neck walls'
assert TAB_END_R > MOUNT_SCREW_CLEAR / 2 + 2.0, 'tab rim too thin at the hole'
assert GUSSET_GAP >= M6_SHCS_HEAD[0] + 6.0, 'gussets crowd the M6 socket head'
assert TAB_Y + TAB_W / 2 + 1 < NECK_Y2, 'tab overlaps the head taper'
assert TAB_Y - TAB_W / 2 > IY1 + 8.0 + 4 + 1, 'tab overlaps the -y insert pad'
assert CTR_X - (C12_FLANGE[0] / 2 + POCKET_CLEAR) > HX1 and \
       CTR_X + (C12_FLANGE[0] / 2 + POCKET_CLEAR) < HX2, '12P flange vs head walls'
assert CONN_Z - C4_CUT_DIA / 2 >= PARTS_TOP + 1.0, '4P rear vs board parts'
assert CONN_Z - C12_CUT[1] / 2 >= PARTS_TOP + 1.0, '12P rear vs board parts'
assert FLOOR + INT_H - (CONN_Z + C4_FLANGE[1] / 2 + POCKET_CLEAR) >= 1.5, \
    '4P pocket too close to the wall top'
# opposing rear bodies need the cable-bend gap between them (v5):
assert (IY2 - C12_BEHIND + POCKET) - (IY1 + C4_BEHIND - POCKET) >= CABLE_GAP, \
    'cable gap between the 12P and 4P rear bodies too small'

import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
CANBOARD = os.environ.get('CANBOARD_DIR', os.path.expanduser('~/CANBoard'))

def canboard(rel):
    p = os.path.join(CANBOARD, rel)
    assert os.path.exists(p), \
        f'{p} missing: clone github.com/corygrant/CANBoard, set CANBOARD_DIR'
    return p

os.makedirs(OUT, exist_ok=True)
