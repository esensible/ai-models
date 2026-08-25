#!/usr/bin/env python3
"""Post-slice verification gate: assert a .gcode.3mf matches what we intended.

Catches the failure modes that have actually bitten us: a stale/unsliced file
passing an exists-check, gcode sliced for the wrong nozzle, overrides that
silently didn't apply, a ramp that didn't get injected, and md5-sidecar
mismatches (the printer rejects those at print time — better to know now).

  verify_gcode.py JOB.gcode.3mf EXPECT.json

EXPECT.json (all fields optional except where noted):
{
  "nozzle_diameter":  "0.4",
  "filament_type":    "PETG",
  "nozzle_temp":      255,             // ; nozzle_temperature
  "flow_ratio":       0.94,            // ; filament_flow_ratio
  "bed_temp_first":   90,              // first M140/M190 in the start gcode
  "initial_layer_speed": 25,
  "bed_ramp":         [85, 80, 75, 70],// injected M140 steps from layer 2
  "bbox":             [xmin, ymin, xmax, ymax],  // layer-1 extrusion bounds
  "bbox_tol":         2.0
}
Exit 0 = verified; nonzero with a message = do not print.
"""
import hashlib
import json
import re
import sys
import zipfile

GCODE = "Metadata/plate_1.gcode"
MD5 = "Metadata/plate_1.gcode.md5"
LAYER = re.compile(r"^; layer num/total_layer_count: (\d+)[/,]")


def fail(msg):
    sys.exit(f"VERIFY FAILED: {msg}")


def main():
    path, expect_path = sys.argv[1], sys.argv[2]
    exp = json.load(open(expect_path))

    z = zipfile.ZipFile(path)
    if GCODE not in z.namelist():
        fail(f"no {GCODE} in archive")
    g = z.read(GCODE)
    if MD5 in z.namelist():
        want = z.read(MD5).decode().strip().lower()
        got = hashlib.md5(g).hexdigest()
        if want != got:
            fail(f"md5 sidecar mismatch: sidecar={want} computed={got}")

    text = g.decode("utf-8", "replace")
    lines = text.splitlines()

    # --- header params -------------------------------------------------------
    def header(key):
        pref = f"; {key} ="
        for ln in lines:
            if ln.startswith(pref):
                return ln.split("=", 1)[1].strip()
        return None

    def first_num(val):
        return float(val.split(",")[0]) if val else None

    for key, field in (("nozzle_diameter", "nozzle_diameter"),
                       ("filament_type", "filament_type")):
        if field in exp:
            got = header(key)
            got_first = got.split(",")[0] if got else None
            if got_first != str(exp[field]):
                fail(f"{key}: gcode says {got!r}, expected {exp[field]!r}")
    checks = (("nozzle_temp", "nozzle_temperature"),
              ("flow_ratio", "filament_flow_ratio"),
              ("initial_layer_speed", "initial_layer_speed"))
    for field, key in checks:
        if field in exp:
            got = first_num(header(key))
            if got is None or abs(got - float(exp[field])) > 1e-6:
                fail(f"{key}: gcode says {got}, expected {exp[field]}")

    # --- first bed temp command in the executable start gcode ----------------
    if "bed_temp_first" in exp:
        m = re.search(r"^M140 S(\d+)", text, re.M)
        if not m or int(m.group(1)) != int(exp["bed_temp_first"]):
            fail(f"first M140 is {m.group(1) if m else 'missing'}, "
                 f"expected {exp['bed_temp_first']}")

    # --- injected ramp + layer-1 extrusion bounds ----------------------------
    layer = 0
    seen_ramp = []
    lo = [1e9, 1e9]
    hi = [-1e9, -1e9]
    for ln in lines:
        m = LAYER.match(ln)
        if m:
            layer = int(m.group(1))
            continue
        if layer >= 2 and ln.startswith("M140") and "injected" in ln:
            seen_ramp.append(int(re.search(r"S(\d+)", ln).group(1)))
        if layer == 1 and (ln.startswith("G1") or ln.startswith("G0")) \
                and re.search(r"E[0-9.]", ln):
            mx = re.search(r"X(-?[0-9.]+)", ln)
            my = re.search(r"Y(-?[0-9.]+)", ln)
            if mx:
                x = float(mx.group(1)); lo[0] = min(lo[0], x); hi[0] = max(hi[0], x)
            if my:
                y = float(my.group(1)); lo[1] = min(lo[1], y); hi[1] = max(hi[1], y)

    if "bed_ramp" in exp and seen_ramp != list(exp["bed_ramp"]):
        fail(f"bed ramp in gcode {seen_ramp} != expected {exp['bed_ramp']}")
    if "bbox" in exp:
        tol = float(exp.get("bbox_tol", 2.0))
        want = exp["bbox"]
        got = [lo[0], lo[1], hi[0], hi[1]]
        if lo[0] > hi[0]:
            fail("no layer-1 extrusion found")
        for w, g_, name in zip(want, got, ("xmin", "ymin", "xmax", "ymax")):
            if abs(w - g_) > tol:
                fail(f"layer-1 {name} {g_:.1f} vs expected {w:.1f} (tol {tol})")

    print(f"verified: nozzle={header('nozzle_diameter')} "
          f"type={header('filament_type')} flow={header('filament_flow_ratio')} "
          f"ramp={seen_ramp or 'none'} "
          f"layer1 x {lo[0]:.1f}..{hi[0]:.1f} y {lo[1]:.1f}..{hi[1]:.1f}")


if __name__ == "__main__":
    main()
