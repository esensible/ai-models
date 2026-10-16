# Battery strap (build123d): flat bar + raised end pads + two bolt holes +
# recessed "Fuck Yeah" on the z=0 face. Re-authored from the measured STL.
# Frame per spec: origin at the bar centre, z=0 = the text (bed) face.
from build123d import *
import os
import spec as S

bar = extrude(RectangleRounded(S.LENGTH, S.WIDTH, S.EDGE_R), S.BAR_T)
part = bar
# Pads carry their top chamfer as a tapered extrude, applied BEFORE the union
# (chamfering after the union fails: the pad's rounded outline meets the bar's
# at a tangent the OCC chamfer builder won't resolve).
for sx in (-1, 1):
    body = extrude(RectangleRounded(S.PAD_L, S.WIDTH, S.EDGE_R),
                   S.PAD_T - S.PAD_CH)
    cap = Pos(0, 0, S.PAD_T - S.PAD_CH) * extrude(
        RectangleRounded(S.PAD_L, S.WIDTH, S.EDGE_R), S.PAD_CH, taper=45)
    part += Pos(sx * S.PAD_CTR_X, 0, 0) * (body + cap)

# bolt holes through the pads
for sx in (-1, 1):
    part -= Pos(sx * S.HOLE_X, 0, S.PAD_T / 2) * \
        Cylinder(S.HOLE_D / 2, S.PAD_T + 2)

# recessed text on the z=0 face -- NOT mirrored: verified against the
# recovered original, which reads correctly viewed onto this face
font_path = os.path.join(os.path.dirname(__file__), "..", "..", ".home",
                         S.FONT)
txt = Text(S.TEXT, font_size=S.TEXT_H,
           font_path=font_path if os.path.exists(font_path) else None,
           align=(Align.CENTER, Align.CENTER))
part -= extrude(txt, S.TEXT_DEPTH)

# ---- verify + export --------------------------------------------------------
bb = part.bounding_box()
print(f"battery_strap: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {part.volume / 1000:.1f} cm3  solids {len(part.solids())}")
assert len(part.solids()) == 1
assert abs(bb.size.X - S.LENGTH) < 0.01 and abs(bb.size.Y - S.WIDTH) < 0.01
assert abs(bb.size.Z - S.PAD_T) < 0.01

def loops_at(z):
    sec = section(part.solids()[0], Plane.XY.offset(z))
    return [w for f in sec.faces() for w in f.inner_wires()]

# holes present through the pads
mid = loops_at(S.BAR_T / 2)
holes = [w for w in mid
         if abs((w.bounding_box().max.X - w.bounding_box().min.X) - S.HOLE_D)
         < 0.1]
print(f"  {len(holes)} bolt holes at Ø{S.HOLE_D} "
      f"({S.HOLE_PITCH} apart)")
assert len(holes) == 2, f"expected 2 bolt holes, found {len(holes)}"
xs = sorted((w.bounding_box().min.X + w.bounding_box().max.X) / 2
            for w in holes)
assert abs((xs[1] - xs[0]) - S.HOLE_PITCH) < 0.05, "hole pitch wrong"

# text really is recessed, and only to TEXT_DEPTH
n_shallow = len(loops_at(S.TEXT_DEPTH / 2))
n_deep = len(loops_at(S.TEXT_DEPTH + 0.5))
print(f"  text recess: {n_shallow} loops at z{S.TEXT_DEPTH / 2}, "
      f"{n_deep} at z{S.TEXT_DEPTH + 0.5} (should drop to the 2 holes)")
assert n_shallow > 5, "text not cut into the face"
assert n_deep == 2, "text recess deeper than TEXT_DEPTH"

# text must span about the original's width and clear the raised pads
tsec = section(part.solids()[0], Plane.XY.offset(S.TEXT_DEPTH / 2))
lw = [w.bounding_box() for f in tsec.faces() for w in f.inner_wires()]
lw = [b for b in lw if (b.max.X - b.min.X) < 40 and
      abs((b.max.X - b.min.X) - S.HOLE_D) > 0.3]
t_lo, t_hi = min(b.min.X for b in lw), max(b.max.X for b in lw)
print(f"  text spans {t_hi - t_lo:.1f}mm (original {S.TEXT_W})")
assert abs((t_hi - t_lo) - S.TEXT_W) < 6.0, "text width off the original"
assert t_lo > -S.LENGTH / 2 + S.PAD_L and t_hi < S.LENGTH / 2 - S.PAD_L, \
    "text runs into a raised pad"

# the flat span really is BAR_T thick between the pads
span = section(part.solids()[0], Plane.XY.offset(S.BAR_T + 1.0))
xs2 = [f.bounding_box() for f in span.faces()]
print(f"  above the bar (z={S.BAR_T + 1.0}): {len(xs2)} pad section(s)")
assert len(xs2) == 2, "expected two separate end pads above the bar"

export_stl(part, f"{S.OUT}/battery_strap.stl")
export_step(part, f"{S.OUT}/battery_strap.step")
print("exported battery_strap.stl/.step")
