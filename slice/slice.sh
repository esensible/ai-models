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
#   * ARRANGE=0 placements pick up a systematic -2.0mm Y shift in the gcode
#     (X exact). Raft+part pairs sliced through this pipeline stay mutually
#     aligned; for absolute-position work, verify the gcode extrusion bbox.
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
# BRIM=0 forces NO brim (profile defaults may be auto_brim, which ignores brim_width
# and auto-scales with part height — bit us on the raft-margin overrun 2026-08-27).
BRIM="${BRIM:-}"
[ -n "$BRIM" ] && echo "[slice] brim: ${BRIM}mm (0 = none)"
# SUPPORT: off (default) | tree = tree(auto) organic-style | normal = normal(auto)
# grid-style (contiguous sheet bases — use over a dissimilar-material raft, where
# organic tree trunks shear off the weak release interface; learned 2026-08-27).
# Both grow from the build plate only (interior shelves print as short bridges).
# SUPPORT_ANGLE: overhang threshold in degrees (default Orca 30). Lower = fewer
# supports; ~15 limits trees to near-horizontal ceilings (e.g. an enclosure roof)
# and skips minor wall-feature overhangs.
SUPPORT="${SUPPORT:-}"
SUPPORT_ANGLE="${SUPPORT_ANGLE:-}"
[ -n "$SUPPORT" ] && echo "[slice] support: $SUPPORT${SUPPORT_ANGLE:+ (threshold ${SUPPORT_ANGLE}deg)}"
# AVOID_CROSSING=1 routes travels AROUND printed walls instead of straight across
# (reduce_crossing_wall). Use for show-face / multi-colour first layers so the nozzle
# doesn't drag strings over visible features. See slice/merge_twocolor.py.
AVOID_CROSSING="${AVOID_CROSSING:-}"
[ -n "$AVOID_CROSSING" ] && echo "[slice] avoid crossing walls: on"
# FUZZY=1: fuzzy skin on EXTERNAL walls only (texture look; hides layer lines).
# LAYER_TIME: minimum seconds per layer (slow_down_layer_time) -- the printer
# stretches faster layers to this. Use to tame thermal stress on tall thin
# PA parts (short wall layers accumulate heat; see prints.jsonl 2026-08-27).
# FLOW_RATIO: override filament_flow_ratio (all entries).
# BED_TEMP: set the bed temp for the CHOSEN plate type, first layer AND rest
#   (per-layer ramps are a post-processing job; see slice/inject_bed_ramp.py).
# FIRST_SPEED_SCALE: multiply initial_layer_speed / initial_layer_infill_speed.
# INFILL: sparse_infill_density percent (e.g. 100 = solid).
# WALLS: wall_loops (perimeter count). Snap-fit flexures want ALL PERIMETERS,
#   not infill -- an all-wall section deflects ~53% further before breaking at
#   equal mass (snap-fit research, 2026-09-09). A 2mm wall wants >=5.
WALLS="${WALLS:-}"
[ -n "$WALLS" ] && echo "[slice] wall loops: $WALLS"
FLOW_RATIO="${FLOW_RATIO:-}"
BED_TEMP="${BED_TEMP:-}"
FIRST_SPEED_SCALE="${FIRST_SPEED_SCALE:-}"
INFILL="${INFILL:-}"
LAYER_TIME="${LAYER_TIME:-}"
FUZZY="${FUZZY:-}"
[ -n "$FUZZY" ] && echo "[slice] fuzzy skin: external walls"
[ -n "$FLOW_RATIO" ] && echo "[slice] flow ratio: $FLOW_RATIO"
[ -n "$BED_TEMP" ] && echo "[slice] bed temp override: ${BED_TEMP}C (first layer + rest)"
[ -n "$FIRST_SPEED_SCALE" ] && echo "[slice] first-layer speed scale: $FIRST_SPEED_SCALE"
[ -n "$INFILL" ] && echo "[slice] infill density: ${INFILL}%"
[ -n "$LAYER_TIME" ] && echo "[slice] min layer time: ${LAYER_TIME}s"
python3 - "$PROF/machine.json" "$PROF/process.json" "$PROF/filament.json" "$BED" "$BRIM" "$AVOID_CROSSING" "$FLOW_RATIO" "$BED_TEMP" "$FIRST_SPEED_SCALE" "$INFILL" "$SUPPORT" "$SUPPORT_ANGLE" "$LAYER_TIME" "$FUZZY" "$WALLS" <<'PY'
import json,sys
mach,proc,fil,bed,brim,avoid,flow,bedtemp,flscale,infill,support,supangle,laytime,fuzzy,walls=sys.argv[1:16]
if walls:
    d=json.load(open(proc)); d["wall_loops"]=str(walls)
    json.dump(d,open(proc,"w"),indent=1)
if fuzzy:
    d=json.load(open(proc))
    d["fuzzy_skin"]="external"; d["fuzzy_skin_thickness"]="0.3"
    d["fuzzy_skin_point_distance"]="0.8"
    json.dump(d,open(proc,"w"),indent=1)
if laytime:
    d=json.load(open(fil))
    v=d.get("slow_down_layer_time")
    d["slow_down_layer_time"]=[laytime]*len(v) if isinstance(v,list) else laytime
    d["slow_down_for_layer_cooling"]=["1"]*len(d.get("slow_down_for_layer_cooling",["1"]))
    json.dump(d,open(fil,"w"),indent=1)
for f in (mach,proc):
    d=json.load(open(f)); d["curr_bed_type"]=bed; json.dump(d,open(f,"w"),indent=1)
if brim == "0":
    d=json.load(open(proc)); d["brim_type"]="no_brim"; json.dump(d,open(proc,"w"),indent=1)
elif brim:
    import os as _os
    _bt = "outer_and_inner" if _os.environ.get("BRIM_INNER") else "outer_only"
    d=json.load(open(proc)); d["brim_type"]=_bt; d["brim_width"]=str(brim)
    # gap 0: the brim must FUSE to the part foot to resist lift. A 0.1 gap
    # left the brim detached from the base on both PA and ASA (user-observed,
    # 2026-08-28) -- the part lifted while its brim stayed down. Trade-off:
    # brim removal needs a knife.
    d["brim_object_gap"]="0"; json.dump(d,open(proc,"w"),indent=1)
if support in ("tree", "normal"):
    d=json.load(open(proc))
    d["enable_support"]="1"
    if support == "tree":
        d["support_type"]="tree(auto)"; d["support_style"]="organic"
    else:
        d["support_type"]="normal(auto)"; d["support_style"]="grid"
    d["support_on_build_plate_only"]="1"
    if supangle: d["support_threshold_angle"]=str(supangle)
    json.dump(d,open(proc,"w"),indent=1)
elif support:
    sys.exit(f"unknown SUPPORT value {support!r} (use 'tree', 'normal' or leave unset)")
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
if infill:
    d=json.load(open(proc)); d["sparse_infill_density"]=str(infill)
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
