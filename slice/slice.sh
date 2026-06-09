#!/usr/bin/env bash
# slice.sh — slice an STL into a Bambu P1S-printable .gcode.3mf, headless.
#   ./slice/slice.sh <model.stl> [output.3mf]
#
# Hard-won notes (OrcaSlicer 2.3.2, arm64, headless):
#   * CLI does NOT resolve profile `inherits` -> we flatten them (flatten_profile.py).
#   * The P1S's dual extruder-variants (Standard/High Flow) crash the CLI's
#     update_values_to_printer_extruders_for_multiple_filaments -> we strip the
#     variant fields to present a single-extruder config.
#   * --export-3mf path is taken RELATIVE to --outputdir, so pass a bare filename.
#   * Thumbnail/GL errors at the end are cosmetic (no display) and safe to ignore.
set -euo pipefail
SLICE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$(cd "$SLICE/.." && pwd)"
STL="${1:?usage: slice.sh <model.stl> [output.3mf]}"
OUT_NAME="$(basename "${2:-$(basename "${STL%.*}").3mf}")"
OUTDIR="$(cd "$(dirname "$STL")" && pwd)"

export HOME="$WS/cad/.home"; export XDG_CONFIG_HOME="$HOME/.config"; mkdir -p "$HOME"
PROF="$SLICE/profiles"; mkdir -p "$PROF"

# Filament profile is overridable to match what's loaded (FILAMENT env var).
FILAMENT="${FILAMENT:-Bambu PLA Basic @BBL X1C}"
echo "[slice] filament: $FILAMENT"
# (Re)build flattened profiles for P1S 0.4 + 0.20mm Standard + chosen filament.
python3 "$SLICE/flatten_profile.py" "Bambu Lab P1S 0.4 nozzle"      "$PROF/machine.json"  >/dev/null
python3 "$SLICE/flatten_profile.py" "0.20mm Standard @BBL X1C"      "$PROF/process.json"  >/dev/null
python3 "$SLICE/flatten_profile.py" "$FILAMENT"                     "$PROF/filament.json" >/dev/null

# Bed/plate type must support the filament (PETG needs Textured PEI, not Cool Plate).
BED="${BED:-Textured PEI Plate}"
echo "[slice] bed: $BED"
# Optional brim for parts with small bed contact (BRIM=mm). Helps round/on-edge prints stick.
BRIM="${BRIM:-}"
[ -n "$BRIM" ] && echo "[slice] brim: ${BRIM}mm"
# AVOID_CROSSING=1 routes travels AROUND printed walls instead of straight across
# (reduce_crossing_wall). Use for show-face / multi-colour first layers so the nozzle
# doesn't drag strings over visible features. See slice/merge_twocolor.py.
AVOID_CROSSING="${AVOID_CROSSING:-}"
[ -n "$AVOID_CROSSING" ] && echo "[slice] avoid crossing walls: on"
python3 - "$PROF/machine.json" "$PROF/process.json" "$BED" "$BRIM" "$AVOID_CROSSING" <<'PY'
import json,sys
mach,proc,bed,brim,avoid=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]
for f in (mach,proc):
    d=json.load(open(f)); d["curr_bed_type"]=bed; json.dump(d,open(f,"w"),indent=1)
if brim:
    d=json.load(open(proc)); d["brim_type"]="outer_only"; d["brim_width"]=str(brim)
    d["brim_object_gap"]="0.1"; json.dump(d,open(proc,"w"),indent=1)
if avoid:
    d=json.load(open(proc)); d["reduce_crossing_wall"]="1"; d["max_travel_detour_distance"]="0"
    json.dump(d,open(proc,"w"),indent=1)
PY

# ARRANGE: unset/auto = OrcaSlicer auto-centres a single object; set ARRANGE=0 to
# DISABLE auto-arrange and honour the STL's own plate coordinates (front-left
# origin, 0..256). Use a positioned STL to place a part e.g. toward the back.
ARRANGE="${ARRANGE:-}"
[ -n "$ARRANGE" ] && echo "[slice] arrange: $ARRANGE (0=keep STL coords)"

echo "[slice] $STL -> $OUTDIR/$OUT_NAME"
orca-slicer \
  --load-settings "$PROF/machine.json;$PROF/process.json" \
  --load-filaments "$PROF/filament.json" \
  ${ARRANGE:+--arrange "$ARRANGE"} \
  --slice 0 --outputdir "$OUTDIR" --export-3mf "$OUT_NAME" \
  "$STL" 2>&1 | grep -iE 'estimated time|filament used|error' | grep -viE 'glfw|glew|opengl|thumbnail' || true

[[ -f "$OUTDIR/$OUT_NAME" ]] && echo "[slice] OK -> $OUTDIR/$OUT_NAME" || { echo "[slice] FAILED"; exit 1; }
