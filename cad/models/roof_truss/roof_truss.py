"""Roof framing as understood for the structural analysis in structural/roof_truss/.

Geometry only (no strength here): wall plates on three walls (two outer, one
mid-span), trusses at 1200 c/c — each a pair of 35x105 rafters at 27 deg,
birdsmouthed onto the outer plates, a 35x105 ceiling joist lapped to the rafter
feet running the full span over the mid wall, a 35x105 collar tie lapped to the
rafters 1 m below the apex — plus 35x105 under-purlins along the building under
the rafters just below the collar junction, a 40x190 ridge beam between the
rafter plumb cuts, cross (room) walls every 4 m carrying the purlins and ridge,
and deep hanging beams along the building sitting on top of the joists, one in
each half. Battens and roofing sheets are not drawn.

  ./cad/run.sh cad/models/roof_truss/roof_truss.py            # -> cad/out/roof_truss.stl (+ per-member STLs)
  ./cad/run.sh cad/models/roof_truss/roof_truss.py --trusses 4 --beam 45x240
X across the span (mm), Y along the building, Z up; plate top = Z 0.
"""
import argparse, math, os
from build123d import *

ap = argparse.ArgumentParser()
ap.add_argument("--span", type=float, default=8500, help="wall plate centres")
ap.add_argument("--pitch", type=float, default=27)
ap.add_argument("--spacing", type=float, default=1200, help="truss centres")
ap.add_argument("--trusses", type=int, default=None, help="default: as many as fit in --bays x --bay")
ap.add_argument("--bay", type=float, default=4000, help="cross-wall spacing carrying the purlins + ridge (0 = none)")
ap.add_argument("--bays", type=int, default=2)
ap.add_argument("--ridge", default="40x190", help="ridge beam b x d ('' for none)")
ap.add_argument("--section", default="35x105", help="b x d of rafters/joists/collar/purlins")
ap.add_argument("--collar-drop", type=float, default=1000, help="collar top face below apex")
ap.add_argument("--eave", type=float, default=450, help="horizontal eave overhang")
ap.add_argument("--beam", default="45x240", help="hanging beam b x d")
ap.add_argument("--beam-x", type=float, default=None, help="hanging beam offset from outer wall (default: half-way to mid wall)")
ap.add_argument("--wall-h", type=float, default=600, help="height of wall stubs drawn under the plates")
ap.add_argument("--out", default="cad/out")
args = ap.parse_args()

