#!/usr/bin/env python3
"""
mongo_regime_rerun.py — closes the regime asymmetry.

WHY THIS EXISTS
---------------
The dossier measures the decomposing engine in THREE regimes — memtable-resident
(M3, x7.50), dataset on disk (M10, x5.94), and read forced onto SSTables
(M15, x1.52) — and then concludes that the per-byte mutation coefficient is a
*regime artefact* rather than a fixed property.

It measures the comparator in ONE regime: cache-resident. Every MongoDB record in
data/raw/ was taken with the working set in WiredTiger's cache.

So the claim "the coefficient is a regime artefact" rests on one engine measured
three times and one engine measured once. Nobody knows whether WiredTiger shows
the same sensitivity. Three outcomes are possible and all three are informative:

  * MongoDB degrades as much as HCD out of cache
      -> the 3x-to-13x latency gap narrows, possibly a lot, and the dossier's
         mutation axis needs restating with its regime attached.
  * MongoDB degrades less
      -> the gap widens out of cache and the dossier's finding is strengthened on
         evidence it does not currently have.
  * MongoDB degrades more
      -> the direction could invert at some size, which would be the most
         interesting result in the dossier and is not currently excluded.

This probe does not decide which. It measures.

PRE-REGISTERED DECISION RULES — fixed before execution. Record the verdict
against these and not against what the numbers suggest afterwards.

  R1  If the cache-resident and evicted supports at a given size are DISJOINT,
      the regime effect is established at that size. If they OVERLAP, it is not.

  R2  The comparison that matters is the RATIO OF GROWTH FACTORS, not the
      latencies: HCD's 1KB->128KB growth against MongoDB's, each measured in its
      own evicted regime. If MongoDB's growth factor is within 20 % of HCD's, the
      dossier's "regime artefact" framing applies to BOTH engines and must be
      restated as a property of LSM-and-B-tree storage generally rather than of
      decomposition.

  R3  A same-size READ control runs at every size and regime. If the read control
      grows within 20 % of the update's growth, the comparison is INCONCLUSIVE by
      the campaign's own control rule — the rule that ruled variant A of M3
      inconclusive.

  R4  Fewer than 25 of 30 timed observations completing at any point => that
      point is FAILED, not summarised.

HOW THE CACHE IS EVICTED, and why this is the honest part
---------------------------------------------------------
There is no supported way to drop WiredTiger's cache without restarting mongod,
and restarting changes more than the cache. This probe therefore uses the method
the dossier can defend: it loads a BALLAST COLLECTION several times the size of
the configured cache and reads it end to end, evicting the collection under test
by ordinary LRU pressure. Before each evicted-arm cycle it verifies eviction
rather than assuming it, by reading serverStatus().wiredTiger.cache and recording
'bytes currently in the cache' plus the pages-read-into-cache counter.

  * If the counter does not move during the evicted arm, the working set was NOT
    evicted and the arm is recorded as NOT_EVICTED rather than reported.
  * The OS page cache is not dropped — no root — so a page read from WiredTiger
    may still be served from the page cache. This exercises the WiredTiger read
    path, not disk seeks. It is the same limit the HCD probe declares.

USAGE
-----
  export MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"
  python3 probes/mongo_regime_rerun.py > data/raw/findings_mongo_regime.json

Writes JSON on stdout only; progress goes to stderr. Creates and drops its own
database. Touches nothing else.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
import uuid
from typing import Any

from pymongo import MongoClient, WriteConcern

SIZES_KB = (1, 8, 32, 128)
REPS = 30
WARMUP = 5
MIN_COMPLETE = 25                 # rule R4
CONTROL_TOLERANCE = 0.20          # rules R2 and R3
BALLAST_MULTIPLE = 3              # ballast = this many times the configured cache


def dist(ms: list[float]) -> dict[str, Any]:
    """Keeps min_ms and the series, for the reason the HCD probe states.

    The helper shared by the other probes in this repository emits
    n / p50 / p95 / p99 / max / stdev and drops both the minimum and the series.
    Separation of support needs the minimum; an interval needs the series.
    Twenty-three of twenty-five latency-bearing records here have neither.
    """
    s = sorted(ms)

    def pct(p: float) -> float:
        k = (len(s) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)

    return {
        "n": len(s),
        "min_ms": round(s[0], 3),
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "max_ms": round(s[-1], 3),
        "stdev_ms": round(statistics.pstdev(s), 3) if len(s) > 1 else 0.0,
        "raw_ms": [round(x, 3) for x in ms],
        "raw_note": "every timed observation, in execution order",
    }


def separated(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a["max_ms"] < b["min_ms"] or b["max_ms"] < a["min_ms"]


def cache_state(db) -> dict[str, Any]:
    """WiredTiger cache figures, read rather than assumed."""
    wt = db.command("serverStatus")["wiredTiger"]["cache"]
    return {
        "bytes_in_cache": wt.get("bytes currently in the cache"),
        "max_bytes_configured": wt.get("maximum bytes configured"),
        "pages_read_into_cache": wt.get("pages read into cache"),
        "pages_evicted": wt.get("unmodified pages evicted"),
    }


def host_fingerprint() -> dict[str, Any]:
    model, mem_gib = "unknown", None
    try:
        with open("/proc/cpuinfo") as fh:
            model = next((l.split(":", 1)[1].strip() for l in fh
                          if l.startswith("model name")), "unknown")
    except OSError:
        pass
    try:
        with open("/proc/meminfo") as fh:
            mem_gib = round(int(next(l for l in fh if l.startswith("MemTotal")).split()[1])
                            / 1024 / 1024, 1)
    except (OSError, StopIteration):
        pass
    try:
        load = list(os.getloadavg())
    except OSError:
        load = None
    return {"hostname": os.uname().nodename, "cpu_model": model,
            "cpu_count": os.cpu_count(), "mem_gib": mem_gib,
            "platform": " ".join(os.uname()), "loadavg_at_start": load,
            "note": ("Must match the host of the HCD regime record for the growth-factor "
                     "comparison of rule R2 to mean anything. Comparing across hosts would "
                     "mix engine with hardware.")}


def doc(doc_id: str, kb: int) -> dict[str, Any]:
    """Field count constant, indexed volume varying — the HCD probe's shape."""
    total, d, i = kb * 1024, {"_id": doc_id, "status": "PENDING"}, 0
    while total > 0:
        n = min(8000, total)
        d[f"ballast_{i}"] = "x" * n
        total -= n
        i += 1
    return d


