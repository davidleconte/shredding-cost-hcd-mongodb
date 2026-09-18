#!/usr/bin/env python3
"""cql_groupby_expressibility.py — is a CQL GROUP BY on the group key expressible
against a table that is NOT partitioned by it?

WHY THIS EXISTS. Challenge D12 (docs/challenges-campagne7.fr.md) withdrew the
campaign-7 clause that reaching HCD's native-CQL aggregation path costs
"pre-designing a table partitioned by the group key". That withdrawal was itself
annulled on 18 September 2026, and the annulment rests on a structural claim:
that the C3b arm's statement is not merely slower against an unaligned table but
REFUSED by the engine, so C3b presupposes the pre-partitioning it was read as
refuting.

That claim was first established in a terminal and published in RESULTS.md,
LIMITATIONS.md and the challenge document as "measured on the ring" WITHOUT any
file under data/raw/ to cite. This repository's own reading rule 9 says a
magnitude quoted without its file cannot be checked. This probe repairs that: it
runs the comparison and writes the result where every other claim's evidence
lives.

PRE-REGISTERED RULES, fixed before execution:

  R1  If `SELECT cat, SUM(amt) ... GROUP BY cat` is ACCEPTED against a table whose
      PRIMARY KEY does not carry `cat`, the annulment's structural argument FAILS
      and must be withdrawn from RESULTS.md, LIMITATIONS.md and the challenge
      document. The x1.28 would then be the only thing in evidence either way.
  R2  If the aligned table's GROUP BY returns a result that does not match the
      ground truth computed in Python, the whole comparison is void.
  R3  The C3a sweep shape (`SELECT SUM(amt) ... WHERE cat=?`) is tested on BOTH
      tables as well. If it is accepted on the unaligned table, then the
      expressibility argument covers C3b only and NOT the arm that produced
      campaign 7's headline 2 011.399 ms — a narrowing that must be published.

Corpus: 2 000 rows, ten categories, amt deterministic from the row index — the
same generator shape as probe_aggregation.py, small because this probe measures
expressibility, not latency. No SAI index is created, so the ring's SAI budget
is untouched. The keyspace is dropped on exit.
"""
import json, os, sys, time, socket
from datetime import datetime, timezone

KS = os.environ.get("EXPR_KS", "d12x")
N = int(os.environ.get("EXPR_N", "2000"))
CATS = 10

def gen(i):
    return f"c{i % CATS}", round(((i * 2654435761) % 1_000_000) / 1000.0, 3)

def ground_truth(n):
    per = {f"c{k}": {"n": 0, "sum": 0.0} for k in range(CATS)}
    for i in range(n):
        c, a = gen(i)
        per[c]["n"] += 1; per[c]["sum"] += a
    return {k: {"n": v["n"], "sum": round(v["sum"], 3)} for k, v in per.items()}

def host_fp():
    try:
        with open("/proc/cpuinfo") as fh:
            model = next((l.split(":", 1)[1].strip() for l in fh if l.startswith("model name")), "?")
    except Exception:
        model = "?"
    return {"hostname": socket.gethostname(), "cpu_model": model, "cpu_count": os.cpu_count()}

def attempt(session, cql):
    """Run a statement and record exactly what the server said. Never raises."""
    t = time.perf_counter()
    try:
        rows = list(session.execute(cql))
        return {"statement": cql, "accepted": True, "rows": len(rows),
                "elapsed_ms": round((time.perf_counter() - t) * 1000, 3),
                "result": {r.cat: {"n": r.n, "sum": round(r.sm, 3)} for r in rows}
                          if rows and hasattr(rows[0], "cat") else None,
                "server_message": None}
    except Exception as e:
        return {"statement": cql, "accepted": False, "rows": None,
                "elapsed_ms": round((time.perf_counter() - t) * 1000, 3),
                "result": None,
                "error_type": type(e).__name__,
                "server_message": str(e)[:400]}

