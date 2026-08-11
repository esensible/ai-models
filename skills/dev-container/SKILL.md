---
name: dev-container
description: Launch and manage a remote-control Claude agent inside the ai-models dev container. Use to start/stop the container, fire up a `claude --remote-control` session in it (or resume a prior one by id), or kill it — via the `dc` helper. Ports silvin's `worktree` skill (launch + resume recipe), adapted for ai-models (single container, no worktrees).
---

# ai-models dev-container agent

Run a Claude agent inside the ai-models dev container — the repo mounted at `/workspace`,
controllable from the Claude app/web. The `dc` helper next to this file automates the launch
(the same hard-won recipe as silvin's `.claude/skills/worktree`), so **don't hand-roll the
`script` / `sleep infinity` dance** each time.

## The container (prereq)

Create it from the ai-models devcontainer (`.devcontainer/`, image `ai-models-dev`): VS Code
"Reopen in Container", or `devcontainer up --workspace-folder <repo>`. It bind-mounts the repo
at `/workspace`, provides `git`/`uv`/`python3`/`claude`, and persists claude auth in the
`ai_models_dot_claude` volume (`CLAUDE_CONFIG_DIR=/root/.claude`).

**One-time:** run `claude` once in that container to log in — it persists in the volume. The
`dc` commands **fail loud** if it isn't authenticated.

## The `dc` helper

```
skills/dev-container/dc ls                 # containers + which repo each mounts at /workspace
skills/dev-container/dc start  <container>
skills/dev-container/dc stop   <container>
skills/dev-container/dc agent  <container> # launch a FRESH remote-control session in /workspace
skills/dev-container/dc resume <container> # relaunch, RESUMING the real prior session by id
skills/dev-container/dc kill   <container> # stop the session (container stays up)
```

`dc agent` preflights the container (ai-models at `/workspace`, tools present, claude
authenticated), launches `claude --remote-control ai-models` under a PTY, and **confirms the
bridge reaches `state=connected`** before returning. Then open the Claude app → remote sessions
→ **ai-models** and accept the one-time folder-trust prompt (a human gate — don't script it).

## Restarting — RESUME, never relaunch blank

A session dies when its process is killed or the remote bridge's JWT refresh fails (common
after a `/login` rotates credentials out from under it). **`dc agent` starts a BLANK
conversation** — a blank relaunch orphans all prior context. To get the context back, use
**`dc resume <container>`**: it finds the real prior session (the **biggest** `.jsonl`
transcript under `…/projects/-workspace/` — a blank relaunch leaves a newer *empty* one) and
relaunches with `--resume <id> --remote-control`. On resume, claude first tries the recorded
(now-dead) bridge, then `--remote-control` builds a fresh one — `state=connected` is the
success signal. (`dc resume` handles all of this; `--resume` first, never `--fork-session`,
never `--continue`.)

## Notes

- **No worktrees here.** Unlike silvin (whose `worktree` skill + `wt` tool this ports from),
  ai-models runs a *single* dev container on the repo at `/workspace` — no `wt`/worktree
  machinery. Need parallel branches? Use separate containers, not in-container worktrees.
- **Runs in the mounted `/workspace`** (like silvin), not a fresh clone — so the agent works on
  your actual checkout. `dc` drives a container *by name* and is image-agnostic; override the
  runtime with `DC_RUNTIME=docker`.
- **Root can't skip permissions.** For an *unattended* agent, drop a scoped
  `.claude/settings.local.json` allow-list in the repo (an explicit allow-list, not a blanket
  `--dangerously-skip-permissions`, which is refused as root) — see the personal skill.
- **Full mechanics/gotchas** (PTY, `TERM`, `--debug-file`, kill-by-PID, the `pkill -f`
  self-match trap): the personal **`dev-containers`** skill.
