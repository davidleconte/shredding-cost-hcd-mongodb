#!/usr/bin/env python3
"""
probe_aggregation.py — the aggregation axis: HCD vs MongoDB.

STRUCTURAL FINDING (recon, not a measurement): HCD's Data API has NO server-side
aggregation pipeline. Its command allow-list exposes only countDocuments and
estimatedDocumentCount; aggregate / $group / distinct all return COMMAND_UNKNOWN.
So this is a CAPABILITY GAP, not a latency race. What is fairly measurable:

  A. count-all           both engines expose it server-side.
  B. filtered count      both expose it server-side (HCD auto-SAI; Mongo needs an
                         index or it collection-scans -> report default AND indexed).
  C. GROUP BY cat, SUM(amt) -> 10 rows:
       C1 mongo   : server-side {$group:{_id:$cat,total:{$sum:$amt},n:{$sum:1}}}
       C2 hcd     : the ONLY document-model path — client scan-and-aggregate over
                    paginated Data API find(); every matching doc crosses the wire.
       C3 cqlref  : LABELLED apples-to-oranges reference — a purpose-built *native
                    CQL* table partitioned by the group key (NOT the shredded
                    document collection). Shows what Cassandra's engine can do if
                    you abandon the document model and pre-design the schema.
                    NOTE: agg_cql_arm.py builds exactly ONE such table and times
                    two query shapes against it (C3a per-partition sweep, C3b
                    cross-partition GROUP BY). Neither is an unaligned schema, and
                    their ratio concerns a query shape rather than the schema
                    design — and does not establish even that, the supports
                    overlapping. See the warning in that probe's docstring.

Percentiles only (no mean), per the campaign convention. Ground truth is computed
in Python so every C-arm result is checked for CORRECTNESS, not just speed.
"""
import argparse, json, os, socket, statistics, sys, time
from datetime import datetime, timezone

CATS = 10

def gen(i):
    cat = f"c{i % CATS}"
    amt = ((i * 2654435761) % 1_000_000) / 1000.0   # deterministic spread 0..999.999
    return cat, round(amt, 3)

def ground_truth(n):
    per_cat_n = {f"c{k}": 0 for k in range(CATS)}
    per_cat_sum = {f"c{k}": 0.0 for k in range(CATS)}
    for i in range(n):
        cat, amt = gen(i)
        per_cat_n[cat] += 1
        per_cat_sum[cat] += amt
    return {"n": n, "per_cat_n": per_cat_n,
            "per_cat_sum": {k: round(v, 3) for k, v in per_cat_sum.items()},
            "grand_sum": round(sum(per_cat_sum.values()), 3)}

def dist(ms):
    if not ms: return {}
    s = sorted(ms)
    def pct(p):
        k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)
    return {"n":len(s),"min_ms":round(s[0],3),"p50_ms":pct(.5),"p95_ms":pct(.95),
            "p99_ms":pct(.99),"max_ms":round(s[-1],3),
            "stdev_ms":round(statistics.pstdev(s),3) if len(s)>1 else 0.0}

def host_fp():
    try:
        with open("/proc/cpuinfo") as fh:
            model=next((l.split(":",1)[1].strip() for l in fh if l.startswith("model name")),"?")
    except Exception:
        model="?"
    return {"hostname":socket.gethostname(),"cpu_model":model,"cpu_count":os.cpu_count()}

def sums_match(got, gt, tol=0.5):
    for k in gt["per_cat_sum"]:
        if abs(got.get(k, {}).get("sum", 1e18) - gt["per_cat_sum"][k]) > tol: return False
        if got.get(k, {}).get("n") != gt["per_cat_n"][k]: return False
    return True

