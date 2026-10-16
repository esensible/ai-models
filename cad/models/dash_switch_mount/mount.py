# Mid-80s Toyota dash switch mount (build123d): plug + show-face flange +
# two opposed reverse-cantilever snap tabs + a through hole for the switch.
# All values from spec.py. Frame per spec: origin at the aperture centre in
# the plane of the dash show face; +z INTO the dash.
from build123d import *
import spec as S

# ---- flange (in front of the panel) and plug body (through/behind it) -------
# Rounded profiles rather than post-hoc fillets: the plug corners MUST be
# radiused to enter the (radiused) Toyota aperture, and building them in is
# far more robust than filleting a solid that already carries the tabs.
flange = Pos(0, 0, -S.FLANGE_T) * extrude(
    RectangleRounded(S.FLANGE_W_TOTAL, S.FLANGE_H, S.BODY_R), S.FLANGE_T)
body = extrude(RectangleRounded(S.PLUG_W, S.PLUG_H, S.BODY_R), S.BODY_D)
part = flange + body

# lead-in chamfer on the leading (deep) edge so the plug starts into the hole
lead = S.LEAD_CH
lead_cut = Pos(0, 0, S.BODY_D) * (
    extrude(RectangleRounded(S.PLUG_W + 4, S.PLUG_H + 4, S.BODY_R), lead + 0.5)
    - extrude(RectangleRounded(S.PLUG_W, S.PLUG_H, S.BODY_R), lead,
              taper=-38.0))
part -= lead_cut

# ---- retention tabs ---------------------------------------------------------
# Reverse cantilever: rooted at the DEEP end (z = BODY_D), the beam runs back
# toward the flange, and the catch sits PANEL_T behind the panel's rear face
# so the flange pulls up tight against the show face.
# Built by REMOVING material: cut a U-shaped slot around each beam, leaving
# it attached only at its root, then subtract the wedge that shapes the hook.
def tab_cuts(sy):
    """sy = +1 / -1: the tab on the +y / -y END face (user pref 2026-09-09:
    tabs on the ends, i.e. the short 18.5-wide faces, not the long sides)."""
    cuts = []
    y_face = sy * S.PLUG_H / 2
    # window through the wall: frees the beam on three sides. The beam is the
    # remaining wall material spanning it; the window runs from the flange
    # end to the beam root at the deep end.
    win_z0 = -0.1                       # start at the show face
    win_z1 = S.TAB_L                    # beam root
    for sx in (-1, 1):                  # a relief slot each side of the beam
        x = sx * (S.TAB_W / 2 + S.TAB_SLOT / 2)
        cuts.append(Pos(x, y_face - sy * 1.5, (win_z0 + win_z1) / 2) *
                    Box(S.TAB_SLOT, 4.0, win_z1 - win_z0))
    # relieve BEHIND the beam so it can flex inward: a pocket leaving the
    # beam's tapered thickness, from the inner face to the beam's back
    STEPS = 12
    for i in range(STEPS):              # stepped taper -> root thick, tip thin
        f = i / STEPS                   # must NOT reach 1.0, or the last step
        #                                 overshoots past the root and eats
        #                                 the block backing the clips
        h = S.TAB_H_ROOT + (S.TAB_H_TIP - S.TAB_H_ROOT) * (1 - f)
        z0 = win_z0 + (win_z1 - win_z0) * f
        dz = (win_z1 - win_z0) / STEPS
        depth = 6.0                     # deep enough to reach the switch bore
        cuts.append(Pos(0, y_face - sy * (h + depth / 2), z0 + dz / 2) *
                    Box(S.TAB_W, depth, dz * 1.02))
    return cuts

for sy in (-1, 1):
    for c in tab_cuts(sy):
        part -= c

# ---- catch (hook) on each tab, at the free end near the flange --------------
# Profile in XZ: rises from the beam's outer face over a 30deg lead-in on the
# insertion side, square-ish shoulder at 45deg on the return side.
def catch(sy):
    y0 = sy * S.PLUG_H / 2
    y1 = y0 + sy * S.TAB_CATCH
    z_shoulder = S.PANEL_T                       # sits behind the panel
    z_lead = z_shoulder + S.TAB_CATCH / 0.577    # 30deg lead-in run
    z_ret = z_shoulder - S.TAB_CATCH             # 45deg return face
    pts = [(y0, z_ret), (y1, z_shoulder), (y0, z_lead)]
    prof = make_face(Plane.YZ * Polyline(*pts, close=True))
    # width must NOT exceed the beam, or the catch bridges the relief slots
    # and ties the beam to the surrounding wall (it then cannot flex)
    return extrude(prof, S.TAB_W / 2, both=True)

for sy in (-1, 1):
    part += catch(sy)

