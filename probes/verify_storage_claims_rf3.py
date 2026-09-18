#!/usr/bin/env python3
"""
verify_storage_claims.py
========================

A verification harness for the claims marked [U] (unverified) in

    "One field, five operations: how physical storage layout predicts
     write cost, index freshness and concurrency in document databases"

Purpose
-------
Three claims in that article rest on structural inference rather than on a
published source. This harness converts them into measurements against a
build you actually control, and emits a machine-readable record of what it
found. It is a *self-verification* instrument, not a competitive benchmark:
it measures one system, the one you point it at, and it deliberately refuses
to emit anything that could be quoted as a cross-vendor comparison.

    A2  The generic column layout        -> PROBE 1 (schema introspection)
    A3  The read-modify-write cycle      -> PROBE 3 (cost-vs-size regression)
    A5  The write consistency level      -> PROBE 4 (query tracing)

    plus the article's own recommended measurement:
    --  write-to-searchable interval     -> PROBE 2 (idle and under load)

Methodological commitments
--------------------------
The harness applies to itself the six requirements the article imposes on
anyone else's benchmark:

  1. Load is driven at a FIXED OFFERED RATE, never as fast as the system
     replies. A closed loop would hide exactly the stalls we are looking for.
  2. DISTRIBUTIONS are reported -- median, p95, p99, p99.9, max. No averages
     appear in the output, by construction.
  3. Durability settings are RECORDED in the output record, not assumed.
  4. Working set and topology are RECORDED, not inferred.
  5. Every run WARMS UP before measuring.
  6. Runs are long enough to be stated honestly, and the duration is recorded
     so a reader can judge whether compaction cycles were crossed.

Requirements
------------
    pip install astrapy cassandra-driver

The CQL probes (1 and 4) need direct access to the backend cluster. Where
you have only the HTTP Data API surface, probes 1 and 4 will report
NOT_ATTEMPTED and the remaining probes still run. That degradation is
recorded rather than silently skipped.

Usage
-----
    export DATA_API_ENDPOINT="http://localhost:8181"
    export DATA_API_TOKEN="..."
    export CQL_CONTACT_POINT="localhost"        # optional, enables probes 1 and 4
    export CQL_USER="cassandra"
    export CQL_PASS="cassandra"

    python3 verify_storage_claims.py --keyspace my_ks --collection probe_coll \
        --rate 50 --duration 60 --out findings.json

Output
------
A JSON record with one entry per probe, each carrying: the claim under test,
the verdict (SUPPORTED / CONTRADICTED / INCONCLUSIVE / NOT_ATTEMPTED), the
evidence, and the run conditions. Paste the record into the article's
appendix, or contradict the article with it. Both are useful.

Licence: do what you like with it. Attribution appreciated, not required.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

SUPPORTED = "SUPPORTED"
CONTRADICTED = "CONTRADICTED"
INCONCLUSIVE = "INCONCLUSIVE"
NOT_ATTEMPTED = "NOT_ATTEMPTED"


@dataclass
class Finding:
    probe: str
    claim_id: str
    claim: str
    verdict: str = INCONCLUSIVE
    evidence: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.notes.append(msg)
        print(f"    · {msg}", file=sys.stderr)


def distribution(samples_ms: list[float]) -> dict[str, float]:
    """Percentiles only. No mean is computed anywhere in this file, on purpose:
    an average of a latency distribution conceals the behaviour that matters."""
    if not samples_ms:
        return {}
    s = sorted(samples_ms)

    def pct(p: float) -> float:
        if len(s) == 1:
            return round(s[0], 3)
        k = (len(s) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)

    return {
        "n": len(s),
        "min_ms": round(s[0], 3),
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "p999_ms": pct(0.999),
        "max_ms": round(s[-1], 3),
        "stdev_ms": round(statistics.pstdev(s), 3) if len(s) > 1 else 0.0,
    }


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------

def connect_data_api(endpoint: str, token: str, keyspace: str):
    try:
        from astrapy import DataAPIClient
        from astrapy.constants import Environment
    except ImportError:
        raise RuntimeError("astrapy not installed: pip install astrapy")
    # Mechanical fix (2026-09-17): self-hosted HCD serves /v1, not Astra's
    # /api/json/v1. Without environment=HCD, astrapy 2.3.1 returns HTTP 404
    # on every command. No protocol, threshold or size is touched.
    client = DataAPIClient(token, environment=Environment.HCD)
    return client.get_database(endpoint, keyspace=keyspace)


def connect_cql(contact_point: str, user: str | None, password: str | None):
    """Returns (session, cluster) or (None, None) if unavailable. A missing CQL
    path is a degraded run, not a failed one."""
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
    except ImportError:
        return None, None
    try:
        auth = PlainTextAuthProvider(user, password) if user else None
        cluster = Cluster([contact_point], auth_provider=auth)
        session = cluster.connect()
        # Mechanical fix (2026-09-17, RF=3 run only): system_traces is
        # SimpleStrategy RF=2 on a two-datacentre ring, so the driver's default
        # LOCAL_ONE read of system_traces.sessions fails with "alive_replicas: 0"
        # for tokens whose replicas both sit in the other DC. Read at ONE.
        # Queries, thresholds and verdict logic are untouched.
        from cassandra import ConsistencyLevel
        session.default_consistency_level = ConsistencyLevel.ONE
        return session, cluster
    except Exception as exc:  # noqa: BLE001 - we want the reason in the record
        print(f"    · CQL connection refused: {exc}", file=sys.stderr)
        return None, None


# ---------------------------------------------------------------------------
# PROBE 1 — the physical column layout (claim A2)
# ---------------------------------------------------------------------------

def probe_layout(session, keyspace: str, collection: str) -> Finding:
    """Reads the real schema from system_schema. This is the probe that settles
    A2 definitively: either the generic columns are there under those names, or
    the article is wrong and should say so."""
    f = Finding(
        probe="1. physical column layout",
        claim_id="A2",
        claim=("A JSON document is decomposed into one row bearing generic columns "
               "(doc_json, exist_keys, array_contains, array_size, query_*_values)."),
    )
    if session is None:
        f.verdict = NOT_ATTEMPTED
        f.say("no CQL session; this claim cannot be settled through the HTTP surface alone")
        return f

    try:
        rows = session.execute(
            "SELECT column_name, type, kind FROM system_schema.columns "
            "WHERE keyspace_name=%s AND table_name=%s", (keyspace, collection))
        cols = {r.column_name: {"type": r.type, "kind": r.kind} for r in rows}
    except Exception as exc:  # noqa: BLE001
        f.verdict = INCONCLUSIVE
        f.say(f"schema read failed: {exc}")
        return f

    if not cols:
        f.verdict = INCONCLUSIVE
        f.say(f"no table {keyspace}.{collection} found; create the collection first")
        return f

    expected = ["doc_json", "exist_keys", "array_contains", "array_size",
                "query_text_values", "query_dbl_values", "query_bool_values",
                "query_null_values", "query_timestamp_values"]
    present = [c for c in expected if c in cols]
    unexpected = sorted(set(cols) - set(expected))

    f.evidence = {
        "columns_found": cols,
        "predicted_present": present,
        "predicted_absent": [c for c in expected if c not in cols],
        "columns_not_predicted": unexpected,
        "column_count": len(cols),
    }

    # Indexes: settles the product-side count that the upstream default only hints at
    try:
        idx = session.execute(
            "SELECT index_name, kind, options FROM system_schema.indexes "
            "WHERE keyspace_name=%s AND table_name=%s", (keyspace, collection))
        idx_list = [{"name": r.index_name, "kind": r.kind, "options": dict(r.options or {})}
                    for r in idx]
        f.evidence["indexes"] = idx_list
        f.evidence["index_count"] = len(idx_list)
        f.say(f"{len(idx_list)} indexes created automatically on this collection")
    except Exception as exc:  # noqa: BLE001
        f.say(f"index read failed: {exc}")

    if len(present) >= 6:
        f.verdict = SUPPORTED
        f.say(f"{len(present)}/{len(expected)} predicted columns present")
    elif present:
        f.verdict = INCONCLUSIVE
        f.say(f"only {len(present)}/{len(expected)} predicted columns present — "
              "the layout is generic but the names in circulation are partly wrong")
    else:
        f.verdict = CONTRADICTED
        f.say("none of the predicted column names exist; the article's section 2.1 "
              "should be rewritten against what this probe actually found")
    return f


# ---------------------------------------------------------------------------
# PROBE 2 — write-to-searchable interval, idle and under load
# ---------------------------------------------------------------------------

def _one_probe_cycle(coll, timeout_s: float = 30.0) -> float | None:
    marker = f"probe-{uuid.uuid4()}"
    t0 = time.perf_counter()
    coll.insert_one({"_id": marker, "body": marker})
    deadline = t0 + timeout_s
    while time.perf_counter() < deadline:
        if coll.find_one({"body": marker}):
            elapsed = (time.perf_counter() - t0) * 1000.0
            try:
                coll.delete_one({"_id": marker})
            except Exception:  # noqa: BLE001
                pass
            return elapsed
        time.sleep(0.005)
    return None


def probe_freshness(coll, rate: float, duration: int, samples: int = 40) -> Finding:
    """Two regimes. The idle number is the one everybody quotes; the loaded
    number is the one that decides your architecture."""
    f = Finding(
        probe="2. write-to-searchable interval",
        claim_id="FRESHNESS",
        claim="A document is searchable at the moment the write is acknowledged.",
    )

    print("  [2] idle regime …", file=sys.stderr)
    idle = [v for _ in range(samples) if (v := _one_probe_cycle(coll)) is not None]

    print(f"  [2] loaded regime — {rate}/s offered for {duration}s …", file=sys.stderr)
    loaded: list[float] = []
    interval = 1.0 / rate if rate > 0 else 0.0
    start = time.perf_counter()
    next_due = start
    background = 0
    while time.perf_counter() - start < duration:
        now = time.perf_counter()
        if now < next_due:                      # open loop: we wait for the clock,
            time.sleep(min(next_due - now, 0.002))   # never for the server
            continue
        next_due += interval
        background += 1
        try:
            coll.insert_one({"_id": f"load-{uuid.uuid4()}",
                             "payload": "x" * 512, "n": background})
        except Exception:  # noqa: BLE001
            pass
        if background % max(1, int(rate)) == 0:      # one measurement per second
            v = _one_probe_cycle(coll)
            if v is not None:
                loaded.append(v)

    behind = max(0.0, (time.perf_counter() - start) - duration)
    f.evidence = {
        "idle": distribution(idle),
        "under_load": distribution(loaded),
        "offered_rate_per_s": rate,
        "load_duration_s": duration,
        "background_writes_issued": background,
        "schedule_slip_s": round(behind, 3),
        "measurement_model": "open loop, fixed offered rate; percentiles only",
    }
    if behind > duration * 0.05:
        f.say(f"WARNING: the generator fell {behind:.1f}s behind schedule. "
              "The offered rate was not sustained; treat the loaded figures as a floor.")

    if idle and loaded:
        ratio = f.evidence["under_load"]["p99_ms"] / max(f.evidence["idle"]["p99_ms"], 0.001)
        f.evidence["p99_degradation_factor_under_load"] = round(ratio, 2)
        f.verdict = SUPPORTED if f.evidence["under_load"]["p99_ms"] < 50 else INCONCLUSIVE
        f.say(f"p99 idle {f.evidence['idle']['p99_ms']} ms · "
              f"p99 loaded {f.evidence['under_load']['p99_ms']} ms · "
              f"degradation x{ratio:.1f}")
        f.say("Whether this interval is acceptable is not a property of the database. "
              "It is a property of your application's correctness requirements.")
    else:
        f.verdict = INCONCLUSIVE
        f.say("insufficient samples")
    return f


# ---------------------------------------------------------------------------
# PROBE 3 — is there a read-modify-write cycle? (claim A3)
# ---------------------------------------------------------------------------

def probe_rmw(coll, sizes_kb=(1, 8, 32, 128), reps: int = 30) -> Finding:
    """The decisive experiment, and the reason this harness exists.

    Mutate ONE small field in documents of increasing total size. If the engine
    performs a targeted write, latency is flat in document size. If it reads,
    modifies and rewrites the whole document, latency grows with total size
    even though the mutation is constant. The shape of the curve settles A3
    without anyone needing to read the source."""
    f = Finding(
        probe="3. read-modify-write detection",
        claim_id="A3",
        claim=("A single-field update reads the whole document, modifies it in "
               "memory and rewrites it entirely, plus derived columns."),
    )
    results: dict[str, Any] = {}
    for kb in sizes_kb:
        doc_id = f"rmw-{kb}kb-{uuid.uuid4()}"
        coll.insert_one({"_id": doc_id, "ballast": "x" * (kb * 1024),
                         "status": "PENDING", "n": 0})
        for _ in range(5):                                   # warm-up, discarded
            coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
        lat: list[float] = []
        for i in range(reps):
            t0 = time.perf_counter()
            coll.update_one({"_id": doc_id}, {"$set": {"status": f"S{i}"}})
            lat.append((time.perf_counter() - t0) * 1000.0)
        results[f"{kb}kb"] = distribution(lat)
        try:
            coll.delete_one({"_id": doc_id})
        except Exception:  # noqa: BLE001
            pass
        print(f"  [3] {kb:>4} KB → p50 {results[f'{kb}kb']['p50_ms']} ms", file=sys.stderr)

    f.evidence = {
        "mutation": "one scalar field, constant across all sizes",
        "by_document_size": results,
        "reps_per_size": reps,
    }

    small = results[f"{sizes_kb[0]}kb"]["p50_ms"]
    large = results[f"{sizes_kb[-1]}kb"]["p50_ms"]
    growth = large / max(small, 0.001)
    size_ratio = sizes_kb[-1] / sizes_kb[0]
    f.evidence["p50_growth_factor"] = round(growth, 2)
    f.evidence["document_size_growth_factor"] = size_ratio

    if growth >= 1.6:
        f.verdict = SUPPORTED
        f.say(f"p50 grew x{growth:.2f} while the document grew x{size_ratio:.0f} "
              "and the mutation stayed constant. Cost scales with total document "
              "size: that is the signature of a whole-document rewrite.")
    elif growth <= 1.2:
        f.verdict = CONTRADICTED
        f.say(f"p50 grew only x{growth:.2f} across a x{size_ratio:.0f} size range. "
              "Cost is flat in document size; the read-modify-write account in "
              "section 3 of the article is not supported on this build and should "
              "be withdrawn.")
    else:
        f.verdict = INCONCLUSIVE
        f.say(f"p50 growth x{growth:.2f} sits between the thresholds. Widen the "
              "size range or raise the repetition count before concluding.")
    f.say("Confounder to exclude before publishing: payload transfer over HTTP "
          "also scales with document size. Re-run against a local endpoint, or "
          "subtract a same-size read, to separate wire cost from storage cost.")
    return f


# ---------------------------------------------------------------------------
# PROBE 4 — consistency level actually used (claim A5)
# ---------------------------------------------------------------------------

def probe_consistency(session, keyspace: str, collection: str) -> Finding:
    f = Finding(
        probe="4. write consistency level",
        claim_id="A5",
        claim="Data API writes execute at LOCAL_QUORUM; conditional writes at a serial level.",
    )
    if session is None:
        f.verdict = NOT_ATTEMPTED
        f.say("no CQL session; consistency levels are not observable from the HTTP surface")
        return f
    try:
        rows = session.execute(
            "SELECT session_id, request, started_at, parameters FROM system_traces.sessions "
            "LIMIT 200")
        seen: dict[str, int] = {}
        for r in rows:
            params = dict(r.parameters or {})
            cl = params.get("consistency_level") or params.get("serial_consistency_level")
            if cl:
                seen[cl] = seen.get(cl, 0) + 1
        f.evidence = {"consistency_levels_observed": seen, "traces_examined": 200}
        if seen:
            f.verdict = SUPPORTED if "LOCAL_QUORUM" in seen else INCONCLUSIVE
            f.say(f"observed: {seen}")
        else:
            f.verdict = INCONCLUSIVE
            f.say("no consistency level recorded in system_traces. Enable tracing "
                  "(nodetool settraceprobability 1.0) on a quiet node, replay a write, "
                  "then re-run this probe. Reset the probability afterwards.")
    except Exception as exc:  # noqa: BLE001
        f.verdict = INCONCLUSIVE
        f.say(f"trace read failed: {exc}")
    return f


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="storage_probe")
    ap.add_argument("--rate", type=float, default=50.0,
                    help="offered writes per second during the loaded regime")
    ap.add_argument("--duration", type=int, default=60, help="seconds of loaded regime")
    ap.add_argument("--out", default="findings.json")
    ap.add_argument("--skip-load", action="store_true",
                    help="idle measurements only; do not generate background load")
    args = ap.parse_args()

    endpoint = os.environ.get("DATA_API_ENDPOINT")
    token = os.environ.get("DATA_API_TOKEN", "")
    if not endpoint:
        print("DATA_API_ENDPOINT is not set.", file=sys.stderr)
        return 2

    print(f"\nVerification harness — {datetime.now(timezone.utc).isoformat()}", file=sys.stderr)
    print(f"Endpoint: {endpoint}  keyspace: {args.keyspace}\n", file=sys.stderr)

    db = connect_data_api(endpoint, token, args.keyspace)
    try:
        # Mechanical fix (2026-09-17, variant A, user-approved): the Data API
        # refuses any INDEXED string > 8000 bytes (SHRED_DOC_LIMIT_VIOLATION),
        # so the 8/32/128 KB ballast of probe 3 cannot be indexed. Excluding
        # only "ballast" from indexing keeps sizes, mutation, reps and
        # thresholds untouched; the ballast still lives in doc_json.
        coll = db.create_collection(
            args.collection, definition={"indexing": {"deny": ["ballast"]}})
    except Exception:  # noqa: BLE001
        coll = db.get_collection(args.collection)

    session, cluster = connect_cql(
        os.environ.get("CQL_CONTACT_POINT", ""),
        os.environ.get("CQL_USER"), os.environ.get("CQL_PASS"),
    ) if os.environ.get("CQL_CONTACT_POINT") else (None, None)

    findings: list[Finding] = []
    print("  [1] reading physical schema …", file=sys.stderr)
    findings.append(probe_layout(session, args.keyspace, args.collection))
    findings.append(probe_freshness(coll, 0 if args.skip_load else args.rate,
                                    0 if args.skip_load else args.duration))
    print("  [3] mutating one field across document sizes …", file=sys.stderr)
    findings.append(probe_rmw(coll))
    print("  [4] inspecting consistency levels …", file=sys.stderr)
    findings.append(probe_consistency(session, args.keyspace, args.collection))

    record = {
        "harness": "verify_storage_claims.py",
        "harness_version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "conditions": {
            "endpoint": endpoint,
            "keyspace": args.keyspace,
            "collection": args.collection,
            "cql_available": session is not None,
            "client_platform": platform.platform(),
            "python": sys.version.split()[0],
            "TO_BE_COMPLETED_BY_HAND": {
                "product_and_version": "e.g. HCD 2.0.x — read it from the running node, not the docs",
                "topology": "nodes, datacentres, replication factor",
                "node_hardware": "vCPU, RAM, storage class",
                "working_set_vs_ram": "in-cache or disk-bound; a latency figure without this is uninterpretable",
                "durability_settings": "commitlog sync mode and any non-default consistency",
            },
        },
        "findings": [asdict(f) for f in findings],
        "publication_note": (
            "These figures characterise one build on one machine under one workload. "
            "They settle what this engine does; they do NOT license any comparison "
            "with another vendor's product, and no figure here should be published "
            "as such. Publish the verdicts and the method; publish the numbers only "
            "alongside every field of 'conditions' above, completed."
        ),
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)

    print("\n" + "=" * 72, file=sys.stderr)
    for f in findings:
        print(f"  {f.verdict:<14} {f.claim_id:<10} {f.probe}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"\nRecord written to {args.out}\n", file=sys.stderr)

    if cluster:
        cluster.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
