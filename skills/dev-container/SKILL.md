---
name: dev-container
description: Run a remote-controllable Claude Code agent in a dev container against this (ai-models) repo. Use to start/stop a container or launch/stop a `claude --remote-control` session for an ai-models branch via the `dc` helper. Defers to the personal `dev-containers` skill for the underlying mechanics and gotchas.
---

# ai-models dev-container agent

Launch a Claude agent inside a Podman/Docker dev container — checked out on an ai-models
branch and controllable from the Claude app/web. The `dc` helper next to this file wraps the
mechanics; the personal **`dev-containers`** skill holds the full, repo-agnostic playbook.

## The `dc` helper

```
skills/dev-container/dc ls                         # containers + which repo each hosts
skills/dev-container/dc start <container>
skills/dev-container/dc stop  <container>
skills/dev-container/dc agent <container> [<branch>]   # clone/update ai-models + launch agent (default: main)
skills/dev-container/dc kill  <container>          # stop the agent session (leaves the container up)
```

`dc agent`:
- **fails loud** if the container lacks `git`/`node`/`uv`/`python3`/`claude` (per
  `docs/eng/conventions.md`);
- clones `esensible/ai-models` to `/root/ai-models` in the container (or updates an existing
  checkout) on the requested branch, and sets the `sensible-claw` git identity;
- launches `claude --remote-control ai-models` with the headless PTY recipe and **confirms the
  remote bridge reaches `state=connected`** before returning.

Then open the Claude app → remote sessions → **ai-models**, and **accept the one-time
folder-trust prompt** on first connect (a human gate — don't script around it).

## Notes

- **Image-agnostic, no external-repo dependency.** `dc` drives a container *by name*; it does
  not prescribe a base image. Provide a container that already has the toolchain and an
  authenticated `claude`. Override the runtime with `DC_RUNTIME=docker`.
- **Root containers can't skip permissions.** Claude refuses `--dangerously-skip-permissions`
  as root. For unattended runs, add a scoped `.claude/settings.local.json` allow-list to the
  checkout (an explicit allow-list, *not* a blanket skip) — see the personal skill for the
  exact shape.
- ai-models ships no committed `.devcontainer`. If you add one later, keep `dc`
  image-agnostic (drive by container name, don't hardcode an image).

## When there's no `dc` (or you're in another repo)

Fall back to the personal **`dev-containers`** skill. It does all of this by hand and is
written to work with or without repo-local tooling — check for a repo helper first, otherwise
apply the recipes directly.
