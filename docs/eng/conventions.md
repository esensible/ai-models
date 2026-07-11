# Engineering conventions

Conventions for any **service code** in this repo (Lambdas, Pulumi infra). The CAD/print
tooling under `cad/`, `slice/`, `bambu/` predates these and is out of scope — this governs
new backend/infra work (e.g. `web/`). These are self-contained: follow *this* file, don't
reach for external repos.

The spine of all of it: **fail loud, trace the inputs, never paper over an unknown state.**

## Error handling & failure behaviour

- **No silent fallbacks that hide an unexpected state.** A default is fine for a genuinely
  optional value; it is *not* fine to swallow an unknown/unexpected input or a "can't happen"
  branch. Unknown input **fails loud** (raise), it does not get defaulted-away.
- **Fail fast on missing required config.** A missing required env var / required field is a
  startup or entry error, not a mid-request surprise — resolve and validate config once at the
  entry point and raise immediately if something required is absent. A misconfigured Lambda
  should die on cold start, not halfway through a request.
- **Log an error once, at the source** — where it happens, with the fields that explain it. A
  returned/raised error is control flow for the caller, not a request to re-log it upstream.
  Don't double-report the same failure at every layer.
- **One log line is enough** for a "should never happen" branch. Don't build
  alerting/metrics/retry scaffolding around a branch that means "bug".

## Instrumentation & logging

- **Structured logging, not string interpolation.** Attach context as fields
  (`model_id`, `bucket`, `request_id`, …), don't bake values into the message string. The
  message is the *operation name* ("listed models", not "We listed the models.").
- **Request-scoped trace id on every line.** At the **start of each invocation**, bind a
  request-scoped id (in Lambda, the request id from the context — `context.aws_request_id`)
  onto the logger so every line in that invocation carries it. That id is the unit for tracing
  one execution end-to-end.
- **Trace the initiating event, once, at entry** — enough to *recreate* the scenario (the S3
  key requested, the list prefix, the caller-supplied params). The triggering input is the one
  thing you can't reconstruct after the fact.
- **Scrub secrets.** Never log tokens, signed-URL query strings, credentials, or full auth
  headers — redact or omit (including in the entry-event capture).
- **Don't log the deterministic middle.** If a step follows deterministically from the event +
  state already logged, logging it is noise. Trace inputs and anomalies, not the plumbing.

## Service (Lambda) shape — Python

- **Thin handler.** The Lambda entry point (`handler(event, context)`) only: binds the
  request-scoped logger, parses/validates the event, calls a plain function/class that holds
  the logic, and shapes the response. **No business logic in the handler, no AWS clients built
  per-request.**
- **Dependency injection, resolved once.** Build every dependency (S3 client, bucket name from
  env, config) **at module load / cold start** in a small `Config`/`Deps` object and pass it
  into the logic. No globals mutated per-request, no clients constructed inside the logic, no
  hidden singletons.
- **Config from the environment, validated once.** Read required env vars at startup via a
  helper that raises on absence (don't `os.environ.get(..., default)` a *required* var into a
  silent empty string). Optional values may default, and say so.
- **Pure, testable core.** Put the real logic in functions that take plain inputs and the
  injected deps, so they're unit-testable without AWS. Table-driven tests (`pytest`
  parametrize / stdlib subtests). Don't build tests on mocks of the whole SDK — test the pure
  core.
- **Handlers return a well-formed HTTP response** (status + JSON body) — a client-facing
  failure returns a proper 4xx/5xx with a scrubbed message, it does not leak a stack trace to
  the client (log the detail, return the shape).

## Pulumi / infra conventions (TypeScript)

- **Always** run state-touching commands with `PULUMI_NODEJS_TRANSPILE_ONLY=true`
  (`pulumi up|preview|refresh`) — otherwise tsc full-type-checks every run and can hang for
  minutes on mixed `@pulumi/aws` versions.
- **No hardcoded account ids, regions, bucket names, or profiles.** `Pulumi.<stack>.yaml` holds
  only `aws:region`. Account/region resolve dynamically in code
  (`aws.getCallerIdentityOutput().accountId`, `aws.config.region`). Credentials/profile come
  from the shell (`AWS_PROFILE` / SSO), never the program.
- **Declare resources at top level** — never create a resource inside `.apply()` (that produces
  duplicates + orphaned state). `.apply()` transforms `Output<T>` values only.
- **Export only what a consumer needs** (endpoints, URLs, distribution id) — not raw
  buckets/tables.
- **Reuse the shared infrastructure components** rather than hand-rolling CloudFront/Lambda
  wiring — see `docs/eng/infra.md` for which packages and how to consume them.
- **CloudFront origin/behavior changes** go through the shared `CfnOriginBehavior` provider
  (non-destructive distribution updates). `PreconditionFailed`/ETag errors on it are **routine
  concurrency races** — re-run the same `pulumi up`; it settles in 2–3 iterations.

## Definition of done

A service change here is deliverable when, from the service directory:

```bash
# Python: the pure core has tests and they pass
pytest

# Pulumi (only if you touched infra): it type-checks / previews
PULUMI_NODEJS_TRANSPILE_ONLY=true pulumi preview
```

If a gate can't run in the current environment (e.g. no cloud creds, packages not installed),
**say so explicitly** in your report — never skip a gate silently. That's the same
fail-loud principle applied to your own work.
