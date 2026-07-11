# AGENTS.md — ai-models

**This repo is the single, canonical home for all 3D modelling and printing work.**
Multiple agents share it. Keep it focused and clean.

## Scope — what belongs here

✅ Everything model/printer related:
- build123d parametric models + the headless render/preview pipeline (`cad/`)
- slicing (OrcaSlicer wrappers, profiles, materials) (`slice/`)
- Bambu P1S control: status, camera, send/print, g-code (`bambu/`)
- the `model` AgentSkill (`skills/model/`)
- a **browser app to preview models before printing** (`web/`) — a service subtree (see below)
- supporting tooling, scripts, and docs for any of the above

## Out of scope — never commit these here

❌ Anything personal or environment-specific:
- personal/health data (e.g. CLL, symptoms) — belongs in the private workspace, never here
- OpenClaw memory / `SOUL.md` / `MEMORY.md` / identity / agent config
- secrets & local state: `*.env`, printer access codes, `bambu/loaded.json`,
  `bambu/printer.env`, camera snapshots (all gitignored — keep it that way)
- anything unrelated to modelling/printing

If you're an OpenClaw agent: model/print code is NOT replicated into the workspace.
It lives **only** here. The workspace loads the skill via `skills.load.extraDirs`
pointing at `ai-models/skills`. Don't copy this code back into the workspace.

## Service & infra work (`web/`, Lambdas, Pulumi)

New backend/infra code follows a different discipline from the CAD scripts — a small set of
engineering conventions distilled into this repo (self-contained; don't reach for external repos):
- `docs/eng/conventions.md` — fail-loud error handling (no silent fallbacks), structured
  tracing, Lambda shape (thin handler + injected deps + fail-fast config), Pulumi rules.
- `docs/eng/infra.md` — the shared `@silvin-ai/infra-*` Pulumi components + how to consume them.
- `docs/tasks/` — task briefs (e.g. `model-preview-web.md`).

The CAD/print tooling under `cad/`/`slice/`/`bambu/` predates these and is exempt.

## Layout
- `cad/`    — build123d models (`cad/models/*.py`), `run.sh`, `setup.sh`, `render.py`
- `slice/`  — `slice.sh`, `flatten_profile.py`, `materials.json`
- `bambu/`  — printer control: `printflow.py`, `print_job.py`, `camera.py`, `send.sh`, `run.sh`, …
- `print.sh` — one-command driver: validate → slice → (optional) print
- `skills/model/SKILL.md` — the agent skill that ties it together (read this first)
- `web/`    — model-preview browser app (frontend + Python Lambda + Pulumi infra)
- `docs/eng/`, `docs/tasks/` — engineering conventions + task briefs for service/infra work

## Quick start
See `README.md` (env setup) and `skills/model/SKILL.md` (full workflow + safety rules).
Printing is physical and irreversible — follow the bed-clear / material-check gates
in the skill before ever starting a print.
