#!/usr/bin/env python3
"""
probe_agg_7bis.py — campaign 7 replayed, corrected.

WRITTEN BY THE MEASURER. Weakest provenance class in the register (audit I2).
Declared here, before any number is read.

What this closes, against campaign 7 (M20-M23) and its adversarial pass D6-D14:

  RAW SERIES   every observation is retained, not only the percentile summary.
               23 of 25 latency-bearing files in this dossier discarded them,
               which is why no confidence interval is computable by anyone.
               This is the single highest-value fix here and it costs nothing.
  D6           n = 15 on the HCD scan arm against n = 3, so the exact
               permutation floor moves from 1/C(18,15)=1.23e-3 to
               1/C(30,15)=6.45e-9. No warm-up on a 134-second full-collection
               scan: there is no meaningful warm-up phase and discarding one
               would cost two minutes for nothing. Declared, not hidden.
  D9           estimatedDocumentCount measured pre-flush, post-flush and
               post-compaction, not only cold.
  D10          index state of every arm recorded IN THE JSON; MongoDB $group
               measured both without and with an index on the group key.
  D13          ingest measured at MATCHED batch size (100, the Data API's
               documented ceiling) and at MongoDB's native 10 000, so the
               batch-ceiling term separates from the per-document term.
  D14          three query shapes: low cardinality (10 groups), high
               cardinality (100 000 groups), and filtered.

PRE-REGISTERED VERDICT RULES, fixed before execution:
  R1  HCD scan p50 outside +/-20% of 133984.229 ms => the n=3 original was not
      representative, and the report says so in its first line.
  R2  post-flush estimatedDocumentCount correct => M22 is a cold-start
      property and nothing more.
  R3  $group without the index not slower than with => D10's resolution holds.
      Slower => D10 was wrong and the report says so.
  R4  MongoDB at batch 100 losing most of its ingest lead => the 46.3x was
      mostly a batch-size artefact and is withdrawn.
  R5  aggregation gap narrowing at high cardinality => D14 was right and M23
      is bounded to its query shape.

Closed-loop, single sequential client. Declared: requirement 1 of the
article's Part II section 4 (fixed offered rate) is NOT met and is not
claimed. A 33-minute continuous scan loads the ring it measures; declared.
"""
import argparse, json, os, platform, socket, statistics, subprocess, sys, time
from collections import defaultdict
from datetime import datetime, timezone

DC1 = ["p16-hcd-node1", "p16-hcd-node2", "p16-hcd-node3"]
NCAT, NUKEY = 10, 100_000


def gen(i):
    return {"_id": f"d{i:09d}",
            "cat": f"c{i % NCAT}",
            "ukey": f"u{i % NUKEY}",
            "amt": round(((i * 2654435761) % 1_000_000) / 1000.0, 3),
            "flag": (i % 3 == 0)}


def ground_truth(n):
    gc, gu, gf = defaultdict(lambda: [0.0, 0]), defaultdict(lambda: [0.0, 0]), defaultdict(lambda: [0.0, 0])
    for i in range(n):
        d = gen(i)
        for g, k in ((gc, d["cat"]), (gu, d["ukey"])):
            g[k][0] = round(g[k][0] + d["amt"], 3); g[k][1] += 1
        if d["flag"]:
            gf[d["cat"]][0] = round(gf[d["cat"]][0] + d["amt"], 3); gf[d["cat"]][1] += 1
    f = lambda g: {k: {"sum": round(v[0], 3), "n": v[1]} for k, v in g.items()}
    return {"by_cat": f(gc), "by_ukey_groups": len(gu), "by_cat_filtered": f(gf), "n": n}


def dist(ms):
    """Summary AND the raw series. The series is the point."""
    if not ms: return {}
    s = sorted(ms)
    def pct(p):
        k = (len(s) - 1) * p; lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)
    return {"n": len(s), "min_ms": round(s[0], 3), "p50_ms": pct(.5), "p95_ms": pct(.95),
            "p99_ms": pct(.99), "max_ms": round(s[-1], 3),
            "stdev_ms": round(statistics.pstdev(s), 3) if len(s) > 1 else 0.0,
            "raw_ms": [round(x, 3) for x in ms],
            "raw_note": "every timed observation, in execution order. Retained so that a third "
                        "party can compute an interval or run a test, which 23 of 25 files in "
                        "this dossier made impossible."}


