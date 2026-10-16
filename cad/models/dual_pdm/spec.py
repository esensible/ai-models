"""Single source of truth for the dual-dingoPDM project.

Every dimensional value used by templates.py / enclosure.py / assembly.py
lives here, tagged by provenance:

  [GROUND TRUTH]  our design decisions that everything derives from
  [DATUM]         coordinate-frame definition
  [MEASURED]      lifted from Cory Grant's dingoPDM artifacts -- each states
                  exactly which file it came from
  [STANDARD]      external standards (screw/tool geometry), not ours to choose
  [CHOSEN]        values we defined -- clearances, tooling, fabrication picks.
                  NOT derived from ground truth; each comment says what
                  constrains it
  [DERIVED]       computed here from the above; no new information

=== GROUND TRUTH ===============================================================
v3 (user 2026-08-28): ENCLOSURE-FIRST. Two STOCK single V7.5 cases, already
printed in PAHT-CF, sit side by side on the user's EXISTING heatsink plate,
HS_LEN = 204 long in the join (x) direction. The cases are positioned for
maximum separation with their OUTER ear tips flush with the heatsink ends;
at that pitch the INNER (join-side) ears overlap by ~21 -- the user cuts
those tabs by hand to interleave (no more crop-wall-and-bridge, no divider,
no joint screw: enclosure.py/raft.py/assembly.py and template3 describe the
OBSOLETE printed-dual design). Boards keep their orientation and stay
CENTRED in their cases (so the roof windows line up) -> board positions are
DERIVED from the case positions. The drill template follows, and adds
chain-drill holes along the corners and edges of every relief pocket to
reduce milling.

=== DATUM ======================================================================
z = 0 at the UNDERSIDE of the PCBs (user's choice).
x-y origin at board A's lower-left PCB corner (our choice): +x from board A
toward board B (the join direction), +y along the boards' long edges. Chosen
so all board-A geometry is positive and axes match the KiCad export axes.
All values below are in this frame unless marked board-local (identical for
board A; add PITCH to x for board B).
"""

# === GROUND TRUTH =============================================================
HS_LEN = 204.0        # [MEASURED] the user's existing heatsink plate, length
                      #   in the join (x) direction (user 2026-08-28; the
                      #   first-quoted 125 was corrected to 204)

# === MEASURED: the board -- dingoPDM repo, DingoPDM/DingoPDM.kicad_pcb =======
BOARD_W = 72.39       # [MEASURED] Edge.Cuts gr_rect, x extent
BOARD_L = 95.25       # [MEASURED] Edge.Cuts gr_rect, y extent
PCB_T = 1.63          # [MEASURED] PCB solid in Export/V7.5/DingoPDM_V7_5.step
                      #   (nominal 1.6; the STEP models 1.63)
M3_HOLES_LOCAL = [    # [MEASURED] MountingHole_3.2mm_M3 footprints H1..H4,
    (4.826, 40.386),  #   kicad (-33.02, 21.59) etc., converted to datum frame
    (64.516, 40.386),
    (16.764, 83.566),
    (64.516, 83.566)]
M3_HOLE_DIA = 3.2     # [MEASURED] same footprints: M3 clearance in the PCB
STUD_P_LOCAL = (13.208, 34.798)   # [MEASURED] J1 +12V RedCube footprint origin
                                  #   kicad (-24.638, 27.178); all pads net +12V
STUD_N_LOCAL = (7.366, 89.154)    # [MEASURED] J2 GND RedCube, kicad
                                  #   (-30.48, -27.178); all pads net GND
PIN_GRID = 3.81       # [MEASURED] RedCube 7461084 footprint: 8 pins, rows at
                      #   y +-3.81, columns x +-1.27 / +-3.81
PIN_DRILL = 1.475     # [MEASURED] RedCube footprint pad drill
DT_CTR_LOCAL = (37.846, 61.976)   # [MEASURED] DT15-12PA footprint at kicad
                                  #   (0,0) = exactly the board center
DT_PIN_HALF = (11.11, 4.56)       # [MEASURED] DT footprint pad extents (2x6
                                  #   grid, rotated -90 on the board)
DT_PIN_DRILL = 1.6    # [MEASURED] DT footprint pads (2.655 pad, ~1.6 drill)

