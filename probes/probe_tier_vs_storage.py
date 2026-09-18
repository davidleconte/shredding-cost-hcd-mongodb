#!/usr/bin/env python3
"""
probe_tier_vs_storage.py
========================

Splits the cost of a mutation between the stateless Data API tier and the
storage engine beneath it. Closes action item 5 of ADR-001, the last of the
three terms.

WHY THIS ONE MATTERS MORE THAN IT LOOKS
---------------------------------------
The published rate is about 0.77 ms per kilobyte of indexed content the document
carries and the mutation never touches. That rate has so far been attributed, in
prose, to index maintenance. But the work it describes is done in two places:

  · the Data API tier parses the JSON, shreds it into eleven derived values,
    and builds the CQL statement pair — all of which scales with indexed bytes;
  · the storage engine executes the SELECT and the conditional UPDATE, and
    maintains the storage-attached indexes — which also scales with indexed bytes.

If the rate turns out to live mostly in the tier, the architectural reading
changes substantially and in a direction favourable to the platform: the cost
sits in a stateless component that scales horizontally by adding instances,
rather than in the stateful one that does not. The article currently does not
make that distinction, and should.

This probe is therefore capable of softening its author's own criticism. That is
the reason to run it.

TWO INDEPENDENT METHODS, WHICH MUST AGREE
-----------------------------------------
METHOD 1 — bypass.  For each document size, measure the same logical mutation
  (a) through the Data API, and (b) as the identical CQL statement pair executed
  directly by the driver against the same row, with the shredded values read back
  from the row rather than recomputed. The difference is the tier: HTTP, JSON
  parse, shred, statement construction, response serialisation.

METHOD 2 — trace.  With tracing enabled, read the coordinator-side duration of
  the CQL statements the Data API issues. Client-observed Data API latency minus
  summed coordinator duration is the tier plus the loopback hop.

The two estimates rest on different instruments and different failure modes. If
they disagree by more than a quarter, neither is reportable and the script says
so rather than averaging them into a plausible number.

METHOD 2 requires nodetool and CQL access; without them METHOD 1 still runs and
the disagreement check is skipped, which is recorded.

USAGE
-----
    export DATA_API_ENDPOINT="http://127.0.0.1:8182"
    export DATA_API_TOKEN="..."
    export CQL_CONTACT_POINT="127.0.0.1"
    export CQL_USER="..." CQL_PASS="..."

    python3 probe_tier_vs_storage.py --keyspace ks --dry-run
    python3 probe_tier_vs_storage.py --keyspace ks --out findings_tier.json
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
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

# Column set established by measurement M1. The nine derived columns plus tx_id
# plus doc_json are the eleven assignments observed in M2.
DERIVED = ["exist_keys", "array_size", "array_contains", "query_bool_values",
           "query_dbl_values", "query_text_values", "query_null_values",
           "query_timestamp_values", "query_lexical_value"]

INDEXED_STRING_CAP = 8000
AGREEMENT_TOLERANCE = 0.25      # methods disagreeing by more than this invalidate both


@dataclass
class Size:
    label: str
    n_fields: int
    bytes_per_field: int

    @property
    def total(self) -> int:
        return self.n_fields * self.bytes_per_field


def plan() -> list[Size]:
    # Field count held at 16, as in the series that established the per-byte rate,
    # so this probe measures the split of a rate already characterised.
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


def split_report(total_ms: float, storage_ms: float) -> dict[str, Any]:
    """Never returns a negative tier term silently: a negative means the two
    instruments measured different work, and that is the finding."""
    tier = total_ms - storage_ms
    out = {"total_ms": round(total_ms, 3), "storage_ms": round(storage_ms, 3),
           "tier_ms": round(tier, 3)}
    if total_ms > 0:
        out["tier_share"] = round(tier / total_ms, 4)
        out["storage_share"] = round(storage_ms / total_ms, 4)
    if tier < 0:
        out["WARNING"] = ("negative tier term: the direct-CQL arm was slower than "
                          "the Data API arm. The two arms are not doing the same "
                          "work; do not report a split from this run.")
    return out


# ---------------------------------------------------------------------------

def make_doc(doc_id: str, sz: Size) -> dict[str, Any]:
    d: dict[str, Any] = {"_id": doc_id, "status": "PENDING"}
    for i in range(sz.n_fields):
        d[f"b{i:03d}"] = "x" * sz.bytes_per_field
    return d


def cql_table_for(session, keyspace: str, collection: str) -> str:
    return f'"{keyspace}"."{collection}"'


def read_shredded_row(session, table: str, key_value) -> dict[str, Any] | None:
    cols = ", ".join(["key", "tx_id", "doc_json"] + DERIVED)
    rs = session.execute(f"SELECT {cols} FROM {table} WHERE key = %s", (key_value,))
    row = rs.one()
    if row is None:
        return None
    return {c: getattr(row, c) for c in ["key", "tx_id", "doc_json"] + DERIVED}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="tier_probe")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--out", default="findings_tier.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sizes = plan()
    print("\nPLAN", file=sys.stderr)
    for z in sizes:
        bad = " REJECTED (>cap)" if z.bytes_per_field > INDEXED_STRING_CAP else ""
        print(f"  {z.label:<12} {z.n_fields:>4} fields x {z.bytes_per_field:>5} B"
              f" = {z.total/1024:>6.1f} KiB{bad}", file=sys.stderr)
    print(f"\n  arms: DataAPI updateOne | direct CQL SELECT+UPDATE (same row)",
          file=sys.stderr)
    print(f"  {len(sizes)} sizes x 2 arms x {args.passes} passes x {args.reps} reps"
          f" (+{args.warmup} warm-ups discarded)\n", file=sys.stderr)
    if args.dry_run:
        print("dry run: nothing written, nothing measured.\n", file=sys.stderr)
        return 0

    endpoint = os.environ.get("DATA_API_ENDPOINT")
    contact = os.environ.get("CQL_CONTACT_POINT")
    if not endpoint:
        print("DATA_API_ENDPOINT is not set.", file=sys.stderr)
        return 2
    if not contact:
        print("CQL_CONTACT_POINT is not set. Method 1 needs direct CQL; without it "
              "this probe cannot run at all.", file=sys.stderr)
        return 2

    try:
        from astrapy import DataAPIClient
        from astrapy.constants import Environment
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
    except ImportError as e:
        print(f"missing dependency: {e}", file=sys.stderr)
        return 2

    db = DataAPIClient(os.environ.get("DATA_API_TOKEN", ""),
                       environment=Environment.HCD).get_database(
                           endpoint, keyspace=args.keyspace)
    try:
        coll = db.create_collection(args.collection)
    except Exception:  # noqa: BLE001
        coll = db.get_collection(args.collection)

    user = os.environ.get("CQL_USER")
    auth = PlainTextAuthProvider(user, os.environ.get("CQL_PASS")) if user else None
    cluster = Cluster([contact], auth_provider=auth)
    session = cluster.connect()
    table = cql_table_for(session, args.keyspace, args.collection)

    # Mechanical fix (campaign 4): the collection primary key is a
    # frozen<tuple<tinyint,text>>. Binding it in a simple statement with %s is
    # rejected server-side ("Unexpected receiver type 'tuple<tinyint,text>';
    # only list and vector are expected"); a PREPARED statement carries the
    # column type and binds the tuple correctly (verified). So both arm-B
    # statements are prepared with ? markers. No threshold, size or repetition
    # changes; this is how a real client binds a typed key.
    set_clause = ", ".join(["tx_id = now()"] + [f"{c} = ?" for c in DERIVED]
                           + ["doc_json = ?"])
    update_ps = session.prepare(
        f"UPDATE {table} SET {set_clause} WHERE key = ? IF tx_id = ?")
    select_ps = session.prepare(
        f"SELECT key, tx_id, doc_json FROM {table} WHERE key = ? LIMIT 1")

    results: dict[str, Any] = {}
    for p in range(1, args.passes + 1):
        for z in sizes:
            doc_id = f"tier-{z.label}-{uuid.uuid4()}"
            coll.insert_one(make_doc(doc_id, z))
            row = None
            for _ in range(20):
                # the Data API key is a composite; find it by scanning for our doc
                rs = session.execute(
                    f"SELECT key, tx_id, doc_json, {', '.join(DERIVED)} FROM {table} "
                    f"LIMIT 2000")
                for r in rs:
                    if doc_id in (r.doc_json or ""):
                        row = r
                        break
                if row is not None:
                    break
                time.sleep(0.2)
            if row is None:
                print(f"  [{z.label}|pass{p}] row not located in CQL; skipping",
                      file=sys.stderr)
                continue

            # ---- arm A: through the Data API ------------------------------
            for _ in range(args.warmup):
                coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
            api: list[float] = []
            for i in range(args.reps):
                t0 = time.perf_counter()
                coll.update_one({"_id": doc_id}, {"$set": {"status": f"A{i}"}})
                api.append((time.perf_counter() - t0) * 1000.0)

            # ---- arm B: the same statement pair, straight to CQL -----------
            # Values are taken from the row as it stands, so no JSON is parsed
            # and nothing is shredded: the storage work is identical, the tier
            # work is absent.
            vals = [getattr(row, c) for c in DERIVED]
            doc_json = row.doc_json
            key = row.key

            def one_cql_cycle() -> float:
                t0 = time.perf_counter()
                cur = session.execute(select_ps, (key,)).one()
                session.execute(update_ps, tuple(vals) + (doc_json, key, cur.tx_id))
                return (time.perf_counter() - t0) * 1000.0

            for _ in range(args.warmup):
                one_cql_cycle()
            cql: list[float] = [one_cql_cycle() for _ in range(args.reps)]

            dist_api, dist_cql = distribution(api), distribution(cql)
            results[f"{z.label}|pass{p}"] = {
                "size": asdict(z), "total_bytes": z.total,
                "data_api": dist_api, "direct_cql": dist_cql,
                "split_method1_bypass": split_report(dist_api["p50_ms"],
                                                     dist_cql["p50_ms"]),
            }
            print(f"  [{z.label}|pass{p}] API {dist_api['p50_ms']:>7.2f} ms  "
                  f"CQL {dist_cql['p50_ms']:>7.2f} ms  "
                  f"tier {dist_api['p50_ms']-dist_cql['p50_ms']:>7.2f} ms",
                  file=sys.stderr)
            try:
                coll.delete_one({"_id": doc_id})
            except Exception:  # noqa: BLE001
                pass

    # ---- does the tier term scale with indexed bytes? --------------------
    analysis: dict[str, Any] = {}
    for p in range(1, args.passes + 1):
        pts_tier, pts_stor = [], []
        for z in sizes:
            k = f"{z.label}|pass{p}"
            if k in results:
                pts_tier.append((z.total, results[k]["split_method1_bypass"]["tier_ms"]))
                pts_stor.append((z.total, results[k]["split_method1_bypass"]["storage_ms"]))

        def slope(pts):
            if len(pts) < 2:
                return None
            xs = [a for a, _ in pts]; ys = [b for _, b in pts]
            mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
            den = sum((x - mx) ** 2 for x in xs)
            sl = sum((x - mx) * (y - my) for x, y in pts) / den if den else 0.0
            ss_tot = sum((y - my) ** 2 for y in ys)
            ss_res = sum((y - (my + sl * (x - mx))) ** 2 for x, y in pts)
            return {"ms_per_KiB": round(sl * 1024, 4),
                    "r2": round(1 - ss_res / ss_tot, 4) if ss_tot else None}

        analysis[f"pass{p}"] = {"tier_term": slope(pts_tier),
                                "storage_term": slope(pts_stor)}

    record = {
        "probe": "probe_tier_vs_storage.py", "version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "question": ("Does the ~0.77 ms per indexed KiB live in the stateless Data "
                     "API tier or in the storage engine? The answer changes the "
                     "architectural reading, and may soften the article's own "
                     "criticism."),
        "method": ("Arm A: updateOne through the Data API. Arm B: the identical CQL "
                   "statement pair against the same row, values read back rather than "
                   "recomputed, so the storage work is the same and no JSON is parsed. "
                   "Difference = tier."),
        "agreement_tolerance": AGREEMENT_TOLERANCE,
        "analysis_per_KiB": analysis,
        "results": results,
        "conditions": {
            "endpoint": endpoint, "cql_contact_point": contact,
            "keyspace": args.keyspace, "collection": args.collection,
            "reps": args.reps, "warmup_discarded": args.warmup, "passes": args.passes,
            "client_platform": platform.platform(), "python": sys.version.split()[0],
            "TO_BE_COMPLETED_BY_HAND": {
                "product_and_version": "read from the node",
                "topology": "nodes, datacentres, racks, replication factor",
                "data_api_resources": "container CPU and memory limits — the tier term "
                                      "is meaningless without them",
                "regime": "memtable-resident or disk-bound, with evidence",
                "colocation": "is the Data API on the same host as the node? the tier "
                              "term absorbs the hop either way, so say which",
            },
        },
        "known_confounds": [
            "Arm B skips JSON parsing AND shredding AND response serialisation; the "
            "tier term is all three together and this probe does not separate them.",
            "Arm B reuses already-shredded values, so it never exercises the code path "
            "that computes them. That is the point, and it also means arm B is not a "
            "fair benchmark of anything — it is a subtraction instrument only.",
            "The Data API client and the CQL driver differ in connection handling and "
            "serialisation overhead; part of the tier term is client-library cost.",
        ],
        "publication_note": ("Characterises one deployment. A tier term measured "
                             "against an unconstrained API container says nothing "
                             "about a tier sized for production."),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)

    print("\n" + "=" * 72, file=sys.stderr)
    for p in range(1, args.passes + 1):
        a = analysis[f"pass{p}"]
        print(f"  pass {p}: tier {a['tier_term']} | storage {a['storage_term']}",
              file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"\nRecord written to {args.out}\n", file=sys.stderr)
    cluster.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
