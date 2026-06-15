#!/usr/bin/env python
"""Tie loose islands (stencil letter-counters) back to the main body with bridges.

Cutting closed letters clean through leaves their centers (the middle of an 'a',
'e', ...) as free-floating pieces that fall out. This finds those islands and
fuses a small bridge from each to the nearest body material so the letters hold.

  ./cad/run.sh cad/bridge_islands.py in.stl out.stl [--min-vol 1.5] [--width 1.6]
"""
import argparse
import numpy as np
import trimesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--min-vol", type=float, default=2.0,
                    help="components smaller than this (cm^3) are treated as islands to bridge")
    ap.add_argument("--width", type=float, default=1.8, help="bridge width (mm)")
    args = ap.parse_args()

    m = trimesh.load(args.inp)
    parts = m.split(only_watertight=False)
    if len(parts) <= 1:
        m.export(args.out)
        print("single body, nothing to bridge")
        return
    parts = sorted(parts, key=lambda p: -p.volume)
    main_body = parts[0]
    islands = [p for p in parts[1:] if p.volume / 1000.0 < args.min_vol]
    big = [p for p in parts[1:] if p.volume / 1000.0 >= args.min_vol]
    if big:
        print(f"WARN: {len(big)} large disconnected bodies (not bridged) — check the design")

    zmid = m.bounding_box.centroid[2]
    zext = m.bounding_box.extents[2]
    solids = [main_body, *parts[1:]]
    mv = main_body.vertices            # vertex-based nearest (no rtree needed)
    bridges = []
    for isl in islands:
        iv = isl.vertices
        # nearest vertex pair between island and main body (project to XY)
        d2 = ((iv[:, None, :2] - mv[None, :, :2]) ** 2).sum(-1)
        ii, jj = np.unravel_index(np.argmin(d2), d2.shape)
        p0, p1 = iv[ii], mv[jj]
        seg = (p1 - p0).astype(float); seg[2] = 0
        gap = np.linalg.norm(seg)
        d = seg / (gap + 1e-9)
        L = gap + 2.0                  # overlap well into both pieces
        box = trimesh.creation.box(extents=[L, args.width, zext + 0.2])
        ang = np.arctan2(d[1], d[0])
        box.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
        mid = (p0 + p1) / 2.0
        box.apply_translation([mid[0], mid[1], zmid])
        bridges.append(box)
        print(f"  bridge: island@({isl.bounding_box.centroid[0]:.0f},{isl.bounding_box.centroid[1]:.0f}) gap~{gap:.1f}mm")

    try:
        combined = trimesh.boolean.union(solids + bridges)
        note = f"unioned, watertight={combined.is_watertight} bodies={combined.body_count}"
    except Exception as e:
        combined = trimesh.util.concatenate(solids + bridges)
        note = f"concatenated (no boolean engine: {type(e).__name__}); slicer will union overlaps"
    combined.export(args.out)
    print(f"bridged {len(islands)} islands -> {args.out}  [{note}]")


if __name__ == "__main__":
    main()
