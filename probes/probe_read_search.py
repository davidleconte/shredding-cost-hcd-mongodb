#!/usr/bin/env python3
"""
probe_read_search.py — the axes the article claims for HCD: freshness, read, filtered search.

Same host, both engines, matched regime (cache-resident). Three axes:

  A. FILTERED READ on an UNDECLARED field, at scale — HCD's "queryability without
     index design". HCD auto-indexes every field (SAI); MongoDB scans unless told.
       hcd            : findOne({qcol: v})  -> automatic SAI lookup
       mongo-default  : findOne({qcol: v})  -> COLLECTION SCAN (no index)
       mongo-wildcard : findOne({qcol: v})  -> wildcard index lookup
     Measured at a large N so the scan cost is visible.

  B. POINT READ by _id — reported honestly even though the Data API tier hop is
     expected to make HCD lose here.

  C. FRESHNESS on a regular secondary index — write, then poll findOne({qcol}) until
     found. HONEST NOTE: both engines index secondary fields SYNCHRONOUSLY, so a tie
     is expected. HCD's real freshness edge is its SYNCHRONOUS search/vector index
     versus MongoDB's ASYNCHRONOUS mongot, which needs Atlas Search / the mongot
     binary and is NOT deployable on a plain replica set — so that edge is declared
     unmeasured, not measured as a tie-that-means-parity.

Emits findings_read_search.json with the per-engine distributions and the load facts.
"""
import argparse, json, os, platform, socket, statistics, sys, time, uuid, random
from datetime import datetime, timezone


def dist(ms):
    if not ms: return {}
    s = sorted(ms)
    def pct(p):
        k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)
    return {"n":len(s),"min_ms":round(s[0],3),"p50_ms":pct(.5),"p95_ms":pct(.95),"p99_ms":pct(.99),
            "max_ms":round(s[-1],3),"stdev_ms":round(statistics.pstdev(s),3) if len(s)>1 else 0.0}

def host_fp():
    with open("/proc/cpuinfo") as fh:
        model=next((l.split(":",1)[1].strip() for l in fh if l.startswith("model name")),"?")
    return {"hostname":socket.gethostname(),"cpu_model":model,"cpu_count":os.cpu_count(),"platform":platform.platform()}

def qval(i): return f"q-{i:09d}"