# ---- the switch aperture through the face ----------------------------------
part -= Pos(0, 0, (S.BODY_D - S.FLANGE_T) / 2) * \
    Box(S.SWITCH_W, S.SWITCH_H, S.BODY_D + S.FLANGE_T + 2)

# ---- rebate for the switch's own flange, so it sits FLUSH -------------------
# Cut from the show face inward, deeper than the mount's own flange. What
# stops it breaking through into the hollow body is the FACE PLATE: the
# cavity below starts at CAV_Z0, leaving LEDGE_T of solid material behind the
# rebate floor for the switch's flange to bear on. (Get this wrong and the
# aperture ends up only at the BACK of the blank -- see spec.py.)
if S.REBATE_D:
    part -= Pos(0, 0, -S.FLANGE_T) * Box(
        S.REBATE_W, S.REBATE_H, S.REBATE_D,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

# ---- hollow the body to a SHELL-thick wall ---------------------------------
# Starts at CAV_Z0 (behind the face plate) and stops ROOT_KEEP short of the
# beam roots, so full-section blocks remain at BOTH ends: the face plate in
# front, the clip-root block behind.
part -= Pos(0, 0, S.CAV_Z0) * Box(
    S.CAV_W, S.CAV_H, S.CAV_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN))

# ---- soften every remaining edge -------------------------------------------
# Applied one edge at a time with a fallback: OCC refuses some edges on a
# shape this busy, and a whole-shape fillet() would abort the build rather
# than skip them. The catch's own lead-in/return faces are excluded -- they
# are functional ramps, not cosmetic edges.
def soften(shape, r):
    done = failed = 0
    for e in shape.edges():
        if e.length < r * 2.5:
            continue
        mid = e @ 0.5
        # leave the catch ramps alone (they live near the panel line)
        if abs(mid.Z - S.PANEL_T) < S.TAB_CATCH * 1.2 and \
                abs(mid.Y) > S.PLUG_H / 2 - 0.5:
            continue
        try:
            shape = fillet([e], r)
            done += 1
        except Exception:
            failed += 1
    return shape, done, failed

part, n_ok, n_skip = soften(part, S.SOFTEN_R)
print(f"  softened {n_ok} edges at R{S.SOFTEN_R} ({n_skip} refused by OCC)")

# ---- verify + export --------------------------------------------------------
bb = part.bounding_box()
print(f"dash_switch_mount: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}"
      f"  vol {part.volume / 1000:.2f} cm3  solids {len(part.solids())}")
assert len(part.solids()) == 1, f"{len(part.solids())} solids -- tabs detached?"
assert abs(bb.size.Y - S.FLANGE_H) < 0.01, "widest Y should be the flange"
assert abs(bb.size.Z - (S.BODY_D + S.FLANGE_T)) < 0.01, "depth wrong"

def width_at(z, axis="x"):
    sec = section(part.solids()[0], Plane.XY.offset(z))
    b = sec.faces()[0].bounding_box() if sec.faces() else None
    xs = [f.bounding_box() for f in sec.faces()]
    lo = min(v.min.X if axis == "x" else v.min.Y for v in xs)
    hi = max(v.max.X if axis == "x" else v.max.Y for v in xs)
    return hi - lo

# tabs now act along Y (the ends), so the catch is measured in Y
w_flange = width_at(-S.FLANGE_T / 2, "y")
w_plug = width_at(S.BODY_D - 1.0, "y")
w_catch = width_at(S.PANEL_T, "y")
print(f"  flange span {w_flange:.2f} (expect {S.FLANGE_H})")
print(f"  plug span   {w_plug:.2f} (expect {S.PLUG_H})")
print(f"  at catch    {w_catch:.2f} (expect {S.PLUG_H + 2 * S.TAB_CATCH}"
      f" -- grips behind a {S.PANEL_T}mm panel)")
assert abs(w_flange - S.FLANGE_H) < 0.05
assert abs(w_plug - S.PLUG_H) < 0.05
assert w_catch > S.PLUG_H + 1.5, "catch does not stand proud enough to grip"

# the beam must be FREE: no material may bridge the relief slots anywhere
# along its length, or it cannot flex (caught exactly this, 2026-09-09)
x_slot = S.TAB_W / 2 + S.TAB_SLOT / 2
for sy in (-1, 1):
    for z in (1.0, S.PANEL_T, 4.0, 8.0, 14.0):
        # probe ONLY the slot's own footprint: from the end face inward the
        # slot depth, at the slot's x. (A probe spanning all y would flag the
        # legitimate wall between the switch bore and the end.)
        probe = Pos(x_slot, sy * (S.PLUG_H / 2 - 1.5), z) * \
            Box(0.3, 3.0, 0.4)
        piece = part.solids()[0].intersect(probe)
        bits = piece.solids() if hasattr(piece, "solids") else []
        assert not bits, (
            f"material bridges the relief slot at z={z}, y-end {sy:+d} -- "
            f"the tab is not free to flex")
