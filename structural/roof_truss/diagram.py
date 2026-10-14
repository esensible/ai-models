"""Labelled diagram of the roof framing as understood: cross-section through a
truss and a longitudinal elevation along the building. Existing members solid,
proposed changes dashed.

  python structural/roof_truss/diagram.py structural/roof_truss/report/components.png
"""
import math, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

out = sys.argv[1] if len(sys.argv) > 1 else "components.png"
SPAN, PITCH, SP, BAY = 8500, 27, 1200, 3600
B, D = 35, 105
th = math.radians(PITCH); tan, cos = math.tan(th), math.cos(th)
PLATE_B, PLATE_T, WALL_T = 105, 35, 90
x0 = PLATE_B / 2 - (D / 3) / tan
soffit = lambda x: (x - x0) * tan
dv = D / cos
XC = SPAN / 2
z_apex = soffit(XC) + dv
z_collar_top = z_apex - 1000
z_cb = z_collar_top - D
x_collar = (z_cb + D / 2) / tan + x0 - 0            # collar centreline meets rafter soffit
x_node = XC - (XC - (soffit(XC) - 1000) / tan)        # collar node (centreline) x from left wall
x_cb = z_cb / tan + x0
x_p = x_cb - 20                                       # under-purlin uphill face
RB, RD = 40, 190
HB, HD = 45, 240

C = dict(wall="#e3ddcf", plate="#b9a27a", rafter="#c8812f", joist="#4f7fb5", collar="#c23b3b",
         purlin="#3a9b5c", ridge="#2d6a4f", beam="#7a4bb0", strut="#d08a00", xwall="#cfc6b4")

fig, (ax, ay) = plt.subplots(2, 1, figsize=(15, 14), gridspec_kw=dict(height_ratios=[1.25, 1]))

# ------------------------------------------------------------------ cross-section
def rect(axx, x, z, w, h, col, **kw):
    axx.add_patch(Rectangle((x, z), w, h, facecolor=col, edgecolor="k", lw=0.8, **kw))

def mirror_poly(pts):
    return [(SPAN - x, z) for x, z in pts]

# walls + plates
for xw, lab in ((0, "outer wall"), (XC, "internal (mid) wall"), (SPAN, "outer wall")):
    rect(ax, xw - WALL_T / 2, -700, WALL_T, 700 - PLATE_T, C["wall"])
    rect(ax, xw - PLATE_B / 2, -PLATE_T, PLATE_B, PLATE_T, C["plate"])
# cross wall behind (gable shape under the rafters)
ax.add_patch(Polygon([(-52, 0), (XC, soffit(XC)), (SPAN + 52, 0)], closed=True, facecolor=C["xwall"],
                     edgecolor="none", alpha=0.5, zorder=0))
# ceiling joist
rect(ax, -PLATE_B / 2, 0, SPAN + PLATE_B, D, C["joist"])
# rafters
xs = -450
raf = [(xs, soffit(xs)), (XC - RB / 2, soffit(XC - RB / 2)), (XC - RB / 2, soffit(XC - RB / 2) + dv), (xs, soffit(xs) + dv)]
for pts in (raf, mirror_poly(raf)):
    ax.add_patch(Polygon(pts, closed=True, facecolor=C["rafter"], edgecolor="k", lw=0.8))
# birdsmouth cover-up (plate region) — fine to leave
# collar tie (existing; proposed removal -> hatched)
xl = (z_collar_top - dv) / tan + x0  # where collar top meets rafter top line
ax.add_patch(Polygon([(xl, z_collar_top), (SPAN - xl, z_collar_top),
                      (SPAN - (z_cb - dv) / tan - x0 + 0, z_cb), ((z_cb - dv) / tan + x0, z_cb)], closed=True,
                     facecolor=C["collar"], edgecolor="k", lw=0.8, hatch="//", alpha=0.6))
# under-purlins (section, on edge under the rafter soffit)
for x in (x_p - B, SPAN - x_p):
    rect(ax, x, soffit(x_p) - D, B, D, C["purlin"])
# ridge beam (section)
rect(ax, XC - RB / 2, z_apex - RD, RB, RD, C["ridge"])
# hanging beams on the joists, under the strut line (position to confirm)
for x in (x_node - HB / 2, SPAN - x_node - HB / 2):
    rect(ax, x, D, HB, HD, C["beam"])
# proposed struts
for x in (x_node - B / 2, SPAN - x_node - B / 2):
    rect(ax, x, D + HD, B, soffit(x_p) - D - (D + HD), C["strut"], ls="--", alpha=0.85)

ax.set_xlim(-900, SPAN + 900); ax.set_ylim(-800, z_apex + 700)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Cross-section through one truss (looking along the building) — existing solid, proposed dashed/hatched",
             fontsize=13, pad=12)

def label(axx, text, xy, xytext, col="k"):
    axx.annotate(text, xy=xy, xytext=xytext, fontsize=10, ha="center", va="center", color=col,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, lw=0.8),
                 arrowprops=dict(arrowstyle="->", color=col, lw=1.0, shrinkA=0, shrinkB=2))

label(ax, "rafter 35×105 @ 1200 c/c, 27°\n(proposed: double to 70×105, or 35×140)",
      (1200, soffit(1200) + dv), (1400, 2000), C["rafter"])
