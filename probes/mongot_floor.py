#!/usr/bin/env python3
"""
mongot_floor.py — closes challenge C10: the TRUE floor of mongot's search lag.

The first measurement (mongot_freshness.py) inserted then immediately polled, so
each cycle waited for the next commit and the cycles SELF-SYNCHRONISED to the
commit schedule — giving a tight ~1015 ms that could be either a fixed pipeline
delay or a refresh interval sampled only at its worst phase.

This de-synchronises: before each insert it sleeps a RANDOM 0–1200 ms, so the
inserts land at uniformly random phases of the commit cycle. Then it polls at
5 ms until the doc is searchable and records the true insert->visible lag.

Interpretation:
  - if the lag is a Lucene-style REFRESH INTERVAL of T, a doc inserted at phase p
    becomes visible at the next commit, so lag ≈ T - p is UNIFORM on [0, T]; the
    MINIMUM observed lag approaches 0 and the mean ≈ T/2. The true floor is ~0.
  - if it is a FIXED pipeline delay D (change-stream read + ingest + commit), every
    lag clusters at ~D regardless of phase; the floor is ~D. ~1 s is then real.

The min and the shape of the distribution decide it.
"""
import os, sys, time, uuid, random, json, statistics
from datetime import datetime, timezone
from pymongo import MongoClient, WriteConcern

def main():
    uri = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27020/?directConnection=true")
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    random.seed(7)
    c = MongoClient(uri, serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db = c.get_database("floorcmp")
    coll = db.get_collection("docs", write_concern=WriteConcern(w="majority", j=True))
    coll.drop()
    coll.insert_many([{"_id": f"seed{i}", "txt": f"seed {i}"} for i in range(200)])
    coll.create_search_index({"name": "sidx", "definition": {"mappings": {"dynamic": True}}})
    print("waiting index READY ...", file=sys.stderr)
    for _ in range(48):
        idx = list(coll.list_search_indexes())
        if idx and idx[0].get("status") == "READY": break
        time.sleep(2)

    def searchable(mk):
        cur = coll.aggregate([{"$search": {"index": "sidx", "text": {"query": mk, "path": "txt"}}},
                              {"$project": {"_id": 1}}, {"$limit": 3}])
        return any(d["_id"] == mk for d in cur)

    lags = []
    for _ in range(cycles):
        time.sleep(random.uniform(0.0, 1.2))          # de-synchronise: random phase
        mk = f"m-{uuid.uuid4()}"
        t0 = time.perf_counter()
        coll.insert_one({"_id": mk, "txt": mk})
        while True:
            if searchable(mk):
                lags.append((time.perf_counter() - t0) * 1000.0); break
            if time.perf_counter() - t0 > 8: lags.append(None); break
            time.sleep(0.005)
        coll.delete_one({"_id": mk})
    c.close()

    ok = [x for x in lags if x is not None]
    s = sorted(ok)
    def pct(p): k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),1)
    dist = {"n": len(s), "min_ms": round(s[0],1), "p10_ms": pct(.1), "p50_ms": pct(.5),
            "p90_ms": pct(.9), "max_ms": round(s[-1],1), "mean_ms": round(sum(s)/len(s),1),
            "stdev_ms": round(statistics.pstdev(s),1)}
    # verdict: uniform (refresh interval) vs clustered (fixed delay)
    spread = dist["max_ms"] - dist["min_ms"]
    near_zero = dist["min_ms"] < 0.2 * dist["max_ms"]
    verdict = ("REFRESH INTERVAL — lag is broadly spread and the minimum approaches zero, so the true "
               "best-case freshness floor is near 0 and the ~1 s was the worst phase of a periodic commit; "
               "mean lag ≈ interval/2") if (near_zero and spread > 0.5*dist["max_ms"]) else (
               "FIXED PIPELINE DELAY — lag clusters regardless of insert phase, so ~%d ms is a real floor for "
               "this mongot build, not a phase artefact" % dist["p50_ms"])
    out = {"probe": "mongot_floor.py", "run_at_utc": datetime.now(timezone.utc).isoformat(),
           "method": "random 0-1200 ms pre-insert sleep to sample all commit-cycle phases, then 5 ms polling",
           "de_synchronised_lag_ms": dist, "verdict": verdict,
           "first_measurement_was": "~1015 ms tight (self-synchronised, worst phase)"}
    json.dump(out, open("findings_mongot_floor.json", "w"), indent=2)
    print(json.dumps(out, indent=2), file=sys.stderr)

if __name__ == "__main__":
    main()
