# Ignition blank (build123d): keyed plug for the cast-aluminium ignition
# bore. Keyed section (circle + tabs) to TAB_DEPTH, round body continuing to
# LENGTH, both tapered for the interference fit; square-cornered lip.
# All values from spec.py; profile from bore_profile.py.
# Frame per spec: z=0 = casting face (lip underside), +z into the bore.
from build123d import *
import spec as S
from bore_profile import keyed_profile

full = keyed_profile()
disc = Circle(S.DIA_BASE / 2)

# Round body: parallel land then drafted taper to LENGTH.
# Keyed section: same land + draft schedule, ending at TAB_DEPTH -- so the
# tab faces stay flush offsets of the round body over their short depth.
def land_and_taper(sk, depth):
    land = extrude(sk, S.LAND)
    taper = Pos(0, 0, S.LAND) * extrude(sk.face(), depth - S.LAND,
                                        taper=S.TAPER_DEG)
    return land + taper

body = land_and_taper(disc, S.LENGTH)
# 45-deg tip chamfer, cut as a revolved wedge (the OCC chamfer builder
# refuses the drafted cone's rim edge outright)
r_tip = S.DIA_BASE / 2 - S.TIP_OFF_SIDE
ch = S.CHAMFER_TIP
wedge_profile = make_face(Plane.XZ * Polyline(
    (r_tip - ch - 0.5, S.LENGTH + 0.5),
    (r_tip + 1.0, S.LENGTH + 0.5),
    (r_tip + 1.0, S.LENGTH - ch),
    (r_tip, S.LENGTH - ch),
    (r_tip - ch - 0.5, S.LENGTH + 0.5),
))
body -= revolve(wedge_profile, Axis.Z)

keyed = land_and_taper(full, S.TAB_DEPTH)
lip = Pos(0, 0, -S.LIP_H) * extrude(
    keyed_profile(S.LIP_OFF, Kind.INTERSECTION), S.LIP_H)
part = body + keyed + lip

# ---- verify + export --------------------------------------------------------
bb = part.bounding_box()
lipbb = keyed_profile(S.LIP_OFF, Kind.INTERSECTION).bounding_box()
print(f"ignition_blank: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {part.volume / 1000:.1f} cm3  solids {len(part.solids())}")
assert len(part.solids()) == 1
assert abs(bb.size.Z - (S.LENGTH + S.LIP_H)) < 0.01, "overall height wrong"
assert abs(bb.size.X - lipbb.size.X) < 0.01, "widest extent must be the lip"

def width_at(z):
    sec = section(part.solids()[0], Plane.XY.offset(z))
    w = sec.faces()[0].outer_wire().bounding_box()
    return w.max.X - w.min.X

def tapered(base, z):
    return base - 2 * S.TIP_OFF_SIDE * max(0.0, z - S.LAND) / S.TAPER_LEN

for z, want, label in (
        (-S.LIP_H / 2, S.HTAB_SPAN + 2 * S.LIP_OFF, "lip"),
        (S.LAND - 0.05, S.HTAB_SPAN, "land end (keyed, full size)"),
        (S.TAB_DEPTH - 0.05, tapered(S.HTAB_SPAN, S.TAB_DEPTH - 0.05),
         "keyed end"),
        (S.TAB_DEPTH + 0.05, tapered(S.DIA_BASE, S.TAB_DEPTH + 0.05),
         "round body past tabs"),
        (S.LENGTH - S.CHAMFER_TIP - 0.05,
         tapered(S.DIA_BASE, S.LENGTH - S.CHAMFER_TIP - 0.05),
         "tip (below chamfer)"),
):
    got = width_at(z)
    assert abs(got - want) < 0.05, f"{label}: width {got:.2f} != {want:.2f}"
    print(f"  {label}: span {got:.2f} (model {want:.2f})")
print(f"  taper: {S.TIP_CLEAR} diametral over {S.TAPER_LEN}mm "
      f"({S.TAPER_DEG:.2f} deg/side), land {S.LAND}mm, "
      f"tabs to z{S.TAB_DEPTH}, body to z{S.LENGTH}")
print(f"  derived: tab underside {S.HTAB_BOT:+.2f} vs CL, "
      f"tab top {S.HTAB_BOT + S.HTAB_H:+.2f}, vtab top {S.VTAB_TOP:+.2f}")
if S.PLACEHOLDERS:
    print("  ** PLACEHOLDER DIMENSIONS -- do not print until measured **")

export_stl(part, f"{S.OUT}/ignition_blank.stl")
export_step(part, f"{S.OUT}/ignition_blank.step")
print("exported ignition_blank.stl/.step")
