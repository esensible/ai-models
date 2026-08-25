"""Verify the simplified-lip stacking geometry: overlap check + section render.

Stacks two 2x2x2 bins at natural rest (+0.5mm visual gap), asserts the boolean
intersection is empty (no lip/base interference), and renders the XZ section
detail to cad/out. Run after ANY change to bin.py's lip or base profile.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from build123d import Location, Plane, Vector

from bin import gridfinity_bin

LIP_TOP_Z = 14.0  # for a 2u bin
# Upper bin's base-profile upper chamfer mates flat-on-flat with the lower
# bin's lip pocket outer chamfer. Setting their lines equal:
#   upper:  x = 39.60 + (z - z_offset - 2.6)
#   lower:  x = 39.85 + (z - 12.1)
# yields z_offset = 9.25 — i.e. the upper bin's z'=4.75 (top of base profile)
# sits at z=14 (lower bin's top edge), and the chamfers coincide over their
# common range (z=12.1 to z=14).
NATURAL_REST_OFFSET = 9.25
EXTRA_GAP = 0.5  # lift the upper bin by this much so the gap is visible


def edges_to_polylines(edges):
    return [
        np.array([(e.position_at(t).X, e.position_at(t).Z) for t in np.linspace(0, 1, max(8, int(e.length * 6)))])
        for e in edges
    ]


def main():
    lower = gridfinity_bin(2, 2, 2, solid=False)
    upper = gridfinity_bin(2, 2, 2, solid=False)

    z_offset = NATURAL_REST_OFFSET + EXTRA_GAP
    upper = upper.moved(Location(Vector(0, 0, z_offset)))

    # Cross-section both
    lower_section = lower.intersect(Plane.XZ)
    upper_section = upper.intersect(Plane.XZ)
    lower_pl = edges_to_polylines(lower_section.edges())
    upper_pl = edges_to_polylines(upper_section.edges())

    # Boolean intersection of the two solids — should be empty if no interference
    overlap = lower.intersect(upper)
    overlap_volume = overlap.volume if overlap and len(overlap.solids()) > 0 else 0.0

    fig = plt.figure(figsize=(11, 9), dpi=130)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.4])
    ax_full = fig.add_subplot(gs[0])
    ax_zoom = fig.add_subplot(gs[1])

    for ax in (ax_full, ax_zoom):
        for pl in lower_pl:
            ax.plot(pl[:, 0], pl[:, 1], "-", color="#1a3a6b", linewidth=1.3, label="_lower")
        for pl in upper_pl:
            ax.plot(pl[:, 0], pl[:, 1], "-", color="#b8431d", linewidth=1.3, label="_upper")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")

    # Legend handles
    from matplotlib.lines import Line2D
    legend = [
        Line2D([0], [0], color="#1a3a6b", lw=1.5, label="lower bin"),
        Line2D([0], [0], color="#b8431d", lw=1.5, label=f"upper bin (z+{z_offset:.2f})"),
    ]
    ax_full.legend(handles=legend, loc="upper right")

    ax_full.set_title(
        f"Stacked 2x2x2 bins — overlap volume = {overlap_volume:.4f} mm³ "
        f"({'CLEAR' if overlap_volume < 1e-3 else 'INTERFERENCE'})"
    )
    ax_zoom.set_title(
        f"Detail at lip/base interface (right edge); upper lifted {EXTRA_GAP} mm above natural rest"
    )
    ax_zoom.set_xlim(38.5, 43)
    ax_zoom.set_ylim(8, 18)

    fig.tight_layout()
    import os

    from bin import OUT

    out_png = os.path.join(OUT, "gridfinity_stack_check.png")
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"overlap volume = {overlap_volume:.6f} mm^3")
    assert overlap_volume < 1e-3, "lip/base INTERFERENCE — bins will not stack"
    print(f"stacking verified; wrote {out_png}")


if __name__ == "__main__":
    main()
