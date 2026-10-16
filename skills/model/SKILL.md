---
name: "model"
description: "Turn a description into a 3D model with build123d, preview it (headless render), and optionally slice + print on the Bambu P1S."
---

# model: description → 3D model → preview → (optional) print

Turn a described part into a **3D model** (build123d), **preview** it with a headless render, and — only if asked — slice and print it on Andrew's **Bambu Lab P1S** (LAN `192.168.1.129`, LAN-only). Modeling and preview are the default; **printing is an explicit, separate, physical step** — never assume a model request means "print it".

> **Where this lives:** all model/printer code is in the **`ai-models` repo** (`github.com/esensible/ai-models`), checked out at `/home/node/.openclaw/workspace/ai-models`. Run everything from there. Keep this repo modelling/printing only — **no personal data, health/CLL info, or OpenClaw memory/soul/config**.

## When to use
- "Model / design / make a 3D model of ___", "draw up a ___", "preview a ___".
- "Print ___ / make ___ on the printer" → do the model + preview, then the optional print half.
- Default to **model + preview only**. Print only when the user clearly asks.

## Stage 1 — model + preview (the core)
```bash
cd /home/node/.openclaw/workspace/ai-models
./cad/run.sh cad/models/<part>.py   # build123d -> cad/out/<part>.stl (+ STL/3MF)
```
- Write a parametric script in `cad/models/`. Run via `./cad/run.sh <script.py>` (sets `PYOPENGL_PLATFORM=osmesa`, writable HOME, the venv).
- Export with `export_stl(part, "...")` (and `export_3mf` if wanted). build123d centres parts at the origin — fine; the slicer places them on the bed.
- **Always sanity-check**: print `part.volume` and `part.bounding_box()`; verify watertight with trimesh (`m.is_watertight`).
- **Preview render** (no printer involved): `./cad/run.sh cad/render.py cad/out/<part>.stl <out.png> --view iso`. **See `skills/preview/SKILL.md`** — it carries the lighting/AO/framing settings that make a render readable (this OSMesa build's point lights are ~1000x weaker than nominal, and without the depth-buffer AO a bore is indistinguishable from a flat grey disc), and the **standing rule that every change is shown from several angles chosen to highlight that specific feature** — one view is not a preview. Do NOT hand-roll a `pyrender.OffscreenRenderer` here; that is what produced years of unreadable images.
- Rebuild the venv if dead (after an image swap): `./cad/setup.sh`.

That's the whole modeling loop. Stop here unless printing is requested.

## Optional — print it on the P1S
Only when the user wants a physical part. One driver:
```bash
./print.sh cad/out/<part>.stl                      # validate + slice + summary  (does NOT print)
./print.sh cad/out/<part>.stl --print              # slice + grab a BED PHOTO, then STOP
#   → review cad/out/preprint_bed.jpg; confirm the plate is clear; then:
./print.sh cad/out/<part>.stl --print --bed-clear  # actually start the print (physical!)
```
`print.sh` (→ `printer/printflow.py`) reads the **user-declared** state in `printer/loaded.json` (filament incl. brand, plate, nozzle — the printer's own reports are screen-entered and NEVER trusted), loads `slice/filaments/<material>.json` + `slice/nozzles.json`, validates plate↔material, then places / slices / injects any configured bed ramp / repacks / runs the `slice/verify_gcode.py` gate / uploads. Supports `--center X Y`, `--back-ymax Y`, `--brim N`. `--print` alone captures a fresh bed photo and refuses to start; only `--print --bed-clear` actually prints.

### Slice details (OrcaSlicer 2.3.2, headless, arm64)
`./slice/slice.sh <stl> [out.3mf]`; env `FILAMENT=...`, `BED=...` (print.sh sets these). **Gotchas (handled by the scripts — don't regress):**
1. CLI doesn't resolve profile `inherits` → `slice/flatten_profile.py` flattens the chain (else 200×200×100 bed + crash).
2. P1S dual extruder-variants segfault `update_values_to_printer_extruders_for_multiple_filaments` → **delete the variant fields** for a single-extruder config. (Found via gdb + a Creality control slice.)
3. P1S uses **X1C** process/filament profiles, not P1P.
4. Keep `from`/`instantiation` when flattening (only strip `inherits`).
5. `--export-3mf` path is relative to `--outputdir` → bare filename.
6. PETG/ABS/ASA need a hot plate (`curr_bed_type=Textured PEI Plate`); Cool Plate fails for them. PLA is fine on Cool Plate.
7. GL/Wayland/thumbnail/XDG errors at the end are cosmetic. A valid `.gcode.3mf` is a zip with `Metadata/plate_1.gcode`.

### Support audit (MANDATORY after every slice, before every print)
Orca's "object needs supports" nag is **GUI-only — the headless CLI emits
NOTHING** (verified 2026-09-01), so the pipeline must derive the risk itself
from what the slicer bakes into the gcode. Run:
`python3 slice/audit_gcode.py <extracted plate_1.gcode>` — it reports, per
layer: bridge line counts, the **longest single bridge line** (the number
that predicts sag/failure), total bridged path, overhang-wall totals, and
whether supports were generated; exit 1 = longest bridge > 20mm with
supports off.
**Protocol — no ambiguity (user rules, 2026-09-01):**
- Longest bridge **under 20mm: fine**, proceed and say so.
- **Over 20mm: STOP and discuss with the user.** NEVER auto-enable
  supports; supports are always the user's call.
- Every pre-print report states the decision explicitly: "supports:
  none — longest bridge 9mm" / "supports: tree (user-approved) —
  longest bridge 77mm at z13".
Failure model (calibrated the hard way): a long bridge ANCHORED AT BOTH
ENDS can consolidate surprisingly well (77mm ASA at 260°C + 120s layers
held). What FAILS is bridge lines that TERMINATE IN FREE SPACE -- the
lines adjacent to a good span whose far end lands on nothing (an
opening, a recess, past an edge) droop and wreck that whole region of
the surface (dual_pdm case roof: usable-draft-at-best, 2026-09-01). So
audit_gcode's span length alone under-detects risk: the question per
bridge region is "does every line end on solid material?" -- openings
in/adjacent to the bridged surface are the tell.
Supports must NEVER stand on a PETG raft (tree supports sheared off the
release interface, 2026-08-27) — raft prints get modeled-in supports or
bridge-tolerant orientation instead.

### Send (LAN) — `printer/print_job.py` via `./printer/send.sh`
- `--status` (filament/state) · `file.3mf` (upload) · `file.3mf --print` (upload+start).
- FTPS = implicit TLS :990, user `bblp`; **override `storbinary` to skip `conn.unwrap()`** (printer never sends close_notify → hangs).
- Start = MQTT `project_file` (port 8883), `url=file:///sdcard/<name>.3mf`, `param=Metadata/plate_1.gcode`.
- **Start confirmation**: `gcode_state=RUNNING` immediately after `project_file`
  is NOT proof — a start can silently die back to IDLE with heaters off
  (observed 2026-09-02). Confirm via `bambu_status.py`: heater TARGETS set
  (nozzle/bed nonzero) and the `File` field naming the job. If IDLE with
  targets 0, re-send the start.

## Pre-print: confirm the bed is CLEAR (MANDATORY)
The printer can't sense an empty plate; a leftover part = crash/ruined print. Before every print: `--print` slices + grabs `cad/out/preprint_bed.jpg` and stops; **Read it** and confirm clear. If the view is blocked (small parts sit centre, occluded by the parked head), **lift the bed in small careful steps** then re-grab: `printer/gcode_send.py "G91" "G1 Z-15 F600" "G90"` then `printer/camera.py cad/out/preprint_bed.jpg`. Only re-run with `--bed-clear` once you've SEEN it's clear. Not clear → tell Andrew, don't print.

## Bed placement: PUSH IT TO THE BACK (STANDING RULE, user)
**Every print goes at the BACK of the bed** — `./print.sh MODEL.stl --back-ymax 250`
(or `--center X Y` with a high Y). Never leave a large part on auto-centre.

WHY: the P1S door is at the FRONT, and in the unheated shed the front edge of
the plate is the coldest, draughtiest part of it. Lift starts there. The log
says so directly — `template1_drill_guide`: *"slight lift on the +x side,
worst at the FRONT-right corner (bed x~230, y~123)"* — and every large
successful print in `prints.jsonl` is placed `back-ymax` (both dual_pdm cases
in ASA and in PAHT-CF, the drill guide, the slim pair).

**A part longer than ~200mm must also be ROTATED so its long axis runs along
X.** Along Y it physically cannot clear the front: 219mm of part plus brim is
~250mm on a 256mm bed, so it spans the whole plate front to back no matter
where you put it. Rotate it and the same part occupies only the back ~90mm.

FAILED THIS WAY 2026-09-18 (battery_clip, PAHT-CF, text-up on tree supports):
sliced on auto-centre at `y 3.9..248.1` — the near end sat 3.9mm from the
front edge. Died at layer 5. The user had given the placement instruction and
it was not carried into the slice. Check the reported `layer1 ... y` range of
every slice before printing: if it reaches the front of the bed, re-place it.

## Environment: the printer lives in an UNHEATED SHED
Ambient tracks outdoor temperature — cold overnight, warmer by day (seen as
low as ~15°C inside the chamber). Consequences: chamber soaks from cold take
the full 20-30min (don't assume residual warmth); high-temp materials
(ASA/PAHT-CF) print best when started during the warmer part of the day;
record `ambient_c` in the print log when known; the ~40°C chamber-proxy
target for PAHT-CF starts is measured from the nozzle sensor while unpowered.

## Physical state — USER-DECLARED ONLY, keep `printer/loaded.json` current
The printer's `vt_tray` material and `nozzle_diameter` are screen-entered and go
stale silently (no RFID on the external spool) — **never trust them; the loaded
filament (type AND brand) and installed nozzle always come from Andrew.**
- `printer/loaded.json` = `{material, plate, nozzle:{diameter,type}, ams, updated}` —
  `material` names a file in `slice/filaments/`; update on every swap. (gitignored — local printer state.)
- `slice/filaments/<name>.json` = one file per physical spool family: per-nozzle
  OrcaSlicer profile names, allowed plates, and proven `overrides` (flow ratio,
  first-layer speed scale, first-layer bed temp, per-layer bed ramp, preheat soak).
  See `slice/filaments/README.md` for the schema; `petg-overture` is the worked example.
- `slice/nozzles.json` = nozzle diameter → machine/process profile names.
- Always confirm the loaded filament with Andrew before slicing.

## Print log — learn across prints (`printer/prints.jsonl`)
Two layers, don't conflate them:
- **Raw corpus** = `printer/prints.jsonl`, append-only, one JSON object per print,
  **committed** (text → clean diffs, merge-friendly; SQLite/DuckDB are only query
  lenses, never the store). `printflow.py` appends a row automatically at print
  start with everything deterministic (unix `ts`, `git_commit`+`git_dirty`, part,
  `config`/`brand`/`material_type`, nozzle, plate, placement, brim, soak min/temp,
  ramp, est time/mass, footprint). Judgment fields start null — fill them after:
  `printer/print_log.py annotate --outcome success --ambient <C> [--note "..."]`
  (updates the most recent row; `--outcome fail:<mode>` e.g. `fail:warp`).
  Query: `printer/print_log.py query "SELECT ... FROM prints WHERE brand='Overture'"`
  (SQL over the JSONL; scalars are real columns). `brand` and `material_type` are
  stored separately so "is all Overture hard, or just the PETG?" is one query.
- **Distilled lessons** = what we act on. A pattern that recurs in the corpus
  graduates into the relevant `slice/filaments/*.json` `notes`/`overrides` (how the
  Overture recipe got captured). Corpus = evidence; filament configs = the fix.

## End-of-print power state (STANDING RULE, user 2026-09-07)
The printer does NOT clean up after itself: end-gcode leaves the exhaust fan
and chamber light as-is (they've run for hours between prints). Rules by how
the print ended:
- **FINISHED, or the USER asked to cancel**: FULL shutdown —
  `printer/gcode_send.py "M140 S0" "M104 S0" "M106 S0" "M106 P2 S0" "M106 P3 S0"`
  (heaters + part/aux/chamber-exhaust fans) and
  `uv run printer/chamber_light.py off` (MQTT ledctrl; light isn't
  gcode-controllable — turn ON for camera bed checks, off after).
  Exception: an explicit "preheat / another print imminent" hold from the
  user keeps heat on while a print is actually pending.
- **FAILED, or a cancel I initiated/spotted** (monitor catch, error, abort):
  hot end OFF (`M104 S0`) but leave the rest powered — bed heat, fans,
  light — the user will attend quickly and may want to resume. If the user
  is offsite: grab a camera image for them to review and await their
  explicit power-down word before shutting the rest off.

## Monitoring every print (STANDING RULE)
**Monitor EVERY print for failure — even ones Andrew starts himself — and alert him.** `print-monitor` cron (every 5 min, main session): if RUNNING, grab a chamber frame, inspect for spaghetti / detached-shifted part / blobs / nozzle gunk; on failure **alert Andrew on WhatsApp** (+61466717319) with what + layer, offer to pause/stop. Healthy → silent. **Never pause/stop without his say-so.**

## Manual control + camera
- `printer/gcode_send.py "G91" "G1 Z-5 F600" "G90"` — raw g-code. **Bed moves in Z: LOWER Z = bed UP, HIGHER Z = bed DOWN.** No position feedback → small self-correcting steps with camera checks. Never `G28` home with a part on the bed.
- `printer/camera.py <out.jpg>` (importable `camera.grab(host,code,out)`) — chamber cam, TLS :6000, 80-byte auth. Camera is top-front-left; bed-centre is worst-covered. Judge honestly: no spaghetti ≠ guaranteed good layers.

## Safety (non-negotiable)
- A model request is NOT a print request. Print only when asked.
- Starting a print is physical/irreversible: slice + summarise, confirm bed clear + right plate, get Andrew's go before `--print --bed-clear`.
- `printflow.py` refuses to start if the printer is busy (still slices).

## Reboot survival
The container rootfs is ephemeral. `/home/node/.openclaw/workspace/setup/provision.sh` replays apt + rebuilds the `ai-models/cad/.venv`. **OrcaSlicer lives at `/opt/squashfs-root` (symlink `/usr/local/bin/orca-slicer`) — verify it exists after a reboot** or slicing breaks. printer creds live in the `printer` named volume (via `$BAMBU_ENV_FILE`), not the repo.

## Key files (all under `ai-models/`)
- Model/preview: `cad/run.sh`, `cad/setup.sh`, `cad/models/*.py`, `cad/render.py` (documented in `skills/preview/SKILL.md`), `cad/requirements.txt`
- Slice: `slice/slice.sh`, `slice/flatten_profile.py`, `slice/filaments/`, `slice/nozzles.json`, `slice/place_stl.py`, `slice/inject_bed_ramp.py`, `slice/verify_gcode.py`, `slice/repack_gcode_3mf.py`
- Print: `print.sh` → `printer/printflow.py`; `printer/send.sh` → `printer/print_job.py`; `printer/camera.py`; `printer/gcode_send.py`; `printer/chamber_light.py`; `printer/loaded.json`; `printer/print_log.py` + `printer/prints.jsonl`; creds in the `printer` volume (`$BAMBU_ENV_FILE`)

## Proven
2026-06-07: 10/6/10mm tube modelled + previewed + printed (PETG, Textured PEI), headless slice → upload → print → camera-confirmed. Bed-clear gate caught a leftover part on a re-print attempt.
