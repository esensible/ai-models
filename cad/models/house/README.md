# house

Measured draft floor plan using the existing build123d workflow:

```sh
./cad/run.sh cad/models/house/floorplan.py
./cad/run.sh cad/render.py cad/out/house/house_plan_slice.stl cad/out/house/house_plan_preview.png --view iso
```

`measurements.json` preserves user measurements separately from modelling assumptions.
`floorplan.py` constructs a boolean CAD wall footprint, exports a 100 mm plan slice
(STEP/STL), and draws that footprint with room labels and dimensions (SVG/PNG).
The slice height is only for plan preview, not a measured wall height.

## Draft interpretations

- Front is at the bottom of the reference plan; no geographic orientation is assumed.
- Dimensions are provisionally treated as clear internal measurements.
- First hall section is 1,720 wide and 4,260 long. Its rightward neck is 815 wide.
- The second hall length of 3,960 is interpreted as including a provisional 200-long neck;
  the next wider section is 1,450. Exact step endpoints still need confirmation.
- Kitchen zone span of 4,815 includes the adjacent passage. The kitchen recess dimension
  of 1,830 is provisionally treated as front-to-back. Its endpoints need confirmation.
- The measured 350 wall thickness is assigned to a short segment at the living transition;
  its exact extent is unmeasured. Other walls are provisionally 200 thick.
- Door openings default to 820; laundry is provisionally 660. The shared laundry/ensuite
  opening also uses 660 provisionally. Door locations/swings and windows follow the
  reference arrangement approximately and are not measured.
- Bedrooms and living area are inferred to fit the measured circulation and service rooms;
  their geometry is not a verified reproduction of the reference room dimensions.
- Verandah and carport are reference outlines; shed dimensions are listed as an inset note.
- Toilet opens to bathroom as on reference; no extra partition inferred there.
- No address, listing URL, or original marketing image is stored in this project.

Outputs are generated under the git-ignored `cad/out/house/` folder.

## Revision 02 verification

Walls are the remaining material after subtracting room interiors and circulation
from a closed building envelope. Openings are cut afterwards. The CAD and merged
STL must be valid/watertight; the previous per-component-only check is removed.
Eleven clear room/hall spans are measured using probes intersecting the final CAD
wall geometry and compared with recorded measurements (`geometry_checks.json`).
The kitchen span is anchored at the actual laundry wall; this corrects a 304 mm
discrepancy in revision 01.

SVG native page size is 8 x 11 inches, scale 1:100. Both axes are checked: a
1,000 mm model span must occupy 10 mm on the physical sheet. Print at actual
size, not fit-to-page. Screen previews resize; use the geometric scale bar.

Hall longitudinal dimensions, kitchen recess depth, and toilet length currently
locate assumed transition datums rather than two continuous enclosing wall faces.
They remain subject to endpoint clarification; verified clear-span checks must not
be interpreted as a complete measured survey of the house.
