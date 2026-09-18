#!/usr/bin/env python3
"""
rmw_postflush.py — closes challenge C2.

The RMW probes (M3/M10) re-read the row they just wrote, which stays memtable-
resident, so no run ever forced the SELECT-before-UPDATE onto an SSTable. This
flushes the keyspace on the dc1 nodes BEFORE EACH timed update, so every cycle's
internal SELECT reads from an SSTable (the storage-engine read path: partition
index, bloom filter, decompression) rather than from the memtable.

Honest limit it does NOT overcome: no root to drop the OS page cache, and the
freshly-flushed SSTables are tiny, so the reads are SSTable-path but page-cache-
warm — not platter-cold. This exercises the SSTable read code, not disk seeks.

Uses variant B (indexed chunks, 1/8/32/128 KB) to match M10's ×5.94, so the
post-flush growth factor is directly comparable to the memtable-under-pressure one.
Flush is NOT timed. Data API updateOne is the RMW under test.
"""
import json, os, subprocess, sys, time, uuid, statistics
from astrapy import DataAPIClient
from astrapy.constants import Environment

DC1 = ["p16-hcd-node1", "p16-hcd-node2", "p16-hcd-node3"]
SIZES_KB = (1, 8, 32, 128)
REPS, WARMUP = 30, 5


def dist(ms):
    s = sorted(ms)
    def pct(p):
        k=(len(s)-1)*p; lo,hi=int(k),min(int(k)+1,len(s)-1); return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)
    return {"n":len(s),"p50_ms":pct(.5),"p95_ms":pct(.95),"p99_ms":pct(.99),"max_ms":round(s[-1],3),
            "stdev_ms":round(statistics.pstdev(s),3) if len(s)>1 else 0.0}


def chunks(kb):
    total=kb*1024; d={}; i=0
    while total>0:
        n=min(8000,total); d[f"ballast_{i}"]="x"*n; total-=n; i+=1
    return d


def flush(ks):
    for n in DC1:
        subprocess.run(["docker","exec",n,"nodetool","flush",ks], capture_output=True)


def main():
    ks = sys.argv[1] if len(sys.argv)>1 else "cmp"
    out = sys.argv[2] if len(sys.argv)>2 else "rmw_postflush.json"
    coll_name = "rmw_postflush_probe"
    db = DataAPIClient(os.environ["DATA_API_TOKEN"], environment=Environment.HCD).get_database(
        os.environ["DATA_API_ENDPOINT"], keyspace=ks)
    try:
        coll = db.create_collection(coll_name)
    except Exception:
        coll = db.get_collection(coll_name)

    results = {}
    for kb in SIZES_KB:
        doc_id = f"pf-{kb}kb-{uuid.uuid4()}"
        coll.insert_one({"_id": doc_id, **chunks(kb), "status": "PENDING", "n": 0})
        for _ in range(WARMUP):
            flush(ks)
            coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})
        lat = []
        for i in range(REPS):
            flush(ks)                       # push the row to an SSTable; NOT timed
            t0 = time.perf_counter()
            coll.update_one({"_id": doc_id}, {"$set": {"status": f"S{i}"}})   # internal SELECT now hits SSTable
            lat.append((time.perf_counter()-t0)*1000.0)
        results[f"{kb}kb"] = dist(lat)
        print(f"  [postflush {kb:>3} KB, {len(chunks(kb))} indexed chunks] p50 {results[f'{kb}kb']['p50_ms']} ms", file=sys.stderr)
        try: coll.delete_one({"_id": doc_id})
        except Exception: pass

    small = results[f"{SIZES_KB[0]}kb"]["p50_ms"]; large = results[f"{SIZES_KB[-1]}kb"]["p50_ms"]
    growth = round(large/max(small,0.001), 2)
    rec = {"probe": "rmw_postflush.py", "variant": "B indexed chunks, flush before each update",
           "regime": "SSTable-read path (page-cache-warm; no root to drop page cache)",
           "by_size": results, "p50_growth_factor": growth,
           "comparison": {"M10_memtable_under_pressure_disk_regime": 5.94,
                          "campaign1_memtable_rf1": 7.50, "this_postflush": growth},
           "reading": ("If this growth is materially above M10's 5.94, forcing the RMW SELECT onto the "
                       "SSTable read path adds cost the memtable runs hid. If similar, the RMW read was "
                       "never the bottleneck and the coefficient is a rewrite/index-maintenance cost, not a read cost.")}
    json.dump(rec, open(out,"w"), indent=2)
    print(f"  growth {growth}x (vs M10 disk 5.94x, campaign1 memtable 7.50x)", file=sys.stderr)
    print(f"written {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
