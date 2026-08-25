#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""Print driver: declared state -> place -> slice -> post-process -> verify -> print.

Operated by the agent (no human CLI ergonomics needed). Sources of truth:
  * printer/loaded.json      USER-DECLARED filament/plate/nozzle (the printer's
                             own vt_tray / nozzle_diameter reports are screen-
                             entered, go stale, and are NEVER trusted)
  * slice/filaments/<material>.json   per-filament profiles + proven overrides
  * slice/nozzles.json       nozzle diameter -> machine/process profile names

  uv run printer/printflow.py MODEL.stl                        # full prep, NO print
  uv run printer/printflow.py MODEL.stl --center 129 183       # place bbox centre
  uv run printer/printflow.py MODEL.stl --back-ymax 233        # place at the back
  uv run printer/printflow.py MODEL.stl --brim 10
  uv run printer/printflow.py MODEL.stl --print                # ...and start
  uv run printer/printflow.py MODEL.stl --print --bed-clear    # skip photo gate
                                                               # (someone LOOKED)

Prep pipeline: place (optional) -> slice.sh (profiles + overrides from config)
-> inject bed ramp (if configured) -> repack 3mf + re-sign md5 -> verify_gcode
gate -> upload. The bed soak (overrides.preheat_hold_min at the first-layer bed
temp) is NOT waited on here — the driver starts the heat-up and reports; the
agent owns the timing (no polling loops in tools).

