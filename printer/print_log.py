#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Append-only JSONL print log + annotate/query helpers.

One JSON object per line in printer/prints.jsonl — COMMITTED, and the single
source of truth. It's text so git diffs it cleanly (each print = one appended
line) and merges without binary conflicts. SQLite/DuckDB are only query lenses
over it, never the store.

printflow.py appends a row automatically at print start with everything it
already knows (unix ts, git commit + dirty, part, filament config/brand/type,
nozzle, plate, placement, brim, soak, ramp, est time/mass, footprint). The
judgment fields are left blank for you to fill after the print:

  # update the most recent row:
  print_log.py annotate --outcome success --ambient 9
  print_log.py annotate --outcome fail:warp --note "old cold strip left on bed"

  # query (SQL over the JSONL via in-memory sqlite; scalar fields are real
  # columns, lists/objects come back as JSON text):
  print_log.py query "SELECT ts, part, brand, outcome FROM prints WHERE brand='Overture'"
  print_log.py query "SELECT material_type, count(*) FROM prints WHERE brand='Overture' GROUP BY material_type"
  # equivalently, if you have duckdb:
  #   duckdb -c "SELECT * FROM 'printer/prints.jsonl' WHERE brand='Overture'"
"""
import argparse
import json
import os
import sqlite3
import sys

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prints.jsonl")


def append(record: dict):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def _load():
    if not os.path.exists(LOG):
        return []
    with open(LOG) as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def _save(rows):
    with open(LOG, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


def annotate(fields):
    rows = _load()
    if not rows:
        sys.exit("no print records yet")
    rows[-1].update(fields)
    _save(rows)
    print(f"annotated last record ({rows[-1].get('part')}): {fields}")


def query(sql):
    rows = _load()
    if not rows:
        sys.exit("no print records yet")
    cols = []
    for r in rows:                       # union of keys, first-seen order
        for k in r:
            if k not in cols:
                cols.append(k)
    db = sqlite3.connect(":memory:")
    quoted = ', '.join('"' + c + '"' for c in cols)
    db.execute(f"CREATE TABLE prints ({quoted})")
    cell = lambda v: json.dumps(v) if isinstance(v, (list, dict)) else v
    db.executemany(
        f"INSERT INTO prints VALUES ({', '.join('?' * len(cols))})",
        [[cell(r.get(c)) for c in cols] for r in rows])
    cur = db.execute(sql)
    print("\t".join(d[0] for d in cur.description))
    for row in cur.fetchall():
        print("\t".join("" if v is None else str(v) for v in row))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("annotate", help="update the most recent record")
    a.add_argument("--outcome", help="success | fail:<mode> (e.g. fail:warp)")
    a.add_argument("--ambient", type=float, help="room temperature, degrees C")
    a.add_argument("--note", help="free-text observation")
    q = sub.add_parser("query", help="run SQL over the log (table name: prints)")
    q.add_argument("sql")
    args = ap.parse_args()

    if args.cmd == "annotate":
        fields = {}
        if args.outcome is not None:
            fields["outcome"] = args.outcome
        if args.ambient is not None:
            fields["ambient_c"] = args.ambient
        if args.note is not None:
            fields["observations"] = args.note
        if not fields:
            sys.exit("nothing to annotate (pass --outcome/--ambient/--note)")
        annotate(fields)
    elif args.cmd == "query":
        query(args.sql)


if __name__ == "__main__":
    main()
