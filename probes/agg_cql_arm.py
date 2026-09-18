#!/usr/bin/env python3
"""
agg_cql_arm.py — the LABELLED, apples-to-oranges CQL-native reference for the
aggregation axis (C3). This is NOT the HCD document model / Data API. It is a
purpose-built *native CQL table*, pre-partitioned by the group key, with typed
columns. It shows what Cassandra's storage engine can do when you abandon the
document model and design the schema for the aggregation up front.

  table: cmp.agg_cql(cat text, id text, amt double, PRIMARY KEY(cat, id))
         -> 10 partitions (one per cat), 20k rows each, RF=3.

  C3a per-partition : SELECT SUM(amt),COUNT(*) WHERE cat=? , swept over 10 cats.
        Single-partition, server-side aggregation — CQL's genuine best case.
  C3b full GROUP BY : SELECT cat,SUM(amt),COUNT(*) ... GROUP BY cat.
        One statement, server-side, returns 10 rows — but a cross-partition
        range scan (coordinator full-scan). The classic Cassandra anti-pattern.

Reads at LOCAL_QUORUM to match the Data API path. Correctness checked vs the
same deterministic ground truth as probe_aggregation.py.
"""
import json, os, sys, time, statistics
from datetime import datetime, timezone
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from cassandra.concurrent import execute_concurrent_with_args

CATS = 10
def gen(i):
    cat = f"c{i % CATS}"
    amt = ((i * 2654435761) % 1_000_000) / 1000.0
    return cat, round(amt, 3)

def ground_truth(n):
    cn={f"c{k}":0 for k in range(CATS)}; cs={f"c{k}":0.0 for k in range(CATS)}
    for i in range(n):
        c,a=gen(i); cn[c]+=1; cs[c]+=a
    return {"per_cat_n":cn,"per_cat_sum":{k:round(v,3) for k,v in cs.items()},
            "grand_sum":round(sum(cs.values()),3),"n":n}

def dist(ms):
    s=sorted(ms)
    def pct(p):
        k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)
    return {"n":len(s),"min_ms":round(s[0],3),"p50_ms":pct(.5),"p95_ms":pct(.95),
            "p99_ms":pct(.99),"max_ms":round(s[-1],3),"stdev_ms":round(statistics.pstdev(s),3) if len(s)>1 else 0.0}

def main():
    n=int(os.environ.get("AGG_N","200000")); reps=int(os.environ.get("AGG_REPS","15"))
    cp=os.environ.get("CQL_CONTACT_POINT","127.0.0.1"); port=int(os.environ.get("CQL_PORT","9142"))
    ks="cmp"; gt=ground_truth(n)
    cl=Cluster([cp],port=port,auth_provider=PlainTextAuthProvider(
        os.environ.get("CQL_USER","cassandra"),os.environ.get("CQL_PASS","cassandra")))
    s=cl.connect(); s.default_consistency_level=ConsistencyLevel.LOCAL_QUORUM
    s.default_timeout=120
    s.execute(f"DROP TABLE IF EXISTS {ks}.agg_cql")
    s.execute(f"CREATE TABLE {ks}.agg_cql (cat text, id text, amt double, PRIMARY KEY (cat, id))")
    ins=s.prepare(f"INSERT INTO {ks}.agg_cql (cat,id,amt) VALUES (?,?,?)")
    t0=time.perf_counter()
    rows=[]
    for i in range(n):
        c,a=gen(i); rows.append((c,f"d{i:09d}",a))
        if len(rows)==5000:
            execute_concurrent_with_args(s,ins,rows,concurrency=64); rows=[]
    if rows: execute_concurrent_with_args(s,ins,rows,concurrency=64)
    load_s=round(time.perf_counter()-t0,1)
    print(f"  cql loaded {n} in {load_s}s",file=sys.stderr)

    perpart=s.prepare(f"SELECT SUM(amt) AS sm, COUNT(*) AS n FROM {ks}.agg_cql WHERE cat=?")
    def sweep_perpartition():
        got={}
        for k in range(CATS):
            r=s.execute(perpart,(f"c{k}",)).one(); got[f"c{k}"]={"sum":round(r.sm,3),"n":r.n}
        return got
    def full_groupby():
        got={}
        for r in s.execute(f"SELECT cat, SUM(amt) AS sm, COUNT(*) AS n FROM {ks}.agg_cql GROUP BY cat"):
            got[r.cat]={"sum":round(r.sm,3),"n":r.n}
        return got

    g1=sweep_perpartition(); g2=full_groupby()
    def correct(g): return all(abs(g[k]["sum"]-gt["per_cat_sum"][k])<0.5 and g[k]["n"]==gt["per_cat_n"][k] for k in gt["per_cat_sum"])
    # warmup
    for _ in range(3): sweep_perpartition(); full_groupby()
    a=[]; b=[]
    for _ in range(reps):
        t=time.perf_counter(); sweep_perpartition(); a.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); full_groupby(); b.append((time.perf_counter()-t)*1000)

    rec={"probe":"agg_cql_arm.py","run_at_utc":datetime.now(timezone.utc).isoformat(),
         "LABEL":"APPLES-TO-ORANGES REFERENCE — native CQL, NOT the HCD document model / Data API. "
                 "Requires abandoning the document model and pre-designing a table partitioned by the group key.",
         "table":"cmp.agg_cql(cat,id,amt) PK(cat,id), RF=3, reads LOCAL_QUORUM",
         "n_loaded":n,"load_seconds":load_s,
         "C3a_per_partition_sweep_10q_ms":dist(a),"C3a_correct":correct(g1),
         "C3b_full_groupby_cat_ms":dist(b),"C3b_correct":correct(g2),
         "C3b_is":"cross-partition range scan (coordinator full-scan anti-pattern), returns 10 rows",
         "result_perpartition":g1,"ground_truth":gt}
    s.execute(f"DROP TABLE IF EXISTS {ks}.agg_cql")
    cl.shutdown()
    json.dump(rec,open("findings_agg_cqlref.json","w"),indent=2)
    print(json.dumps({"C3a_per_partition_sweep_10q_ms":rec["C3a_per_partition_sweep_10q_ms"],
                      "C3b_full_groupby_cat_ms":rec["C3b_full_groupby_cat_ms"],
                      "C3a_correct":rec["C3a_correct"],"C3b_correct":rec["C3b_correct"]},indent=2),file=sys.stderr)
    print("written findings_agg_cqlref.json (table dropped)",file=sys.stderr)

if __name__=="__main__":
    main()