def timed(fn, r):
    out = []
    for _ in range(r):
        t = time.perf_counter(); fn(); out.append((time.perf_counter() - t) * 1000.0)
    return out


def host_fp():
    with open("/proc/cpuinfo") as fh:
        m = next((l.split(":", 1)[1].strip() for l in fh if l.startswith("model name")), "?")
    la = os.getloadavg()
    return {"hostname": socket.gethostname(), "cpu_model": m, "cpu_count": os.cpu_count(),
            "loadavg_1_5_15": [round(x, 2) for x in la],
            "load_note": "the host carries an unrelated demo estate throughout; declared, never subtracted"}


def nodetool(*a):
    for n in DC1:
        subprocess.run(["docker", "exec", n, "nodetool", *a], capture_output=True)


# ───────────────────────────────── MongoDB ─────────────────────────────────
def run_mongo(n, reps):
    from pymongo import MongoClient, WriteConcern
    c = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000); c.admin.command("ping")
    db = c.get_database("aggdb7b")
    res = {"engine": "mongodb", "server_version": c.server_info()["version"], "n_loaded": n}

    # ---- D13: ingest at MATCHED batch (100) and at native (10 000) ----
    res["ingest"] = {}
    for B, name in ((100, "batch_100_matched_to_dataapi_ceiling"), (10000, "batch_10000_native")):
        col = db.get_collection("load_" + str(B), write_concern=WriteConcern(w="majority", j=True))
        col.drop()
        t0 = time.perf_counter()
        for base in range(0, n, B):
            col.insert_many([gen(base + k) for k in range(min(B, n - base))], ordered=False)
        el = round(time.perf_counter() - t0, 3)
        res["ingest"][name] = {"seconds": el, "batch_size": B, "calls": (n + B - 1) // B,
                               "ms_per_call": round(el * 1000 / ((n + B - 1) // B), 3),
                               "docs_per_s": round(n / el, 1)}
        print(f"  mongo ingest B={B}: {el}s", file=sys.stderr)
        if B == 100: col.drop()

    coll = db.get_collection("load_10000", write_concern=WriteConcern(w="majority", j=True))

    # ---- counts, with index state recorded (D10) ----
    res["counts"] = {"count_all": coll.count_documents({}), "estimated": coll.estimated_document_count(),
                     "filtered_cat_c3": coll.count_documents({"cat": "c3"})}
    res["A_count_all_ms"] = dist(timed(lambda: coll.count_documents({}), reps))
    res["A_estimated_ms"] = dist(timed(lambda: coll.estimated_document_count(), reps))

    SHAPES = {
        "low_cardinality_10_groups": [{"$group": {"_id": "$cat", "sum": {"$sum": "$amt"}, "n": {"$sum": 1}}}],
        "high_cardinality_100k_groups": [{"$group": {"_id": "$ukey", "sum": {"$sum": "$amt"}, "n": {"$sum": 1}}}],
        "filtered_then_grouped": [{"$match": {"flag": True}},
                                  {"$group": {"_id": "$cat", "sum": {"$sum": "$amt"}, "n": {"$sum": 1}}}],
    }
    gt = ground_truth(n)
    res["C_groupby"] = {}
    for idx_state in ("no_index_beyond_id", "cat_and_ukey_and_flag_indexed"):
        if idx_state.startswith("cat_and"):
            coll.create_index([("cat", 1)], name="cat_idx")
            coll.create_index([("ukey", 1)], name="ukey_idx")
            coll.create_index([("flag", 1)], name="flag_idx")
        res["C_groupby"][idx_state] = {"indexes_present": sorted(i["name"] for i in coll.list_indexes())}
        for sname, pipe in SHAPES.items():
            rows = list(coll.aggregate(pipe))
            got = {r["_id"]: {"sum": round(r["sum"], 3), "n": r["n"]} for r in rows}
            if sname == "low_cardinality_10_groups":   ok = got == gt["by_cat"]
            elif sname == "filtered_then_grouped":     ok = got == gt["by_cat_filtered"]
            else:                                      ok = len(got) == gt["by_ukey_groups"]
            res["C_groupby"][idx_state][sname] = {
                "ms": dist(timed(lambda p=pipe: list(coll.aggregate(p)), reps)),
                "rows": len(rows), "correct_against_ground_truth": ok}
            print(f"  mongo $group {idx_state[:12]} {sname[:22]}: "
                  f"p50 {res['C_groupby'][idx_state][sname]['ms']['p50_ms']} ms correct={ok}", file=sys.stderr)

    res["B_filtered_count_ms"] = dist(timed(lambda: coll.count_documents({"cat": "c3"}), reps))
    res["index_state_note"] = ("D10: campaign 7 did not record which index state its $group ran "
                               "under. Both states are measured here and both are named in the record.")
    coll.drop(); c.close()
    return res


# ─────────────────────────────────── HCD ───────────────────────────────────
def run_hcd(n, reps, ks, cname):
    from astrapy import DataAPIClient
    from astrapy.constants import Environment
    db = DataAPIClient(os.environ["DATA_API_TOKEN"], environment=Environment.HCD).get_database(
        os.environ["DATA_API_ENDPOINT"], keyspace=ks)
    try: coll = db.create_collection(cname)
    except Exception: coll = db.get_collection(cname)
    res = {"engine": "hcd-dataapi", "n_loaded": n,
           "indexes": "automatic nine SAI; cat/ukey covered by query_text_values, amt by query_dbl_values",
           "index_state_note": "D10: automatic and not selectable; recorded rather than assumed."}

    B = 100
    t0 = time.perf_counter()
    for base in range(0, n, B):
        coll.insert_many([gen(base + k) for k in range(min(B, n - base))])
        if (base // B) % 250 == 0: print(f"    hcd loaded ~{base+B}", file=sys.stderr)
    el = round(time.perf_counter() - t0, 3)
    res["ingest"] = {"batch_100_dataapi_ceiling": {
        "seconds": el, "batch_size": B, "calls": (n + B - 1) // B,
        "ms_per_call": round(el * 1000 / ((n + B - 1) // B), 3), "docs_per_s": round(n / el, 1),
        "note": "100 is the documented maximum insertions per transaction; not a choice."}}

    def safe(fn):
        try: return fn(), None
        except Exception as e: return None, type(e).__name__ + ": " + str(e)[:150]

    def counts_now(tag):
        ca, ea = safe(lambda: coll.count_documents({}, upper_bound=max(n * 2, 1000)))
        est, _ = safe(lambda: coll.estimated_document_count())
        return {"phase": tag, "count_all": ca, "count_all_error": ea, "estimated": est,
                "estimated_correct": est == n}

    res["D9_estimate_by_phase"] = [counts_now("pre_flush_cold")]
    res["A_estimated_ms_pre_flush"] = dist(timed(lambda: coll.estimated_document_count(), reps))

    # ---- the scan: measured ONCE at n=reps, all three shapes from the same pages ----
    gt = ground_truth(n)
    def scan_and_aggregate():
        gc, gu, gf = defaultdict(lambda: [0.0, 0]), defaultdict(lambda: [0.0, 0]), defaultdict(lambda: [0.0, 0])
        seen = 0
        for d in coll.find({}, projection={"cat": 1, "ukey": 1, "amt": 1, "flag": 1, "_id": 0}):
            seen += 1; a = d["amt"]
            gc[d["cat"]][0] += a; gc[d["cat"]][1] += 1
            gu[d["ukey"]][0] += a; gu[d["ukey"]][1] += 1
            if d.get("flag"): gf[d["cat"]][0] += a; gf[d["cat"]][1] += 1
        return seen, gc, gu, gf

    lat, last = [], None
    for r in range(reps):
        t = time.perf_counter(); last = scan_and_aggregate(); e = (time.perf_counter() - t) * 1000.0
        lat.append(e); print(f"    hcd scan {r+1}/{reps}: {e/1000:.1f}s", file=sys.stderr)
    seen, gc, gu, gf = last
    fmt = lambda g: {k: {"sum": round(v[0], 3), "n": v[1]} for k, v in g.items()}
    res["C2_scan_and_aggregate_ms"] = dist(lat)
    res["C2_docs_scanned"] = seen
    res["C2_shapes"] = {
        "low_cardinality_10_groups": {"correct": fmt(gc) == gt["by_cat"], "rows": len(gc)},
        "high_cardinality_100k_groups": {"correct": len(gu) == gt["by_ukey_groups"], "rows": len(gu)},
        "filtered_then_grouped": {"correct": fmt(gf) == gt["by_cat_filtered"], "rows": len(gf)}}
    res["C2_design_note"] = ("One scan pass serves all three shapes: the Data API has no aggregation "
                             "surface, so the scan pulls the whole corpus regardless of grouping and "
                             "the grouping itself is client-side arithmetic. Measuring three separate "
                             "scans would have measured the same transport three times.")

    # ---- D9: flush, then compaction, re-measure ----
    print("  nodetool flush cmp ...", file=sys.stderr); nodetool("flush", ks)
    res["D9_estimate_by_phase"].append(counts_now("post_flush"))
    res["A_estimated_ms_post_flush"] = dist(timed(lambda: coll.estimated_document_count(), reps))
    print("  nodetool compact cmp ...", file=sys.stderr); nodetool("compact", ks)
    res["D9_estimate_by_phase"].append(counts_now("post_compaction"))
    res["A_estimated_ms_post_compaction"] = dist(timed(lambda: coll.estimated_document_count(), reps))

    # ---- axis C again, now on a flushed/compacted (non-cache) regime ----
    lat2 = []
    for r in range(max(reps // 3, 3)):
        t = time.perf_counter(); scan_and_aggregate(); e = (time.perf_counter() - t) * 1000.0
        lat2.append(e); print(f"    hcd scan post-compaction {r+1}: {e/1000:.1f}s", file=sys.stderr)
    res["C2_scan_post_compaction_ms"] = dist(lat2)
    res["regime_note"] = ("Campaign 7 ran entirely cache-resident, which M22's zero proved. Axis C is "
                          "measured here both before any flush and after flush + major compaction, so "
                          "the regime is no longer an unexamined condition.")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["mongodb", "hcd"], required=True)
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--reps", type=int, default=15)
    ap.add_argument("--keyspace", default="cmp"); ap.add_argument("--collection", default="agg7b")
    a = ap.parse_args()
    r = run_mongo(a.n, a.reps) if a.engine == "mongodb" else run_hcd(a.n, a.reps, a.keyspace, a.collection)
    rec = {"probe": "probe_agg_7bis.py", "campaign": "7bis — aggregation replayed, corrected",
           "run_at_utc": datetime.now(timezone.utc).isoformat(), "host": host_fp(),
           "provenance": "WRITTEN BY THE MEASURER — weakest evidence class (audit I2), declared before the run",
           "closes": ["raw series retained", "D6 n=15", "D9 estimate by phase", "D10 index state recorded",
                      "D13 matched batch size", "D14 three query shapes"],
           "not_met": ["fixed offered rate (Part II section 4, requirement 1) — closed loop, declared",
                       "concurrency", "multi-host", "storage class"],
           "verdict_rules_preregistered": {
               "R1": "HCD scan p50 outside +/-20% of 133984.229 ms => n=3 original not representative",
               "R2": "post-flush estimate correct => M22 is a cold-start property only",
               "R3": "$group no slower without the index => D10 resolution holds",
               "R4": "MongoDB batch-100 ingest lead collapses => 46.3x withdrawn",
               "R5": "gap narrows at high cardinality => M23 bounded to its query shape"},
           "result": r}
    p = f"findings_agg7bis_{a.engine}.json"
    json.dump(rec, open(p, "w"), indent=2)
    print(f"written {p}", file=sys.stderr)


if __name__ == "__main__":
    main()
