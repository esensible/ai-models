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
- **Preview render** (no printer involved): pyrender works headless via OSMesa. Load the STL with trimesh, render with a `pyrender.OffscreenRenderer`, save a PNG to `cad/out/<part>_render.png`, and show it. Good for "let me see it first". (Example: the test_plate / tube renders in `cad/out/`.)
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
`print.sh` (→ `bambu/printflow.py`) reads the **live** loaded material off the printer, cross-checks the **recorded** plate in `bambu/loaded.json`, looks up `slice/materials.json`, validates plate↔material, slices, and summarises. `--print` alone captures a fresh bed photo and refuses to start; only `--print --bed-clear` actually prints.

### Slice details (OrcaSlicer 2.3.2, headless, arm64)
`./slice/slice.sh <stl> [out.3mf]`; env `FILAMENT=...`, `BED=...` (print.sh sets these). **Gotchas (handled by the scripts — don't regress):**
1. CLI doesn't resolve profile `inherits` → `slice/flatten_profile.py` flattens the chain (else 200×200×100 bed + crash).
2. P1S dual extruder-variants segfault `update_values_to_printer_extruders_for_multiple_filaments` → **delete the variant fields** for a single-extruder config. (Found via gdb + a Creality control slice.)
3. P1S uses **X1C** process/filament profiles, not P1P.
4. Keep `from`/`instantiation` when flattening (only strip `inherits`).
5. `--export-3mf` path is relative to `--outputdir` → bare filename.
6. PETG/ABS/ASA need a hot plate (`curr_bed_type=Textured PEI Plate`); Cool Plate fails for them. PLA is fine on Cool Plate.
7. GL/Wayland/thumbnail/XDG errors at the end are cosmetic. A valid `.gcode.3mf` is a zip with `Metadata/plate_1.gcode`.

### Send (LAN) — `bambu/print_job.py` via `./bambu/send.sh`
- `--status` (filament/state) · `file.3mf` (upload) · `file.3mf --print` (upload+start).
- FTPS = implicit TLS :990, user `bblp`; **override `storbinary` to skip `conn.unwrap()`** (printer never sends close_notify → hangs).
- Start = MQTT `project_file` (port 8883), `url=file:///sdcard/<name>.3mf`, `param=Metadata/plate_1.gcode`.

## Pre-print: confirm the bed is CLEAR (MANDATORY)
The printer can't sense an empty plate; a leftover part = crash/ruined print. Before every print: `--print` slices + grabs `cad/out/preprint_bed.jpg` and stops; **Read it** and confirm clear. If the view is blocked (small parts sit centre, occluded by the parked head), **lift the bed in small careful steps** then re-grab: `bambu/gcode_send.py "G91" "G1 Z-15 F600" "G90"` then `bambu/camera.py cad/out/preprint_bed.jpg`. Only re-run with `--bed-clear` once you've SEEN it's clear. Not clear → tell Andrew, don't print.

## Physical state the printer can't report — keep `bambu/loaded.json` current
Reports material (`vt_tray.tray_type`) + nozzle, but NOT plate / bed-clear / live Z.
- `bambu/loaded.json` = `{plate, material, filament_brand, ams, updated}` — update on every swap; `printflow.py` warns on material mismatch. (gitignored — local printer state.)
- `slice/materials.json` = material → `{filament, allowed plates}`; add a material = one entry. (PLA, PETG, ABS, ASA, TPU.)
- Always check loaded filament before slicing.

## Monitoring every print (STANDING RULE)
**Monitor EVERY print for failure — even ones Andrew starts himself — and alert him.** `print-monitor` cron (every 5 min, main session): if RUNNING, grab a chamber frame, inspect for spaghetti / detached-shifted part / blobs / nozzle gunk; on failure **alert Andrew on WhatsApp** (+61466717319) with what + layer, offer to pause/stop. Healthy → silent. **Never pause/stop without his say-so.**

## Manual control + camera
- `bambu/gcode_send.py "G91" "G1 Z-5 F600" "G90"` — raw g-code. **Bed moves in Z: LOWER Z = bed UP, HIGHER Z = bed DOWN.** No position feedback → small self-correcting steps with camera checks. Never `G28` home with a part on the bed.
- `bambu/camera.py <out.jpg>` (importable `camera.grab(host,code,out)`) — chamber cam, TLS :6000, 80-byte auth. Camera is top-front-left; bed-centre is worst-covered. Judge honestly: no spaghetti ≠ guaranteed good layers.

## Safety (non-negotiable)
- A model request is NOT a print request. Print only when asked.
- Starting a print is physical/irreversible: slice + summarise, confirm bed clear + right plate, get Andrew's go before `--print --bed-clear`.
- `printflow.py` refuses to start if the printer is busy (still slices).

## Reboot survival
The container rootfs is ephemeral. `/home/node/.openclaw/workspace/setup/provision.sh` replays apt + rebuilds the `ai-models/cad/.venv`. **OrcaSlicer lives at `/opt/squashfs-root` (symlink `/usr/local/bin/orca-slicer`) — verify it exists after a reboot** or slicing breaks. printer creds live in `bambu/printer.env` (gitignored).

## Key files (all under `ai-models/`)
- Model/preview: `cad/run.sh`, `cad/setup.sh`, `cad/models/*.py`, `cad/render.py`, `cad/requirements.txt`
- Slice: `slice/slice.sh`, `slice/flatten_profile.py`, `slice/materials.json`
- Print: `print.sh` → `bambu/printflow.py`; `bambu/send.sh` → `bambu/print_job.py`; `bambu/camera.py`; `bambu/gcode_send.py`; `bambu/loaded.json`; `bambu/printer.env` (gitignored)

## Proven
2026-06-07: 10/6/10mm tube modelled + previewed + printed (PETG, Textured PEI), headless slice → upload → print → camera-confirmed. Bed-clear gate caught a leftover part on a re-print attempt.
