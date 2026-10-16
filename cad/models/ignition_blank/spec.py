"""Single source of truth for the ignition blank.

A blanking plug for a KEYED ignition-switch bore in CAST ALUMINIUM: the bore
cross-section (circle + two side tabs + one top tab) extruded with a taper
for interference fit, plus a stop lip -- the same profile offset outward --
at the outer end. Inserts body-first; the lip seats against the casting face.

Provenance tags (repo convention):
  [GROUND TRUTH]   design decisions everything derives from
  [MEASURED]       caliper readings off the physical casting
  [PLACEHOLDER]    user's verbal approximations, awaiting confirmation
                   -- the build banners these; do not print while any remain
  [CHOSEN]         our picks; comment says what constrains
  [DERIVED]        computed; no new information

=== DATUM ======================================================================
Profile frame: origin at the circle centre, +y up (bore as viewed).
z=0 at the underside of the lip (the casting face plane); +z into the bore.
Body spans z 0..LENGTH; lip spans z -LIP_H..0.

=== DIMENSION LETTERS (as agreed with the user, 2026-09-05) ====================
  a  DIA_BASE    circle diameter
  b  B_SPAN      largest span, side-tab top-outside corner to the opposite
                 side of the circle (redefined 2026-09-06; underside height
                 above CL is now DERIVED from a,b,c,d)
  c  HTAB_SPAN   outside-to-outside across the side tabs
  d  HTAB_H      side-tab height
  e  VTAB_W      vertical tab width
  f  VTAB_REACH  vertical tab top to the bottom edge of the circle
  g  LIP_OFF     lip outward offset from the body profile
  h  LIP_H       lip extrusion thickness
  i  TIP_CLEAR   diametral clearance at the far (tip) end
  j  LAND        parallel full-size land under the lip

=== FIT MODEL (user + recommendation, 2026-09-05) ==============================
Full-size profile from z=0 to z=LAND (parallel bearing land), then tapering
so the tip runs TIP_CLEAR smaller diametrally: easy entry, interference
carried near the casting face. Line-to-line at the land is an effective
interference for printed PETG into aluminium (print roughness + slight
over-extrusion); adjust after the first test fit.
"""
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

PLACEHOLDERS = False  # all core dims measured by the user, 2026-09-06

# --- profile (letters a-f), [MEASURED] user calipers 2026-09-06 ---------------
DIA_BASE = 26.3       # a [MEASURED] circle diameter
B_SPAN = 31.5         # b [MEASURED] LARGEST span from a side tab's TOP
                      #   OUTSIDE corner to the opposite side of the circle
                      #   (redefined 2026-09-06: the max span runs through
                      #   the circle centre, so b = dist(corner,centre) + a/2)
HTAB_SPAN = 34.5      # c [MEASURED] outside-to-outside across the side tabs
HTAB_H = 10.0         # d [MEASURED] side-tab height. NOTE: with a,b,c this
                      #   puts the tab UNDERSIDE 3.74 BELOW the centre line
                      #   (top +6.26) -- supersedes the initial "5mm above
                      #   CL" eyeball; user flagged-and-built 2026-09-06
VTAB_W = 5.9          # e [MEASURED] vertical tab width
VTAB_REACH = 29.1     # f [MEASURED] vertical tab top to circle bottom edge
                      #   (tab stands 2.8 proud of the circle)

# --- lip (letters g-h) --------------------------------------------------------
LIP_OFF = 4.0         # g [MEASURED] outward offset. Outside corners SQUARE
                      #   (Kind.INTERSECTION), per user 2026-09-06 -- corner
                      #   points land > g from the body profile (accepted)
LIP_H = 3.0           # h [MEASURED] lip extrusion thickness

# --- depths [GROUND TRUTH user 2026-09-06] ------------------------------------
LENGTH = 15.0         # round body engagement length into the bore
TAB_DEPTH = 4.0       # the keyed features (side + vertical tabs) extrude
                      #   only this far -- beyond it the plug is circle-only
TIP_CLEAR = 0.8       # i [GROUND TRUTH user] DIAMETRAL clearance at the tip
                      #   (read as diametral -> 0.4/side; confirm if per-side)
LAND = 2.0            # j [CHOSEN] parallel full-size land below the lip: a
                      #   pure cone seats only at the face edge; 2mm of
                      #   cylinder gives a real bearing surface + centring
CHAMFER_TIP = 0.2     # [GROUND TRUTH user] chamfer on the front (tip) face

# === DERIVED ==================================================================
# Side-tab underside height above the centre line, from the b span:
#   corner = (c/2, HTAB_BOT + d); |corner - centre| = b - a/2
#   HTAB_BOT = sqrt((b - a/2)^2 - (c/2)^2) - d
_corner_r = B_SPAN - DIA_BASE / 2
_corner_y2 = _corner_r**2 - (HTAB_SPAN / 2)**2
assert _corner_y2 > 0, (
    f"b span {B_SPAN} is too short for tab span c={HTAB_SPAN} -- re-measure")
HTAB_BOT = math.sqrt(_corner_y2) - HTAB_H          # -3.74: tabs straddle the CL
assert HTAB_BOT > -DIA_BASE / 2, "tab underside below the circle -- re-measure"

TIP_OFF_SIDE = TIP_CLEAR / 2                       # 0.4/side profile offset
TAPER_LEN = LENGTH - LAND                          # 13
TAPER_DEG = math.degrees(math.atan(TIP_OFF_SIDE / TAPER_LEN))   # 1.76/side
VTAB_TOP = -DIA_BASE / 2 + VTAB_REACH              # +15.95 above centre
assert TAB_DEPTH > LAND, "keyed section must outlast the parallel land"

assert TIP_OFF_SIDE < VTAB_W / 2, "tip offset would erase the vertical tab"
assert LAND < LENGTH