label(ax, "ridge beam 40×190 on edge\nbears on the cross walls", (XC, z_apex), (XC, z_apex + 450), C["ridge"])
label(ax, "collar tie 35×105, top 1 m below ridge\n(lapped to rafters — PROPOSED REMOVED)",
      (XC, z_collar_top), (XC, z_collar_top - 420), C["collar"])
label(ax, "under-purlin 35×105 on edge, along the building,\nunder the rafter just below the collar junction,\nbears on the cross walls — ties the trusses together",
      (SPAN - x_p + B / 2, soffit(x_p) - D), (SPAN - 1500, 1750), C["purlin"])
label(ax, "ceiling joist 35×105 @ 1200 c/c\nlapped to the rafter feet, ties the walls\n(carries the plasterboard ceiling)",
      (1000, D / 2), (1300, -420), C["joist"])
label(ax, "hanging beam ≥190 deep (drawn 45×240)\nalong the building, sitting on the joists —\nSIZE, SPAN AND POSITION TO CONFIRM",
      (SPAN - x_node, D + HD), (SPAN - 1700, 800), C["beam"])
label(ax, "PROPOSED strut 35×105 at every truss\nfrom the rafter/under-purlin junction\ndown onto the hanging beam",
      (x_node, (D + HD + soffit(x_p) - D) / 2), (XC - 1400, 350), C["strut"])
label(ax, "outer wall + plate\n(8.5 m between supports)", (0, -300), (300, -600))
label(ax, "mid wall under the joists", (XC, -300), (XC + 1300, -600))
label(ax, "cross (room) wall behind, every 3.6 m:\nsupports under-purlins, ridge, hanging beams", (6500, 500), (6900, -300), "#7a7062")
ax.annotate("", xy=(0, -780), xytext=(SPAN, -780), arrowprops=dict(arrowstyle="<->", lw=1))
ax.text(XC, -760, "8500", ha="center", va="bottom", fontsize=10)

# ------------------------------------------------------------------ longitudinal elevation
L = 2 * BAY
walls_y = [0, BAY, 2 * BAY]
truss_y = [600 + k * SP for k in range(6)]
z_j, z_b, z_p, z_r = D / 2, D + HD / 2, soffit(x_p) - D / 2, z_apex - RD / 2
# cross walls (full height bands)
for yw in walls_y:
    ay.add_patch(Rectangle((yw - WALL_T / 2, -300), WALL_T, z_apex + 300, facecolor=C["xwall"], edgecolor="k", lw=0.5, alpha=0.7))
# runners along the building
rect(ay, -200, 0, L + 400, D, C["joist"])                      # a joist line (one per truss, drawn as a band)
rect(ay, -200, D, L + 400, HD, C["beam"])
rect(ay, -200, soffit(x_p) - D, L + 400, D, C["purlin"])
rect(ay, -200, z_apex - RD, L + 400, RD, C["ridge"])
# trusses: rafter line (vertical at this x) + strut
for y in truss_y:
    rect(ay, y - B / 2, soffit(x_p), B, z_apex - RD - soffit(x_p), C["rafter"])
    rect(ay, y - B / 2, D + HD, B, soffit(x_p) - D - (D + HD), C["strut"], ls="--", alpha=0.85)
    # collar (hatched, proposed removed) crosses behind at this height
    rect(ay, y - B / 2 + B, z_cb, B, D, C["collar"], hatch="//", alpha=0.6)
ay.set_xlim(-600, L + 600); ay.set_ylim(-400, z_apex + 500); ay.set_aspect("equal"); ay.axis("off")
ay.set_title("Longitudinal elevation at the under-purlin line (looking across the span), two bays", fontsize=13, pad=12)
label(ay, "cross (room) walls every 3.6 m, mid-way between trusses", (BAY, 1900), (BAY, z_apex + 300), "#7a7062")
label(ay, "trusses @ 1200 c/c (rafter seen end-on)", (truss_y[1], 1600), (truss_y[1] + 300, 2100), C["rafter"])
label(ay, "ridge beam 40×190, continuous over the cross walls", (truss_y[4], z_r), (truss_y[4] + 400, z_apex + 300), C["ridge"])
label(ay, "under-purlin 35×105, continuous over the cross walls", (truss_y[3], z_p), (truss_y[3] + 500, 1500), C["purlin"])
label(ay, "collar ties (one per truss, proposed removed)", (truss_y[2] + B, z_cb + D / 2), (truss_y[2] + 200, 800), C["collar"])
label(ay, "PROPOSED struts, one per truss, beam to under-purlin", (truss_y[0], (D + HD + soffit(x_p) - D) / 2), (truss_y[0] + 200, -250), C["strut"])
label(ay, "hanging beam on the joists, continuous over the cross walls", (truss_y[4], z_b), (truss_y[4] + 300, -250), C["beam"])
label(ay, "ceiling joists (one per truss) on the plates", (truss_y[2], z_j), (truss_y[2] + 600, -300), C["joist"])
ay.annotate("", xy=(0, z_apex + 120), xytext=(BAY, z_apex + 120), arrowprops=dict(arrowstyle="<->", lw=1))
ay.text(BAY / 2, z_apex + 140, "3600", ha="center", va="bottom", fontsize=10)
ay.annotate("", xy=(truss_y[0], 1300), xytext=(truss_y[1], 1300), arrowprops=dict(arrowstyle="<->", lw=1))
ay.text((truss_y[0] + truss_y[1]) / 2, 1320, "1200", ha="center", va="bottom", fontsize=10)

fig.tight_layout()
fig.savefig(out, dpi=110)
print("wrote", out)
