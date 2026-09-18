#!/usr/bin/env python3
"""
vector_freshness_rf3.py
=======================
Tests the article's section-4 [D] claim — "a document becomes searchable as soon
as it is written" — against the ONE case it does not cover: a VECTOR search at
RF = 3, which the Data API tier runs at consistency.vector-search = LOCAL_ONE
(one replica) while writes commit at LOCAL_QUORUM (two of three replicas).

Hypothesis under test: a vector-ANN query issued immediately after a write is
acknowledged can miss the just-written vector, because the single replica it
reads (LOCAL_ONE) may be the one the LOCAL_QUORUM write did not reach, or may not
yet carry the vector in its JVector graph.

Decisive intra-run contrast, per cycle and on the SAME first attempt:
  - vector search  sort {$vector: v}   -> reads at LOCAL_ONE      (may miss)
  - key read       find_one({_id})      -> reads at LOCAL_QUORUM   (must see a LQ write)
If key(LOCAL_QUORUM)=hit while vector(LOCAL_ONE)=miss on some cycles, the window
is real and attributable to LOCAL_ONE. If both always hit, the window is shorter
than one HTTP round trip on this topology and is reported as NOT DETECTABLE — not
as a refutation of the claim.

This harness NEVER adjusts sizes/thresholds to make a result agree with the
article. 0 miss is reported as 0 miss.
"""
import argparse, json, os, random, sys, time, uuid
from astrapy import DataAPIClient
from astrapy.constants import Environment

def unit(dim):
    v = [random.gauss(0, 1) for _ in range(dim)]
    n = sum(x*x for x in v) ** 0.5 or 1.0
    return [x/n for x in v]

