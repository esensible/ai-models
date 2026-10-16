#!/usr/bin/env python
"""Headless preview render of an STL -> PNG (pyrender + OSMesa).

  ./cad/run.sh cad/render.py <model.stl> <out.png> [--view ...] [--color R,G,B]

  --view   face | top | angle | iso | side   (face = -Z, top = +Z)
  --bg     light (default) | dark
  --ao / --ao-radius   ambient occlusion strength and radius (radius is a
           fraction of the model's bounding radius, so it is size-independent)
  --lines  edge-line strength
  --deboss grazing key light for recessed text
  --zoom   >1 crops in, <1 pulls back (the frame is fitted to the part first)

Run via cad/run.sh so PYOPENGL_PLATFORM=osmesa and a writable HOME are set.

WHY THIS IS NOT JUST "ADD MORE LIGHTS"
--------------------------------------
Diffuse shading alone cannot distinguish a bore from a flat grey disc: both
are lit by the same lamps at the same angle, so both come out the same value.
Every preview from this script used to fail exactly there -- holes, chamfers
and recesses all read as flat blobs, which is useless for checking whether a
feature was actually cut. Two post-passes off the depth buffer fix it:

  * AMBIENT OCCLUSION -- darkens pixels whose neighbours stand in front of
    them. This is the cue that makes a hole look like a hole; pyrender has no
    SSAO of its own, so we compute it here from the depth buffer.
  * EDGE LINES -- dark contours at depth discontinuities (silhouettes, bore
    rims) and at shading creases (chamfer facet boundaries). This is what CAD
    viewers draw, and it is what makes a 0.9mm chamfer visible at all.

Lighting is then deliberately soft and even: once AO and edges carry the form,
hard lamps only add glare. Background defaults to LIGHT -- a dark part on a
dark ground has no silhouette.
"""
import argparse
import numpy as np
import trimesh
import pyrender


def look_at(eye, target, up=np.array([0, 0, 1.0])):
    f = target - eye
    f = f / np.linalg.norm(f)
    if abs(np.dot(f, up)) > 0.999:          # degenerate: looking straight up/down
        up = np.array([0, 1.0, 0])
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    M = np.eye(4)
    M[:3, 0] = s
    M[:3, 1] = u
    M[:3, 2] = -f
    M[:3, 3] = eye
    return M


def view_positions(depth, yfov, w, h):
    """Camera-space XYZ for every pixel, from the linear depth buffer."""
    ty = np.tan(yfov / 2.0)
    tx = ty * (w / h)
    j = (2.0 * (np.arange(w) + 0.5) / w - 1.0) * tx
    i = (1.0 - 2.0 * (np.arange(h) + 0.5) / h) * ty
    X = depth * j[None, :]
    Y = depth * i[:, None]
    return np.stack([X, Y, -depth], axis=-1).astype(np.float32)


def surface_normals(P, valid):
    """Per-pixel normals from the position buffer (central differences)."""
    dx = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    dy = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    n = np.cross(dx, dy)
    ln = np.linalg.norm(n, axis=-1, keepdims=True)
    n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 1e-9)
    # face the camera (camera looks down -z, so +z points back at it)
    n *= np.sign(n[..., 2:3] + 1e-12)
    return n * valid[..., None]


def occlusion(depth, valid, yfov, scale_px, radius_w):
    """Normal-oriented screen-space AO.

    Occlusion is the fraction of nearby surface that lies in the HEMISPHERE
    ABOVE this pixel's own normal. That orientation is the whole point: a
    tilted flat face has all its neighbours in its own tangent plane, so it
    stays unoccluded however steeply it faces away from the camera, while the
    inside of a bore is surrounded by wall standing above its normal and goes
    properly dark.

    Two simpler versions were tried and measured first, both useless:
      * raw depth difference per direction -- shades every tilted plane, so
        the part washes out to an even grey;
      * opposed sample pairs taking min(d+, d-) -- cancels the tilt, but then
        only fires in a narrow V-groove. Measured contribution to a plug
        render: 0.4 grey levels out of 255. It was doing nothing at all.
    """
    h, w = depth.shape
    P = view_positions(depth, yfov, w, h)
    N = surface_normals(P, valid)
    occ = np.zeros(depth.shape, dtype=np.float32)
    n = 0
    bias = 0.12                             # reject self-occlusion from noise
    for frac in (0.3, 0.55, 0.8, 1.0):
        r = max(1, int(round(scale_px * frac)))
        for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            dy = int(round(r * np.sin(ang)))
            dx = int(round(r * np.cos(ang)))
            S = np.roll(np.roll(P, dy, axis=0), dx, axis=1)
            ok = np.roll(np.roll(valid, dy, axis=0), dx, axis=1)
            v = S - P
            d = np.linalg.norm(v, axis=-1)
            cos = np.divide((v * N).sum(-1), d, out=np.zeros_like(d),
                            where=d > 1e-9)
            # in front of the tangent plane, and close enough to count
            contrib = np.clip(cos - bias, 0.0, 1.0) * (radius_w / (radius_w + d))
            occ += np.where(ok, contrib, 0.0)
            n += 1
    return np.where(valid, np.clip(occ / n * 6.0, 0.0, 1.0), 0.0)


