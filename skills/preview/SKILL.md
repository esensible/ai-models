---
name: "preview"
description: "Render readable preview images of a CAD part with cad/render.py — the lighting/AO/framing settings that actually work headless, and the standing rule to show every change from several angles chosen to highlight it."
---

# preview: showing Andrew what the model looks like

Every model change gets **pictures**, not just numbers. This skill is how to
produce ones that can actually be read. Use it whenever you build or modify
something in `cad/models/` — it pairs with the `model` skill, which owns the
build-and-print half.

```bash
./cad/run.sh cad/render.py cad/out/<part>.stl /path/out.png --view iso
```

Always via `cad/run.sh` (sets `PYOPENGL_PLATFORM=osmesa`, a writable HOME, the
venv). Write previews to the scratchpad, not into the repo.

---

## STANDING RULE: several angles, chosen to show the change

**One render is not a preview.** A single view almost always hides the thing
under discussion — a chamfer sits on the face pointing away, a clip is on the
back, a pocket is edge-on. Andrew has to be able to see the feature being
discussed without asking for another picture.

So, for every change:

1. **Pick the views from the FEATURE, not from habit.** Ask "which direction
   makes this specific edit unmistakable?" and use that as the primary view.
   `--view iso` is a starting point, not an answer.
2. **Send at least two or three**, and say what each one shows. A typical set:
   one overall view for context, one square-on or near-square-on at the
   modified feature, and one from the opposite side if the change has a back.
3. **Compare against the previous state when the change is subtle** — same
   view, before and after, so the difference is visible rather than asserted.
4. **Use a montage** when sending several: render tiles at ~480–520px, label
   each with `PIL.ImageDraw`, paste into one grid PNG. Far easier to compare
   than separate files, and cheaper to look at.
5. If a feature genuinely cannot be seen from outside (an internal cavity, a
   wall thickness), **don't fake it with a render** — section the solid and
   assert on the numbers. See "a render is not proof" below.

---

## Why the renderer is built the way it is

Previews from this script used to be unreadable — "really hard to actually
discern anything" (Andrew, 2026-09-18). Four separate causes, all **measured**
on this build rather than guessed. Don't undo these:

### 1. Point lights on this OSMesa build are ~1000x weaker than nominal
`DirectionalLight` contributes **nothing at all**; `PointLight` needs enormous
intensities to register. Benchmarked: at `I/d² = 15` a white surface renders at
pixel value **13**, while `ambient_light = 0.3` alone renders **133**. Every
earlier preview was therefore lit almost entirely by flat ambient — no
directional shading, no form. The rig now runs the key at `~1950 * dist²` with
ambient down at 0.16.

Intensity is scaled by **camera distance squared** and the lamps sit at that
distance, so `I/d²` — and hence exposure — is invariant to part size, aspect
ratio and `--zoom`.

### 2. Ambient occlusion is what makes a hole look like a hole
Diffuse shading **cannot** distinguish a bore from a flat grey disc: both take
the same light at the same angle. pyrender has no SSAO, so `render.py` computes
it from the depth buffer — reconstruct camera-space positions, derive per-pixel
normals, then measure how much nearby surface lies in the hemisphere **above
each pixel's own normal**.

The normal orientation is the whole point, and two simpler versions were tried
and **measured** first, both useless:
- raw per-direction depth differences → shades every tilted plane, so the part
  washes out to an even grey;
- opposed sample pairs taking `min(d+, d-)` → cancels the tilt but only fires
  in a narrow V-groove. Contribution to a real plug render: **0.4 grey levels
  out of 255**. It was doing nothing.

`--ao-radius` is a fraction of the model's **bounding radius**, not a pixel
count. Sizing it off the pixel grid gave a 0.55mm radius on a part whose
features are 3.7mm — which is how it came to contribute nothing.

### 3. Edge lines
Dark contours at depth discontinuities (silhouettes, bore rims) and at shading
creases (chamfer facet boundaries) — what CAD viewers draw. This is what makes
a 0.9mm chamfer visible at all.

### 4. Frame fitting
The camera distance used to be a fixed multiple of the bounding-**sphere**
radius, which crops anything elongated viewed broadside (the 219mm battery
strap lost both ends) and wastes the frame on anything compact. It now solves
for the exact minimum distance that fits every vertex in the frustum: a
camera-space vertex `u` sits at `z = u_z - d`, so it is inside when
`d >= u_z + |u_x|/tan(xfov/2)` (likewise in y); take the max over all vertices,
plus 6% breathing room.

Measured effect of all of this on the 12-way DT plug, part pixels only —
p5→p95 spread went from **37 to 96** grey levels (shading 37→46, AO +33,
lines +17).

---

## Flags

| flag | default | notes |
|---|---|---|
| `--view` | `angle` | `face` (−Z), `top` (+Z), `angle`, `iso`, `side` |
| `--bg` | `light` | a dark part on a dark ground has no silhouette |
| `--ao` | `0.62` | AO strength; 0 disables |
| `--ao-radius` | `0.058` | fraction of the model's bounding radius — raise for large smooth parts, lower for fine detail |
| `--lines` | `0.75` | edge-line strength; 0 disables |
| `--deboss` | off | grazing key light for **recessed text** |
| `--zoom` | `1.0` | >1 crops in, <1 pulls back (applied after the frame is fitted) |
| `--flip` | off | rotate 180° about X |
| `--color`, `--size`, `--overlay`, `--overlay-color` | | overlay draws a second STL (e.g. a raft, or the mating part) |

Practical picks:
- Bores, chamfers, pockets → `--view iso` or square-on to the face; leave AO on.
- Recessed or raised lettering → `--deboss`, square-on to that face (`--view face`
  or `--view top`, plus `--flip` if it is on the far side).
- Long thin parts → the frame fitter handles them; no need to fiddle `--zoom`.
- Perforated faces can look over-darkened; drop `--ao-radius` toward 0.035.

---

## A render is not proof

Renders are for **Andrew to look at**, never for verifying that geometry is
correct. Two chamfer attempts on the DT plugs looked perfectly fine in a render
while one cut **air** and the other cut **every hole**. Both were caught only by
sectioning the solid and asserting on the result.

So: show the picture, but back every geometric claim with verification-as-code
in the model script — section it, measure it, `assert` it, and print the
numbers. If the two ever disagree, the assert is right.

---

## Files
- `cad/render.py` — the renderer (this skill documents it)
- `cad/run.sh` — the headless wrapper; always use it
- `skills/model/SKILL.md` — building, slicing and printing
