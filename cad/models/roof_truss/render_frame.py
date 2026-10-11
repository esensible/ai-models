"""Colour-coded render of the roof framing STLs (matplotlib; no GL needed).

  python cad/models/roof_truss/render_frame.py cad/out cad/out/roof_truss_render.png
"""
import os, sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

src, out = sys.argv[1], sys.argv[2]
COL = {"wall": "#d9d4c7", "plate": "#b9a27a", "rafter": "#c8812f", "joist": "#4f7fb5",
       "collar": "#c23b3b", "purlin": "#3a9b5c", "beam": "#7a4bb0"}
LABEL = {"wall": "walls (outer x2 + mid)", "plate": "wall plates", "rafter": "rafters 35x105",
         "joist": "ceiling joists 35x105", "collar": "collar ties 35x105",
         "purlin": "under-purlins 35x105", "beam": "hanging beams 45x240"}

meshes = {k: trimesh.load(os.path.join(src, f"roof_truss_{k}.stl")) for k in COL}
allv = np.vstack([m.vertices for m in meshes.values()])
lo, hi = allv.min(0), allv.max(0)
ctr, rng = (lo + hi) / 2, (hi - lo).max() / 2

fig = plt.figure(figsize=(16, 7.5))
views = [(28, -55, "isometric: X across span, Y along building"),
         (0, -90, "end elevation (looking along the building)")]
for i, (elev, azim, title) in enumerate(views):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    for k, m in meshes.items():
        pc = Poly3DCollection(m.vertices[m.faces], facecolor=COL[k], edgecolor="k",
                              linewidths=0.15, alpha=0.5 if k == "wall" else 1.0)
        ax.add_collection3d(pc)
    ax.set_xlim(ctr[0] - rng, ctr[0] + rng); ax.set_ylim(ctr[1] - rng, ctr[1] + rng)
    ax.set_zlim(ctr[2] - rng * 0.6, ctr[2] + rng * 0.6)
    ax.set_box_aspect((1, 1, 0.6))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title); ax.set_xlabel("X mm"); ax.set_ylabel("Y mm"); ax.set_zlabel("Z mm")
    if i == 1:
        ax.set_yticks([])
handles = [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in COL]
fig.legend(handles, [LABEL[k] for k in COL], loc="lower center", ncol=4, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(out, dpi=110)
print("wrote", out)