def main():
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.policies import DCAwareRoundRobinPolicy
    from cassandra.concurrent import execute_concurrent_with_args

    auth = PlainTextAuthProvider(username=os.environ.get("CQL_USER", "cassandra"),
                                 password=os.environ.get("CQL_PASS", "cassandra"))
    cluster = Cluster([os.environ.get("CQL_HOST", "127.0.0.1")],
                      port=int(os.environ.get("CQL_PORT", "9142")),
                      auth_provider=auth,
                      load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="dc1"))
    s = cluster.connect()
    s.execute(f"CREATE KEYSPACE IF NOT EXISTS {KS} WITH replication = "
              "{'class':'NetworkTopologyStrategy','dc1':'3'}")
    s.execute(f"CREATE TABLE IF NOT EXISTS {KS}.aligned "
              "(cat text, id text, amt double, PRIMARY KEY (cat, id))")
    s.execute(f"CREATE TABLE IF NOT EXISTS {KS}.unaligned "
              "(cat text, id text, amt double, PRIMARY KEY (id))")

    rows = [(gen(i)[0], f"d{i:07d}", gen(i)[1]) for i in range(N)]
    for tbl in ("aligned", "unaligned"):
        ps = s.prepare(f"INSERT INTO {KS}.{tbl} (cat, id, amt) VALUES (?, ?, ?)")
        execute_concurrent_with_args(s, ps, rows, concurrency=64)

    gt = ground_truth(N)
    GROUPBY = "SELECT cat, SUM(amt) AS sm, COUNT(*) AS n FROM {ks}.{t} GROUP BY cat"
    SWEEP   = "SELECT SUM(amt) AS sm, COUNT(*) AS n FROM {ks}.{t} WHERE cat='c3'"

    out = {
        "C3b_groupby_on_aligned":            attempt(s, GROUPBY.format(ks=KS, t="aligned")),
        "C3b_groupby_on_unaligned":          attempt(s, GROUPBY.format(ks=KS, t="unaligned")),
        "C3b_groupby_on_unaligned_allowfilt":attempt(s, GROUPBY.format(ks=KS, t="unaligned") + " ALLOW FILTERING"),
        "C3a_sweep_on_aligned":              attempt(s, SWEEP.format(ks=KS, t="aligned")),
        "C3a_sweep_on_unaligned":            attempt(s, SWEEP.format(ks=KS, t="unaligned")),
        "C3a_sweep_on_unaligned_allowfilt":  attempt(s, SWEEP.format(ks=KS, t="unaligned") + " ALLOW FILTERING"),
    }

    aligned_correct = out["C3b_groupby_on_aligned"]["result"] == gt
    r1_triggered = out["C3b_groupby_on_unaligned"]["accepted"] or \
                   out["C3b_groupby_on_unaligned_allowfilt"]["accepted"]
    r3_triggered = out["C3a_sweep_on_unaligned"]["accepted"] or \
                   out["C3a_sweep_on_unaligned_allowfilt"]["accepted"]

    s.execute(f"DROP KEYSPACE {KS}")
    cluster.shutdown()

    rec = {
        "probe": "cql_groupby_expressibility.py",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": host_fp(),
        "conditions": {"keyspace": KS, "replication": "NetworkTopologyStrategy dc1:3",
                       "rows_per_table": N, "categories": CATS,
                       "indexes_created": "none — the ring's SAI budget is untouched",
                       "keyspace_dropped_on_exit": True},
        "verdict_rules_preregistered": {
            "R1": "GROUP BY cat accepted on a table whose PRIMARY KEY lacks cat "
                  "=> the D12 annulment's structural argument fails and must be withdrawn",
            "R2": "aligned GROUP BY result != Python ground truth => comparison void",
            "R3": "C3a sweep accepted on the unaligned table => the expressibility argument "
                  "covers C3b only, not the arm behind campaign 7's headline 2 011.399 ms",
        },
        "result": out,
        "ground_truth": gt,
        "verdicts": {
            "R1_triggered": r1_triggered,
            "R2_aligned_result_correct": aligned_correct,
            "R3_triggered": r3_triggered,
        },
        "reading": "Establishes, or refutes, one structural claim: whether CQL's GROUP BY on the "
                   "group key is expressible at all against a table not partitioned by it. It is "
                   "not a latency measurement and carries no percentile.",
    }
    out_path = os.environ.get("EXPR_OUT", "data/raw/findings_cql_groupby_expressibility.json")
    json.dump(rec, open(out_path, "w"), indent=2)
    for k, v in out.items():
        print(f"  {k:36} accepted={v['accepted']}  {v.get('server_message') or ''}"[:150], file=sys.stderr)
    print(f"  R1 triggered={r1_triggered}  R2 aligned correct={aligned_correct}  "
          f"R3 triggered={r3_triggered}", file=sys.stderr)
    print(f"written {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
