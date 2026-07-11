# Shared infrastructure components

Cloud infra here is built on a set of **published, versioned Pulumi packages** — reuse them
instead of hand-rolling CloudFront/Lambda/S3 wiring. They arrive as normal npm dependencies
from a private registry; **this repo has no source dependency on the repo that produces them.**

## The packages

Published to **GitHub Packages** under the `@silvin-ai` scope:

| Package | Provides |
|---|---|
| `@silvin-ai/infra-providers` | Custom Pulumi dynamic providers: **`CfnOriginBehavior`** (add/update a CloudFront origin + cache behavior on an existing distribution, non-destructively) and `GoLambdaBuilder` (Go→arm64 Lambda zip). |
| `@silvin-ai/infra-components` | Higher-level components: **`CfnDistro`** (CloudFront + S3 + ACM + Route53 + signed-cookie key groups), `WebSocketService`, plus `openai/` and bootstrap helpers. |
| `@silvin-ai/infra-utils` | `createNamer(prefix)` → stable, hashed resource names. |

## Consuming them

1. Add an `.npmrc` at the Pulumi project root binding the scope to the registry, plus a token
   with `read:packages`:
   ```
   @silvin-ai:registry=https://npm.pkg.github.com
   //npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
   ```
   (`GITHUB_TOKEN` = a GitHub PAT with `read:packages`; keep it in the env, never commit it.)
2. Depend on them by version in `package.json`, e.g. `"@silvin-ai/infra-components": "^1.0.0"`,
   `"@silvin-ai/infra-providers": "^1.0.0"`, `"@silvin-ai/infra-utils": "^1.0.0"`.
3. Import and use:
   ```typescript
   import { CfnOriginBehavior } from "@silvin-ai/infra-providers";
   import { CfnDistro } from "@silvin-ai/infra-components";
   import { createNamer } from "@silvin-ai/infra-utils";
   ```

## Fit for this repo's web app

- **`CfnDistro`** is the natural front door (CloudFront + S3 origin). ⚠️ It also wires ACM +
  Route53 + a hosted zone; if this app is deployed to an account **without** the domain/SSM
  setup `CfnDistro` expects, either supply the config it needs or fall back to a plain
  `aws.cloudfront.Distribution` + S3 origin. **Decide this at `pulumi preview` time** against a
  real account — don't guess; if you can't preview (no creds), author the `CfnDistro` path and
  note the unverified assumption explicitly.
- **`CfnOriginBehavior`** is how you attach the **list/serve Lambda** to the distribution as an
  additional behavior (e.g. path `/api/*`) without recreating it.
- Python Lambdas don't have a shared builder here — package them with a plain
  `aws.lambda.Function` + `pulumi.asset.FileArchive("<lambda-dir>")` (or an equivalent
  packaging step). Keep to the Lambda shape in `docs/eng/conventions.md`.

If a needed capability isn't in these packages, prefer a **small local resource** in this repo
over forking the shared packages — and note it.
