"""S3 event -> DynamoDB index. Triggered on ObjectCreated:* / ObjectRemoved:*.

Keeps the index in sync for files that arrive OUTSIDE the directory service (e.g. a
direct S3 upload), then broadcasts a `changed` event so live WS clients refresh.
"""
from __future__ import annotations

import json
import os
from urllib.parse import unquote_plus

import viewer_common as vc

WS_ENDPOINT = os.environ.get("WS_ENDPOINT", "")


def handler(event, _context):
    changed_folders: set[str] = set()

    for rec in event.get("Records", []):
        name = rec.get("eventName", "")
        key = unquote_plus(rec["s3"]["object"]["key"])
        if not key.lower().endswith(".3mf"):
            continue  # index only 3mf files

        if name.startswith("ObjectCreated"):
            obj = rec["s3"]["object"]
            size = int(obj.get("size", 0))
            etag = obj.get("eTag", "")
            mtime = rec.get("eventTime", "")
            changed_folders.add(vc.put_file(key, size, mtime, etag))
        elif name.startswith("ObjectRemoved"):
            changed_folders.add(vc.delete_file(key))

    if WS_ENDPOINT:
        for folder in changed_folders:
            vc.broadcast(WS_ENDPOINT, json.dumps({"type": "changed", "path": folder}).encode())

    return {"statusCode": 200, "indexed": len(event.get("Records", []))}