# === MEASURED: the stock case -- dingoPDM repo, Export/V7.5/Case/Case.step ===
# (case frame = board-center frame; verified: its screw holes land on the
#  Baseplate.step corner holes and its DT boss centers on the DT connector)
WALL_OUT = 40.195     # [MEASURED] side-wall outer face, from board center
WALL_T = 3.0          # [MEASURED] wall thickness (side and front/back alike)
CASE_HALF_L = 51.625  # [MEASURED] front/back wall outer faces from center
SKIRT_DROP = 3.175    # [MEASURED] case bottom is 3.675 below PCB underside
                      #   = 3.175 below the heatsink-top plane (see HS_TOP)
CASE_BOT = -3.675     # [MEASURED] absolute case bottom, datum z
ROOF_BOT = 12.2       # [MEASURED] main roof underside (probe scan)
ROOF_TOP = 15.05      # [MEASURED, +-0.15] main roof top surface (probe scan;
                      #   varies slightly across the roof)
CASE_TOP = 16.19      # [MEASURED] highest plate/boss surface (light towers
                      #   reach 20.19)
LOBE_R = 8.0          # [MEASURED] corner screw-boss (lobe) outer radius
LOBE_TOP = 4.8        # [MEASURED] lobe top face = stock screw seat height
CASE_SCREW_DX = 48.195  # [MEASURED] case/baseplate screw lines from board
CASE_SCREW_DY = 43.625  #   center (Case.step bosses + Baseplate.step holes)
CASE_SCREW_HOLE = 7.0   # [MEASURED] M6 clearance holes in the lobes

# === MEASURED: Baseplate.step + assembly STEP + dingoPDM docs ================
MOUNT_DIA = 7.0       # [GROUND TRUTH] end mounting holes: UN-THREADED
                      #   clearance, Ø7 (user 2026-08-28; was 8). On the
                      #   plate-edge mid-lines at (+-CASE_SCREW_DX, mid) --
                      #   BETWEEN the ear pairs at each end, so still on the
                      #   204 plate and reachable from above
REDCUBE_TOP = 15.23   # [MEASURED] DingoPDM_V7_5.step: RedCube block top, datum
                      #   z -- pokes THROUGH the roof; bus bars bolt on above it
PAD_T = 0.5           # [MEASURED] docs/hardware/case.md: 0.5 thermal pad both
                      #   sides of the heatsink (e.g. 3M 5583S).
                      #   v2 [GROUND TRUTH] (user, 2026-08-27): SINGLE plate --
                      #   no spacer-plate + baseplate stack. THT pin reliefs are
                      #   milled into the one plate; ONE pad layer on its top
                      #   face (heights unchanged: HS_TOP = -PAD_T). Pad must be
                      #   cut to ~the PCB outline -- if it runs under the case
                      #   walls (inner face 1.0 past the PCB edge) the FLAT_BASE
                      #   enclosure rides 0.5 proud and the screw seats shift.
# stock hardware (docs/hardware/case.md exploded-assembly table):
#   board screws M3x0.5x12, case screws M6x1.0x14 -- both reused unchanged

# === STANDARD (all metric -- board screws M3 and case screws M6 thread into
# tapped holes in the heatsink; only the end mounting holes are un-threaded) ==
TAP_DRILL_M3 = 2.5    # [STANDARD] tap drill for M3x0.5
TAP_DRILL_M6 = 5.0    # [STANDARD] tap drill for M6x1.0
M6_SHCS_HEAD = (10.0, 6.0)   # [STANDARD] socket head cap screw head dia x height

# === CHOSEN: router tooling (user's machines) ================================
CUTTER = 6.0          # [CHOSEN] trim-router end mill diameter
BUSH = 15.0           # [CHOSEN] template tracer bushing OD

# === CHOSEN: fabrication ======================================================
TEMPLATE_THICKNESS = 5.0   # [CHOSEN] printed template thickness. Note: must
                           #   exceed the bushing's protrusion below the router
                           #   base or the bushing drags on the work -- checked
                           #   at the bench, not modeled here
