"""Shared helpers for the viewer lambdas: path normalisation, DynamoDB, WS broadcast."""
from __future__ import annotations

import os
from typing import Iterable

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("TABLE_NAME", "")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
CONN_PK = "$conn"  # connection rows live under this partition

_ddb = None
_s3 = None


def table():
    global _ddb
    if _ddb is None:
        _ddb = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _ddb


def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


# ---- path helpers -----------------------------------------------------------
# Folders are normalised with a leading and trailing slash: "/", "/covers/".
def norm_folder(p: str) -> str:
    p = "/" + p.strip("/") + "/"
    return "/" if p == "//" else p


def split_key(key: str) -> tuple[str, str]:
    """S3 key 'covers/a.3mf' -> ('/covers/', 'a.3mf'); 'a.3mf' -> ('/', 'a.3mf')."""
    key = key.lstrip("/")
    if "/" in key:
        folder, name = key.rsplit("/", 1)
        return norm_folder(folder), name
    return "/", key


def key_for(path: str) -> str:
    """Logical path '/covers/a.3mf' -> S3 key 'covers/a.3mf'."""
    return path.lstrip("/")


def ancestor_dirs(folder: str) -> Iterable[tuple[str, str]]:
    """Yield (parent_folder, dir_name) rows for every ancestor of `folder` (excl. root)."""
    folder = norm_folder(folder)
    parts = [p for p in folder.strip("/").split("/") if p]
    cur = "/"
    for p in parts:
        yield cur, p
        cur = norm_folder(cur + p)


# ---- DynamoDB row helpers ---------------------------------------------------
def put_file(key: str, size: int, mtime: str, etag: str) -> str:
    parent, name = split_key(key)
    table().put_item(Item={
        "pk": parent, "sk": name, "type": "file",
        "s3key": key, "size": size, "mtime": mtime, "etag": etag,
    })
    for p, d in ancestor_dirs(parent):
        table().put_item(Item={"pk": p, "sk": d, "type": "dir"})
    return parent


def delete_file(key: str) -> str:
    parent, name = split_key(key)
    table().delete_item(Key={"pk": parent, "sk": name})
    return parent


def list_folder(folder: str) -> list[dict]:
    folder = norm_folder(folder)
    resp = table().query(KeyConditionExpression=Key("pk").eq(folder))
    out = []
    for it in resp.get("Items", []):
        e = {"name": it["sk"], "type": it["type"]}
        if it["type"] == "file":
            e.update(size=int(it.get("size", 0)), mtime=it.get("mtime", ""),
                     key=it.get("s3key", ""))
        out.append(e)
    out.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))
    return out


# ---- WebSocket broadcast ----------------------------------------------------
def _mgmt(endpoint: str):
    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint)


def connection_ids() -> list[str]:
    resp = table().query(KeyConditionExpression=Key("pk").eq(CONN_PK))
    return [it["sk"] for it in resp.get("Items", [])]


def post_to(endpoint: str, connection_id: str, data: bytes) -> bool:
    """Send to one connection. Returns False (and prunes) if the connection is gone."""
    try:
        _mgmt(endpoint).post_to_connection(ConnectionId=connection_id, Data=data)
        return True
    except Exception as e:  # GoneException etc.
        if "GoneException" in type(e).__name__ or "410" in str(e):
            table().delete_item(Key={"pk": CONN_PK, "sk": connection_id})
        return False


def broadcast(endpoint: str, payload: bytes) -> None:
    for cid in connection_ids():
        post_to(endpoint, cid, payload)
