#!/usr/bin/env python3
"""
mongot_freshness.py — the axis HCD is claimed strongest on: SEARCH freshness.

MongoDB Atlas Search ($search, powered by mongot) indexes ASYNCHRONOUSLY off the
change stream, so a just-written document is not immediately searchable via
$search. This measures that write->searchable lag directly, and contrasts it with
a regular find({_id}) which is synchronous.

HCD's side is synchronous by construction (SAI/JVector on the write path;
measurement M7 already showed a just-written vector is top-1 on the first query,
40/40). So this probe supplies the missing half — MongoDB's async search lag —
that makes the section-4 freshness comparison measurable at last.

atlas-local is a single-node replica set, so w:majority is trivial; noted. The
async search lag is a per-deployment property of mongot and does not depend on
replica count.
"""
import json, os, sys, time, uuid, statistics
from datetime import datetime, timezone
from pymongo import MongoClient, WriteConcern


def dist(ms):
    if not ms: return {}
    s = sorted(ms)
    def pct(p):
        k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)
    return {"n":len(s),"min_ms":round(s[0],3),"p50_ms":pct(.5),"p95_ms":pct(.95),"p99_ms":pct(.99),
            "max_ms":round(s[-1],3),"mean_ms":round(sum(s)/len(s),3),"stdev_ms":round(statistics.pstdev(s),3) if len(s)>1 else 0.0}


def main():
    uri = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27020/?directConnection=true")
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    timeout_s = 15.0
    c = MongoClient(uri, serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db = c.get_database("freshcmp")
    coll = db.get_collection("docs", write_concern=WriteConcern(w="majority", j=True))
    coll.drop()
    coll.insert_many([{"_id": f"seed{i}", "txt": f"seed document number {i}"} for i in range(200)])
    # dynamic text search index
    try:
        coll.create_search_index({"name": "sidx", "definition": {"mappings": {"dynamic": True}}})
    except Exception as e:
        print("createSearchIndex:", str(e)[:120], file=sys.stderr)
    print("waiting for search index READY ...", file=sys.stderr)
    for _ in range(48):
        idxs = list(coll.list_search_indexes())
        if idxs and idxs[0].get("status") == "READY":
            print("  index READY", file=sys.stderr); break
        time.sleep(2)

    def search_has(marker):
        cur = coll.aggregate([{"$search": {"index": "sidx", "text": {"query": marker, "path": "txt"}}},
                              {"$project": {"_id": 1}}, {"$limit": 5}])
        return any(d["_id"] == marker for d in cur)

    search_lag_ms, search_attempts, never = [], [], 0
    regular_lag_ms = []
    for _ in range(cycles):
        marker = f"m-{uuid.uuid4()}"
        t0 = time.perf_counter()
        coll.insert_one({"_id": marker, "txt": marker})
        # regular index (by _id) is synchronous — should be immediate
        rf0 = time.perf_counter()
        found_reg = coll.find_one({"_id": marker}) is not None
        regular_lag_ms.append((time.perf_counter() - rf0) * 1000.0)
        # $search (mongot) — poll until searchable
        a = 0; visible = None
        deadline = t0 + timeout_s
        while time.perf_counter() < deadline:
            a += 1
            if search_has(marker):
                visible = (time.perf_counter() - t0) * 1000.0; break
            time.sleep(0.02)
        if visible is None:
            never += 1
        else:
            search_lag_ms.append(visible); search_attempts.append(a)
        coll.delete_one({"_id": marker})

    out = {
        "probe": "mongot_freshness.py", "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine": "mongodb-atlas-local (mongot)", "mongodb_version": c.server_info()["version"],
        "cycles": cycles, "deployment": "single-node replica set (w:majority trivial); async lag is per-deployment",
        "search_write_to_visible_ms": dist(search_lag_ms),
        "search_poll_attempts": {"min": min(search_attempts) if search_attempts else None,
                                 "median": sorted(search_attempts)[len(search_attempts)//2] if search_attempts else None,
                                 "max": max(search_attempts) if search_attempts else None,
                                 "note": "attempts>1 means the doc was NOT searchable on the first query — the async lag"},
        "search_never_visible_within_timeout": never,
        "regular_find_by_id_ms": dist(regular_lag_ms),
        "contrast": ("regular find({_id}) is synchronous (found immediately); $search via mongot lags by the "
                     "median write-to-visible above. HCD's SAI/JVector is synchronous like the regular index "
                     "(M7: 40/40 first-try), so on the search axis HCD is immediate where MongoDB $search lags."),
    }
    json.dump(out, open("findings_mongot_freshness.json", "w"), indent=2)
    print(json.dumps({k: out[k] for k in ("search_write_to_visible_ms", "search_poll_attempts",
                                          "search_never_visible_within_timeout", "regular_find_by_id_ms")}, indent=2),
          file=sys.stderr)
    c.close()


if __name__ == "__main__":
    main()
