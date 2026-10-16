# PETG sacrificial raft for canbox PAHT-CF prints (build123d).
# Sized to the part being printed on it: rounded slab = part bbox + MARGIN.
# Thinner than the dual_pdm raft (user 2026-08-27: 6 layers was too much) --
# 4 layers @0.2. Release still comes from the dissimilar-material interface.
from build123d import *
import spec as S

RAFT_H = 1.2          # [CHOSEN] back to the validated 6 layers @0.2: after
                      #   two lift failures with reuse + thin rafts in play,
                      #   the only fully successful PA prints all sat on
                      #   virgin 1.2 (2026-08-27)
MARGIN = 4.0          # [CHOSEN] slab beyond the part outline

part = import_step(f'{S.OUT}/canbox_base.step')
bb = part.bounding_box()
X1, Y1 = bb.min.X - MARGIN, bb.min.Y - MARGIN
X2, Y2 = bb.max.X + MARGIN, bb.max.Y + MARGIN

raft = extrude(
    Pos((X1 + X2) / 2, (Y1 + Y2) / 2) * RectangleRounded(X2 - X1, Y2 - Y1, 6),
    RAFT_H)

rb = raft.bounding_box()
print(f"raft: {rb.size.X:.1f} x {rb.size.Y:.1f} x {rb.size.Z:.1f}  "
      f"vol {raft.volume/1000:.1f} cm3  (part + {MARGIN} margin)")
sec = section(raft.solids()[0], Plane.XY.offset(RAFT_H / 2))
inner = [w for f in sec.faces() for w in f.inner_wires()]
assert not inner, "raft must be SOLID"
export_stl(raft, f"{S.OUT}/canbox_raft.stl")
print("exported canbox_raft.stl")