def run() -> dict[str, Any]:
    uri = os.environ["MONGO_URI"]
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    dbname = f"regime_{uuid.uuid4().hex[:8]}"
    db = client[dbname]
    # Durability mapped as everywhere in this dossier: majority + journalling,
    # against LOCAL_QUORUM + periodic sync on the comparator. Declared, not assumed.
    coll = db.get_collection("t", write_concern=WriteConcern(w="majority", j=True))

    out: dict[str, Any] = {"arms": {}, "cache": {}}
    try:
        out["cache"]["before"] = cache_state(db)
        cache_max = out["cache"]["before"].get("max_bytes_configured") or (1 << 30)

        # ---- arm 1: cache-resident, the regime every existing record used ----
        for kb in SIZES_KB:
            d = doc(f"d{kb}", kb)
            coll.replace_one({"_id": d["_id"]}, d, upsert=True)
            ups, rds, failed = [], [], 0
            for i in range(REPS + WARMUP):
                t0 = time.perf_counter()
                try:
                    coll.update_one({"_id": d["_id"]}, {"$set": {"status": f"S{i}"}})
                except Exception:
                    failed += 1
                    continue
                dt = (time.perf_counter() - t0) * 1000
                t1 = time.perf_counter()
                coll.find_one({"_id": d["_id"]})
                dr = (time.perf_counter() - t1) * 1000
                if i >= WARMUP:
                    ups.append(dt)
                    rds.append(dr)
            entry: dict[str, Any] = {"size_kb": kb}
            entry["cached_update"] = (dist(ups) if len(ups) >= MIN_COMPLETE
                                      else {"FAILED": f"{len(ups)}/{REPS}", "errors": failed})
            entry["cached_read_control"] = (dist(rds) if len(rds) >= MIN_COMPLETE
                                            else {"FAILED": f"{len(rds)}/{REPS}"})
            out["arms"][f"{kb}KB"] = entry
            print(f"  cached {kb} KB done", file=sys.stderr)

        # ---- evict: ballast several times the configured cache, read end to end ----
        print(f"  loading ballast ({BALLAST_MULTIPLE}x cache)…", file=sys.stderr)
        bal = db.get_collection("ballast", write_concern=WriteConcern(w=1))
        target, written, n = cache_max * BALLAST_MULTIPLE, 0, 0
        chunk = doc("x", 128)
        while written < target:
            batch = [dict(chunk, _id=f"b{n+j}") for j in range(50)]
            bal.insert_many(batch, ordered=False)
            written += 50 * 128 * 1024
            n += 50
        for _ in bal.find({}, {"_id": 1}):          # force it through the cache
            pass
        out["cache"]["after_ballast"] = cache_state(db)

        # ---- arm 2: the same series, working set now evicted ----
        for kb in SIZES_KB:
            before = cache_state(db)
            d_id = f"d{kb}"
            ups, rds, failed = [], [], 0
            for i in range(REPS + WARMUP):
                t0 = time.perf_counter()
                try:
                    coll.update_one({"_id": d_id}, {"$set": {"status": f"E{i}"}})
                except Exception:
                    failed += 1
                    continue
                dt = (time.perf_counter() - t0) * 1000
                t1 = time.perf_counter()
                coll.find_one({"_id": d_id})
                dr = (time.perf_counter() - t1) * 1000
                if i >= WARMUP:
                    ups.append(dt)
                    rds.append(dr)
            after = cache_state(db)
            moved = ((after.get("pages_read_into_cache") or 0)
                     - (before.get("pages_read_into_cache") or 0))
            entry = out["arms"][f"{kb}KB"]
            entry["pages_read_into_cache_during_arm"] = moved
            if moved <= 0:
                # eviction is verified, not assumed — rule of this probe
                entry["evicted_update"] = {
                    "NOT_EVICTED": "pages read into cache did not move during this arm; "
                                   "the working set was still resident and the arm is not reported"}
                entry["evicted_read_control"] = {"NOT_EVICTED": True}
            else:
                entry["evicted_update"] = (dist(ups) if len(ups) >= MIN_COMPLETE
                                           else {"FAILED": f"{len(ups)}/{REPS}", "errors": failed})
                entry["evicted_read_control"] = (dist(rds) if len(rds) >= MIN_COMPLETE
                                                 else {"FAILED": f"{len(rds)}/{REPS}"})
            print(f"  evicted {kb} KB done ({moved} pages read in)", file=sys.stderr)
    finally:
        client.drop_database(dbname)

    # ---- verdicts, against the rules fixed above ----
    a, z = out["arms"].get("1KB", {}), out["arms"].get("128KB", {})
    v: dict[str, Any] = {}

    def g(lo: dict, hi: dict) -> float | None:
        return round(hi["p50_ms"] / lo["p50_ms"], 3) if "p50_ms" in lo and "p50_ms" in hi else None

    for regime in ("cached", "evicted"):
        u_lo, u_hi = a.get(f"{regime}_update", {}), z.get(f"{regime}_update", {})
        r_lo, r_hi = a.get(f"{regime}_read_control", {}), z.get(f"{regime}_read_control", {})
        gu, gr = g(u_lo, u_hi), g(r_lo, r_hi)
        rule: dict[str, Any] = {"update_growth_p50": gu, "read_control_growth_p50": gr}
        if gu and gr:
            rule["R3_inconclusive_by_control_rule"] = abs(gu - gr) / gu < CONTROL_TOLERANCE
        v[regime] = rule

    # R1, per size: does the regime separate at all?
    for kb in SIZES_KB:
        e = out["arms"].get(f"{kb}KB", {})
        c_, x_ = e.get("cached_update", {}), e.get("evicted_update", {})
        if "min_ms" in c_ and "min_ms" in x_:
            v[f"R1_regime_separated_{kb}KB"] = separated(c_, x_)

    v["R2_note"] = ("Compare v['evicted']['update_growth_p50'] with the decomposing engine's "
                    "growth factor from findings_disk_regime_rerun.json, taken on the SAME host. "
                    "Within 20 % => the 'regime artefact' framing applies to both engines and must "
                    "be restated as a property of storage generally, not of decomposition.")
    out["verdicts"] = v
    try:
        out["loadavg_at_end"] = list(os.getloadavg())
    except OSError:
        out["loadavg_at_end"] = None
    return out


