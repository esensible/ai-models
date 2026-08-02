"""API Gateway WebSocket directory service.

Routes:
  $connect    — validate ?token=<shared secret>, register the connection
  $disconnect — drop the connection
  $default    — actions: list | rename | delete | presign
"""
from __future__ import annotations

import json
import os

import viewer_common as vc

API_TOKEN = os.environ.get("API_TOKEN", "")
AUTH_DISABLED = os.environ.get("AUTH_DISABLED", "") == "true"
PRESIGN_TTL = int(os.environ.get("PRESIGN_TTL", "900"))


def _endpoint(event) -> str:
    rc = event["requestContext"]
    return os.environ.get("WS_ENDPOINT") or f"https://{rc['domainName']}/{rc['stage']}"


def _reply(event, payload: dict) -> None:
    rc = event["requestContext"]
    vc.post_to(_endpoint(event), rc["connectionId"], json.dumps(payload).encode())


def handler(event, _context):
    rc = event["requestContext"]
    route = rc.get("routeKey")
    cid = rc["connectionId"]

    if route == "$connect":
        token = (event.get("queryStringParameters") or {}).get("token", "")
        if not AUTH_DISABLED and token != API_TOKEN:
            return {"statusCode": 401, "body": "unauthorized"}
        vc.table().put_item(Item={"pk": vc.CONN_PK, "sk": cid})
        return {"statusCode": 200}

    if route == "$disconnect":
        vc.table().delete_item(Key={"pk": vc.CONN_PK, "sk": cid})
        return {"statusCode": 200}

    # $default — dispatch on action
    try:
        msg = json.loads(event.get("body") or "{}")
        action = msg.get("action")

        if action == "list":
            folder = vc.norm_folder(msg.get("path", "/"))
            _reply(event, {"type": "list", "path": folder, "entries": vc.list_folder(folder)})

        elif action == "presign":
            key = vc.key_for(msg["path"])
            url = vc.s3().generate_presigned_url(
                "get_object",
                Params={"Bucket": vc.BUCKET_NAME, "Key": key},
                ExpiresIn=PRESIGN_TTL,
            )
            _reply(event, {"type": "presign", "path": msg["path"], "url": url,
                           "expiresIn": PRESIGN_TTL})

        elif action == "delete":
            key = vc.key_for(msg["path"])
            vc.s3().delete_object(Bucket=vc.BUCKET_NAME, Key=key)
            folder = vc.delete_file(key)
            vc.broadcast(_endpoint(event),
                         json.dumps({"type": "changed", "path": folder}).encode())

        elif action == "rename":
            src, dst = vc.key_for(msg["from"]), vc.key_for(msg["to"])
            vc.s3().copy_object(Bucket=vc.BUCKET_NAME,
                                CopySource={"Bucket": vc.BUCKET_NAME, "Key": src}, Key=dst)
            vc.s3().delete_object(Bucket=vc.BUCKET_NAME, Key=src)
            head = vc.s3().head_object(Bucket=vc.BUCKET_NAME, Key=dst)
            f_old = vc.delete_file(src)
            f_new = vc.put_file(dst, int(head.get("ContentLength", 0)),
                                head.get("LastModified").isoformat() if head.get("LastModified") else "",
                                head.get("ETag", "").strip('"'))
            ep = _endpoint(event)
            for folder in {f_old, f_new}:
                vc.broadcast(ep, json.dumps({"type": "changed", "path": folder}).encode())

        else:
            _reply(event, {"type": "error", "message": f"unknown action: {action}"})

    except Exception as e:  # surface errors to the caller, don't 500 the socket
        _reply(event, {"type": "error", "message": str(e)})

    return {"statusCode": 200}
