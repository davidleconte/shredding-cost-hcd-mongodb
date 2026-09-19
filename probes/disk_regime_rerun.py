#!/usr/bin/env python3
"""
disk_regime_rerun.py — closes the evidence gap the arXiv note declares.

WHY THIS EXISTS
---------------
The dossier's strongest architectural claim is that the per-byte mutation
coefficient is a *regime artefact*: x7.50 memtable-resident (M3), x5.94 with the
dataset on disk (M10), x1.52 once the read half of the read-modify-write cycle is
forced onto SSTables (M15).

The re-analysis in data/derived/inference.json marks two of those three
comparisons UNDETERMINABLE:

  REGIME-M10-disk-1kb-vs-128kb    "records only p50 per size — no n, no min,
                                   no max, no percentiles. Neither separation of
                                   support nor any ratio interval can be computed."
  REGIME-M15-postflush-1kb-vs-128kb  "the raw record does not store min and/or max
                                   for at least one arm"

So the evidence carrying the dossier's best argument is the evidence least able
to defend itself: two bare medians. This probe re-runs both regimes and keeps
EVERY observation, so that a third party can compute an interval, run a test, or
re-percentile — none of which is possible against the existing records.

The cause of the original defect is worth naming, because it was not carelessness
in the measurement but in the summarising: the shared dist() helper in
rmw_postflush.py and its siblings emits n / p50 / p95 / p99 / max / stdev and
DROPS BOTH the minimum and the series. Separation of support needs the minimum.
This probe does not call that helper.

PRE-REGISTERED DECISION RULES — fixed before execution, per the dossier's own
convention. Record the verdict against these, not against what the data suggest
afterwards.

  R1  If the post-flush growth factor's support at 1 KB and at 128 KB are
      DISJOINT, the collapse to ~x1.5 is established as a direction.
      If they OVERLAP, it is not, and the dossier must say so.

  R2  If the disk-regime growth factor is not separated from the memtable one by
      disjoint supports, then "the coefficient is a regime artefact" is a
      statement about medians and must be labelled as such wherever it appears.

  R3  A same-size READ control is run at every size. If the read control grows by
      a factor within 20 % of the update's growth factor, the comparison is
      INCONCLUSIVE by the campaign's own control rule (the rule that ruled
      variant A inconclusive in M3) — the growth is then not attributable to the
      mutation path.

  R4  If fewer than 25 of the 30 timed observations complete without error at any
      size, that size is reported as FAILED rather than summarised.

HONEST LIMITS, stated before anyone finds them
----------------------------------------------
  * No root, so the OS page cache cannot be dropped. Flushed SSTables are small
    and page-cache-warm: this exercises the SSTable read path, not platter seeks.
    That limit is inherited from rmw_postflush.py and is not repaired here.
  * Single sequential closed-loop client, as everywhere in this dossier. The
    percentiles are service-time percentiles at negligible utilisation, and are
    not load tails.
  * One host. Nothing here addresses concurrency or multi-node topology.

USAGE
-----
  export DATA_API_ENDPOINT=http://127.0.0.1:8181
  export ASTRA_DB_USERNAME=... ASTRA_DB_PASSWORD=...
  python3 probes/disk_regime_rerun.py > data/raw/findings_disk_regime_rerun.json

Writes JSON on stdout only; progress goes to stderr. Nothing is written in place.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from typing import Any

from astrapy import DataAPIClient
from astrapy.authentication import UsernamePasswordTokenProvider
from astrapy.constants import Environment

DC1_NODES = ["p16-hcd-node1", "p16-hcd-node2", "p16-hcd-node3"]
SIZES_KB = (1, 8, 32, 128)
REPS = 30
WARMUP = 5
INDEXED_STRING_CAP = 8000          # the interface refuses indexed strings above this
MIN_COMPLETE = 25                  # rule R4
CONTROL_TOLERANCE = 0.20           # rule R3


# --------------------------------------------------------------------------- #
# Summary that keeps what separation of support needs.
# --------------------------------------------------------------------------- #
def dist(ms: list[float]) -> dict[str, Any]:
    """Every field the dossier's other probes emit, PLUS min_ms, PLUS the series.

    min_ms is what makes separation of support computable at all; raw_ms is what
    makes an interval, a rank test or a re-percentiling possible for a reader who
    does not trust our summary. Twenty-three of twenty-five latency-bearing
    records in this dossier have neither, permanently.
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
        "raw_ms": [round(x, 3) for x in ms],   # execution order, not sorted
        "raw_note": (
            "every timed observation, in execution order. Retained so that a third "
            "party can compute an interval or run a test — which the records this "
            "probe exists to replace made impossible."
        ),
    }


