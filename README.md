# ai-models

Parametric 3D models authored in code with [build123d](https://github.com/gumyr/build123d)
(Python), plus a **headless render pipeline** that previews them as PNGs on a machine
with no display (pyrender + OSMesa software GL).

These models are the front end of a model → preview → slice → **print** workflow that
drives an FDM 3D printer. This repo holds the modelling and preview side; printer- and
toolchain-specific configuration is kept out by design.

## Models

| Script | What it is |
| --- | --- |
| `cad/models/cube20.py` | 20&nbsp;mm calibration cube |
| `cad/models/tube.py` | Plain parametric tube |
| `cad/models/spacers.py` | Cylindrical spacers — parametric ID/OD/length, optional 45° cut end |
| `cad/models/wheel.py` | Wheel with twin flanges and a bearing seat |
| `cad/models/pin_cone.py` | Cone with a coaxial bore + a vertical slice and edge fillets |
| `cad/models/speaker_cover.py` | Round speaker cover with a perforation field |
| `cad/models/speaker_cover_text.py` | Speaker cover with large face text + a golden-spiral perforation field |
| `cad/models/speaker_plate.py` | Flat speaker mounting plate |
| `cad/models/test_plate.py` | Minimal test part (pipeline smoke test) |

Most scripts are parametric — run with `--help` to see options (diameters, lengths,
text, etc.) and export STL/3MF.

## Quick start

```bash
# 1. System GL libraries for headless rendering (Debian/Ubuntu names):
sudo apt install libosmesa6 libosmesa6-dev libgl1 libglu1-mesa

# 2. Build the Python env (requires uv: https://github.com/astral-sh/uv):
./cad/setup.sh

# 3. Fonts used for engraved/embossed text (fetched, not vendored):
./cad/fonts/fetch.sh

# 4. Run a model — exports to cad/out/ and can render a preview PNG:
./cad/run.sh cad/models/speaker_cover_text.py --diameter 130 --line1 Hello --line2 World
./cad/run.sh cad/render.py cad/out/speaker_cover_text.stl cad/out/preview.png --view face
```

`cad/run.sh` wraps the venv with `PYOPENGL_PLATFORM=osmesa` and a writable cache HOME so
rendering works with no display attached.

## Notes

- Generated artifacts (`cad/out/`, STL/3MF/G-code, PNGs) and the venv are git-ignored.
- Fonts are fetched from Google Fonts (OFL / Apache) rather than vendored — see
  `cad/fonts/fetch.sh`. Proprietary fonts are never committed.

## License

See [LICENSE](LICENSE).
