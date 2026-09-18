#!/usr/bin/env python3
"""
hcd_cql_arm.py — closes challenge C1.

Adds an HCD-CQL-DIRECT arm to the comparison: the identical single-field
mutation measured against HCD's storage engine WITHOUT the Data API tier — the
same SELECT + conditional UPDATE the Data API issues (M2), run straight through
the CQL driver on the row the Data API shredded. This is HCD's storage cost with
the stateless tier (HTTP + JSON parse + shred + serialise) removed, so the
comparison against MongoDB becomes engine-vs-engine rather than stack-vs-stack.

It emits a record in probe_comparative.py's shape (arms / conditions.host /
reps / passes) so `probe_comparative.py --compare` can merge it with the
existing cmp_mongo.json and cmp_hcd.json — same host, same series, same shape,
same cache-resident regime.

This is the measurer's own code (declared, per challenge C5); the storage work
it times is identical to the Data-API path's, only the tier is absent.
"""
import json, os, platform, socket, statistics, sys, time, uuid
from astrapy import DataAPIClient
from astrapy.constants import Environment
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel

DERIVED = ["exist_keys", "array_size", "array_contains", "query_bool_values",
           "query_dbl_values", "query_text_values", "query_null_values",
           "query_timestamp_values", "query_lexical_value"]
SIZES = [(f"16x{b}B", 16, b) for b in (512, 1024, 2048, 4096, 8000)]
REPS, WARMUP, PASSES = 30, 5, 2


def dist(ms):
    s = sorted(ms)
    def pct(p):
        k = (len(s)-1)*p; lo, hi = int(k), min(int(k)+1, len(s)-1)
        return round(s[lo]+(s[hi]-s[lo])*(k-lo), 3)
    return {"n": len(s), "min_ms": round(s[0],3), "p50_ms": pct(.5), "p95_ms": pct(.95),
            "p99_ms": pct(.99), "max_ms": round(s[-1],3),
            "stdev_ms": round(statistics.pstdev(s),3) if len(s)>1 else 0.0}


def host_fp():
    with open("/proc/cpuinfo") as fh:
        model = next((l.split(":",1)[1].strip() for l in fh if l.startswith("model name")), "unknown")
    with open("/proc/meminfo") as fh:
        memkb = int(next(l for l in fh if l.startswith("MemTotal")).split()[1])
    return {"hostname": socket.gethostname(), "cpu_model": model, "cpu_count": os.cpu_count(),
            "mem_gib": round(memkb/1024/1024,1), "platform": platform.platform()}


def main():
    ks = sys.argv[1] if len(sys.argv) > 1 else "cmp"
    coll_name = "cmp_cql_probe"
    out = sys.argv[2] if len(sys.argv) > 2 else "cmp_hcdcql.json"
    tok = os.environ["DATA_API_TOKEN"]; ep = os.environ["DATA_API_ENDPOINT"]
    db = DataAPIClient(tok, environment=Environment.HCD).get_database(ep, keyspace=ks)
    try:
        coll = db.create_collection(coll_name)
    except Exception:
        coll = db.get_collection(coll_name)
    cl = Cluster([os.environ["CQL_CONTACT_POINT"]],
                 auth_provider=PlainTextAuthProvider(os.environ["CQL_USER"], os.environ["CQL_PASS"]))
    s = cl.connect(); s.default_consistency_level = ConsistencyLevel.LOCAL_QUORUM
    table = f'"{ks}"."{coll_name}"'
    set_clause = ", ".join(["tx_id = now()"] + [f"{c} = ?" for c in DERIVED] + ["doc_json = ?"])
    update_ps = s.prepare(f"UPDATE {table} SET {set_clause} WHERE key = ? IF tx_id = ?")
    select_ps = s.prepare(f"SELECT key, tx_id, doc_json FROM {table} WHERE key = ? LIMIT 1")

    results = {}
    for p in range(1, PASSES+1):
        for label, nf, bpf in SIZES:
            doc_id = f"cqlarm-{label}-{uuid.uuid4()}"
            coll.insert_one({"_id": doc_id, "status": "PENDING", **{f"b{i:03d}": "x"*bpf for i in range(nf)}})
            # locate the shredded row
            row = None
            for _ in range(20):
                for r in s.execute(f"SELECT key, tx_id, doc_json, {', '.join(DERIVED)} FROM {table} LIMIT 2000"):
                    if doc_id in (r.doc_json or ""):
                        row = r; break
                if row: break
                time.sleep(0.2)
            if not row:
                print(f"  [{label}|pass{p}] row not located; skip", file=sys.stderr); continue
            vals = [getattr(row, c) for c in DERIVED]; dj = row.doc_json; key = row.key
            def cycle():
                t0 = time.perf_counter()
                cur = s.execute(select_ps, (key,)).one()
                s.execute(update_ps, tuple(vals) + (dj, key, cur.tx_id))
                return (time.perf_counter()-t0)*1000.0
            for _ in range(WARMUP): cycle()
            lat = [cycle() for _ in range(REPS)]
            results[f"{label}|pass{p}"] = {"size": {"label": label, "n_fields": nf, "bytes_per_field": bpf},
                                           "total_bytes": nf*bpf, "update": dist(lat)}
            print(f"  [hcd-cql {label} pass{p}] p50 {results[f'{label}|pass{p}']['update']['p50_ms']:.2f} ms", file=sys.stderr)
            try: coll.delete_one({"_id": doc_id})
            except Exception: pass
    cl.shutdown()
    rec = {"probe": "hcd_cql_arm.py", "version": "1.0", "engine": "hcd-cql-direct",
           "arms": {"hcd-cql-direct": {"results": results,
                    "indexes_present": ["automatic — nine SAI per collection (same as hcd arm); tier bypassed"]}},
           "durability_mapping": {"engine": "hcd-cql-direct", "write_consistency": "LOCAL_QUORUM",
                                  "serial_consistency": "LOCAL_SERIAL (implicit on the IF)",
                                  "note": "same storage work as the Data API path (M2), tier removed"},
           "conditions": {"host": host_fp(), "reps": REPS, "passes": PASSES, "warmup_discarded": WARMUP,
                          "python": sys.version.split()[0],
                          "TO_BE_COMPLETED_BY_HAND": {"regime": "cache-resident, matched to the hcd and mongodb arms",
                                                      "note": "storage engine only; Data API tier (HTTP+parse+shred+serialise) absent"}}}
    json.dump(rec, open(out, "w"), indent=2)
    print(f"written {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
