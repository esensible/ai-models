#!/usr/bin/env python
"""Headless preview render of an STL -> PNG (pyrender + OSMesa).

  ./cad/run.sh cad/render.py <model.stl> <out.png> [--view face|angle] [--color R,G,B]

Run via cad/run.sh so PYOPENGL_PLATFORM=osmesa and a writable HOME are set.
"""
import argparse
import numpy as np
import trimesh
import pyrender


def look_at(eye, target, up=np.array([0, 0, 1.0])):
    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    M = np.eye(4)
    M[:3, 0] = s
    M[:3, 1] = u
    M[:3, 2] = -f
    M[:3, 3] = eye
    return M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("out")
    ap.add_argument("--view", default="angle", choices=["face", "angle", "iso", "side"])
    ap.add_argument("--color", default="210,215,222")
    ap.add_argument("--size", default="1100x1100")
    ap.add_argument("--deboss", action="store_true",
                    help="low ambient + grazing key light so recessed text reads")
    ap.add_argument("--overlay", default=None, help="second STL drawn in --overlay-color")
    ap.add_argument("--overlay-color", default="30,32,38")
    ap.add_argument("--zoom", type=float, default=1.0, help="<1 pulls camera back")
    args = ap.parse_args()

    mesh = trimesh.load(args.stl)
    shift = -mesh.bounding_box.centroid
    mesh.apply_translation(shift)
    radius = np.linalg.norm(mesh.bounding_box.extents) / 2.0

    rgb = [int(c) / 255.0 for c in args.color.split(",")]
    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[*rgb, 1.0], metallicFactor=0.25, roughnessFactor=0.55
    )

    amb = [0.10, 0.11, 0.12] if args.deboss else [0.28, 0.30, 0.33]
    scene = pyrender.Scene(bg_color=[0.09, 0.10, 0.12, 1.0], ambient_light=amb)
    scene.add(pyrender.Mesh.from_trimesh(mesh, material=material, smooth=False))

    if args.overlay:
        ov = trimesh.load(args.overlay)
        ov.apply_translation(shift)   # align to the main mesh's centering
        orgb = [int(c) / 255.0 for c in args.overlay_color.split(",")]
        omat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=[*orgb, 1.0], metallicFactor=0.1, roughnessFactor=0.8)
        scene.add(pyrender.Mesh.from_trimesh(ov, material=omat, smooth=False))

    # The clean perforated face points -Z. View it from below (-Z side).
    if args.view == "face":
        direction = np.array([0.06, -0.18, -0.98])   # nearly head-on to the face
        dist = radius * 2.3
    elif args.view == "iso":
        direction = np.array([0.6, -0.7, 0.55])       # 3/4 from above (Z up)
        dist = radius * 2.6
    elif args.view == "side":
        direction = np.array([0.1, -1.0, 0.18])       # near side-profile (Z up)
        dist = radius * 2.6
    else:
        direction = np.array([0.45, -0.55, -0.70])   # 3/4 hero angle
        dist = radius * 2.5
    dist = dist / args.zoom
    direction = direction / np.linalg.norm(direction)
    eye = direction * dist
    cam_pose = look_at(eye, np.array([0, 0, 0.0]))

    scene.add(pyrender.PerspectiveCamera(yfov=np.pi / 5.0), pose=cam_pose)

    if args.deboss:
        # grazing key (rakes across the face to shadow recess walls) + soft fill
        lights = [((0.85, 0.45, -0.28), 5.5), ((-0.4, -0.2, -0.9), 1.2)]
    else:
        lights = [((0.4, -0.6, -1.0), 4.2), ((-0.7, -0.3, -0.6), 2.0),
                  ((0.0, 0.5, 0.8), 1.6)]
    for vec, intensity in lights:
        v = np.array(vec); v = v / np.linalg.norm(v)
        scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=intensity),
                  pose=look_at(v * dist, np.array([0, 0, 0.0])))

    w, h = (int(x) for x in args.size.split("x"))
    r = pyrender.OffscreenRenderer(w, h)
    color, _ = r.render(scene)
    r.delete()

    from PIL import Image
    Image.fromarray(color).save(args.out)
    print(f"wrote {args.out}  ({w}x{h}, view={args.view})")


if __name__ == "__main__":
    main()