def separated(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True when the two observed ranges do not intersect."""
    return a["max_ms"] < b["min_ms"] or b["max_ms"] < a["min_ms"]


def ratio_interval(slow: dict[str, Any], fast: dict[str, Any]) -> list[float]:
    """The widest ratio the observed ranges permit. Contains 1.0 iff they overlap."""
    return [round(slow["min_ms"] / fast["max_ms"], 3),
            round(slow["max_ms"] / fast["min_ms"], 3)]


# --------------------------------------------------------------------------- #
# Document shape: field count constant, indexed volume varying.
# --------------------------------------------------------------------------- #
def ballast(kb: int) -> dict[str, str]:
    total, out, i = kb * 1024, {}, 0
    while total > 0:
        n = min(INDEXED_STRING_CAP, total)
        out[f"ballast_{i}"] = "x" * n
        total -= n
        i += 1
    return out


def host_fingerprint() -> dict[str, Any]:
    """Identifies the machine, so that a reader can refuse to compare this record
    with one taken elsewhere.

    `findings_disk_rf3.json` — the record carrying the x5.94 this probe exists to
    replace — does NOT carry one. Its host is known from campaign context and not
    from the file, which is a second defect beyond the missing minimum and count.
    """
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
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1 = load5 = load15 = None
    return {
        "hostname": os.uname().nodename,
        "cpu_model": model,
        "cpu_count": os.cpu_count(),
        "mem_gib": mem_gib,
        "platform": " ".join(os.uname()),
        "loadavg_at_start": [load1, load5, load15],
        "note": ("The published x7.50 / x5.94 / x1.52 were measured on `alphadebunker`. "
                 "A record taken on any other machine cannot be compared with them: the "
                 "ratio would mix engine with hardware, which is the confound this "
                 "dossier exists to avoid."),
    }


def flush_dc1() -> None:
    """Flush is NOT timed and NOT part of any reported figure."""
    for node in DC1_NODES:
        subprocess.run(["docker", "exec", node, "nodetool", "flush"],
                       check=False, capture_output=True)


# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    endpoint = os.environ["DATA_API_ENDPOINT"]
    token = UsernamePasswordTokenProvider(os.environ["ASTRA_DB_USERNAME"],
                                          os.environ["ASTRA_DB_PASSWORD"])
    db = DataAPIClient(environment=Environment.HCD).get_database(endpoint, token=token)
    ks = f"regime_{uuid.uuid4().hex[:8]}"
    coll = db.create_collection(ks)

    result: dict[str, Any] = {"arms": {}}
    try:
        for kb in SIZES_KB:
            doc = {"_id": f"d{kb}", "status": "PENDING", **ballast(kb)}
            coll.insert_one(doc)

            # ---- arm 1: memtable-resident update, no flush between cycles ----
            mem_up, mem_rd, failed = [], [], 0
            for i in range(REPS + WARMUP):
                t0 = time.perf_counter()
                try:
                    coll.update_one({"_id": doc["_id"]},
                                    {"$set": {"status": f"S{i}"}})
                except Exception:
                    failed += 1
                    continue
                dt = (time.perf_counter() - t0) * 1000
                t1 = time.perf_counter()
                coll.find_one({"_id": doc["_id"]})           # R3 control
                dr = (time.perf_counter() - t1) * 1000
                if i >= WARMUP:
                    mem_up.append(dt)
                    mem_rd.append(dr)

            # ---- arm 2: flush before EVERY cycle, so the RMW read hits SSTables ----
            ss_up, ss_rd, failed_ss = [], [], 0
            for i in range(REPS + WARMUP):
                flush_dc1()                                   # untimed
                t0 = time.perf_counter()
                try:
                    coll.update_one({"_id": doc["_id"]},
                                    {"$set": {"status": f"F{i}"}})
                except Exception:
                    failed_ss += 1
                    continue
                dt = (time.perf_counter() - t0) * 1000
                flush_dc1()
                t1 = time.perf_counter()
                coll.find_one({"_id": doc["_id"]})
                dr = (time.perf_counter() - t1) * 1000
                if i >= WARMUP:
                    ss_up.append(dt)
                    ss_rd.append(dr)

            entry: dict[str, Any] = {"size_kb": kb}
            for label, series, nfail in (("memtable_update", mem_up, failed),
                                         ("memtable_read_control", mem_rd, failed),
                                         ("sstable_update", ss_up, failed_ss),
                                         ("sstable_read_control", ss_rd, failed_ss)):
                if len(series) < MIN_COMPLETE:                # rule R4
                    entry[label] = {"FAILED": f"only {len(series)} of {REPS} completed",
                                    "errors": nfail}
                else:
                    entry[label] = dist(series)
            result["arms"][f"{kb}KB"] = entry
            print(f"  {kb} KB done", file=sys.stderr)
    finally:
        db.drop_collection(ks)

    # ---- verdicts, against the rules fixed above and nothing else ----
    a, z = result["arms"].get("1KB", {}), result["arms"].get("128KB", {})
    v: dict[str, Any] = {}

    def growth(lo: dict, hi: dict) -> float | None:
        if "p50_ms" in lo and "p50_ms" in hi:
            return round(hi["p50_ms"] / lo["p50_ms"], 3)
        return None

    for regime in ("memtable", "sstable"):
        u_lo, u_hi = a.get(f"{regime}_update", {}), z.get(f"{regime}_update", {})
        r_lo, r_hi = a.get(f"{regime}_read_control", {}), z.get(f"{regime}_read_control", {})
        gu, gr = growth(u_lo, u_hi), growth(r_lo, r_hi)
        rule = {}
        if "min_ms" in u_lo and "min_ms" in u_hi:
            rule["R1_supports_disjoint_1KB_vs_128KB"] = separated(u_hi, u_lo)
            rule["ratio_interval"] = ratio_interval(u_hi, u_lo)
        rule["update_growth_p50"] = gu
        rule["read_control_growth_p50"] = gr
        if gu and gr:                                          # rule R3
            rule["R3_inconclusive_by_control_rule"] = abs(gu - gr) / gu < CONTROL_TOLERANCE
        v[regime] = rule

    # rule R2: is the collapse between regimes itself separated?
    mu, su = a.get("memtable_update", {}), a.get("sstable_update", {})
    if "min_ms" in mu and "min_ms" in su:
        v["R2_regimes_separated_at_1KB"] = separated(mu, su)
    result["verdicts"] = v
    try:
        result["loadavg_at_end"] = list(os.getloadavg())
    except OSError:
        result["loadavg_at_end"] = None
    return result


if __name__ == "__main__":
    out = {
        "probe": "disk_regime_rerun.py",
        "purpose": ("Re-runs the two regime comparisons that data/derived/inference.json "
                    "marks UNDETERMINABLE, retaining every observation so that separation "
                    "of support and any interval are computable."),
        "closes": ["REGIME-M10-disk-1kb-vs-128kb", "REGIME-M15-postflush-1kb-vs-128kb"],
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "host": host_fingerprint(),
        "conditions": {
            "sizes_kb": list(SIZES_KB),
            "reps_per_point": REPS,
            "warmup_discarded": WARMUP,
            "field_count": "constant per size; indexed volume varies",
            "indexed_string_cap": INDEXED_STRING_CAP,
            "flush_timed": False,
            "client": "single sequential closed-loop",
        },
        "verdict_rules_preregistered": {
            "R1": "disjoint supports at 1 KB vs 128 KB => the growth direction is established",
            "R2": "regimes not separated => 'regime artefact' is a statement about medians",
            "R3": "read control within 20 % of update growth => INCONCLUSIVE by the campaign's own rule",
            "R4": f"fewer than {MIN_COMPLETE} of {REPS} completing => the size is FAILED, not summarised",
        },
        "not_met": [
            "No root: the OS page cache is never dropped, so SSTable reads are page-cache-warm. "
            "This exercises the SSTable read path, not disk seeks.",
            "Single sequential closed-loop client; percentiles are service-time, not load tails.",
            "One host, one build. Nothing here addresses concurrency or multi-node topology.",
            "The host was shared and under uncontrolled background load; loadavg is recorded at "
            "start and at end so that a reader can judge the drift rather than trust the run.",
        ],
    }
    out["result"] = run()
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()
