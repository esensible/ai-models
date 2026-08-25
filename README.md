# ai-models

Parametric 3D models authored in code with [build123d](https://github.com/gumyr/build123d),
plus everything needed to take them to a print on a Bambu Lab P1S, headless and
LAN-only: preview rendering (pyrender + OSMesa), OrcaSlicer CLI slicing, and
printer control over MQTT/FTPS.

## Layout

- `cad/` — models (`cad/models/`, one script or directory per part), the
  headless render pipeline (`render.py`), env setup (`setup.sh`,
  `requirements.txt`). Everything runs through `./cad/run.sh`; exports land in
  the git-ignored `cad/out/`.
- `slice/` — STL → printable `.gcode.3mf`: `slice.sh` (OrcaSlicer CLI + its
  quirk workarounds), per-filament configs (`filaments/`), nozzle→profile map
  (`nozzles.json`), placement/post-processing/verification tools.
- `printer/` — P1S LAN control: status, chamber camera, g-code, FTPS/MQTT
  send, and the print driver (`printflow.py`).
- `print.sh` — the one-command front door to the print driver.
- `skills/model/SKILL.md` — **the operational runbook for agents**: modelling
  conventions, slice/print gotchas, safety rules. Read it before doing
  anything non-trivial; it is the detail this README deliberately omits.

## Up and running

```bash
# Dev container users: .devcontainer/ provides all of this — skip to step 3.
sudo apt install libosmesa6 libgl1 libglu1-mesa   # headless GL
./cad/setup.sh                                    # build the venv (needs uv)

./cad/run.sh cad/models/<model>.py                # build + export a model
./cad/run.sh cad/render.py cad/out/<part>.stl cad/out/preview.png
```

Models with engraved/embossed text need fonts once: `./cad/fonts/fetch.sh`.

## Printing

`./print.sh <part>.stl` prepares and verifies a job; `--print` gates the
actual start behind a bed-photo check. Two things the printer cannot tell you,
so the repo never guesses them:

- **Physical state is user-declared.** `printer/loaded.json` (git-ignored)
  records the loaded filament, plate, and nozzle. If it's missing or stale,
  ask the user — never trust the printer's own filament/nozzle reports.
- **Credentials** (host / access code / serial) load from `$BAMBU_ENV_FILE`
  (a named volume in the dev container) — never the repo.

## License

See [LICENSE](LICENSE).