# ---------------- MongoDB ----------------
def run_mongo(n, reps, warmup):
    from pymongo import MongoClient, WriteConcern
    gt = ground_truth(n)
    c = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db = c.get_database("aggdb")
    coll = db.get_collection("agg", write_concern=WriteConcern(w="majority", j=True))
    coll.drop()
    t0=time.perf_counter(); B=10000
    for base in range(0, n, B):
        docs=[{"_id":f"d{base+k:09d}", "cat":gen(base+k)[0], "amt":gen(base+k)[1]} for k in range(min(B,n-base))]
        coll.insert_many(docs, ordered=False)
    load_s=round(time.perf_counter()-t0,1)

    def timed(fn, r=reps, w=warmup):
        for _ in range(w): fn()
        out=[]
        for _ in range(r):
            s=time.perf_counter(); fn(); out.append((time.perf_counter()-s)*1000)
        return out

    # A count-all
    cnt_all = coll.count_documents({})
    A = dist(timed(lambda: coll.count_documents({})))
    est = coll.estimated_document_count()
    Aest = dist(timed(lambda: coll.estimated_document_count()))
    # B filtered count — default (no index on cat = collscan)
    cnt_f = coll.count_documents({"cat":"c3"})
    Bdef = dist(timed(lambda: coll.count_documents({"cat":"c3"})))
    # B filtered — WITH index on cat (fair vs HCD auto-SAI)
    coll.create_index([("cat",1)], name="cat_idx")
    Bidx = dist(timed(lambda: coll.count_documents({"cat":"c3"})))
    # C1 server-side group-by-sum
    def group():
        return list(coll.aggregate([{"$group":{"_id":"$cat","sum":{"$sum":"$amt"},"n":{"$sum":1}}}]))
    rows = group(); got = {r["_id"]:{"sum":round(r["sum"],3),"n":r["n"]} for r in rows}
    C1 = dist(timed(group, r=max(reps//2,10)))
    coll.drop(); idx_note="_id + cat_idx (created after B-default)"; c.close()
    return {"engine":"mongodb","n_loaded":n,"load_seconds":load_s,"indexes":idx_note,
            "counts":{"count_all":cnt_all,"estimated":est,"filtered_cat_c3":cnt_f,
                      "count_all_correct":cnt_all==n,"filtered_correct":cnt_f==gt["per_cat_n"]["c3"]},
            "A_count_all_ms":A,"A_estimated_count_ms":Aest,
            "B_filtered_count_default_collscan_ms":Bdef,"B_filtered_count_cat_index_ms":Bidx,
            "C1_groupby_sum_serverside_ms":C1,
            "C1_rows":len(rows),"C1_correct":sums_match(got,gt),"C1_result":got,
            "ground_truth":gt}

# ---------------- HCD (Data API, document model) ----------------
def run_hcd(n, reps, warmup, ks, cname):
    from astrapy import DataAPIClient
    from astrapy.constants import Environment
    gt = ground_truth(n)
    db = DataAPIClient(os.environ["DATA_API_TOKEN"], environment=Environment.HCD).get_database(
        os.environ["DATA_API_ENDPOINT"], keyspace=ks)
    try: coll = db.create_collection(cname)
    except Exception: coll = db.get_collection(cname)
    # fresh
    try: coll.delete_many({})
    except Exception: pass
    t0=time.perf_counter(); B=100
    for base in range(0, n, B):
        docs=[{"_id":f"d{base+k:09d}", "cat":gen(base+k)[0], "amt":gen(base+k)[1]} for k in range(min(B,n-base))]
        coll.insert_many(docs)
        if (base//B)%400==0: print(f"    hcd loaded ~{base}", file=sys.stderr)
    load_s=round(time.perf_counter()-t0,1)

    def timed(fn, r, w=warmup):
        for _ in range(w): fn()
        out=[]
        for _ in range(r):
            s=time.perf_counter(); fn(); out.append((time.perf_counter()-s)*1000)
        return out

    # A count-all (server-side countDocuments). HCD may enforce its own max-count cap
    # regardless of client upper_bound -> capture that as a finding rather than crash.
    def safe_count(filt):
        try:
            return coll.count_documents(filt, upper_bound=max(n*2,1000)), None
        except Exception as e:
            return None, type(e).__name__+": "+str(e)[:160]
    cnt_all, cnt_all_err = safe_count({})
    A = dist(timed(lambda: coll.count_documents({}, upper_bound=max(n*2,1000)), r=reps)) if cnt_all is not None else {}
    est = coll.estimated_document_count()
    Aest = dist(timed(lambda: coll.estimated_document_count(), r=reps))
    cnt_f, cnt_f_err = safe_count({"cat":"c3"})
    Bf = dist(timed(lambda: coll.count_documents({"cat":"c3"}, upper_bound=max(n*2,1000)), r=reps)) if cnt_f is not None else {}
    # C2 client scan-and-aggregate over paginated find (the ONLY doc-model path)
    def scan_agg():
        acc={f"c{k}":{"sum":0.0,"n":0} for k in range(CATS)}
        seen=0
        for d in coll.find({}, projection={"cat":1,"amt":1,"_id":0}):
            a=acc[d["cat"]]; a["sum"]+=d["amt"]; a["n"]+=1; seen+=1
        return acc, seen
    got, seen = scan_agg()
    got={k:{"sum":round(v["sum"],3),"n":v["n"]} for k,v in got.items()}
    C2 = dist(timed(lambda: scan_agg(), r=max(reps//10,3)))
    return {"engine":"hcd-dataapi","n_loaded":n,"load_seconds":load_s,
            "indexes":"automatic nine SAI (cat covered by query_text_values)",
            "counts":{"count_all":cnt_all,"count_all_error":cnt_all_err,"estimated":est,
                      "filtered_cat_c3":cnt_f,"filtered_error":cnt_f_err,
                      "count_all_correct":(cnt_all==n),"filtered_correct":(cnt_f==gt["per_cat_n"]["c3"]),
                      "estimated_note":"SSTable-metadata estimate; reads 0 until memtable flush"},
            "A_count_all_ms":A,"A_estimated_count_ms":Aest,"B_filtered_count_saidx_ms":Bf,
            "C2_client_scan_aggregate_ms":C2,"C2_docs_scanned":seen,
            "C2_correct":sums_match(got,gt),"C2_result":got,
            "C2_note":"no server-side aggregation exists; every doc is pulled to the client via paginated find and summed in app code",
            "ground_truth":gt}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["mongodb","hcd"], required=True)
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--keyspace", default="cmp")
    ap.add_argument("--collection", default="agg")
    ap.add_argument("--out", default=None)
    a=ap.parse_args()
    res = run_mongo(a.n,a.reps,a.warmup) if a.engine=="mongodb" else run_hcd(a.n,a.reps,a.warmup,a.keyspace,a.collection)
    rec={"probe":"probe_aggregation.py","run_at_utc":datetime.now(timezone.utc).isoformat(),
         "host":host_fp(),"result":res,
         "structural":"HCD Data API has no server-side aggregation pipeline (aggregate/$group/distinct = COMMAND_UNKNOWN); only countDocuments/estimatedDocumentCount. MongoDB has the full aggregation framework."}
    out=a.out or f"findings_agg_{a.engine}.json"
    json.dump(rec, open(out,"w"), indent=2)
    r=res
    print(f"[{a.engine}] load {r['load_seconds']}s  counts={r['counts']}", file=sys.stderr)
    print(json.dumps({k:v for k,v in r.items() if k.endswith('_ms')}, indent=2), file=sys.stderr)
    if a.engine=="mongodb":
        print(f"  C1 rows={r['C1_rows']} correct={r['C1_correct']}", file=sys.stderr)
    else:
        print(f"  C2 docs_scanned={r['C2_docs_scanned']} correct={r['C2_correct']}", file=sys.stderr)
    print(f"written {out}", file=sys.stderr)

if __name__=="__main__":
    main()
