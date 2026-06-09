#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["paho-mqtt>=2.1"]
# ///
"""End-to-end print driver: validate -> slice -> (optionally) print.

Bridges the two sources of truth:
  * LIVE from printer  : material loaded, idle/busy   (queried over MQTT)
  * RECORDED by you    : build plate installed         (bambu/loaded.json)

  uv run bambu/printflow.py MODEL.stl                 # validate + slice + summary (NO print)
  uv run bambu/printflow.py MODEL.stl --print         # ...and start the print
  uv run bambu/printflow.py MODEL.stl --material PLA  # override detected material
  uv run bambu/printflow.py MODEL.stl --plate "Cool Plate"

Safe by default: without --print it never starts the printer.
"""
import argparse, json, os, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import print_job as pj  # reuse get_status / ftps_upload / start_print
import camera           # reuse camera.grab


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def gcode_summary(threemf):
    """Pull temps/time/weight from the sliced 3mf's embedded gcode."""
    out = {}
    with zipfile.ZipFile(threemf) as z:
        g = z.read("Metadata/plate_1.gcode").decode("utf-8", "replace")
    for line in g.splitlines():
        if "total estimated time:" in line and "time" not in out:
            out["time"] = line.split("total estimated time:", 1)[1].strip()
        for key, label in (("; filament_type =", "type"),
                            ("; nozzle_temperature =", "nozzle"),
                            ("; hot_plate_temp =", "bed"),
                            ("; filament used [g] =", "grams"),
                            ("; curr_bed_type =", "plate")):
            if line.startswith(key):
                val = line.split("=", 1)[-1].strip()
                out[label] = val.split(",")[0] if label == "nozzle" else val
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="STL to print")
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--bed-clear", dest="bed_clear", action="store_true",
                    help="confirm the plate is physically CLEAR (required to actually start a print)")
    ap.add_argument("--material", help="override detected material (PLA/PETG/...)")
    ap.add_argument("--plate", help="override recorded plate")
    ap.add_argument("--name", help="job name on printer")
    args = ap.parse_args()

    host = os.environ.get("BAMBU_HOST"); code = os.environ.get("BAMBU_CODE"); serial = os.environ.get("BAMBU_SERIAL")
    if not (host and code and serial):
        sys.exit("ERROR: need BAMBU_HOST/BAMBU_CODE/BAMBU_SERIAL (run via bambu/print.sh)")

    materials = load_json(os.path.join(WS, "slice", "materials.json"))
    loaded = load_json(os.path.join(HERE, "loaded.json"))

    # --- live printer state ---
    print("· reading printer ...")
    state = pj.get_status(host, code, serial)
    gstate = state.get("gcode_state")
    live_mat = (state.get("vt_tray", {}) or {}).get("tray_type")

    material = (args.material or live_mat or loaded.get("material") or "").upper()
    plate = args.plate or loaded.get("plate")

    problems, warnings = [], []
    # cross-check recorded vs live material
    if live_mat and loaded.get("material") and live_mat.upper() != loaded["material"].upper():
        warnings.append(f"loaded.json says {loaded['material']} but printer reports {live_mat} — update loaded.json")
    if args.material and live_mat and args.material.upper() != live_mat.upper():
        warnings.append(f"you forced {args.material} but printer has {live_mat} loaded")
    if material not in materials:
        problems.append(f"no profile for material {material!r} (known: {', '.join(k for k in materials if not k.startswith('_'))})")
    busy = gstate not in ("FINISH", "IDLE", "FAILED", None)
    if busy and args.do_print:
        problems.append(f"printer is busy (state={gstate}) — refuse to start a print")
    elif busy:
        warnings.append(f"printer busy (state={gstate}); will slice but not print")

    spec = materials.get(material, {})
    if spec and plate not in spec.get("plates", []):
        problems.append(f"{material} cannot print on {plate!r}; allowed: {', '.join(spec['plates'])}")

    for w in warnings:
        print(f"  ⚠ {w}")
    if problems:
        print("\n✗ pre-flight failed:")
        for p in problems:
            print(f"   - {p}")
        sys.exit(1)

    # --- slice ---
    stl = os.path.abspath(args.model)
    out_3mf = os.path.splitext(os.path.basename(stl))[0] + ".3mf"
    out_path = os.path.join(os.path.dirname(stl), out_3mf)
    env = dict(os.environ, FILAMENT=spec["filament"], BED=plate)
    print(f"· slicing {os.path.basename(stl)}  [{material} / {plate}]")
    r = subprocess.run([os.path.join(WS, "slice", "slice.sh"), stl, out_3mf], env=env)
    if r.returncode != 0 or not os.path.exists(out_path):
        sys.exit("✗ slice failed")

    g = gcode_summary(out_path)
    print("\n── job ─────────────────────────")
    print(f"  model   {os.path.basename(stl)}")
    print(f"  material {material} ({loaded.get('filament_brand','?')})")
    print(f"  plate   {plate}")
    print(f"  temps   nozzle {g.get('nozzle','?')}°C / bed {g.get('bed','?')}°C")
    print(f"  time    {g.get('time','?')}    filament {g.get('grams','?')} g")
    print("────────────────────────────────")

    if not args.do_print:
        print("✓ sliced & validated. NOT printed (no --print).")
        return

    # Pre-flight: never start a print until the bed is confirmed PHYSICALLY CLEAR.
    # The printer can't sense this, so we force a fresh chamber photo + a deliberate
    # second invocation (--bed-clear) after a human/agent has actually looked.
    if not args.bed_clear:
        shot = os.path.join(os.path.dirname(out_path), "preprint_bed.jpg")
        try:
            n = camera.grab(host, code, shot)
            print(f"\n✋ BED CHECK — captured {n} B -> {shot}")
        except Exception as e:
            print(f"\n✋ BED CHECK — camera grab FAILED ({e}); inspect another way before printing.")
        print("   Confirm the plate is CLEAR (no leftover part/debris). If the view is")
        print("   blocked, raise the bed for a better look — careful, small steps:")
        print('     bambu/gcode_send.py "G91" "G1 Z-15 F600" "G90"   # bed UP ~15mm')
        print("   Once you've SEEN it's clear, re-run with --bed-clear to start.")
        return

    name = args.name or os.path.splitext(out_3mf)[0]
    print(f"· bed confirmed clear; uploading + starting '{name}' ...")
    size, ok = pj.ftps_upload(host, code, out_path, out_3mf)
    print(f"  uploaded {size} B (present={ok})")
    pj.start_print(host, code, serial, out_3mf, name, use_ams=loaded.get("ams", False),
                   bed="textured_plate" if "PEI" in plate or "Textured" in plate else "auto")
    print("✓ print started.")


if __name__ == "__main__":
    main()