GUIDE_CLEAR = 0.1     # [CHOSEN] drill-to-guide-bore running clearance
PRINT_COMP = 0.2      # [CHOSEN] FDM hole-shrink compensation; tune per printer
PIN_R = 0.7           # [CHOSEN] assumed protruding-pin radius (drill 1.475
                      #   implies pin ~1.3-1.4; stock design trims pins flush)
RELIEF_MARGIN = 0.5   # [CHOSEN] relief pocket margin past the pin OD (RedCube)
DT_MARGIN = 1.0       # [CHOSEN] relief margin for the DT pocket (roomier)
RELIEF_DEPTH = 3.5    # [CHOSEN] pin-relief rout depth (>= SKIRT_DROP; pins
                      #   trimmed flush per stock practice)
PCB_CLEAR = 0.5       # [CHOSEN] divider-wall lateral clearance to each PCB edge
DIV_CLEAR = 0.3       # [CHOSEN] divider bottom sits this far above HS_TOP:
                      #   seating is skirt-on-rebate-floor; the un-rebated
                      #   divider carries the tolerance (user's rule)
SKIRT_CLEAR = 0.3     # [CHOSEN] rebate lateral clearance past skirt inner face
CUT_MARGIN = 0.3      # [CHOSEN] enclosure cut plane at least this far inside
                      #   the wall inner face
CUT_LOCAL = 36.5      # [CHOSEN] actual enclosure cut plane (board-center
                      #   frame). Constraints: <= WALL_OUT-WALL_T-CUT_MARGIN
                      #   (36.895) and inside the full-height flat roof, clear
                      #   of interior features (light-pipe pin ends at 34.9)
RECESS_D = 11.5       # [CHOSEN] joint-screw recess bore: > SHCS head 10 +
                      #   drop-in/driver room; BOSS_R must exceed it by a wall
JOINT_HOLE = 7.2      # [CHOSEN] joint M6 clearance = stock 7.0 + PRINT_COMP
BOSS_R = 6.5          # [CHOSEN] joint boss radius: >= recess + 0.75 wall;
                      #   overhangs each board edge 1.5 from z 4.0 up (clear of
                      #   the one edge component, an 0805 LED, by 0.8/1.3)
BOSS_BOT = 4.0        # [CHOSEN] joint boss underside, above PCB top + parts
JOINT_V = 60.0        # [CHOSEN] joint screw y. Constraint window: clear of the
                      #   +12V bar corridor (<=44.8+liner), the GND corridor
                      #   (>=79.15-liner) and the DT boss opening (shaft must
                      #   clear x 34.25) -> between the DT connectors
BAR_RELIEF = 1.0      # [CHOSEN] roof relief depth under the bus bars (bars sit
                      #   on REDCUBE_TOP 15.23, roof top ~15.05: ~0.2 nominal!)
BAR_W_P = 16.0        # [CHOSEN] +12V bar relief width (open area there)
BAR_W_N = 13.5        # [CHOSEN] GND bar relief width; HARD CAP ~14.2 = 2 x
                      #   (CASE_HALF_L - WALL_T - |STUD_N_LOCAL.y - center|):
                      #   the GND bar itself cannot exceed ~13 at the crossing
BAR_END = 8.5         # [CHOSEN] relief overrun past each stud (ring-lug room)
HS_THICK_NOM = 12.0   # [CHOSEN] nominal heatsink thickness, ASSEMBLY DISPLAY
                      #   ONLY -- nothing derives from it

# === DERIVED ==================================================================
# v3 enclosure-first: case ear tips flush with the heatsink ends fix the
# case pitch; boards stay centred in their cases.
CASE_TAB_TIP = CASE_SCREW_DX + LOBE_R  # 56.195 ear tip from case centre
                                       #   (verified = Case.step bbox half-x)
PITCH = HS_LEN - 2 * CASE_TAB_TIP      # 91.61 case/board-centre pitch
GAP = PITCH - BOARD_W                  # 19.22 board edge-to-edge (was 10 in
                                       #   the board-first v1 design)
B_OFF = PITCH                          # add to x for any board-B feature
# facing-ear geometry at the join (the user cuts these to interleave):
EAR_OVERLAP = 2 * CASE_TAB_TIP - PITCH # 20.78 of x where both cases' inner
                                       #   ears want to exist
