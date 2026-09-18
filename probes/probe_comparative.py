#!/usr/bin/env python3
"""
probe_comparative.py
====================

Runs the identical mutation series against HCD's Data API and against MongoDB,
so that the comparison in "One field, five operations" stops being eleven
measurements on one side and none on the other.

THE TWO WAYS THIS COMPARISON IS USUALLY RIGGED
----------------------------------------------
Almost every published comparison of these engines is invalid for one of two
reasons, and this harness is built to make both impossible to commit silently.

**Rigging 1 — mismatched indexing.** HCD's Data API indexes every field
automatically. MongoDB indexes nothing you did not declare. Measuring an
auto-indexed HCD document against an unindexed MongoDB document compares a
system doing index maintenance with one that is not, and the result is
meaningless. MongoDB's own answer to that capability is the *wildcard index*
over the `$**` pattern, which supports queries on arbitrary fields. This harness
therefore runs MongoDB **twice**:

    mongo-default   no index on the ballast — what a team would actually deploy
    mongo-wildcard  a wildcard index — capability matched to HCD's default

Neither arm alone is the fair comparison. The pair is the finding: the first
shows what MongoDB costs as used, the second what it costs doing HCD's job.

**Rigging 2 — mismatched durability.** HCD's Data API commits at LOCAL_QUORUM
with LOCAL_SERIAL on conditional writes. The comparable MongoDB setting is a
majority write concern with journalling. The mapping is a judgement, not a fact;
it is recorded in the output and must be reported with any number. Running
MongoDB at w:1 against HCD at quorum is the oldest trick in this literature.

WHAT THIS HARNESS REFUSES TO DO
-------------------------------
It will not emit a cross-engine ratio unless both engines were measured on the
same host in the same session, with the same document series and the same
repetition counts. Comparing a run taken here against a run taken elsewhere is
the confound the accompanying article spends a section warning about, and the
record will say `cross_engine_comparison_permitted: false` if the condition is
not met. Two numbers in one JSON file do not make a comparison.

USAGE
-----
    # MongoDB arms
    export MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"
    python3 probe_comparative.py --engine mongodb --out mongo.json

    # HCD arm, same host, same session
    export DATA_API_ENDPOINT="http://127.0.0.1:8181" DATA_API_TOKEN="..."
    python3 probe_comparative.py --engine hcd --keyspace ks --out hcd.json

    # merge and compare — refuses if the conditions differ
    python3 probe_comparative.py --compare mongo.json hcd.json --out comparison.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

INDEXED_STRING_CAP = 8000     # HCD refuses indexed strings above this


@dataclass
class Size:
    label: str
    n_fields: int
    bytes_per_field: int

    @property
    def total(self) -> int:
        return self.n_fields * self.bytes_per_field


def series() -> list[Size]:
    """Field count fixed at 16, bytes per field varying — the series that
    established the per-kilobyte rate on HCD, so the comparison speaks to a
    quantity already characterised on one side."""
    return [Size(f"16x{b}B", 16, b) for b in (512, 1024, 2048, 4096, 8000)]


def distribution(ms: list[float]) -> dict[str, Any]:
    if not ms:
        return {}
    s = sorted(ms)

    def pct(p: float) -> float:
        if len(s) == 1:
            return round(s[0], 3)
        k = (len(s) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)

    return {"n": len(s), "min_ms": round(s[0], 3), "p50_ms": pct(0.50),
            "p95_ms": pct(0.95), "p99_ms": pct(0.99), "max_ms": round(s[-1], 3),
            "stdev_ms": round(statistics.pstdev(s), 3) if len(s) > 1 else 0.0}


def slope_per_kib(points: list[tuple[int, float]]) -> dict[str, Any]:
    if len(points) < 2:
        return {}
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    sl = sum((x - mx) * (y - my) for x, y in points) / den if den else 0.0
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (my + sl * (x - mx))) ** 2 for x, y in points)
    return {"ms_per_KiB": round(sl * 1024, 4),
            "r2": round(1 - ss_res / ss_tot, 4) if ss_tot else None,
            "endpoint_ratio": round(ys[-1] / ys[0], 3) if ys[0] else None,
            "y_range_ms": [round(ys[0], 3), round(ys[-1], 3)]}


def make_doc(doc_id: str, sz: Size) -> dict[str, Any]:
    d: dict[str, Any] = {"_id": doc_id, "status": "PENDING"}
    for i in range(sz.n_fields):
        d[f"b{i:03d}"] = "x" * sz.bytes_per_field
    return d


def host_fingerprint() -> dict[str, Any]:
    """Identifies the machine, so a merge of two records can refuse when they do
    not come from the same one."""
    try:
        with open("/proc/cpuinfo") as fh:
            model = next((l.split(":", 1)[1].strip() for l in fh
                          if l.startswith("model name")), "unknown")
    except OSError:
        model = "unknown"
    try:
        with open("/proc/meminfo") as fh:
            memkb = int(next(l for l in fh if l.startswith("MemTotal")).split()[1])
    except (OSError, StopIteration):
        memkb = 0
    return {"hostname": socket.gethostname(), "cpu_model": model,
            "cpu_count": os.cpu_count(), "mem_gib": round(memkb / 1024 / 1024, 1),
            "platform": platform.platform()}


# ---------------------------------------------------------------------------
# MongoDB arms
# ---------------------------------------------------------------------------

def run_mongodb(uri: str, reps: int, warmup: int, passes: int,
                db_name: str, wildcard: bool) -> dict[str, Any]:
    from pymongo import MongoClient, WriteConcern

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    # Durability mapped to HCD's LOCAL_QUORUM + journalling. Declared, not assumed.
    db = client.get_database(db_name)
    name = "cmp_wildcard" if wildcard else "cmp_default"
    coll = db.get_collection(name, write_concern=WriteConcern(w="majority", j=True))
    coll.drop()
    if wildcard:
        coll.create_index([("$**", 1)], name="wildcard_all")

    out: dict[str, Any] = {}
    for p in range(1, passes + 1):
        for sz in series():
            doc_id = f"cmp-{sz.label}-{uuid.uuid4()}"
            coll.insert_one(make_doc(doc_id, sz))
            for _ in range(warmup):
                coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
            lat: list[float] = []
            for i in range(reps):
                t0 = time.perf_counter()
                coll.update_one({"_id": doc_id}, {"$set": {"status": f"S{i}"}})
                lat.append((time.perf_counter() - t0) * 1000.0)
            out[f"{sz.label}|pass{p}"] = {"size": asdict(sz),
                                          "total_bytes": sz.total,
                                          "update": distribution(lat)}
            print(f"    [{name} {sz.label} pass{p}] p50 "
                  f"{out[f'{sz.label}|pass{p}']['update']['p50_ms']:.2f} ms",
                  file=sys.stderr)
            coll.delete_one({"_id": doc_id})
    indexes = [i["name"] for i in coll.list_indexes()]
    client.close()
    return {"results": out, "indexes_present": indexes}


# ---------------------------------------------------------------------------
# HCD arm
# ---------------------------------------------------------------------------

def run_hcd(endpoint: str, token: str, keyspace: str, collection: str,
            reps: int, warmup: int, passes: int) -> dict[str, Any]:
    from astrapy import DataAPIClient
    from astrapy.constants import Environment

    db = DataAPIClient(token, environment=Environment.HCD).get_database(
        endpoint, keyspace=keyspace)
    try:
        coll = db.create_collection(collection)
    except Exception:  # noqa: BLE001
        coll = db.get_collection(collection)

    out: dict[str, Any] = {}
    for p in range(1, passes + 1):
        for sz in series():
            doc_id = f"cmp-{sz.label}-{uuid.uuid4()}"
            coll.insert_one(make_doc(doc_id, sz))
            for _ in range(warmup):
                coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
            lat: list[float] = []
            for i in range(reps):
                t0 = time.perf_counter()
                coll.update_one({"_id": doc_id}, {"$set": {"status": f"S{i}"}})
                lat.append((time.perf_counter() - t0) * 1000.0)
            out[f"{sz.label}|pass{p}"] = {"size": asdict(sz),
                                          "total_bytes": sz.total,
                                          "update": distribution(lat)}
            print(f"    [hcd {sz.label} pass{p}] p50 "
                  f"{out[f'{sz.label}|pass{p}']['update']['p50_ms']:.2f} ms",
                  file=sys.stderr)
            try:
                coll.delete_one({"_id": doc_id})
            except Exception:  # noqa: BLE001
                pass
    return {"results": out, "indexes_present": ["automatic — nine SAI per collection"]}


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def compare(paths: list[str], out_path: str) -> int:
    recs = [json.load(open(p, encoding="utf-8")) for p in paths]
    fps = [r["conditions"]["host"] for r in recs]
    same_host = all(f["hostname"] == fps[0]["hostname"]
                    and f["cpu_model"] == fps[0]["cpu_model"] for f in fps)
    same_shape = all(r["conditions"]["reps"] == recs[0]["conditions"]["reps"]
                     and r["conditions"]["passes"] == recs[0]["conditions"]["passes"]
                     for r in recs)
    permitted = same_host and same_shape

    arms: dict[str, Any] = {}
    for r in recs:
        for arm, payload in r["arms"].items():
            pts = []
            for sz in series():
                k = f"{sz.label}|pass1"
                if k in payload["results"]:
                    pts.append((sz.total, payload["results"][k]["update"]["p50_ms"]))
            arms[arm] = {"slope": slope_per_kib(pts),
                         "indexes_present": payload.get("indexes_present")}

    record = {
        "comparison": "probe_comparative.py merge", "version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "cross_engine_comparison_permitted": permitted,
        "why": ("permitted only when every record comes from the same host and the "
                "same series shape; otherwise the ratio mixes engines with hardware "
                "and is the confound this study exists to avoid"),
        "same_host": same_host, "same_series_shape": same_shape,
        "hosts": fps,
        "arms": arms,
        "reading_guide": (
            "mongo-default is MongoDB as a team would deploy it: nothing indexed that "
            "was not asked for. mongo-wildcard is MongoDB doing HCD's job: every field "
            "queryable without declaration. Quoting the first against HCD overstates "
            "MongoDB's advantage; quoting only the second understates how MongoDB is "
            "actually used. Report both or report neither."),
    }
    json.dump(record, open(out_path, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: record[k] for k in
                      ("cross_engine_comparison_permitted", "same_host",
                       "same_series_shape")}, indent=2), file=sys.stderr)
    for a, v in arms.items():
        print(f"  {a:<16} {v['slope']}", file=sys.stderr)
    return 0 if permitted else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=["mongodb", "hcd"])
    ap.add_argument("--compare", nargs="+")
    ap.add_argument("--keyspace", default="cmp")
    ap.add_argument("--collection", default="cmp_probe")
    ap.add_argument("--db-name", default="cmpdb")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--smoke", action="store_true",
                    help="1 pass, 5 reps — validates the instrument, measures nothing")
    ap.add_argument("--out", default="comparative.json")
    args = ap.parse_args()

    if args.compare:
        return compare(args.compare, args.out)
    if not args.engine:
        ap.error("--engine or --compare is required")

    reps, passes = (5, 1) if args.smoke else (args.reps, args.passes)

    arms: dict[str, Any] = {}
    if args.engine == "mongodb":
        uri = os.environ.get("MONGO_URI")
        if not uri:
            print("MONGO_URI is not set.", file=sys.stderr)
            return 2
        print("\n  arm: mongo-default (no index on ballast)", file=sys.stderr)
        arms["mongo-default"] = run_mongodb(uri, reps, args.warmup, passes,
                                            args.db_name, wildcard=False)
        print("\n  arm: mongo-wildcard (capability matched to HCD)", file=sys.stderr)
        arms["mongo-wildcard"] = run_mongodb(uri, reps, args.warmup, passes,
                                             args.db_name, wildcard=True)
        durability = {"engine": "mongodb", "write_concern": "majority", "journal": True,
                      "mapped_to": "HCD LOCAL_QUORUM + commitlog",
                      "mapping_is_a_judgement": True}
    else:
        endpoint = os.environ.get("DATA_API_ENDPOINT")
        if not endpoint:
            print("DATA_API_ENDPOINT is not set.", file=sys.stderr)
            return 2
        print("\n  arm: hcd (automatic indexing, the platform default)", file=sys.stderr)
        arms["hcd"] = run_hcd(endpoint, os.environ.get("DATA_API_TOKEN", ""),
                              args.keyspace, args.collection, reps, args.warmup, passes)
        durability = {"engine": "hcd", "write_consistency": "LOCAL_QUORUM",
                      "serial_consistency": "LOCAL_SERIAL",
                      "note": "tier defaults, not set by the client"}

    record = {
        "probe": "probe_comparative.py", "version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "smoke_test": bool(args.smoke),
        "engine": args.engine,
        "arms": arms,
        "durability_mapping": durability,
        "conditions": {
            "host": host_fingerprint(), "reps": reps, "passes": passes,
            "warmup_discarded": args.warmup, "python": sys.version.split()[0],
            "TO_BE_COMPLETED_BY_HAND": {
                "deployment_shape": "single node or cluster; replication factor; "
                                    "for MongoDB, replica set size",
                "regime": "memtable/cache-resident or disk-bound, with evidence",
                "resource_limits": "CPU and memory limits of every process involved",
                "colocation": "client and server on the same host?",
            },
        },
        "warning": ("A single-record file is not a comparison. Merge with --compare, "
                    "which refuses to emit a ratio unless both engines were measured "
                    "on the same host with the same series shape."),
    }
    if args.smoke:
        record["publication_note"] = (
            "SMOKE TEST. Five repetitions on an unqualified machine. This validates "
            "that the instrument runs; it measures nothing and must never be quoted.")
    json.dump(record, open(args.out, "w", encoding="utf-8"), indent=2)
    print(f"\nRecord written to {args.out}\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
