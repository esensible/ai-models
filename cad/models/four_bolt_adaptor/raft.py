# PETG sacrificial bed-plate for the PAHT-CF four_bolt_adaptor (build123d).
# A SOLID slab -- the part's holes/bore deliberately do NOT extend into it
# (user spec). Same outline construction as plate.py, offset RAFT_MARGIN
# further out; the part prints on top and releases at the weak PA/PETG
# interface. Values from spec.py.
from build123d import *
import spec as S

pts = list(S.ALL_HOLES_PLATE.values())


def hull(points):
    pts = sorted(set(points))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (
                (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


OUTLINE_OFF = S.HOLE_DIA / 2 + S.EDGE_MARGIN + S.RAFT_MARGIN
hull_face = make_face(Polyline(*hull(pts), close=True))
raft = extrude(offset(hull_face, OUTLINE_OFF, kind=Kind.ARC), S.RAFT_H)

bb = raft.bounding_box()
print(f"raft: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
      f"vol {raft.volume/1000:.1f} cm3")
sec = section(raft.solids()[0], Plane.XY.offset(S.RAFT_H / 2))
inner = [w for f in sec.faces() for w in f.inner_wires()]
assert not inner, f"raft must be SOLID (no holes); found {len(inner)} inner wires"
export_stl(raft, f"{S.OUT}/four_bolt_adaptor_raft.stl")
print("exported four_bolt_adaptor_raft.stl")
