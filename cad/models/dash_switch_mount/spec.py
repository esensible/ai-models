"""Single source of truth for the mid-80s Toyota dash switch mount.

An adaptor that fills a vacant Toyota rocker-switch aperture and carries a
different switch: a rectangular plug entering the dash opening from the
FRONT, stopped by a flange on the show face, retained from behind by snap
tabs, with a rectangular hole through the face for the new switch.

Provenance tags (repo convention):
  [GROUND TRUTH]   design decisions everything derives from
  [MEASURED]       caliper readings off the physical dash
  [PLACEHOLDER]    awaiting measurement -- the build banners these
  [CHOSEN]         our picks; comment says what constrains
  [DERIVED]        computed; no new information

=== DATUM ======================================================================
Origin at the centre of the aperture, in the plane of the dash SHOW FACE.
+x = aperture width, +y = aperture height, +z = INTO the dash (behind).
Flange spans z -FLANGE_T..0; the plug body runs z 0..BODY_D.

=== FIT MODEL ==================================================================
The plug body is undersized from the aperture by PLUG_CLEAR (per side) so it
enters without scraping; the flange overlaps the panel by FLANGE_W all round
and sets the depth stop; snap tabs behind the panel take up the remaining
thickness. Panel thickness is the critical unknown -- see PANEL_T.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

PLACEHOLDERS = False  # PANEL_T measured 2026-09-09; CORNER_R still estimated

# === MEASURED (user, 2026-09-09) =============================================
OPEN_H = 38.0         # [MEASURED] aperture height
OPEN_W = 19.0         # [MEASURED] aperture width
FLANGE_W = 2.0        # [MEASURED] flange overlap onto the panel, per side
FLANGE_T = 2.0        # [MEASURED] flange thickness / depth (proud of the
                      #   show face)

# --- the switch this mount carries -----------------------------------------
# SWITCH selects from SWITCHES below; each entry is the switch as MEASURED,
# and the apertures are derived from it rather than typed in twice.
SWITCHES = {
    # name:      (body_w, body_h, flange_w, flange_h, flange_t)
    "rocker":    (13.0, 18.8, None, None, None),   # as printed 2026-09-09:
                                                   #   body only, no flange
                                                   #   rebate was needed
    "small":     (6.7, 18.9, 9.8, 21.3, 2.1),      # [MEASURED user
                                                   #   2026-09-18]
}
SWITCH = os.environ.get("SWITCH", "small")
_sw = SWITCHES[SWITCH]
SWITCH_CLEAR = 0.2    # [CHOSEN] per-side clearance around the switch body,
                      #   and around the flange in its rebate. Printed holes
                      #   run undersize, so this is deliberately generous --
                      #   the switch must drop in, it is not a press fit.
SWITCH_W = _sw[0] + 2 * SWITCH_CLEAR
SWITCH_H_BODY = _sw[1] + 2 * SWITCH_CLEAR
# The flange is REBATED so the switch sits flush in the mount's face rather
# than standing proud of it. The rebate is cut from the show face downward;
# at 2.1 deep it consumes the mount's own 2.0 flange and bites 0.1 into the
# plug body, which is solid there.
REBATE_W = None if _sw[2] is None else _sw[2] + 2 * SWITCH_CLEAR
REBATE_H = None if _sw[3] is None else _sw[3] + 2 * SWITCH_CLEAR
REBATE_D = _sw[4]

SWITCH_H = SWITCH_H_BODY

PANEL_T = 2.0         # [MEASURED] dash panel thickness at the aperture.
                      #   A single step suits this: no ratchet needed.
CORNER_R = 2.0        # [PLACEHOLDER] aperture corner radius (Toyota apertures
                      #   are radiused, not sharp) -- measure or eyeball

# === MATERIAL + ORIENTATION (research-driven, 2026-09-09) ====================
# MATERIAL: ASA. NOT PETG -- PETG's HDT is 68C against a measured hot-car
#   dash of 69.4C, and PETG yields at 4-5% (vs 9.5% at break), so an
#   overstrained tab takes PERMANENT SET and silently loses grip instead of
#   failing visibly. ASA: HDT 92-100C, 10x the UV resistance of ABS, the
#   standard automotive-trim choice. PAHT-CF works but its 3860MPa modulus
#   (vs ASA 2450) costs 1.6x the force per unit strain.
# ORIENTATION: print ON ITS SIDE -- insertion axis horizontal along the bed,
#   the 37.5 dimension vertical, 18.5 across. The tab beams then run along X
#   and flex IN-PLANE. Printing flange-down (prettier show face) stands the
#   beams up in Z, where bending loads layer bonds in tension: notched
#   impact falls to 25-31% of XY and the roots delaminate. Do NOT trade tab
#   orientation for face finish -- sand and paint the face instead.
# ASA also needs ~0.22% XY shrinkage compensation, which Bambu does not
#   ship (Prusa does) -- calibrate it or lose it from PLUG_CLEAR.

# === CHOSEN ==================================================================
PLUG_CLEAR = 0.25     # [CHOSEN] per-side clearance of plug body in the
                      #   aperture: enough for FDM tolerance without rattle
BED_CHAMFER = 0.5     # [CHOSEN] 45deg chamfer on every bed-touching edge --
                      #   elephant's foot would otherwise eat PLUG_CLEAR
SHELL = 2.0           # [GROUND TRUTH user] wall thickness of the hollowed
                      #   body (5 perimeters at 0.4 nozzle -- prints solid,
                      #   no infill needed)
BODY_R = 2.0          # [GROUND TRUTH user] "generous" rounding on the outside
                      #   of the plug body: eases entry AND matches the
                      #   radiused corners of the real Toyota aperture (a
                      #   square-cornered plug would not seat)
LEAD_CH = 1.2         # [CHOSEN] chamfer on the leading (deep) edge of the
                      #   plug -- the ramp that starts it into the aperture
SOFTEN_R = 0.4        # [GROUND TRUTH user] fillet everywhere else
ROOT_KEEP = 3.0       # [CHOSEN] the cavity stops this far SHORT of the beam
                      #   roots, leaving a full-thickness block around and
                      #   behind the clips (user: "leave some strength behind
                      #   the clips"). Root support = ROOT_KEEP + the collar
                      #   from TAB_L to BODY_D.

# --- retention tabs: REVERSE CANTILEVER, one per long face -------------------
# Rooted at the DEEP end and cantilevered back toward the flange, so beam
# length is set by plug depth rather than by panel thickness (a flange-rooted
# beam would be only PANEL_T long -- unusably stiff).
TAB_L = 18.0          # [CHOSEN] beam length; L/h = 10.8 so no short-beam
                      #   (Q) correction is needed
TAB_H_ROOT = 1.67     # [CHOSEN] root thickness = 4 perimeters at 0.4 nozzle
                      #   (perimeters overlap: 4 = 1.671, not 1.6)
TAB_H_TIP = 0.86      # [CHOSEN] tip thickness = 2 perimeters; the h/2 taper
                      #   buys +63% permissible deflection for free
TAB_W = 12.0          # [CHOSEN] beam width across the 37.5 face
TAB_SLOT = 1.0        # [CHOSEN] relief slot each side of the beam
TAB_FILLET = 1.0      # [CHOSEN] root fillet, R >= 0.6h, in the XY plane
TAB_LEAD_DEG = 30.0   # [CHOSEN] insertion lead-in; >=45deg risks the barb
                      #   shearing instead of deflecting
TAB_RETURN_DEG = 45.0 # [CHOSEN] return face -- REMOVABLE. Not 90deg: a
                      #   square catch does not guarantee permanence (the
                      #   foot rotates back) and friction self-locks at
                      #   ~59deg anyway
TAB_CATCH = 1.0       # [CHOSEN] catch depth beyond the aperture edge
DESIGN_STRAIN = 0.010 # [CHOSEN] 1.0% = one third of ASA's ~3% yield strain.
                      #   NOTE: no published allowable strain exists for ASA
                      #   -- verify on a printed coupon in the final
                      #   orientation before trusting the force numbers
BODY_D = 20.0         # [DERIVED-ish/PLACEHOLDER] plug depth behind the show
                      #   face. Driven by TAB_L: the reverse cantilever roots
                      #   at the deep end, so the body must carry the whole
                      #   18mm beam plus a root. CHECK THERE IS 20mm OF
                      #   CLEARANCE BEHIND THE DASH APERTURE -- if not, the
                      #   tabs must shorten (and thin, to keep L/h >= 10)
FACE_R = 0.5          # [CHOSEN] softening radius on the visible flange edge

# === DERIVED =================================================================
PLUG_H = OPEN_H - 2 * PLUG_CLEAR                  # 37.5
PLUG_W = OPEN_W - 2 * PLUG_CLEAR                  # 18.5
FLANGE_H = OPEN_H + 2 * FLANGE_W                  # 42.0
FLANGE_W_TOTAL = OPEN_W + 2 * FLANGE_W            # 23.0

assert PLUG_H > 0 and PLUG_W > 0
assert BODY_D > PANEL_T, "body must reach behind the panel"
# the switch hole must leave real material in the face all round
FACE_WALL_X = (PLUG_W - SWITCH_W) / 2             # 2.75 per side
FACE_WALL_Y = (PLUG_H - SWITCH_H) / 2             # 9.75 per side
assert FACE_WALL_X >= 1.5, (
    f"only {FACE_WALL_X:.2f}mm of face material beside the switch hole")
# the switch's flange rebate must leave real material around it
if REBATE_D:
    assert REBATE_W < PLUG_W - 2 * 1.5, (
        f"rebate {REBATE_W:.1f} wide leaves under 1.5mm of face each side of "
        f"the {PLUG_W} plug")
    assert REBATE_H < PLUG_H - 2 * 1.5, "rebate too long for the plug"
    assert REBATE_W > SWITCH_W and REBATE_H > SWITCH_H, (
        "rebate smaller than the switch body it counterbores")
    REBATE_LIP_X = (REBATE_W - SWITCH_W) / 2   # ledge the flange lands on
    REBATE_LIP_Y = (REBATE_H - SWITCH_H) / 2
    assert min(REBATE_LIP_X, REBATE_LIP_Y) >= 0.8, (
        f"only {min(REBATE_LIP_X, REBATE_LIP_Y):.2f}mm of ledge for the "
        f"switch flange to seat on")

assert FACE_WALL_Y >= 1.5, (
    f"only {FACE_WALL_Y:.2f}mm of face material above/below the switch hole")

# Tab check: available deflection (tapered-beam form) vs what's needed to
# clear the aperture edge on the way in.
TAB_DEFLECT = 1.09 * DESIGN_STRAIN * TAB_L**2 / TAB_H_ROOT      # ~2.1mm
TAB_NEEDED = TAB_CATCH + PLUG_CLEAR                              # 1.25mm
assert TAB_DEFLECT > TAB_NEEDED * 1.3, (
    f"tab deflection {TAB_DEFLECT:.2f} leaves no margin over the "
    f"{TAB_NEEDED:.2f} needed to clear the aperture")
assert TAB_W + 2 * TAB_SLOT < PLUG_W, "tab + relief slots wider than the end"
assert TAB_L < BODY_D + PANEL_T, "beam longer than the plug can carry"

# --- face plate: the material that actually CARRIES the switch aperture -----
# The cavity is far wider than the switch bore, so wherever the cavity runs
# there is NO aperture and NO ledge -- just a hole into the hollow body. The
# face plate is the solid slab in front of the cavity that the switch aperture
# is cut through and the switch's flange seats on.
#
# WHY THIS EXISTS (failure, printed 2026-09-18): the "small" switch added a
# 2.1mm flange rebate cut from the show face, which consumed the whole 2.0mm
# flange, while the cavity still started at z=0. Between them they removed
# every bit of material that should have held the aperture. The printed part
# had the rebate at the front, a hollow void behind it, and the correctly
# sized 7.1x19.3 hole only at the BACK of the blank, 18mm in -- with nothing
# anywhere for the flange to sit on. The rocker variant escaped only because
# it has no rebate, so its 2mm flange survived to carry the aperture.
LEDGE_T = 1.5         # [CHOSEN] solid material behind the rebate floor. This
                      #   is what the switch's flange bears against and what
                      #   the body aperture is bored through; 1.5mm is ~4
                      #   perimeters, enough to take the switch's retention
                      #   load without bulking out the face.
REBATE_FLOOR_Z = (-FLANGE_T + REBATE_D) if REBATE_D else -FLANGE_T
CAV_Z0 = REBATE_FLOOR_Z + LEDGE_T if REBATE_D else 0.0   # cavity STARTS here
CAV_Z1 = TAB_L - ROOT_KEEP                        # ... and ends here (15.0)

# hollow body: cavity leaves SHELL walls all round and stops short of the roots
CAV_W = PLUG_W - 2 * SHELL                        # 14.5
CAV_H = PLUG_H - 2 * SHELL                        # 33.5
CAV_Z = CAV_Z1 - CAV_Z0                           # cavity length
ROOT_BLOCK = BODY_D - CAV_Z1                      # 5.0 of full-section material
FACE_PLATE = CAV_Z0 + FLANGE_T                    # show face -> cavity
assert CAV_W > SWITCH_W and CAV_H > SWITCH_H, (
    "cavity smaller than the switch bore -- the switch would not pass")
assert CAV_Z > 0 and ROOT_BLOCK >= 4.0, (
    f"only {ROOT_BLOCK:.1f}mm of solid material behind the clip roots")
assert CAV_Z0 < CAV_Z1, "cavity starts behind where it ends"
if REBATE_D:
    assert CAV_Z0 >= REBATE_FLOOR_Z + 1.0, (
        f"only {CAV_Z0 - REBATE_FLOOR_Z:.2f}mm of ledge behind the rebate "
        f"floor -- the switch flange has nothing to seat on")
    assert REBATE_D < FACE_PLATE, (
        f"rebate {REBATE_D} deep vs a {FACE_PLATE:.2f}mm face plate -- the "
        f"rebate would break through into the hollow body")