WALL_GAP = PITCH - 2 * WALL_OUT        # 11.22 clear air between facing walls
assert EAR_OVERLAP > 0 and WALL_GAP > 0, 'case placement infeasible'
CTR_A = (BOARD_W / 2, BOARD_L / 2)     # (36.195, 47.625) board A center
CTR_B = (CTR_A[0] + PITCH, CTR_A[1])
JOIN_X = CTR_A[0] + PITCH / 2          # 77.39 gap centerline
OFFSET = (BUSH - CUTTER) / 2           # 4.5 template-to-cut offset
OPEN_R = CUTTER / 2 + OFFSET           # 7.5 opening corner radius -> r3 cut
BORE_M3 = TAP_DRILL_M3 + GUIDE_CLEAR + PRINT_COMP    # 2.8 guide bore
BORE_M6 = TAP_DRILL_M6 + GUIDE_CLEAR + PRINT_COMP    # 5.3 guide bore
BORE_MOUNT = MOUNT_DIA + GUIDE_CLEAR + PRINT_COMP    # 8.3 guide bore
HS_TOP = -PAD_T                        # -0.5 heatsink top = PCB underside - pad
REBATE_DEPTH = SKIRT_DROP              # 3.175 exactly: skirt seats on floor

FLAT_BASE = True      # [GROUND TRUTH] v2 (user, 2026-08-27): remove the skirt/
                      #   flange below the heatsink-top plane -- the heat shield
                      #   base plate will NOT get the milled rebate. Enclosure
                      #   bottom becomes a flat face at z = HS_TOP, seating
                      #   directly on the plate at the same height the rebated
                      #   design gave (REBATE_DEPTH == SKIRT_DROP). Template T3
                      #   (skirt rebate) is obsolete under this option.
SEAT_Z = LOBE_TOP                      # 4.8 joint screw seat = stock seat
POCKET_HALF = PIN_GRID + PIN_R + RELIEF_MARGIN       # 5.01 RedCube pocket half
DT_HALF = (DT_PIN_HALF[0] + DT_PIN_DRILL / 2 + DT_MARGIN,   # 12.91
           DT_PIN_HALF[1] + DT_PIN_DRILL / 2 + DT_MARGIN)   # 6.36
# case screw positions (v3: ALL EIGHT lobes exist -- 4 outer + 4 inner. The
# inner pairs sit in the ear-overlap zone only 2*CASE_SCREW_DX - PITCH =
# 4.78 apart in x; after the user cuts the tabs, only the SURVIVING inner
# ears get tapped -- the template drills both candidates):
SX1, SX2 = CTR_A[0] - CASE_SCREW_DX, CTR_B[0] + CASE_SCREW_DX  # -12.0, 176.0
SXI_A = CTR_A[0] + CASE_SCREW_DX       # 84.39  board-A inner screws
SXI_B = CTR_B[0] - CASE_SCREW_DX       # 79.61  board-B inner screws
SY1, SY2 = CTR_A[1] - CASE_SCREW_DY, CTR_A[1] + CASE_SCREW_DY  # 4.0, 91.25
CASE_SCREWS = [(SX1, SY1), (SX1, SY2), (SX2, SY1), (SX2, SY2)]
CASE_SCREWS_INNER = [(SXI_A, SY1), (SXI_A, SY2), (SXI_B, SY1), (SXI_B, SY2)]
# ^ [SUPERSEDED AS-BUILT 2026-09-01] the stock inner-hole positions above no
# longer exist on the hardware. As built: the user cut both cases' inner tabs
# at 102.0 from the opposite outer tip (tab ends butt at the heatsink
# centreline, bisecting the stock holes), installed the covers, drilled NEW
# round holes through the partial arcs IN PLACE, then match-drilled and
# tapped M6 into the heatsink at those spots. The inner screw positions are
# therefore defined by the physical parts (near the butt line, one per tab
# end) -- do not derive them from this spec; any future template must treat
# them as as-drilled.
JOINT_SCREW = (JOIN_X, JOINT_V)        # [OBSOLETE v3] printed-dual only
MOUNT_HOLES = [(SX1, CTR_A[1]), (SX2, CTR_A[1])]     # end mid-lines, between
                                                     # the ear pairs (restored
                                                     # v3.1, Ø MOUNT_DIA)
