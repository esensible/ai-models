# 2D cross-section of the ignition blank (keyed bore shape): circle + two
# side tabs + one top tab. Exposes keyed_profile(grow) for the 3D build;
# run as a script to draw the dimensioned review figure.
# Frame: origin at circle centre, +y up (bore as viewed).
from build123d import *
import spec as S


def keyed_profile(grow=0.0, corners=None):
    """The bore cross-section as a build123d Sketch, offset outward by
    `grow` mm. Offsetting the finished union keeps every edge equidistant,
    so the lip (grow=+g) is a true parallel offset of the same shape.
    corners: Kind.ARC (default) rounds the offset's outside corners;
    Kind.INTERSECTION keeps them SQUARE (user spec for the lip)."""
    R = S.DIA_BASE / 2
    hslab = Pos(0, S.HTAB_BOT + S.HTAB_H / 2) * Rectangle(S.HTAB_SPAN, S.HTAB_H)
    vtab = Pos(0, S.VTAB_TOP / 2) * Rectangle(S.VTAB_W, S.VTAB_TOP)
    base = Circle(R) + hslab + vtab
    if grow:
        base = offset(base, grow, kind=corners or Kind.ARC)
    return base


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mp

    R = S.DIA_BASE / 2
    profile = keyed_profile()
    vtab_top = S.VTAB_TOP
    bb = profile.bounding_box()
    print(f"profile: {bb.size.X:.1f} wide x {bb.size.Y:.1f} tall, "
          f"area {profile.area:.0f}mm2")
    assert abs(bb.size.X - S.HTAB_SPAN) < 0.01
    assert abs(bb.max.Y - vtab_top) < 0.01
    assert abs(bb.min.Y - -R) < 0.01

    fig, ax = plt.subplots(figsize=(9, 10))
    ax.set_aspect("equal")

    def draw(sk, fc, ec, lw):
        verts = []
        for edge in sk.face().outer_wire().edges():
            pts = [edge @ (i / 24) for i in range(25)]
            verts += [(p.X, p.Y) for p in pts]
        ax.add_patch(mp.Polygon(verts, closed=True, facecolor=fc,
                                edgecolor=ec, lw=lw))

    draw(keyed_profile(S.LIP_OFF, Kind.INTERSECTION),
         "#e4e8ee", "#7a8494", 1.0)   # lip outline, square outside corners
    draw(profile, "#b9c0cc", "#222", 1.5)                        # body
    ax.axhline(0, color="#888", lw=0.6, ls="--")
    ax.axvline(0, color="#888", lw=0.6, ls="--")

    def dim(x0, y0, x1, y1, text, off=(0, 0), color="#c0392b"):
        ax.annotate("", (x1, y1), (x0, y0),
                    arrowprops=dict(arrowstyle="<->", color=color, lw=1.2))
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text,
                color=color, fontsize=10, ha="center", va="center",
                bbox=dict(fc="white", ec="none", alpha=0.85))

    dim(-R, -R - 4, R, -R - 4, f"a = Ø{S.DIA_BASE:.0f} circle", off=(0, -2))
    # b: largest span from the tab's top outside corner to the opposite side
    # of the circle -- runs through the centre (that's what maximises it)
    import math as _m
    _px, _py = S.HTAB_SPAN / 2, S.HTAB_BOT + S.HTAB_H
    _n = _m.hypot(_px, _py)
    _fx, _fy = -R * _px / _n, -R * _py / _n
    dim(_px, _py, _fx, _fy,
        f"b = {S.B_SPAN:.1f} corner to opposite side (largest span)",
        off=(-9, -3), color="#1a6e2e")
    dim(-S.HTAB_SPAN / 2, S.HTAB_BOT - 3.5, S.HTAB_SPAN / 2, S.HTAB_BOT - 3.5,
        f"c = {S.HTAB_SPAN:.0f} outside-to-outside (heard '5m' -- CONFIRM)",
        off=(0, -2))
    dim(S.HTAB_SPAN / 2 + 3, S.HTAB_BOT, S.HTAB_SPAN / 2 + 3,
        S.HTAB_BOT + S.HTAB_H,
        f"d = {S.HTAB_H:.0f} tab height (not given)", off=(13, 0))
    dim(-S.VTAB_W / 2, vtab_top + 3, S.VTAB_W / 2, vtab_top + 3,
        f"e = {S.VTAB_W:.0f} wide", off=(0, 2.5))
    dim(-R - 4, -R, -R - 4, vtab_top,
        f"f = {S.VTAB_REACH:.0f} tab top to circle bottom", off=(-3, 0))
    lipbb = keyed_profile(S.LIP_OFF, Kind.INTERSECTION).bounding_box()
    dim(-S.HTAB_SPAN / 2 - S.LIP_OFF, -R + 2, -S.HTAB_SPAN / 2, -R + 2,
        f"g = {S.LIP_OFF:.0f} lip offset (CONFIRM)", off=(-1, -3))

    ax.set_xlim(lipbb.min.X - 16, lipbb.max.X + 20)
    ax.set_ylim(lipbb.min.Y - 10, lipbb.max.Y + 8)
    ax.set_title("ignition blank — body profile + lip outline "
                 "(ALL PLACEHOLDER DIMS)")
    ax.set_xlabel("mm")
    fig.tight_layout()
    fig.savefig(f"{S.OUT}/ignition_blank_profile.png", dpi=110)
    print("wrote ignition_blank_profile.png")
