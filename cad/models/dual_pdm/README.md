# Dual dingoPDM mount

Two [dingoPDM](https://github.com/corygrant/dingoPDM) V7.5 boards side by side
(long edges adjacent, 10 mm apart) on one monolithic aluminum heatsink, with a
single-print enclosure and 3D-printed machining templates for the heatsink.

**Ground truth is the board layout**: two boards at **82.39 mm pitch**
(72.39 board + 10 gap), identical orientation, so the +12V studs and GND studs
each line up for straight bus bars. The enclosure derives from the boards; the
templates derive from the boards/enclosure; nothing depends on the heatsink's
dimensions (cuts that reach a heatsink edge just run off it).

Datum frame: board A's lower-left PCB corner, X toward board B, Y along the
board's long axis, z=0 at the PCB underside. Heatsink top = z −0.5 (0.5 mm
thermal pad, e.g. 3M 5583S, both sides electrical isolation as per dingoPDM
docs).

## Scripts (run with `cad/run.sh`; needs `DINGOPDM_DIR` pointing at a clone
of the dingoPDM repo for the stock Case/PCBA STEPs)

- `templates.py` — three 10 mm printed templates for machining the heatsink,
  parameterized on the trim-router **6 mm cutter / 15 mm guide bush**
  (offset = (bush − cutter)/2 = 4.5):
  1. **drill guide** (31 Ø-specific bores): 8× M3 board holes (2.5 drill,
     tap M3×0.5), 16× blind dog-bone drills at relief-pocket corner pins
     (ring-marked, ~4 deep), 5× M6 case screws (5.0 drill, tap M6×1.0),
     2× Ø8 end mounting holes (no tap).
  2. **pin reliefs**: routed pockets ≥3.5 deep for RedCube/DT through-pins;
     registers on 4 M3 screws into the freshly tapped holes.
  3. **skirt rebate island**: bush rides the outer edge; every edge inset
     (wall 3.0 + 0.3 clearance + 4.5 offset) from the enclosure walls.
     Rebate depth exactly **3.175** (stock skirt height): seating is
     skirt-on-floor, tolerance lives in the enclosure divider instead.
- `enclosure.py` — single-print dual case from the stock Case.step: join
  walls/tabs booleaned off, cut profile extruded across the gap, solid
  divider wall between the boards (bottom 0.3 above the heatsink plane),
  one enclosed recessed M6 SHCS between the DT connectors, 1 mm bus-bar
  relief channels in the roof (bars bolt onto the RedCube tops above the
  roof; GND bar ≤ ~13 wide at the crossing).
- `assembly.py` — named-component STEP (+zip, +boards-free 3MF) of heatsink
  blank, both PCBAs, enclosure, and templates for clearance checks in
  Fusion/Orca.

## Heatsink (minimum, grows freely outward)

Rectangle **(−12, 4) → (166.78, 91.25)**, thickness your stock (≥10 for
screw engagement). 8× M3 + 5× M6 tapped, 2× Ø8 mounting through-holes on the
end mid-lines (stock cuts the edge through them as half-slots). Hardware:
stock M3×0.5×12 board screws, M6×1.0×14 case screws.