def both(pt):
    """Board-local point -> [board A instance, board B instance]."""
    return [pt, (pt[0] + B_OFF, pt[1])]

M3_HOLES = [p for h in M3_HOLES_LOCAL for p in both(h)]
STUDS_P = both(STUD_P_LOCAL)
STUDS_N = both(STUD_N_LOCAL)
# dog-bone drills: every RedCube corner pin (r3 cut corners encroach ~0.3)
CORNER_DRILLS = [(s[0] + dx, s[1] + dy)
                 for stud in (STUD_P_LOCAL, STUD_N_LOCAL) for s in both(stud)
                 for dx in (-PIN_GRID, PIN_GRID) for dy in (-PIN_GRID, PIN_GRID)]
# relief pockets (x1, y1, x2, y2), both boards:
RELIEF_POCKETS = [r for off in (0, B_OFF) for r in (
    (STUD_P_LOCAL[0] + off - POCKET_HALF, STUD_P_LOCAL[1] - POCKET_HALF,
     STUD_P_LOCAL[0] + off + POCKET_HALF, STUD_P_LOCAL[1] + POCKET_HALF),
    (DT_CTR_LOCAL[0] + off - DT_HALF[0], DT_CTR_LOCAL[1] - DT_HALF[1],
     DT_CTR_LOCAL[0] + off + DT_HALF[0], DT_CTR_LOCAL[1] + DT_HALF[1]),
    (STUD_N_LOCAL[0] + off - POCKET_HALF, STUD_N_LOCAL[1] - POCKET_HALF,
     STUD_N_LOCAL[0] + off + POCKET_HALF, STUD_N_LOCAL[1] + POCKET_HALF))]
# chain drilling (v3): guide bores along the corners and edges of every
# relief pocket so most pocket material comes out with a drill before the
# mill. Blind holes -- RELIEF_DEPTH, same convention as the old corner
# drills. Hole centres are inset D_CHAIN/2 from the pocket walls (tangent
# from inside); intermediates keep the TEMPLATE web >= 0.4 between bores.
D_CHAIN = 4.0         # [CHOSEN] chain drill diameter -- change to match the
                      #   drill actually in hand and re-export
BORE_CHAIN = D_CHAIN + GUIDE_CLEAR + PRINT_COMP      # 4.3 guide bore

def _chain_ring(rect):
    x1, y1, x2, y2 = rect
    r = D_CHAIN / 2
    pts = [(x1 + r, y1 + r), (x2 - r, y1 + r), (x2 - r, y2 - r), (x1 + r, y2 - r)]
    min_pitch = BORE_CHAIN + 0.4
    for span, fixed, along in (
            (x2 - x1 - D_CHAIN, (y1 + r, y2 - r), 'x'),
            (y2 - y1 - D_CHAIN, (x1 + r, x2 - r), 'y')):
        nseg = max(1, int(span // min_pitch))
        for i in range(1, nseg):
            d = span * i / nseg
            for f in fixed:
                pts.append((x1 + r + d, f) if along == 'x' else (f, y1 + r + d))
    return pts

CHAIN_DRILLS = [p for rect in RELIEF_POCKETS for p in _chain_ring(rect)]
# the RedCube pocket-corner chain holes swallow the protruding corner pins,
# superseding the old CORNER_DRILLS dog-bones:
_corner_to_pin = ((POCKET_HALF - D_CHAIN / 2) - PIN_GRID) ** 2 * 2
assert _corner_to_pin ** 0.5 <= D_CHAIN / 2 - PIN_R, \
    'chain corner hole does not cover the RedCube corner pin'

# KiCad-export STEP origin in the datum frame (for placing DingoPDM_V7_5.step):
KICAD_ORG = (37.846, 61.976)           # = -EdgeCuts min x, +EdgeCuts max y

import os
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'out')
DINGOPDM = os.environ.get('DINGOPDM_DIR', os.path.expanduser('~/dingoPDM'))

def dingopdm(rel):
    p = os.path.join(DINGOPDM, rel)
    assert os.path.exists(p), \
        f'{p} missing: clone github.com/corygrant/dingoPDM, set DINGOPDM_DIR'
    return p

os.makedirs(OUT, exist_ok=True)
