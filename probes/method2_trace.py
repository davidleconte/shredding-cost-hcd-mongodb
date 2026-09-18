#!/usr/bin/env python3
"""
method2_trace.py — the second, independent estimate for campaign 4.

For each size (16 fields x {512,1024,2048,4096,8000} B), with tracing at 1.0 on
the dc1 nodes: run N updateOne operations through the Data API, measuring the
client-observed latency, then read the coordinator-side duration of the CQL
statements the Data API issued (SELECT + conditional UPDATE) from
system_traces.sessions. Per size:

    tier_method2 (p50) = client_p50_latency - coordinator_p50(SELECT + UPDATE)

This is the tier plus the loopback hop, by a different instrument than the
bypass method. It does NOT create its own collection: it reuses tier_probe
(left by probe_tier_vs_storage) to stay inside the index budget.

Resets tracing to 0.0 on exit and verifies it.
"""
import argparse, json, os, re, sys, time, uuid, statistics, subprocess
from astrapy import DataAPIClient
from astrapy.constants import Environment
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel

SIZES = [(f"16x{b}B", 16, b) for b in (512, 1024, 2048, 4096, 8000)]
DC1 = ["p16-hcd-node1", "p16-hcd-node2", "p16-hcd-node3"]

def p50(xs):
    if not xs: return None
    s = sorted(xs); k = (len(s)-1)*0.5; lo, hi = int(k), min(int(k)+1, len(s)-1)
    return round(s[lo] + (s[hi]-s[lo])*(k-lo), 3)

def nt(node, *a):
    subprocess.run(["docker","exec",node,"nodetool",*a], capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="tier_probe")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--out", default="findings_tier_method2.json")
    a = ap.parse_args()

    tok = os.environ["DATA_API_TOKEN"]; ep = os.environ["DATA_API_ENDPOINT"]
    db = DataAPIClient(tok, environment=Environment.HCD).get_database(ep, keyspace=a.keyspace)
    try:
        coll = db.create_collection(a.collection)
    except Exception:
        coll = db.get_collection(a.collection)
    cl = Cluster([os.environ["CQL_CONTACT_POINT"]],
                 auth_provider=PlainTextAuthProvider(os.environ["CQL_USER"], os.environ["CQL_PASS"]))
    s = cl.connect(); s.default_consistency_level = ConsistencyLevel.ONE

    print("tracing 1.0 on dc1 nodes ...", file=sys.stderr)
    for n in DC1: nt(n, "settraceprobability", "1.0")

    out = {"probe": "method2_trace.py", "sizes": {}}
    try:
        for label, nf, bpf in SIZES:
            doc_id = f"m2-{label}-{uuid.uuid4()}"
            coll.insert_one({"_id": doc_id, "status": "PENDING",
                             **{f"b{i:03d}": "x"*bpf for i in range(nf)}})
            for _ in range(a.warmup):
                coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
            t_start = time.time()
            client = []
            for i in range(a.reps):
                t0 = time.perf_counter()
                coll.update_one({"_id": doc_id}, {"$set": {"status": f"M{i}"}})
                client.append((time.perf_counter()-t0)*1000.0)
            time.sleep(2)  # let traces flush
            # read coordinator durations for SELECT and UPDATE on this table since t_start
            sel, upd = [], []
            rows = s.execute("SELECT started_at, duration, parameters FROM system_traces.sessions")
            for r in rows:
                params = dict(r.parameters or {}); q = params.get("query", "") or ""
                if a.collection not in q or r.duration is None: continue
                if r.started_at is None or r.started_at.timestamp() < t_start - 1: continue
                qu = q.strip().upper()
                if qu.startswith("SELECT"): sel.append(r.duration/1000.0)     # us -> ms
                elif qu.startswith("UPDATE"): upd.append(r.duration/1000.0)
            coord = (p50(sel) or 0) + (p50(upd) or 0)
            tier2 = p50(client) - coord if client else None
            out["sizes"][label] = {"total_bytes": nf*bpf, "client_p50_ms": p50(client),
                                   "coord_select_p50_ms": p50(sel), "coord_update_p50_ms": p50(upd),
                                   "coord_sum_p50_ms": round(coord, 3),
                                   "tier_method2_p50_ms": round(tier2, 3) if tier2 is not None else None,
                                   "n_select_traces": len(sel), "n_update_traces": len(upd)}
            print(f"  {label}: client {p50(client)} - coord {round(coord,3)} = tier2 {round(tier2,3)} ms", file=sys.stderr)
            try: coll.delete_one({"_id": doc_id})
            except Exception: pass
    finally:
        print("resetting tracing to 0.0 ...", file=sys.stderr)
        for n in DC1: nt(n, "settraceprobability", "0")
        probs = []
        for n in DC1:
            r = subprocess.run(["docker","exec",n,"nodetool","gettraceprobability"], capture_output=True, text=True)
            probs.append(r.stdout.strip())
        out["tracing_reset_verified"] = probs
        print("tracing now:", probs, file=sys.stderr)

    json.dump(out, open(a.out, "w"), indent=2)
    cl.shutdown()
    print(f"written {a.out}", file=sys.stderr)

if __name__ == "__main__":
    raise SystemExit(main())
