# viewer — 3MF browser + viewer

A general-purpose **3MF file manager and viewer**. `.3mf` files live in S3; a Lambda
keeps a DynamoDB index in sync; a WebSocket directory service lists/renames/deletes
files and mints presigned download URLs; a mobile-first SPA browses and previews them.

> Lives in the `ai-models` repo per request, but it's a self-contained web/infra app
> under `viewer/` — independent of the CAD/print toolchain.

## Architecture

```
            ┌─────────────┐  ObjectCreated/Removed   ┌──────────────┐
   S3  ────▶│  indexer λ  │ ───────────────────────▶ │  DynamoDB    │
 (.3mf)     └─────────────┘    upsert/delete row      │  index table │
   ▲                                  │ broadcast      └──────────────┘
   │ presigned PUT/GET                ▼ "changed"              ▲ query
   │                          ┌───────────────┐  list/rename/  │
   │                          │  directory λ  │  delete/presign │
   │                          │  (API GW WS)  │ ◀───────────────┘
   │                          └───────────────┘
   │                                  ▲ wss://      ▼ presigned GET (off-socket)
   └──────────────────────────  React SPA (S3 + CloudFront)  ──────────────────
```

- **S3 (data bucket):** `.3mf` files in an arbitrary folder structure (`covers/x.3mf`).
- **indexer λ (Python):** S3 event → upsert/delete the file row + ancestor folder rows
  in DynamoDB, then broadcasts a `changed` event to live WS clients.
- **directory λ (Python):** API Gateway **WebSocket**. Routes: `$connect` (token auth),
  `$disconnect`, `$default` (actions: `list`, `rename`, `delete`, `presign`).
- **frontend (React + TS + Vite + Tailwind + three.js):** mobile-first; live file tree
  over the WS, downloads `.3mf` via presigned GET, renders with `3MFLoader`.
- **infra:** Pulumi (TypeScript). **deploy/build:** inside the devcontainer only.

## Data model — DynamoDB (single table)

| field         | type | notes                                                        |
| ------------- | ---- | ------------------------------------------------------------ |
| `pk`          | S    | parent folder, normalised with leading/trailing `/` (`/`, `/covers/`) |
| `sk`          | S    | entry name (`a.3mf`, or `covers` for a subfolder)            |
| `type`        | S    | `file` \| `dir`                                              |
| `s3key`       | S    | full S3 key (files only)                                     |
| `size`        | N    | bytes (files only)                                           |
| `mtime`       | S    | ISO-8601 last-modified (files only)                          |
| `etag`        | S    | S3 ETag (files only)                                         |

Listing a folder = `Query(pk = <folder>)`. The indexer also upserts a `dir` row for each
ancestor so subfolders show up. Connection IDs are stored as `pk="$conn"`, `sk=<id>`.

## WebSocket protocol (JSON)

Client → server:
```jsonc
{ "action": "list",    "path": "/covers/" }
{ "action": "rename",  "from": "/covers/a.3mf", "to": "/covers/b.3mf" }
{ "action": "delete",  "path": "/covers/a.3mf" }
{ "action": "presign", "path": "/covers/a.3mf" }   // download URL, off-socket
```
Server → client:
```jsonc
{ "type": "list",    "path": "/covers/", "entries": [ { "name","type","size","mtime","key" } ] }
{ "type": "presign", "path": "/covers/a.3mf", "url": "https://…", "expiresIn": 900 }
{ "type": "changed", "path": "/covers/" }          // broadcast → clients refresh
{ "type": "error",   "message": "…" }
```
Auth: `$connect` validates `?token=<shared-secret>` against the configured API token.

## Lambda environment

| var            | used by      | value                                            |
| -------------- | ------------ | ------------------------------------------------ |
| `TABLE_NAME`   | both         | DynamoDB table                                   |
| `BUCKET_NAME`  | both         | data bucket                                      |
| `WS_ENDPOINT`  | indexer      | `https://<api>.execute-api.<region>.amazonaws.com/<stage>` |
| `API_TOKEN`    | directory    | shared secret for `$connect`                     |
| `PRESIGN_TTL`  | directory    | presigned-URL seconds (default 900)              |

## Build & deploy — devcontainer only (no host clutter)

Built with **podman**, orchestrated with the **devcontainer CLI**:

```bash
# from repo root, on the host:
devcontainer up    --workspace-folder viewer --docker-path podman
devcontainer exec  --workspace-folder viewer --docker-path podman -- make deploy
```

Inside the container: `node`/`npm`, `python`+`uv`, `pulumi`, `aws` CLI. See
`Makefile` for `build` (frontend + lambda bundles), `preview`, `deploy`, `destroy`.

## Config (Pulumi)

`pulumi config set viewer:region ap-southeast-2`, `:namePrefix ai-models-viewer`,
`:apiToken <secret>` (secret). Auth can be disabled with `:authDisabled true`.