def load_and_measure_mongo(uri, n, reps, warmup, wildcard):
    from pymongo import MongoClient, WriteConcern
    c=MongoClient(uri, serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db=c.get_database("rsdb"); name="rs_wild" if wildcard else "rs_def"
    coll=db.get_collection(name, write_concern=WriteConcern(w="majority", j=True))
    coll.drop()
    if wildcard: coll.create_index([("$**",1)], name="wildcard_all")
    t0=time.perf_counter()
    B=10000
    for base in range(0, n, B):
        docs=[{"_id":f"d{base+k:09d}","qcol":qval(base+k),"pay":"x"*80} for k in range(min(B,n-base))]
        coll.insert_one if False else coll.insert_many(docs, ordered=False)
    load_s=round(time.perf_counter()-t0,1)
    # A: filtered read on qcol (existing random values)
    fa=[]
    vals=[qval(random.randint(0,n-1)) for _ in range(reps+warmup)]
    for j,v in enumerate(vals):
        if j<warmup: coll.find_one({"qcol":v}); continue
        s=time.perf_counter(); coll.find_one({"qcol":v}); fa.append((time.perf_counter()-s)*1000)
    # B: point read by _id
    pb=[]
    ids=[f"d{random.randint(0,n-1):09d}" for _ in range(reps+warmup)]
    for j,i in enumerate(ids):
        if j<warmup: coll.find_one({"_id":i}); continue
        s=time.perf_counter(); coll.find_one({"_id":i}); pb.append((time.perf_counter()-s)*1000)
    # C: freshness on secondary index qcol
    attempts=[]; fresh_ms=[]
    for _ in range(40):
        mk=f"fresh-{uuid.uuid4()}"
        t=time.perf_counter(); coll.insert_one({"_id":mk,"qcol":mk,"pay":"x"})
        a=0
        while True:
            a+=1
            if coll.find_one({"qcol":mk}): break
            time.sleep(0.002)
        attempts.append(a); fresh_ms.append((time.perf_counter()-t)*1000); coll.delete_one({"_id":mk})
    idx=[i["name"] for i in coll.list_indexes()]; c.close()
    return {"n_loaded":n,"load_seconds":load_s,"indexes":idx,
            "A_filtered_read_qcol":dist(fa),"B_point_read_id":dist(pb),
            "C_freshness_secondary":{"insert_to_found_ms":dist(fresh_ms),
              "find_attempts_histogram":{str(k):attempts.count(k) for k in sorted(set(attempts))}}}


def load_and_measure_hcd(ep, tok, ks, coll_name, n, reps, warmup):
    from astrapy import DataAPIClient
    from astrapy.constants import Environment
    db=DataAPIClient(tok, environment=Environment.HCD).get_database(ep, keyspace=ks)
    try: coll=db.create_collection(coll_name)
    except Exception: coll=db.get_collection(coll_name)
    t0=time.perf_counter()
    B=100  # Data API max insertions per transaction
    for base in range(0,n,B):
        docs=[{"_id":f"d{base+k:09d}","qcol":qval(base+k),"pay":"x"*80} for k in range(min(B,n-base))]
        coll.insert_many(docs)
        if (base//B)%200==0: print(f"    hcd loaded ~{base+B}", file=sys.stderr)
    load_s=round(time.perf_counter()-t0,1)
    fa=[]; vals=[qval(random.randint(0,n-1)) for _ in range(reps+warmup)]
    for j,v in enumerate(vals):
        if j<warmup: coll.find_one({"qcol":v}); continue
        s=time.perf_counter(); coll.find_one({"qcol":v}); fa.append((time.perf_counter()-s)*1000)
    pb=[]; ids=[f"d{random.randint(0,n-1):09d}" for _ in range(reps+warmup)]
    for j,i in enumerate(ids):
        if j<warmup: coll.find_one({"_id":i}); continue
        s=time.perf_counter(); coll.find_one({"_id":i}); pb.append((time.perf_counter()-s)*1000)
    attempts=[]; fresh_ms=[]
    for _ in range(40):
        mk=f"fresh-{uuid.uuid4()}"
        t=time.perf_counter(); coll.insert_one({"_id":mk,"qcol":mk,"pay":"x"})
        a=0
        while True:
            a+=1
            if coll.find_one({"qcol":mk}): break
            time.sleep(0.002)
        attempts.append(a); fresh_ms.append((time.perf_counter()-t)*1000)
        try: coll.delete_one({"_id":mk})
        except Exception: pass
    return {"n_loaded":n,"load_seconds":load_s,"indexes":["automatic — nine SAI incl. query_text_values covering qcol"],
            "A_filtered_read_qcol":dist(fa),"B_point_read_id":dist(pb),
            "C_freshness_secondary":{"insert_to_found_ms":dist(fresh_ms),
              "find_attempts_histogram":{str(k):attempts.count(k) for k in sorted(set(attempts))}}}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["mongodb","hcd"], required=True)
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--keyspace", default="cmp")
    ap.add_argument("--collection", default="rs_probe")
    ap.add_argument("--out", default="findings_read_search.json")
    a=ap.parse_args()
    random.seed(42)
    if a.engine=="mongodb":
        uri=os.environ["MONGO_URI"]
        arms={"mongo-default":load_and_measure_mongo(uri,a.n,a.reps,a.warmup,False),
              "mongo-wildcard":load_and_measure_mongo(uri,a.n,a.reps,a.warmup,True)}
    else:
        arms={"hcd":load_and_measure_hcd(os.environ["DATA_API_ENDPOINT"],os.environ.get("DATA_API_TOKEN",""),
                                         a.keyspace,a.collection,a.n,a.reps,a.warmup)}
    rec={"probe":"probe_read_search.py","engine":a.engine,"n":a.n,"reps":a.reps,
         "run_at_utc":datetime.now(timezone.utc).isoformat(),"arms":arms,
         "host":host_fp(),
         "mongot_note":"HCD's structural freshness edge is its SYNCHRONOUS search/vector index (JVector) vs MongoDB's ASYNCHRONOUS mongot. mongot/Atlas Search is not deployable on a plain replica set, so axis C here measures only regular SECONDARY-index freshness, where BOTH engines are synchronous. A tie on C is parity on regular indexes, NOT evidence against HCD's search-freshness claim, which remains unmeasured."}
    json.dump(rec, open(a.out,"w"), indent=2)
    for arm,d in arms.items():
        print(f"  {arm}: load {d['load_seconds']}s | A filtered p50 {d['A_filtered_read_qcol'].get('p50_ms')} | B point p50 {d['B_point_read_id'].get('p50_ms')} | C fresh p50 {d['C_freshness_secondary']['insert_to_found_ms'].get('p50_ms')} attempts {d['C_freshness_secondary']['find_attempts_histogram']}", file=sys.stderr)
    print(f"written {a.out}", file=sys.stderr)

if __name__=="__main__":
    main()