Without --print nothing is started. With --print but not --bed-clear, a fresh
chamber photo is captured and the driver stops — a human/agent must LOOK at it
and re-run with --bed-clear.
"""
import argparse
import json
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import print_job as pj    # ftps_upload / start_print / get_status
import camera             # camera.grab


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def run(cmd, **kw):
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"step failed ({cmd[0]}): exit {r.returncode}")


def gcode_summary(threemf):
    out = {}
    with zipfile.ZipFile(threemf) as z:
        g = z.read("Metadata/plate_1.gcode").decode("utf-8", "replace")
    for line in g.splitlines():
        if "total estimated time:" in line and "time" not in out:
            out["time"] = line.split("total estimated time:", 1)[1].strip()
        for key, label in (("; nozzle_temperature =", "nozzle"),
                           ("; filament used [g] =", "grams")):
            if line.startswith(key):
                out[label] = line.split("=", 1)[-1].strip().split(",")[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="STL to prepare")
    ap.add_argument("--center", nargs=2, type=float, metavar=("X", "Y"))
    ap.add_argument("--back-ymax", type=float)
    ap.add_argument("--brim", type=float)
    ap.add_argument("--plate", help="override the declared plate")
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--bed-clear", action="store_true",
                    help="the plate has been LOOKED at and is clear")
    ap.add_argument("--name")
    args = ap.parse_args()

    host = os.environ.get("BAMBU_HOST")
    code = os.environ.get("BAMBU_CODE")
    serial = os.environ.get("BAMBU_SERIAL")
    if not (host and code and serial):
        sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL (run via print.sh)")

    # --- declared state ------------------------------------------------------
    loaded = load_json(os.path.join(HERE, "loaded.json"))
    material = loaded["material"]
    fil_path = os.path.join(WS, "slice", "filaments", f"{material}.json")
    if not os.path.exists(fil_path):
        sys.exit(f"no filament config for declared material {material!r} "
                 f"(slice/filaments/{material}.json)")
    fil = load_json(fil_path)
    nozzles = load_json(os.path.join(WS, "slice", "nozzles.json"))
    noz_d = loaded["nozzle"]["diameter"]
    if noz_d not in nozzles:
        sys.exit(f"no slice/nozzles.json entry for declared nozzle {noz_d}")
    if noz_d not in fil["profiles"]:
        sys.exit(f"{material} has no filament profile for nozzle {noz_d}")
    plate = args.plate or loaded.get("plate") or fil["default_plate"]
    if plate not in fil["plates"]:
        sys.exit(f"{material} may not print on {plate!r}; allowed: {fil['plates']}")
    ov = fil.get("overrides", {})

    print(f"── declared state (printer/loaded.json, updated {loaded.get('updated', '?')})")
    print(f"   filament {material}: {fil['display']}")
    print(f"   nozzle   {noz_d} {loaded['nozzle'].get('type', '')}")
    print(f"   plate    {plate}")

    # advisory only — NEVER trusted (see memory: filament info from user only)
    state = pj.get_status(host, code, serial)
    live = (state.get("vt_tray", {}) or {}).get("tray_type")
    if live and live.upper() != fil["type"].upper():
        print(f"   ⚠ printer screen claims {live!r} loaded (advisory only; "
              f"if the DECLARATION is wrong, stop and fix loaded.json)")
    busy = state.get("gcode_state") not in ("FINISH", "IDLE", "FAILED", None)
    if busy:
        sys.exit(f"printer is busy (state={state.get('gcode_state')})")

    # --- place ---------------------------------------------------------------
    stl = os.path.abspath(args.model)
    if args.center or args.back_ymax is not None:
        placed = os.path.splitext(stl)[0] + "_placed.stl"
        place = [sys.executable, os.path.join(WS, "slice", "place_stl.py"), stl, placed]
        place += ["--center", str(args.center[0]), str(args.center[1])] if args.center \
                 else ["--back-ymax", str(args.back_ymax)]
        run(place)
        stl = placed

    # --- slice ---------------------------------------------------------------
    base_3mf = os.path.splitext(stl)[0] + ".3mf"
    env = dict(os.environ,
               FILAMENT=fil["profiles"][noz_d],
               MACHINE=nozzles[noz_d]["machine"],
               PROCESS=nozzles[noz_d]["process"],
               BED=plate,
               ARRANGE="0" if (args.center or args.back_ymax is not None) else "")
    if args.brim:
        env["BRIM"] = str(args.brim)
    if "flow_ratio" in ov:
        env["FLOW_RATIO"] = str(ov["flow_ratio"])
    if "bed_temp_first_layer" in ov:
        env["BED_TEMP"] = str(ov["bed_temp_first_layer"])
    if "first_layer_speed_scale" in ov:
        env["FIRST_SPEED_SCALE"] = str(ov["first_layer_speed_scale"])
    run([os.path.join(WS, "slice", "slice.sh"), stl, os.path.basename(base_3mf)], env=env)

    # --- post-process: bed ramp ----------------------------------------------
    out_3mf = base_3mf
    tmp = os.path.splitext(base_3mf)[0]
    if ov.get("bed_ramp_per_layer"):
        raw = tmp + "_plate1.gcode"
        ramped = tmp + "_plate1_ramped.gcode"
        with zipfile.ZipFile(base_3mf) as z, open(raw, "wb") as fh:
            fh.write(z.read("Metadata/plate_1.gcode"))
        run([sys.executable, os.path.join(WS, "slice", "inject_bed_ramp.py"), raw,
             ramped, ",".join(str(t) for t in ov["bed_ramp_per_layer"])])
        out_3mf = tmp + "_final.gcode.3mf"
        run([sys.executable, os.path.join(WS, "slice", "repack_gcode_3mf.py"),
             base_3mf, ramped, out_3mf])

    # --- verify gate ---------------------------------------------------------
    expect = {"nozzle_diameter": noz_d, "filament_type": fil["type"]}
    if "flow_ratio" in ov:
        expect["flow_ratio"] = ov["flow_ratio"]
    if "bed_temp_first_layer" in ov:
        expect["bed_temp_first"] = ov["bed_temp_first_layer"]
    if ov.get("bed_ramp_per_layer"):
        expect["bed_ramp"] = ov["bed_ramp_per_layer"]
    expect_path = tmp + "_expect.json"
    with open(expect_path, "w") as fh:
        json.dump(expect, fh, indent=1)
    run([sys.executable, os.path.join(WS, "slice", "verify_gcode.py"), out_3mf, expect_path])

    g = gcode_summary(out_3mf)
    print(f"── job: {os.path.basename(out_3mf)}  nozzle {g.get('nozzle', '?')}C  "
          f"{g.get('time', '?')}  {g.get('grams', '?')} g")
    if ov.get("preheat_hold_min"):
        print(f"   NOTE: {material} wants a {ov['preheat_hold_min']}min bed soak at "
              f"{ov.get('bed_temp_first_layer', '?')}C before starting — the agent "
              f"owns that timing (M140 via gcode_send.py + its own timer).")

    # --- upload --------------------------------------------------------------
    remote = os.path.basename(out_3mf)
    size, ok = pj.ftps_upload(host, code, out_3mf, remote)
    print(f"── uploaded {size} B (present={ok})")

    if not args.do_print:
        print("✓ prepared & verified. NOT printed (no --print).")
        return

    if not args.bed_clear:
        shot = os.path.join(os.path.dirname(out_3mf), "preprint_bed.jpg")
        try:
            n = camera.grab(host, code, shot)
            print(f"✋ BED CHECK — captured {n} B -> {shot}")
        except Exception as e:
            print(f"✋ BED CHECK — camera grab FAILED ({e}); inspect another way.")
        print("   LOOK at the photo; if clear, re-run with --bed-clear.")
        return

    name = args.name or os.path.splitext(remote)[0]
    pj.start_print(host, code, serial, remote, name, use_ams=loaded.get("ams", False),
                   bed="textured_plate" if "Textured" in plate else "auto")
    print(f"✓ print '{name}' started.")


if __name__ == "__main__":
    main()