print("  relief slots clear along the full beam: tabs free to flex")

# hollow-body checks: wall thickness where the cavity bites, and that the
# root block really is full section
def spans_along(axis, z, other=0.0):
    box = Box(60, 0.3, 0.4) if axis == "x" else Box(0.3, 60, 0.4)
    probe = Pos(0 if axis == "x" else other, other if axis == "x" else 0, z) * box
    piece = part.solids()[0].intersect(probe)
    bits = piece.solids() if hasattr(piece, "solids") else []
    key = (lambda b: (b.min.X, b.max.X)) if axis == "x" else \
        (lambda b: (b.min.Y, b.max.Y))
    return sorted(key(s.bounding_box()) for s in bits)

mid = (S.CAV_Z0 + S.CAV_Z1) / 2
side_walls = [round(hi - lo, 2) for lo, hi in spans_along("x", mid)]
print(f"  side walls at mid-cavity: {side_walls} (expect ~{S.SHELL})")
assert all(abs(w - S.SHELL) < 0.15 for w in side_walls), "side shell wrong"
# the clips root in the ENDS, so measure end-wall depth there (along Y)
root_end = [round(hi - lo, 2) for lo, hi in spans_along("y", S.BODY_D - 1.0)]
cav_end = [round(hi - lo, 2) for lo, hi in spans_along("y", mid)]
print(f"  end wall in the cavity (z={mid}): {cav_end} (hollowed to ~{S.SHELL})")
print(f"  end wall at the root block (z={S.BODY_D - 1.0}): {root_end} "
      f"(full section, {S.ROOT_BLOCK:.0f}mm long behind the clips)")
assert max(root_end) > 4 * S.SHELL, "root block was hollowed out"
print(f"  tab deflection {S.TAB_DEFLECT:.2f}mm available vs "
      f"{S.TAB_NEEDED:.2f}mm needed")
print("  PRINT ON ITS SIDE: insertion axis along the bed, tabs flexing "
      "in-plane (see spec)")

# ---- THE CHECK THAT WAS MISSING --------------------------------------------
# Walk the aperture from the show face to the back and assert what the SWITCH
# actually meets at each depth. The part printed 2026-09-18 had its only
# correctly-sized hole at the BACK of the blank, behind 16mm of open cavity,
# with nothing for the switch flange to seat on -- and every check here
# passed, because they all measured outside spans and wall thicknesses and
# none of them measured the hole the switch goes through.
def opening_at(z):
    """(w, h) of the largest opening in the section at z, else None."""
    sec = section(part.solids()[0], Plane.XY.offset(z))
    best = None
    for f in sec.faces():
        for wire in f.inner_wires():
            b = wire.bounding_box()
            if best is None or b.size.X * b.size.Y > best[0] * best[1]:
                best = (b.size.X, b.size.Y)
    return best

def expect_opening(z, w, h, what, tol=0.6):
    got = opening_at(z)
    assert got is not None, f"{what}: no opening at all at z={z:.2f}"
    print(f"  z={z:+6.2f}  {what:<34s} {got[0]:5.2f} x {got[1]:5.2f} "
          f"(expect {w:.2f} x {h:.2f})")
    assert abs(got[0] - w) < tol and abs(got[1] - h) < tol, (
        f"{what}: opening is {got[0]:.2f} x {got[1]:.2f}, expected "
        f"{w:.2f} x {h:.2f} -- the switch will not fit here")

print("  aperture through the depth:")
if S.REBATE_D:
    expect_opening(-S.FLANGE_T + S.REBATE_D / 2, S.REBATE_W, S.REBATE_H,
                   "flange rebate")
    expect_opening(S.REBATE_FLOOR_Z + S.LEDGE_T / 2, S.SWITCH_W, S.SWITCH_H,
                   "LEDGE the flange seats on")
else:
    expect_opening(-S.FLANGE_T / 2, S.SWITCH_W, S.SWITCH_H, "face plate")
expect_opening(S.CAV_Z1 + S.ROOT_BLOCK / 2, S.SWITCH_W, S.SWITCH_H,
               "rear aperture")
print(f"  face plate {S.FACE_PLATE:.2f}mm thick "
      f"({S.REBATE_D or 0:.2f} rebate + {S.LEDGE_T if S.REBATE_D else S.FLANGE_T:.2f} ledge), "
      f"cavity z {S.CAV_Z0:.2f}..{S.CAV_Z1:.2f}")

name = f"dash_switch_mount_{S.SWITCH}"
export_stl(part, f"{S.OUT}/{name}.stl")
export_step(part, f"{S.OUT}/{name}.step")
print(f"  exported {name}.stl/.step")
print("exported dash_switch_mount.stl/.step")
