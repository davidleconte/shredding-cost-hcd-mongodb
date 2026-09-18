#!/usr/bin/env python3
"""
turn_latency.py — closes challenge D1: does MongoDB's search-freshness lag matter
at a realistic RAG turn latency, or is it swamped?

For a sweep of write->search gaps tau (the "turn latency" a RAG app spends
generating before it retrieves), write a marker, sleep tau, do ONE search, record
hit/miss. The miss-rate(tau) curve says where the freshness window bites.

  MongoDB $search (mongot, refresh interval ~1.1s): miss-rate high at small tau,
    -> 0 once tau exceeds the interval.
  HCD (synchronous on-write index): 0 miss at tau=0 already (M17); confirmed here.

If a conversational RAG turn (1-10 s of LLM generation) sits past the interval,
MongoDB never misses -> HCD's synchronous edge is moot for that use case, and
only matters for sub-second automated write-then-search.
"""
import os, sys, time, uuid, json, random
TAUS = [0, 100, 250, 500, 750, 1000, 1500, 2000, 3000]
N = 30

def run_mongo():
    from pymongo import MongoClient, WriteConcern
    c = MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27020/?directConnection=true"),
                    serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db = c.get_database("d1"); coll = db.get_collection("docs", write_concern=WriteConcern(w="majority", j=True))
    coll.drop(); coll.insert_many([{"_id": f"s{i}", "txt": f"seed {i}"} for i in range(200)])
    coll.create_search_index({"name": "sidx", "definition": {"mappings": {"dynamic": True}}})
    for _ in range(48):
        idx = list(coll.list_search_indexes())
        if idx and idx[0].get("status") == "READY": break
        time.sleep(2)
    def searchable(mk):
        cur = coll.aggregate([{"$search": {"index": "sidx", "text": {"query": mk, "path": "txt"}}},
                              {"$project": {"_id": 1}}, {"$limit": 3}])
        return any(d["_id"] == mk for d in cur)
    curve = {}
    for tau in TAUS:
        miss = 0
        for _ in range(N):
            mk = f"m-{uuid.uuid4()}"; coll.insert_one({"_id": mk, "txt": mk})
            time.sleep(tau/1000.0)
            if not searchable(mk): miss += 1
            coll.delete_one({"_id": mk})
        curve[str(tau)] = {"miss": miss, "n": N, "miss_rate": round(miss/N, 3)}
        print(f"  mongo tau={tau:>4}ms  miss {miss}/{N} = {100*miss/N:.0f}%", file=sys.stderr)
    c.close(); return curve

def run_hcd():
    from astrapy import DataAPIClient; from astrapy.constants import Environment
    def unit(d):
        v=[random.gauss(0,1) for _ in range(d)]; n=sum(x*x for x in v)**.5 or 1; return [x/n for x in v]
    db=DataAPIClient(os.environ["DATA_API_TOKEN"], environment=Environment.HCD).get_database(os.environ["DATA_API_ENDPOINT"], keyspace="cmp")
    try: coll=db.create_collection("d1_vec", definition={"vector":{"dimension":16,"metric":"cosine"}})
    except Exception: coll=db.get_collection("d1_vec")
    for i in range(200): coll.insert_one({"_id":f"s{i}","$vector":unit(16)})
    def searchable(v, mk):
        return any(d.get("_id")==mk for d in coll.find({}, sort={"$vector":v}, limit=5, projection={"_id":1}))
    curve={}
    for tau in TAUS:
        miss=0
        for _ in range(N):
            v=unit(16); mk=f"m-{uuid.uuid4()}"; coll.insert_one({"_id":mk,"$vector":v})
            time.sleep(tau/1000.0)
            if not searchable(v, mk): miss+=1
            try: coll.delete_one({"_id":mk})
            except Exception: pass
        curve[str(tau)]={"miss":miss,"n":N,"miss_rate":round(miss/N,3)}
        print(f"  hcd   tau={tau:>4}ms  miss {miss}/{N} = {100*miss/N:.0f}%", file=sys.stderr)
    return curve

def main():
    random.seed(3); eng = sys.argv[1]
    curve = run_mongo() if eng == "mongodb" else run_hcd()
    out = {"probe":"turn_latency.py","engine":eng,"N_per_tau":N,"tau_ms":TAUS,
           "miss_rate_by_tau_ms": curve,
           "reading":"miss_rate is the fraction of just-written docs NOT returned by a single search issued tau ms after the write. HCD synchronous -> 0 at tau=0; MongoDB $search -> falls to 0 once tau exceeds the ~1.1s refresh interval."}
    json.dump(out, open(f"findings_turn_{eng}.json","w"), indent=2)
    print(f"written findings_turn_{eng}.json", file=sys.stderr)

if __name__ == "__main__":
    main()
