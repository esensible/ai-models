"""Single source of truth for the SLIM CANBoard enclosure ("canbox_slim").

A fresh, minimal design (user 2026-08-28): just the bare CANBoard -- no
panel-mount connectors. Wires enter through a plain hole in each end wall.
Smooth, rounded, low profile. Mounts on the same fixed chassis holes as the
full canbox: 87.5 pitch, on external tabs, hole line perpendicular to the
cable axis.

Provenance tags as per dual_pdm/canbox:
  [GROUND TRUTH] user decisions   [DATUM] frame   [MEASURED] from artifacts
  [STANDARD] external standards   [CHOSEN] ours   [DERIVED] computed

=== DATUM ======================================================================
z = 0 at the PCB underside. x-y origin at the board's lower-left corner,
+y along the cable axis (holes on the +-y end walls), tabs on +-x.
"""

# === MEASURED: CANBoard V2 -- corygrant/CANBoard repo ========================
BOARD = 40.0          # [MEASURED] Edge.Cuts square outline
BOARD_R = 3.1         # [MEASURED] corner arcs
PCB_T = 1.6           # [MEASURED]
HOLES_LOCAL = [(33.638, 3.178), (3.158, 36.833)]   # [MEASURED] M3 holes
PARTS_TOP = 3.38      # [MEASURED] tallest part above PCB underside
KICAD_ORG = (-118.0, 103.0)   # [DERIVED] datum position of KiCad STEP origin

# === GROUND TRUTH =============================================================
MOUNT_PITCH = 87.5    # fixed chassis holes, unchanged
CABLE_D = 9.0         # plain cable hole, one per end wall. Sized for the
                      #   bundle: 12x 18AWG TXL (~1.9 OD each) packs to
                      #   ~7.7 -- 9.0 feeds easily (user 2026-08-28; was 10)
LID_TEXT = ("Fuck", "Yeah")   # recessed on the lid top, two lines (user)
LID_TEXT_H = 12.0     # letter height per line
LID_TEXT_D = 0.8      # recess depth
LID_TEXT_ROT = 15.0   # block rotated 15 deg to the left (CCW), user
LID_TEXT_FONT = 'ComicNeue-Bold.ttf'   # user asked for Chalkboard (Apple,
                      #   unavailable here) -- Comic Neue Bold is its closest
                      #   free equivalent; TTF lives in cad/.home
# sleek / minimal / smooth / rounded / low profile

# === STANDARD =================================================================
MOUNT_SCREW_CLEAR = 6.6       # [STANDARD] M6 clearance
INSERT_HOLE = 4.0     # [STANDARD] M3 heat-set insert pilot
INSERT_DEPTH = 6.5    # [STANDARD]
LID_SCREW_CLEAR = 3.4 # [STANDARD] M3 clearance
CSK_HEAD_D = 6.5      # [STANDARD] DIN 7991 M3 flat head 6.0 + breathing room
PCB_SCREW_PILOT = 2.5 # [STANDARD] M3 thread-forming pilot

# === CHOSEN ===================================================================
WALL_T = 3.0          # [CHOSEN] light walls -- small box, no connector loads
BASE_T = 2.4          # [CHOSEN]
BOSS_H = 3.0          # [CHOSEN] low board standoff (low profile)
BOSS_D = 7.0          # [CHOSEN]
PCB_CLEAR = 2.5       # [CHOSEN] board edge to side wall (x)
WIRE_END = 9.5        # [CHOSEN] board edge to each end wall (y): room for the
                      #   entering wires AND the corner insert columns (which
                      #   moved inboard for the clamshell split)
CABLE_Z = 5.0         # [CHOSEN] cable hole centre above the PCB underside --
                      #   hole bottom at board level, wires arrive just above
                      #   the board edge
TOP_MARGIN = 3.0      # [CHOSEN] wall above the cable hole (must exceed
                      #   REBATE_D so the lid plug clears the hole crest)
LID_T = 3.0           # [CHOSEN] lid plate above the wall top
# clamshell split (user 2026-08-28): the lid extends down the sides; the
# parting line runs through the cable hole centres so the holes OPEN with
# the lid (wires lay into cradles, no threading)
LIP_T = 1.5           # [CHOSEN] registration lip: inner half of the base
                      #   wall continues up past the parting line
