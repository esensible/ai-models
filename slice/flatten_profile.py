#!/usr/bin/env python3
"""Flatten an OrcaSlicer profile by resolving its `inherits` chain.

OrcaSlicer's CLI does not resolve `inherits` when profiles are passed directly via
--load-settings, so leaf profiles are missing parent fields (bed size, extruder
config, ...) and slicing crashes. This merges root->leaf into one self-contained
JSON.  Usage:  flatten_profile.py "<profile name>" <out.json>
"""
import json, os, sys

# Path to OrcaSlicer's bundled Bambu (BBL) profile tree. Override via env if your
# install differs (e.g. the AppImage extraction dir, or a Flatpak resources path).
BASE = os.environ.get("ORCA_PROFILES_DIR", "/opt/squashfs-root/resources/profiles/BBL")
SUBDIRS = ("machine", "process", "filament")
# Only `inherits` must be stripped (we resolve it here). `from`/`instantiation`
# are required by the CLI loader and are kept (leaf value wins via merge order).
DROP = {"inherits"}


def find(name):
    for sub in SUBDIRS:
        p = f"{BASE}/{sub}/{name}.json"
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"profile not found: {name}")


def chain(name):
    """Return [root, ..., leaf] dicts."""
    out = []
    while name:
        d = json.load(open(find(name)))
        out.append(d)
        name = d.get("inherits")
    return list(reversed(out))


# The P1S exposes two *extruder variants* ("Direct Drive Standard" / "High Flow").
# Their presence makes the CLI take update_values_to_printer_extruders_for_multiple_
# filaments, which indexes these arrays against single-element fields (nozzle_diameter)
# and segfaults. Simple single-extruder printers (e.g. Creality) lack these fields
# entirely and slice fine. So for headless slicing we DELETE the variant fields to
# present a clean single-extruder config, and collapse any other 2-element nozzle
# arrays to one.
VARIANT_DELETE = {
    "printer_extruder_variant", "extruder_variant_list", "print_extruder_variant",
    "printer_extruder_id", "print_extruder_id", "master_extruder_id",
    "physical_extruder_map",
}
VARIANT_COLLAPSE = {"nozzle_type", "nozzle_volume"}


def flatten(name, single_variant=True):
    merged = {}
    for d in chain(name):
        for k, v in d.items():
            if k in DROP:
                continue
            merged[k] = v
    merged["name"] = name
    merged.pop("inherits", None)
    if single_variant:
        for k in VARIANT_DELETE:
            merged.pop(k, None)
        for k in VARIANT_COLLAPSE:
            v = merged.get(k)
            if isinstance(v, list) and len(v) > 1:
                merged[k] = v[:1]
    return merged


if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    json.dump(flatten(name), open(out, "w"), indent=1)
    print(f"flattened '{name}' -> {out}")
