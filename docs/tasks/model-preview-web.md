# Task: mobile model-preview web app

## Why
Right now there's no way to **preview a 3D model in a phone browser before printing**. Build a
small web app that lists the models sitting in an S3 bucket and renders a selected one in a
mobile browser, so a model can be eyeballed on a phone before committing a print.

## Scope
Build it under a new top-level **`web/`** directory. Three parts:

1. **`web/frontend/`** — a static, **mobile-first** single-page app:
   - Fetches the model list from the backend (`GET /api/models`) and shows it (name + maybe
     size/date).
   - On selecting a model, renders it in an interactive 3D viewer (orbit/zoom/pan) sized for a
     phone screen.
   - Viewer: **three.js** + its off-the-shelf **`3MFLoader`** (models are `.3mf`). Vendor/pin
     three.js (don't rely on an unpinned CDN — it's served from S3/CloudFront).
2. **`web/backend/`** — a **Python** Lambda (follow `docs/eng/conventions.md`):
   - `GET /api/models` → lists the `.3mf` objects in the models S3 bucket, returns JSON
     (`name`, `size`, `last_modified`, and a URL to fetch the model).
   - **No auth** — this is intentionally public.
   - Thin handler + injected deps + fail-fast config + request-scoped trace id, per the
     conventions. Put the list/format logic in a pure function with `pytest` tests.
3. **`web/infra/`** — Pulumi (TypeScript), following `docs/eng/infra.md` and the Pulumi
   conventions:
   - An **S3 bucket** for models (assume `.3mf` files are already uploaded to it by an external
     process — **model creation/upload is out of scope**), and static hosting for the frontend.
   - **CloudFront** in front, **no auth**. Serve the frontend from S3, the model files from S3
     (public *through CloudFront*), and route `/api/*` to the Lambda (attach it with
     `CfnOriginBehavior`).
   - Serving the `.3mf` bytes: prefer letting CloudFront serve them from the S3 origin directly
     (simplest, no-auth); presigned URLs from the Lambda are an acceptable alternative — pick
     one, note why.

## Non-goals
- No modelling, slicing, or upload pipeline — assume models arrive in the bucket already.
- No auth, no login, no user accounts.
- **Do not deploy.** The target AWS account doesn't exist yet. Author the code + infra so it's
  ready to deploy later; don't run `pulumi up`.

## Constraints
- Follow **`docs/eng/conventions.md`** (error handling, tracing, Lambda shape, Pulumi rules) and
  **`docs/eng/infra.md`** (use the published `@silvin-ai/infra-*` components; don't hand-roll
  what they provide). These docs are the contract — if something's ambiguous, follow them, and
  if they're wrong/insufficient, flag it in your report rather than inventing a different style.
- **No dependency on any other repo.** Everything you need is these docs + the published
  packages.
- Keep the existing CAD/print tooling untouched.

## Definition of done (what to report)
- `pytest` green for the backend's pure core.
- `web/infra` **type-checks / previews** if creds + the `@silvin-ai` packages are available
  (needs a `read:packages` `GITHUB_TOKEN` for `npm install`, and AWS creds for `pulumi
  preview`). If either is missing, **say so explicitly** and list exactly what's unverified —
  do not skip silently.
- A short `web/README.md`: what it is, how to run the frontend locally, how to deploy later
  (the `.npmrc` + token, the stack config, `pulumi up`).
- A summary of design decisions + any assumptions you couldn't verify.