LIP_H = 2.5           # [CHOSEN] lip height above the parting line
LIP_CLEAR = 0.15      # [CHOSEN] lid groove clearance around the lip
PAD_R = 4.0           # [CHOSEN] insert column radius (freestanding, inboard)
TAB_T = 4.0           # [CHOSEN] tab thickness at base level
GUSSET_T = 3.0        # [CHOSEN] gusset fin thickness (y)
GUSSET_H = 5.5        # [CHOSEN] gusset height above the tab top (wall is
                      #   only PART_Z tall here -- fin stays below the lip)
GUSSET_GAP = 18.0     # [CHOSEN] clear span between fins: M6 head + socket
TAB_W = GUSSET_GAP + 2 * GUSSET_T   # [DERIVED] 24 -- fins ride the tab edges,
                      #   end arc tangent to their outer faces (house rule)
CAVITY_R = 4.0        # [CHOSEN] interior plan corner radius
SOFT_R = 0.5          # [CHOSEN] global edge softening
TOP_R = 2.0           # [CHOSEN] lid top-perimeter roundover (the "smooth" look)

# === DERIVED ==================================================================
CTR_X, CTR_Y = BOARD / 2, BOARD / 2
IX1, IX2 = -PCB_CLEAR, BOARD + PCB_CLEAR             # interior x: -2.5..42.5
IY1, IY2 = -WIRE_END, BOARD + WIRE_END               # interior y: -8..48
FLOOR = -BOSS_H
INT_H = BOSS_H + CABLE_Z + CABLE_D / 2 + TOP_MARGIN  # 15.0 floor->wall top
TOP = FLOOR + INT_H                                  # 12.0
EX1, EX2 = IX1 - WALL_T, IX2 + WALL_T                # -5.5..45.5
EY1, EY2 = IY1 - WALL_T, IY2 + WALL_T                # -11..51
EZ1 = FLOOR - BASE_T                                 # -5.4
EZ2 = TOP + LID_T                                    # 15.0 overall top
PART_Z = CABLE_Z                                     # [DERIVED] parting plane
                                                     #   = cable hole centre
MOUNT_HOLES = [(CTR_X - MOUNT_PITCH / 2, CTR_Y), (CTR_X + MOUNT_PITCH / 2, CTR_Y)]
TAB_END_R = TAB_W / 2                                # tangent-end rule
TAB_REACH = MOUNT_PITCH / 2 - (CTR_X - EX1)          # hole beyond -x wall
# lid inserts: four freestanding columns in the end bays, inboard of the
# descending lid walls, clear of the board corners and the wire path from
# each cable hole to the board:
INSERT_XO = 14.0                                     # column x = CTR_X -+ 14
INSERTS = [(CTR_X - INSERT_XO, IY1 + PAD_R + 0.75),
           (CTR_X + INSERT_XO, IY1 + PAD_R + 0.75),
           (CTR_X - INSERT_XO, IY2 - PAD_R - 0.75),
           (CTR_X + INSERT_XO, IY2 - PAD_R - 0.75)]
PCB_BOSSES = list(HOLES_LOCAL)

assert TAB_REACH > TAB_END_R - 4, 'tab too stubby for its end radius'
assert TOP >= CABLE_Z + CABLE_D / 2 + TOP_MARGIN - 0.01, 'hole vs wall top'
assert PART_Z > PARTS_TOP + 1.0, 'parting line below the board parts'
assert LIP_T < WALL_T, 'lip eats the whole wall'
for _x, _y in INSERTS:
    # column vs board edges (board occupies 0..BOARD in both axes)
    _dy = -_y if _y < CTR_Y else _y - BOARD
    assert _dy - PAD_R >= 0.5, 'insert column hits the board edge'
    # column vs the wire path out of the cable hole (hole spans CTR_X +- D/2)
    assert abs(_x - CTR_X) - PAD_R >= CABLE_D / 2 + 1.5, \
        'insert column blocks the cable path'
    assert abs(_y - CTR_Y) > TAB_W / 2 + 4, 'insert column in the tab band'

import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
CANBOARD = os.environ.get('CANBOARD_DIR', os.path.expanduser('~/CANBoard'))

def canboard(rel):
    p = os.path.join(CANBOARD, rel)
    assert os.path.exists(p), \
        f'{p} missing: clone github.com/corygrant/CANBoard, set CANBOARD_DIR'
    return p

os.makedirs(OUT, exist_ok=True)
