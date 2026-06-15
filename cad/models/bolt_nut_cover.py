"""M8 bolt/nut screw-on cover cap.

Stack, open bottom -> closed top:
  - Nut cavity: cylindrical recess to swallow a 17mm AF nut (across-corners ~19.6mm).
  - M8x1.25 internal thread: grabs the bolt protruding above the nut.
  - 24mm AF hex grip: up top, kept clear of the thin cavity walls for strength.

Prototype: PETG. Eventual: TPU (will be soft/floppy threads - clearance added).
"""
import os
import math
from build123d import *

# ---- parameters (mm) ----
NUT_BORE      = 20.5    # clears 17mm AF nut (across-corners ~19.6) + a little slack
NUT_DEPTH     = 11.0    # nut is 10mm high

M8_MAJOR      = 8.0
THREAD_CLEAR  = 0.4     # printed-thread clearance so it actually spins onto a real M8
INT_MAJOR     = M8_MAJOR + THREAD_CLEAR   # 8.4
PITCH         = 1.25    # M8 coarse
THREAD_LEN    = 20.0

CAP           = 4.0     # solid roof above the thread
BASE_OD       = 28.0    # round base around the nut cavity (walls ~3.75mm)
COLLAR_H      = 5.0     # round collar above cavity, keeps the hex away from the cavity
HEX_AF        = 24.0    # hex grip across-flats (apothem = AF/2)

ROUND_H = NUT_DEPTH + COLLAR_H          # round section height (16)
TOTAL_H = NUT_DEPTH + THREAD_LEN + CAP  # 35
HEX_H   = TOTAL_H - ROUND_H             # 19

with BuildPart() as cover:
    # round base (nut cavity + collar)
    Cylinder(radius=BASE_OD / 2, height=ROUND_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # hex grip on top of the round section
    with BuildSketch(Plane.XY.offset(ROUND_H)):
        RegularPolygon(radius=HEX_AF / 2, side_count=6, major_radius=False)
    extrude(amount=HEX_H)

    # nut cavity bore (open bottom)
    with BuildSketch(Plane.XY):
        Circle(NUT_BORE / 2)
    extrude(amount=NUT_DEPTH, mode=Mode.SUBTRACT)
    # bolt/thread bore above the cavity (thread fuses onto this wall)
    with BuildSketch(Plane.XY.offset(NUT_DEPTH)):
        Circle(INT_MAJOR / 2)
    extrude(amount=THREAD_LEN, mode=Mode.SUBTRACT)

# Internal ISO-style thread, built by sweeping a triangular ridge along a right-hand
# helix (build123d 0.10 dropped IsoThread). The ridge sits on the INT_MAJOR bore wall
# and points inward to a ~7.0mm minor dia, so a real M8 bolt threads in with clearance.
THR_R = INT_MAJOR / 2     # bore wall radius the ridge fuses onto (4.2)
THR_DEPTH = 0.7           # radial ridge height -> minor dia ~7.0mm
OVER = 0.1                # bite into the wall for a clean union

helix = Helix(pitch=PITCH, height=THREAD_LEN, radius=THR_R)
pln = Plane(origin=(THR_R, 0, 0), x_dir=(1, 0, 0), z_dir=(helix % 0))
prof = make_face(Polyline(
    (OVER, -0.49 * PITCH), (OVER, 0.49 * PITCH), (-THR_DEPTH, 0), (OVER, -0.49 * PITCH)
))
thread = sweep(pln.from_local_coords(prof), path=helix, is_frenet=True)

part = cover.part + thread.located(Location((0, 0, NUT_DEPTH)))

print(f"volume_mm3={part.volume:.1f}")
bb = part.bounding_box()
print(f"bbox={bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")

out = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(out, exist_ok=True)
stl = os.path.join(out, "bolt_nut_cover.stl")
export_stl(part, stl)
print(f"wrote {os.path.relpath(stl)}")

# watertight check
try:
    import trimesh
    m = trimesh.load(stl)
    print(f"watertight={m.is_watertight}")
except Exception as e:
    print(f"watertight_check_failed={e}")
