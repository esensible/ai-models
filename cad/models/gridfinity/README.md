# Gridfinity models

Migrated from github.com/esensible/gridfinity @ a442056 (these exact models
were printed Apr 2026). Grouped here so all Gridfinity work shares one
generator. Run any of them via `./cad/run.sh cad/models/gridfinity/<file>.py`;
exports land in `cad/out/` prefixed `gridfinity_`.

- `bin.py` — the core generator: no per-unit grid feet, perimeter base
  profile, vertical outer walls, simplified single-chamfer lip with
  `WALL = 1.9` (canonical 0.25 mm/side stacking clearance AND canonical
  mating-chamfer width simultaneously). Library only; every model imports it.
- `verify_stack.py` — verification-as-code for the lip/base mate: stacks two
  bins, asserts zero boolean interference, renders the section detail.
  Run after any change to `bin.py`.
- `die_tray.py` — 4×4 tray, 22 threading dies (4-5-4-5-4 rows), embossed
  labels (floor + back wall). Non-integer z_units (height set by die
  clearance, documented in the file).
- `large_die_tray.py` — 4×4 tray, 12 large (40 mm) dies, raised floor for an
  8 mm recess.
- `tap_bin.py` — pair of side-by-side bins (combined 6×5) holding 35 taps,
  top-tangent aligned pockets, floor/wall labels, standard-pitch highlight
  rings. Reads `tap_sizes.csv` (RECONSTRUCTED — see the file's docstring;
  the M18×1.5 length is an estimate).
- `tap_bins.py` — earlier rectpack-packed 5×5 variant of the tap storage
  (three bins, super-blocks per diameter). Kept for reference/re-print;
  needs `rectpack` (in cad/requirements.txt).

The upstream repo's matplotlib render helpers were not migrated — previews
come from the shared `cad/render.py` pipeline. Design rules for new bins
(canonical dimensions, drop-in stadium pockets, cavity clipping, stacking
clearance) live in the gridfinity skill.
