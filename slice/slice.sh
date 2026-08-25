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

# Profiles are overridable to match the loaded filament and installed nozzle
# (FILAMENT / MACHINE / PROCESS env vars; see slice/nozzles.json for the
# machine+process pairs per nozzle diameter).
FILAMENT="${FILAMENT:-Bambu PLA Basic @BBL X1C}"
MACHINE="${MACHINE:-Bambu Lab P1S 0.4 nozzle}"
PROCESS="${PROCESS:-0.20mm Standard @BBL X1C}"
echo "[slice] filament: $FILAMENT"
echo "[slice] machine:  $MACHINE"
echo "[slice] process:  $PROCESS"
python3 "$SLICE/flatten_profile.py" "$MACHINE"   "$PROF/machine.json"  >/dev/null
python3 "$SLICE/flatten_profile.py" "$PROCESS"   "$PROF/process.json"  >/dev/null
python3 "$SLICE/flatten_profile.py" "$FILAMENT"  "$PROF/filament.json" >/dev/null

# A stale output must never masquerade as a fresh slice: if the slicer dies,
# the pre-existing file would pass the exists-check below (bit us 2026-08-24).
rm -f "$OUTDIR/$OUT_NAME"

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
# FLOW_RATIO: override filament_flow_ratio (all entries).
# BED_TEMP: set the bed temp for the CHOSEN plate type, first layer AND rest
#   (per-layer ramps are a post-processing job; see slice/inject_bed_ramp.py).
# FIRST_SPEED_SCALE: multiply initial_layer_speed / initial_layer_infill_speed.
FLOW_RATIO="${FLOW_RATIO:-}"
BED_TEMP="${BED_TEMP:-}"
FIRST_SPEED_SCALE="${FIRST_SPEED_SCALE:-}"
[ -n "$FLOW_RATIO" ] && echo "[slice] flow ratio: $FLOW_RATIO"
[ -n "$BED_TEMP" ] && echo "[slice] bed temp override: ${BED_TEMP}C (first layer + rest)"
[ -n "$FIRST_SPEED_SCALE" ] && echo "[slice] first-layer speed scale: $FIRST_SPEED_SCALE"
python3 - "$PROF/machine.json" "$PROF/process.json" "$PROF/filament.json" "$BED" "$BRIM" "$AVOID_CROSSING" "$FLOW_RATIO" "$BED_TEMP" "$FIRST_SPEED_SCALE" <<'PY'
import json,sys
mach,proc,fil,bed,brim,avoid,flow,bedtemp,flscale=sys.argv[1:10]
for f in (mach,proc):
    d=json.load(open(f)); d["curr_bed_type"]=bed; json.dump(d,open(f,"w"),indent=1)
if brim:
    d=json.load(open(proc)); d["brim_type"]="outer_only"; d["brim_width"]=str(brim)
    d["brim_object_gap"]="0.1"; json.dump(d,open(proc,"w"),indent=1)
if avoid:
    d=json.load(open(proc)); d["reduce_crossing_wall"]="1"; d["max_travel_detour_distance"]="0"
    json.dump(d,open(proc,"w"),indent=1)
if flow:
    d=json.load(open(fil)); v=d["filament_flow_ratio"]
    d["filament_flow_ratio"]=[flow]*len(v) if isinstance(v,list) else flow
    json.dump(d,open(fil,"w"),indent=1)
if bedtemp:
    key={"Textured PEI Plate":"textured_plate_temp","Cool Plate":"cool_plate_temp",
         "Engineering Plate":"eng_plate_temp","High Temp Plate":"hot_plate_temp",
         "Smooth PEI Plate":"hot_plate_temp"}[bed]
    d=json.load(open(fil))
    for k in (key,key+"_initial_layer"):
        v=d.get(k); d[k]=[bedtemp]*len(v) if isinstance(v,list) else bedtemp
    json.dump(d,open(fil,"w"),indent=1)
if flscale:
    d=json.load(open(proc)); s=float(flscale)
    for k in ("initial_layer_speed","initial_layer_infill_speed"):
        v=d[k]
        d[k]=[str(float(x)*s) for x in v] if isinstance(v,list) else str(float(v)*s)
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