B, D = (float(v) for v in args.section.lower().split("x"))
BB, BD = (float(v) for v in args.beam.lower().split("x"))
RB, RD = (float(v) for v in args.ridge.lower().split("x")) if args.ridge else (0.0, 0.0)
th = math.radians(args.pitch)
tan, cos = math.tan(th), math.cos(th)
S, SP = args.span, args.spacing
L_bld = args.bays * args.bay if args.bay > 0 else (args.trusses or 4) * SP   # building length drawn
N = args.trusses or int((L_bld - SP / 2) // SP) + 1                          # trusses at SP/2, 3SP/2, ...
PLATE_B, PLATE_T = 105.0, 35.0       # wall plates laid flat
WALL_T = 90.0

# ---- rafter setting-out -------------------------------------------------------
# birdsmouth: plumb cut on the plate's inner face, seat height = D/3 (35 mm)
heel = D / 3
x_inner = PLATE_B / 2
x0 = x_inner - heel / tan            # where the rafter soffit crosses the plate top
def soffit(x): return (x - x0) * tan
d_vert = D / cos                     # vertical thickness of the rafter
z_apex_top = soffit(S / 2) + d_vert  # ridge point on the rafter top faces
x_c = S / 2

def box(x0_, x1_, y0_, y1_, z0_, z1_):
    return Box(x1_ - x0_, y1_ - y0_, z1_ - z0_, align=Align.MIN).moved(Location((x0_, y0_, z0_)))

def rafter_left(y):
    """left rafter, thickness B in Y starting at y, as a solid in X-Z."""
    xs = -args.eave
    xe = x_c - RB / 2                 # plumb cut against the ridge beam
    pts = [(xs, soffit(xs)), (xe, soffit(xe)), (xe, soffit(xe) + d_vert), (xs, soffit(xs) + d_vert)]
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            Polygon(*pts, align=None)
        extrude(amount=-B)            # Plane.XZ normal is -Y: extrude -B to go +Y
    r = p.part.moved(Location((0, y, 0)))
    notch = box(x0 - 1, x_inner, y - 1, y + B + 1, -D, 0)   # birdsmouth
    return r - notch

def mirror_x(solid):
    return solid.mirror(Plane.YZ.offset(x_c))

# region under the two rafter top faces (to trim the collar tie flush with the rafter tops)
roof_prism_pts = [(-args.eave, soffit(-args.eave) + d_vert), (x_c, z_apex_top),
                  (S + args.eave, soffit(-args.eave) + d_vert), (S + args.eave, -1), (-args.eave, -1)]
with BuildPart() as _rp:
    with BuildSketch(Plane.XZ):
        Polygon(*roof_prism_pts, align=None)
    extrude(amount=-(L_bld + 2000))
ROOF_PRISM = _rp.part.moved(Location((0, -1000, 0)))

members = {}   # name -> list of solids
def add(name, s): members.setdefault(name, []).append(s)

# ---- walls + plates -------------------------------------------------------------
for xw in (0, S / 2, S):
    add("wall", box(xw - WALL_T / 2, xw + WALL_T / 2, 0, L_bld, -args.wall_h - PLATE_T, -PLATE_T))
    add("plate", box(xw - PLATE_B / 2, xw + PLATE_B / 2, 0, L_bld, -PLATE_T, 0))

# ---- trusses ------------------------------------------------------------------
z_collar_top = z_apex_top - args.collar_drop
for i in range(N):
    y = SP / 2 + i * SP               # rafter occupies y .. y+B
    rl = rafter_left(y)
    add("rafter", rl); add("rafter", mirror_x(rl))
    # ceiling joist lapped on the -Y side of the rafters, full span, bearing on all three plates
    add("joist", box(-PLATE_B / 2, S + PLATE_B / 2, y - B, y, 0, D))
    # collar tie lapped on the +Y side, trimmed to the rafter top faces
    collar = box(0, S, y + B, y + 2 * B, z_collar_top - D, z_collar_top) & ROOF_PRISM
    add("collar", collar)

# ---- under-purlins: on edge, along the building, just below the collar junction -------
z_cb = z_collar_top - D                     # collar bottom
x_cb = z_cb / tan + x0                      # where the collar bottom meets the rafter soffit (left)
x_p = x_cb - 20                             # purlin's uphill face a little downslope of the junction
purlin = box(x_p - B, x_p, 0, L_bld, soffit(x_p) - D, soffit(x_p))
add("purlin", purlin); add("purlin", mirror_x(purlin))

# ---- ridge beam: on edge between the rafter plumb cuts, top at the rafter tops ------------
if RB:
    add("ridge", box(x_c - RB / 2, x_c + RB / 2, 0, L_bld, z_apex_top - RD, z_apex_top))

# ---- cross walls (room walls across the building) under the purlins and ridge --------------
if args.bay > 0:
    with BuildPart() as _sp:          # region under the rafter soffits
        with BuildSketch(Plane.XZ):
            Polygon(*[(-args.eave, soffit(-args.eave)), (x_c, soffit(x_c)), (S + args.eave, soffit(-args.eave)),
                      (S + args.eave, -2000), (-args.eave, -2000)], align=None)
        extrude(amount=-(L_bld + 2000))
    UNDER_SOFFIT = _sp.part.moved(Location((0, -1000, 0)))
    yw = 0.0
    while yw <= L_bld + 1:
        wall = box(-PLATE_B / 2, S + PLATE_B / 2, yw - WALL_T / 2, yw + WALL_T / 2,
                   -args.wall_h - PLATE_T, z_apex_top) & UNDER_SOFFIT
        wall = wall - box(-PLATE_B, S + PLATE_B, yw - WALL_T, yw + WALL_T, -PLATE_T - 1, D + 1)   # plate + joist band
        for cut in (purlin, mirror_x(purlin)):          # purlins bear on the wall: notch their envelope out
            bb = cut.bounding_box()
            wall = wall - box(bb.min.X - 1, bb.max.X + 1, yw - WALL_T, yw + WALL_T, bb.min.Z - 1, bb.max.Z + 1)
        if RB:
            wall = wall - box(x_c - RB / 2 - 1, x_c + RB / 2 + 1, yw - WALL_T, yw + WALL_T, z_apex_top - RD - 1, z_apex_top + 1)
        add("xwall", wall)
        yw += args.bay

# ---- hanging beams: on top of the joists, one per half ---------------------------
bx = args.beam_x if args.beam_x is not None else S / 4
beam = box(bx - BB / 2, bx + BB / 2, 0, L_bld, D, D + BD)
add("beam", beam); add("beam", mirror_x(beam))

# ---- export ---------------------------------------------------------------------
os.makedirs(args.out, exist_ok=True)
everything = None
for name, solids in members.items():
    comp = Compound(solids)
    export_stl(comp, os.path.join(args.out, f"roof_truss_{name}.stl"))
    everything = comp if everything is None else Compound([everything, comp])
export_stl(everything, os.path.join(args.out, "roof_truss.stl"))
bb = everything.bounding_box()
print(f"rise {soffit(x_c):.0f} mm (soffit) / apex top {z_apex_top:.0f} mm; collar top {z_collar_top:.0f}, "
      f"purlin at x={x_p:.0f}; beams at x={bx:.0f}/{S-bx:.0f}; building length {L_bld:.0f}, cross walls every {args.bay:.0f}")
print(f"bbox {bb.min} -> {bb.max}")
for name, solids in members.items():
    print(f"  {name:7s} x{len(solids):2d}  vol {sum(s.volume for s in solids)/1e9:.4f} m^3")