def contours(depth, valid, lum, depth_thresh, lum_thresh):
    """Dark line mask: depth discontinuities + shading creases."""
    def grad(a):
        gx = np.abs(np.diff(a, axis=1, prepend=a[:, :1]))
        gy = np.abs(np.diff(a, axis=0, prepend=a[:1, :]))
        gx2 = np.abs(np.diff(a[:, ::-1], axis=1, prepend=a[:, -1:])[:, ::-1])
        gy2 = np.abs(np.diff(a[::-1, :], axis=0, prepend=a[-1:, :])[::-1, :])
        return np.maximum(np.maximum(gx, gy), np.maximum(gx2, gy2))

    d = np.where(valid, depth, np.nan)
    gd = np.nan_to_num(grad(np.nan_to_num(d, nan=0.0)))
    # the silhouette (valid -> invalid) is a real edge but its depth jump is
    # meaningless, so take it from the mask instead
    sil = grad(valid.astype(np.float32)) > 0.5
    e_depth = np.clip(gd / depth_thresh, 0.0, 1.0)
    e_depth = np.where(sil, 1.0, e_depth)
    e_lum = np.clip(grad(lum) / lum_thresh, 0.0, 1.0) * valid
    return np.clip(np.maximum(e_depth, e_lum * 0.85), 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("out")
    ap.add_argument("--view", default="angle",
                    choices=["face", "top", "angle", "iso", "side"])
    ap.add_argument("--color", default="233,236,241")
    ap.add_argument("--size", default="1100x1100")
    ap.add_argument("--bg", default="light", choices=["light", "dark"])
    ap.add_argument("--deboss", action="store_true",
                    help="grazing key light so recessed text reads (AO and "
                         "edge lines stay on -- they are what make it legible)")
    ap.add_argument("--ao", type=float, default=0.62,
                    help="ambient-occlusion strength, 0 disables")
    ap.add_argument("--ao-radius", type=float, default=0.058,
                    help="AO sampling radius as a fraction of the model's "
                         "bounding radius; raise it for large smooth parts, "
                         "lower it for fine detail")
    ap.add_argument("--lines", type=float, default=0.75,
                    help="edge-line strength, 0 disables")
    ap.add_argument("--overlay", default=None,
                    help="second STL drawn in --overlay-color")
    ap.add_argument("--overlay-color", default="120,128,145")
    ap.add_argument("--zoom", type=float, default=1.0, help="<1 pulls camera back")
    ap.add_argument("--flip", action="store_true",
                    help="rotate 180 deg about X (put the bottom end up top)")
    args = ap.parse_args()

    mesh = trimesh.load(args.stl)
    if args.flip:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    shift = -mesh.bounding_box.centroid
    mesh.apply_translation(shift)
    radius = np.linalg.norm(mesh.bounding_box.extents) / 2.0

    rgb = [int(c) / 255.0 for c in args.color.split(",")]
    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[*rgb, 1.0], metallicFactor=0.0, roughnessFactor=0.50
    )

    if args.bg == "light":
        bg = [0.94, 0.945, 0.955, 1.0]
        amb = [0.16, 0.165, 0.175]
    else:
        bg = [0.11, 0.12, 0.14, 1.0]
        amb = [0.10, 0.105, 0.115]
    if args.deboss:
        amb = [v * 0.80 for v in amb]
    scene = pyrender.Scene(bg_color=bg, ambient_light=amb)
    scene.add(pyrender.Mesh.from_trimesh(mesh, material=material, smooth=False))

    if args.overlay:
        ov = trimesh.load(args.overlay)
        if args.flip:
            ov.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        ov.apply_translation(shift)   # align to the main mesh's centering
        orgb = [int(c) / 255.0 for c in args.overlay_color.split(",")]
        omat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=[*orgb, 1.0], metallicFactor=0.1, roughnessFactor=0.8)
        scene.add(pyrender.Mesh.from_trimesh(ov, material=omat, smooth=False))

    # The clean perforated face points -Z. View it from below (-Z side).
    if args.view == "face":
        direction = np.array([0.06, -0.18, -0.98])   # nearly head-on to the -Z face
    elif args.view == "top":
        direction = np.array([0.06, -0.18, 0.98])    # nearly head-on to the +Z face
    elif args.view == "iso":
        direction = np.array([0.6, -0.7, 0.55])       # 3/4 from above (Z up)
    elif args.view == "side":
        direction = np.array([0.1, -1.0, 0.18])       # near side-profile (Z up)
    else:
        direction = np.array([0.45, -0.55, -0.70])   # 3/4 hero angle
    direction = direction / np.linalg.norm(direction)

    # FIT THE FRAME TO THE ACTUAL PART, not to its bounding sphere. A fixed
    # multiple of the bounding radius crops anything elongated viewed broadside
    # (the 219mm battery strap lost both ends) and wastes most of the frame on
    # anything compact. Camera-space vertex u sits at z = u_z - d, so it is
    # inside the frustum when d >= u_z + |u_x|/tan(xfov/2), likewise in y;
    # taking the max over every vertex gives the exact minimum distance.
    yfov = np.pi / 5.0
    w, h = (int(x) for x in args.size.split("x"))
    ty = np.tan(yfov / 2.0)
    tx = ty * (w / h)
    Rm = look_at(direction * radius * 3.0, np.array([0, 0, 0.0]))[:3, :3]
    verts = np.asarray(mesh.vertices)
    if args.overlay:
        verts = np.vstack([verts, np.asarray(ov.vertices)])
    u = verts @ Rm                      # == (Rm.T @ v) per row
    need = np.maximum(u[:, 2] + np.abs(u[:, 0]) / tx,
                      u[:, 2] + np.abs(u[:, 1]) / ty)
    dist = float(need.max()) * 1.06 / args.zoom     # 6% breathing room
    eye = direction * dist
    cam_pose = look_at(eye, np.array([0, 0, 0.0]))

    scene.add(pyrender.PerspectiveCamera(yfov=yfov), pose=cam_pose)

    # NOTE: pyrender DirectionalLight contributes NOTHING under this OSMesa
    # build, so we use PointLights. Their intensity is nominally candela, but
    # measured on this build a point light needs ~1000x the "obvious" value to
    # matter: at I/d^2 = 15 a white surface renders at pixel value ~13, while
    # ambient 0.3 alone renders ~133. Every earlier preview from this script
    # was therefore lit almost entirely by AMBIENT -- flat, formless, and the
    # direct cause of "can't discern anything". The coefficients below are
    # picked so the key contributes ~100/255 and ambient only ~45, i.e. the
    # lights actually model the form.
    #
    # Intensity is scaled by the camera distance squared and the lamps sit at
    # that distance, so I/d^2 -- and hence exposure -- is invariant to part
    # size, aspect ratio and --zoom.
    # Scale by the CAMERA DISTANCE, not the model radius: now that the frame
    # is fitted to the part, those two diverge for elongated shapes and only
    # I/d^2 keeps exposure constant.
    P = dist * dist
    if args.deboss:
        lights = [((0.85, 0.45, -0.28), 2400.0 * P),  # grazing key
                  ((-0.45, -0.25, -0.85), 500.0 * P),
                  ((-0.2, 0.7, 0.4), 320.0 * P)]
    else:
        lights = [((0.45, -0.60, 0.80), 1950.0 * P),  # key, high 3/4
                  ((-0.80, -0.35, 0.15), 320.0 * P),  # fill, opposite + level
                  ((0.05, 0.75, -0.45), 200.0 * P),   # rim, behind/below
                  ((-0.1, -0.9, -0.3), 130.0 * P)]    # bounce into the underside
    for vec, intensity in lights:
        v = np.array(vec); v = v / np.linalg.norm(v)
        scene.add(pyrender.PointLight(color=[1, 1, 1], intensity=intensity),
                  pose=look_at(v * dist, np.array([0, 0, 0.0])))

    r = pyrender.OffscreenRenderer(w, h)
    color, depth = r.render(scene)
    r.delete()

    img = color.astype(np.float32) / 255.0
    valid = depth > 0
    if valid.any():
        lum = img[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        # world size of one pixel at the part, used to set both thresholds in
        # real units so they do not drift with model size or --zoom
        px_w = (2.0 * dist * np.tan(np.pi / 10.0)) / h

        if args.ao > 0:
            # AO radius is set in MODEL units, not pixels: it must span a real
            # feature (a 3.7mm bore, a 0.9mm chamfer) to see anything. Sizing
            # it off the pixel grid instead gave a 0.55mm radius here and the
            # whole pass contributed 0.4 grey levels out of 255 -- measured,
            # not guessed. Being model-relative also makes it invariant to
            # --size and --zoom.
            ao_r_w = radius * args.ao_radius
            scale_px = float(np.clip(ao_r_w / px_w, 3.0, h / 12.0))
            ao = occlusion(depth, valid, yfov=np.pi / 5.0,
                           scale_px=scale_px, radius_w=ao_r_w)
            img[..., :3] *= (1.0 - args.ao * ao)[..., None]

        if args.lines > 0:
            e = contours(depth, valid, lum,
                         depth_thresh=px_w * 2.5,
                         lum_thresh=0.13)
            img[..., :3] *= (1.0 - args.lines * e)[..., None]

    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(args.out)
    print(f"wrote {args.out}  ({w}x{h}, view={args.view}, bg={args.bg}, "
          f"ao={args.ao}, lines={args.lines})")


if __name__ == "__main__":
    main()
