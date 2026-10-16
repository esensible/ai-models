"""Single source of truth for the DT benchtop test plugs (4-way and 12-way).

PURPOSE (user, 2026-09-16): bench-test fixtures, NOT production connectors.
Loose crimped terminals push into the rear and are held in separate cavities
so they cannot touch each other or flop about. Deliberately omitted: the
wedge-lock, the contact retention clips, the side latch, any sealing. It must
slide in and out of the receptacle easily -- generous clearance everywhere.

Provenance tags (repo convention):
  [MEASURED-STEP]  probed off the Amphenol vendor STEP (AT04-*-PM11.stp) --
                   the receptacles this plug mates with
  [MEASURED-USER]  caliper readings off the physical parts
  [PLACEHOLDER]    not yet known -- the build banners these
  [CHOSEN]         our picks; comment says what constrains

=== WHAT THE VENDOR STEPS DO AND DON'T GIVE US ================================
The Amphenol models are SIMPLIFIED HOUSING SHELLS: they carry the shroud and
flange geometry but contain NO contacts and NO contact cavities (verified by
scanning every section from the mating tip to the rear -- the only circular
features anywhere are the flange screw holes). So the mating ENVELOPE is
ground truth from the STEP, but the CONTACT PATTERN must come from a
datasheet or from measuring the physical connector.

=== DATUM ======================================================================
Origin at the centre of the shroud bore, in the plane of the receptacle's
mating tip. +z points INTO the receptacle (the insertion direction); x is the
bore's long axis, y its short axis.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

PLACEHOLDERS = True   # contact pattern + terminal size still unknown

# === MEASURED-STEP: the shroud bores the plugs must enter ====================
# Probed at 6mm depth by walking a 0.3mm probe outward until it hits material.
BORE_4 = (18.4, 17.4)     # [MEASURED-STEP] AT04-4P bore, x by z
BORE_4_Z_CTR = -1.6       # [MEASURED-STEP] bore centre sits below the STEP's
                          #   x-axis in its own frame
BORE_12 = (38.4, 18.4)    # [MEASURED-STEP] AT04-12PA bore at mid-height; the
                          #   bore narrows toward top/bottom (half-width 19.2
                          #   at centre, 15.8 at z=+-5, 14.6 at z=+-8), i.e.
                          #   big corner radii -- the plug profile is taken as
                          #   a true offset of the bore section, not re-drawn
SHROUD_DEPTH = 13.0       # [MEASURED-STEP] tip to the step where the bore
                          #   ends (both parts, section area changes at 13.3)
WALL_4 = 1.4              # [MEASURED-STEP] shroud wall thickness

# === SIZE 16 CONTACTS + DT GRID (TE controlled drawings, 2026-09-16) ========
# Solid socket 0462-201-16141 / solid pin 0460-202-16141 / stamped 1062-16,
# 1060-16. The whole size-16 family shares its retention geometry:
SHOULDER_D = 3.38         # [DATASHEET] retention shoulder OD, MAX (3.28-3.38)
                          #   -- the widest thing the cavity must pass
BODY_D = 2.87             # [DATASHEET] socket body / sleeve OD, max
PIN_D = 1.61              # [DATASHEET] mating pin OD, max
CONTACT_LEN_MAX = 21.74   # [DATASHEET] longest variant (stamped pin); solid
                          #   socket is 19.28, solid pin 20.85
# CONTACT POSITIONS ARE NOT SET HERE. plug.py reads them straight out of the
# genuine DT06 STEP, so body profile and cavity grid share one frame -- which
# matters because the grid is NOT centred in the body (the latch side is
# taller). These constants are kept only as the cross-check:
PITCH_A = 4.445           # DT pitch within a row (.175in). STEP gives x =
                          #   +-2.223, +-6.668, +-11.113 = exactly .0875in,
                          #   .2625in, .4375in.
PITCH_B = 9.118           # DT row-to-row (.359in). STEP gives y = +-4.559.
# Pattern read from the STEPs: 12-way = 6 x 2; 4-way = 2 x 2 but TRANSPOSED
# (x +-4.559, y +-2.235) -- the 4-way's rows run the other way, which a
# datasheet-only reading got backwards.
#
# CORROBORATED BY THE USER 2026-09-16 on the physical 12-pin header: six-pin
# row span measured 22.5 vs 5 * 4.445 = 22.225, rows measured 9.0 vs 9.118 --
# both inside hand-measurement error. Note 22.5 is also exactly 5 * 4.5, so a
# metric 4.5 pitch would fit that reading; we stay IMPERIAL (user's call,
# same date) because every extracted coordinate is a clean inch fraction.
# Tell-tale if it were ever wrong: end cavities bind while the middle ones
# sit free (a 4.5 pitch would put the outermost 0.14 off, against 0.16 of
# radial slop).

# === CHOSEN: cavity + body sizing ===========================================
CAV_D = 3.7               # [CHOSEN] cavity bore. Hard-constrained from BOTH
                          #   sides: it must pass the 3.38 shoulder (plus FDM
                          #   hole shrink, which runs holes undersize), yet
                          #   PITCH_A is only 4.445, so every 0.1 of bore is
                          #   0.1 off the wall between neighbours. 3.7 leaves
                          #   0.745 -- two thin perimeters. This is the whole
                          #   tension in the part and it comes from the DT
                          #   grid itself, not from us: even a moulded DT
                          #   housing has well under 1mm here.
                          #   PRINT A FIT COUPON before the full part.
# NECK_D / FRONT_NECK_L: REMOVED 2026-09-16. There was a Ø2.4 x 2.0 neck at
# the front to stop a contact pushing out the mating face. The user does not
# want the contact retained at all -- the cavities are straight through-bores
# whose only job is to stop adjacent contacts touching as they flex. A
# terminal can slide clean through either way, which is the point.
NOSE_L = 12.0             # [CHOSEN] nose length inside the 13mm bore
BODY_L = 26.0             # [CHOSEN] total: cavity depth must swallow the
                          #   21.74 longest contact behind the 2.0 neck
REAR_LIP = 1.5            # [CHOSEN] the rear body steps out this far: acts as
                          #   the depth stop and gives something to grip

# === CHOSEN ==================================================================
FIT_CLEAR = 0.4           # [CHOSEN] per-side clearance of the plug body in
                          #   the shroud bore. Deliberately loose: the user
                          #   wants easy in/out, and there is no seal to
                          #   compress. (A production DT plug runs far
                          #   tighter.)
CAV_CLEAR = 0.3           # [CHOSEN] per-side clearance in the contact
                          #   cavities: terminals must drop in by hand
WALL_MIN = 0.7            # [CHOSEN] minimum wall between adjacent cavities.
                          #   Was 1.2 until the build asserted: 1.2 is
                          #   geometrically impossible on a 4.445 pitch with a
                          #   3.38 shoulder to pass (it would need a 2.05
                          #   bore). 0.7 = two perimeters at 0.35 width.
LEAD_CH = 0.8             # [CHOSEN] lead-in chamfer on the plug nose
REAR_FLARE = 1.0          # [CHOSEN] funnel at the rear cavity mouths so a
                          #   terminal finds its hole without fiddling

# === PIN 1 MARKER (user 2026-09-16: "a simple rebate around pin 1") =========
# DT numbering, read off the TE customer drawings (rear / wire-entry views):
#   12-way: two rows of six. One row runs 1..6, the other 7..12 the OPPOSITE
#           way, so pin 1 and pin 12 share an end and pin 6 and 7 share the
#           other. Pin 1 is diagonally opposite pin 7.
#   4-way:  with the latch UP in the rear view -- 4 top-left, 1 top-right,
#           3 bottom-left, 2 bottom-right.
#
# Mapping that numbering onto OUR frame is the weak link, because the numbers
# exist only as moulded text on the real housing -- they are not in the STEP.
# What IS in the STEP is the latch, which breaks the y symmetry:
#   4-way  body y -7.00..+10.23  -> latch at +y
#   12-way body y -9.09.. +9.80  -> latch at +y
# The rear face is +z, so looking at it from outside, +x runs right and +y up.
#   4-way:  SOLID. Latch up fixes the row, the view handedness fixes the end
#           -> pin 1 at (+x, +y).
#   12-way: LESS SOLID. Its drawing view is rotated 90deg (long axis vertical)
#           and the latch side had to be read off a low-contrast edge, so the
#           end could be 180deg out.
# CHECK IT against the moulded "1" on a real housing; if wrong, flip the sign
# in PIN1_CORNER and rebuild -- nothing else depends on it.
PIN1_CORNER_4 = (+1, +1)   # (sign_x, sign_y) of pin 1, 4-way
PIN1_CORNER_12 = (+1, -1)  # (sign_x, sign_y) of pin 1, 12-way
PIN1_CHAMFER = 0.9    # [CHOSEN] radial width of the chamfer AROUND THE PIN 1
                      #   BORE on the rear face -- the pin-1 marker (user
                      #   2026-09-18: not a dimple beside it, and not a
                      #   chamfer on the body corner; the HOLE is chamfered).
                      #   45deg, so this is also its depth.
                      #
                      #   IT BREAKS INTO THE NEAREST NEIGHBOURING BORE, BY
                      #   DESIGN. The DT pitch (4.445) leaves only ~0.75mm of
                      #   wall between Ø3.7 bores, so a 45deg chamfer can grow
                      #   just 0.27mm before it touches -- invisible. An
                      #   earlier build kept clear of the neighbour by going
                      #   deep and shallow-angled instead; the user rejected
                      #   that ("human eyes can't perceive that") and accepted
                      #   the impingement. The breach is a crescent in the top
                      #   PIN1_CHAMFER of the neighbour's mouth only; both
                      #   bores stay full Ø CAV_D below it, so neither loses
                      #   its grip on a terminal.
PIN1_BREACH_MAX = 0.5 # [CHOSEN] how far the chamfer may eat into the
                      #   neighbouring bore's wall, radially. Guards against a
                      #   future CAV_D/pitch change quietly merging the two
                      #   cavities into one slot.

_UNUSED_REBATE_D = 4.0  # superseded by PIN1_CHAMFER; kept only as the note
                      # below explains why a concentric rebate was impossible
                      #   the bore: at a 4.445 pitch a concentric rebate big
                      #   enough to see would break into the next cavity
                      #   (max r = 4.445 - CAV_D/2 = 2.6). So it sits in the
                      #   clear material outboard of the end cavity instead,
                      #   the way a moulded pin-1 dot does.
REBATE_DEPTH = 1.0    # [CHOSEN] deep enough to see and feel, shallow enough
                      #   to leave plenty of rear wall