def pct(s, p):
    if not s: return None
    s = sorted(s); k = (len(s)-1)*p; lo, hi = int(k), min(int(k)+1, len(s)-1)
    return round(s[lo] + (s[hi]-s[lo])*(k-lo), 3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="vec_freshness")
    ap.add_argument("--dim", type=int, default=16)
    ap.add_argument("--corpus", type=int, default=200)
    ap.add_argument("--cycles", type=int, default=60)
    ap.add_argument("--rate", type=float, default=0.0, help="background vector writes/s during the cycles (0 = idle)")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--out", default="vector_freshness.json")
    a = ap.parse_args()

    tok = os.environ["DATA_API_TOKEN"]; ep = os.environ["DATA_API_ENDPOINT"]
    db = DataAPIClient(tok, environment=Environment.HCD).get_database(ep, keyspace=a.keyspace)
    try:
        coll = db.create_collection(a.collection, definition={"vector": {"dimension": a.dim, "metric": "cosine"}})
        print(f"created vector collection {a.collection} dim={a.dim} cosine", file=sys.stderr)
    except Exception as e:
        coll = db.get_collection(a.collection); print(f"reusing {a.collection}: {str(e)[:120]}", file=sys.stderr)

    print(f"seeding {a.corpus} background vectors ...", file=sys.stderr)
    for i in range(a.corpus):
        coll.insert_one({"_id": f"bg-{i}", "$vector": unit(a.dim), "kind": "bg"})

    cycles = []
    interval = 1.0/a.rate if a.rate > 0 else 0.0
    next_bg = time.perf_counter()
    print(f"running {a.cycles} freshness cycles (rate={a.rate}/s background) ...", file=sys.stderr)
    for c in range(a.cycles):
        # optional background load between cycles
        if a.rate > 0:
            now = time.perf_counter()
            while now >= next_bg:
                coll.insert_one({"_id": f"load-{uuid.uuid4()}", "$vector": unit(a.dim), "kind": "load"})
                next_bg += interval
                now = time.perf_counter()

        marker = f"probe-{uuid.uuid4()}"; v = unit(a.dim)
        t0 = time.perf_counter()
        coll.insert_one({"_id": marker, "$vector": v, "kind": "probe"})   # writes = LOCAL_QUORUM
        # FIRST attempt, both reads, vector first:
        vec_hit_first = _vector_has(coll, v, marker)                     # vector-search = LOCAL_ONE
        key_hit_first = coll.find_one({"_id": marker}) is not None       # reads = LOCAL_QUORUM
        # poll vector search until visible
        attempts = 1; visible_ms = None
        if vec_hit_first:
            visible_ms = (time.perf_counter()-t0)*1000.0
        else:
            deadline = t0 + a.timeout
            while time.perf_counter() < deadline:
                attempts += 1
                if _vector_has(coll, v, marker):
                    visible_ms = (time.perf_counter()-t0)*1000.0; break
                time.sleep(0.005)
        cycles.append({"vec_hit_first": vec_hit_first, "key_hit_first": key_hit_first,
                       "vec_attempts": attempts, "insert_to_vec_visible_ms": visible_ms})
        try: coll.delete_one({"_id": marker})
        except Exception: pass
        if (c+1) % 20 == 0: print(f"  {c+1}/{a.cycles}", file=sys.stderr)

    n = len(cycles)
    vec_first = sum(1 for x in cycles if x["vec_hit_first"])
    key_first = sum(1 for x in cycles if x["key_hit_first"])
    contrast = sum(1 for x in cycles if x["key_hit_first"] and not x["vec_hit_first"])
    never = sum(1 for x in cycles if x["insert_to_vec_visible_ms"] is None)
    att_hist = {}
    for x in cycles: att_hist[str(x["vec_attempts"])] = att_hist.get(str(x["vec_attempts"]), 0) + 1
    vis = [x["insert_to_vec_visible_ms"] for x in cycles if x["insert_to_vec_visible_ms"] is not None]
    out = {
        "test": "vector-search freshness at RF=3, vector-search=LOCAL_ONE vs writes/reads=LOCAL_QUORUM",
        "keyspace": a.keyspace, "collection": a.collection, "dim": a.dim,
        "background_corpus": a.corpus, "cycles": n, "background_rate_per_s": a.rate,
        "vector_search_first_try_hits": f"{vec_first}/{n}",
        "key_read_first_try_hits": f"{key_first}/{n}",
        "cycles_key_hit_but_vector_missed": contrast,
        "cycles_vector_never_visible_within_timeout": never,
        "vector_attempts_histogram": att_hist,
        "insert_to_vector_visible_ms": {"p50": pct(vis,0.5), "p95": pct(vis,0.95), "p99": pct(vis,0.99), "max": max(vis) if vis else None, "n": len(vis)},
        "interpretation": _interpret(vec_first, key_first, contrast, n),
    }
    json.dump({"summary": out, "cycles": cycles}, open(a.out, "w"), indent=2)
    print(json.dumps(out, indent=2), file=sys.stderr)

def _vector_has(coll, v, marker, k=5):
    try:
        cur = coll.find({}, sort={"$vector": v}, limit=k, projection={"_id": 1})
        return any(d.get("_id") == marker for d in cur)
    except Exception as e:
        print(f"    vector find error: {str(e)[:140]}", file=sys.stderr); return False

def _interpret(vec_first, key_first, contrast, n):
    if n == 0: return "no cycles"
    if contrast == 0 and vec_first == n:
        return ("NOT DETECTABLE on this topology: the vector was top-k on the first LOCAL_ONE "
                "query in every cycle. The window, if any, is shorter than one HTTP round trip "
                "on a single-host ring with sub-ms inter-replica latency. This neither confirms "
                "nor refutes the claim; it bounds the window below the measurement floor.")
    if contrast > 0:
        return (f"WINDOW OBSERVED: in {contrast}/{n} cycles the key read (LOCAL_QUORUM) found the "
                "document while the vector search (LOCAL_ONE) missed it on the same first attempt. "
                "The document was therefore replicated to a quorum but absent from the single "
                "replica the vector search read — a real 'not searchable at acknowledgement' "
                "window at RF=3 under the default vector-search=LOCAL_ONE. Whether the missing "
                "replica lacked the row or lacked it in the JVector graph is not separated here "
                "(run a second Data API with vector-search=LOCAL_QUORUM to disambiguate).")
    return (f"MIXED: vector first-try {vec_first}/{n}, key first-try {key_first}/{n}, no clean "
            "key-hit/vector-miss contrast. Report raw and widen sampling before concluding.")

if __name__ == "__main__":
    raise SystemExit(main())
