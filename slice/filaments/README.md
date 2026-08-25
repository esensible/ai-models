# Filament configs — one file per physical filament

Each file describes one spool family we actually own: which OrcaSlicer profile
it slices with (per nozzle diameter), which plates it may print on, and any
proven overrides on top of the stock profile.

**Selection is always user-declared, never printer-reported.** The printer's
`vt_tray` is whatever was last typed on its screen (no RFID on the external
spool) and goes stale silently. The loaded filament — including brand — comes
from the user and is recorded in `printer/loaded.json` (`material` = a filename
here, minus `.json`, uppercased by convention in conversation).

## Schema

```json
{
  "display":       "human name, brand + colour",
  "type":          "PETG",            // material family; used only to warn if
                                      // the printer's vt_tray disagrees
  "profiles":      {"0.4": "<OrcaSlicer filament profile name>",
                    "0.6": "..."},    // per nozzle diameter; verify the name
                                      // exists under the Orca BBL tree before
                                      // adding (many share the base name)
  "plates":        ["Textured PEI Plate", "..."],
  "default_plate": "Textured PEI Plate",
  "overrides": {                      // all optional; omit = stock profile
    "flow_ratio":              0.94,  // filament_flow_ratio
    "first_layer_speed_scale": 0.5,   // multiplies initial_layer_* speeds
    "bed_temp_first_layer":    90,    // held through layer 1 (and preheat)
    "bed_ramp_per_layer":      [85, 80, 75, 70],  // M140 steps from layer 2,
                                      // post-processed into the gcode
                                      // (slicers can't do per-layer bed temps)
    "preheat_hold_min":        10     // soak at first-layer bed temp before start
  },
  "notes": "why the overrides exist; provenance of the numbers"
}
```

The print driver (`printer/printflow.py`) consumes these; `slice/nozzles.json`
maps nozzle diameter to machine/process profiles.