if __name__ == "__main__":
    rec = {
        "probe": "mongo_regime_rerun.py",
        "purpose": ("Measures the comparator in a second regime. Every existing MongoDB record in "
                    "this dossier was taken cache-resident, while the decomposing engine was "
                    "measured in three regimes; the 'regime artefact' claim therefore rests on an "
                    "asymmetry this probe exists to remove."),
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "host": host_fingerprint(),
        "conditions": {
            "sizes_kb": list(SIZES_KB),
            "reps_per_point": REPS,
            "warmup_discarded": WARMUP,
            "field_count": "constant per size; indexed volume varies",
            "write_concern": "majority + journalling, as everywhere in this dossier",
            "eviction_method": f"ballast collection {BALLAST_MULTIPLE}x the configured cache, "
                               f"read end to end; eviction VERIFIED per arm via "
                               f"pages-read-into-cache, not assumed",
            "client": "single sequential closed-loop",
        },
        "verdict_rules_preregistered": {
            "R1": "disjoint supports cached vs evicted => the regime effect is established at that size",
            "R2": "MongoDB growth within 20 % of HCD's => 'regime artefact' applies to both engines",
            "R3": "read control within 20 % of update growth => INCONCLUSIVE by the campaign's own rule",
            "R4": f"fewer than {MIN_COMPLETE} of {REPS} completing => the point is FAILED",
        },
        "not_met": [
            "The OS page cache is never dropped — no root — so a page evicted from WiredTiger may "
            "still be served from the page cache. This exercises the WiredTiger read path, not disk "
            "seeks. Same limit as the HCD probe.",
            "Eviction by ballast pressure is not the same as a cold start; it is the method that "
            "does not require restarting mongod, which would change more than the cache.",
            "Single sequential closed-loop client; percentiles are service-time, not load tails.",
            "One host, one build. Nothing here addresses concurrency or multi-node topology.",
        ],
    }
    rec["result"] = run()
    json.dump(rec, sys.stdout, indent=2, ensure_ascii=False)
    print()
