# `data/raw/` — data dictionary

Thirty-eight JSON files. Every one of them is byte-identical to the output the probe wrote
when it ran. They are not reformatted, not re-keyed, not pruned of the runs that went
against the author, and not corrected after the fact. Where a later measurement refuted an
earlier one, the earlier file stays exactly as it was and the refutation lives in a separate
file next to it — `findings_mongot_freshness.json` still says `p50_ms: 1015.201` even though
`findings_mongot_floor.json` proved that figure was the worst phase of a refresh cycle.
Editing evidence to tidy it would cost more credibility than the tidying is worth, and in a
dossier whose only claim to authority is that it argued against itself, an edited raw file
would be the end of the argument.

Each file also carries a fingerprint of the run that produced it — the host, the endpoint,
the keyspace, the ring, or some subset of those — recorded by the probe, not added by hand.
Those fingerprints are the reason a number here can be traced to a regime. They are not
uniform, and the exact shape each file carries is listed under **Host fingerprint** below.

**Do not modify anything in `data/raw/`.** If a file needs a correction, the correction is a
new file and a note in the campaign report.

**Checking that nothing here has been modified.** `data/MANIFEST.sha256` carries one SHA-256
per file, in the ordinary `sha256sum` format, so it can be checked without any script from
this repository:

```bash
sha256sum -c data/MANIFEST.sha256      # from the repository root
```

Its paths are relative to the repository root, so it must be run from there — run from inside
`data/` it reports every file as *No such file or directory*, which looks like corruption and
is not. CI re-verifies it on every push (job 1), so an alteration fails at the commit that
introduces it. The manifest lived at `.github/evidence.sha256` until 18 September 2026; it was
moved here, beside the evidence it describes, because that is where a reader looks.

---

## How to quote a number out of this directory

1. **Quote the regime with the number.** Almost every latency figure here is
   memtable- or cache-resident. The per-byte rate of 0.7775 ms/KiB is a *memtable*
   coefficient (`rmw_postflush.json` shows it flattening to ×1.52 growth once the read half
   of the read-modify-write cycle is forced onto SSTables). A number quoted without its
   regime is a misquote.
2. **Quote the contest with the number.** Several headline figures are disputed by this
   dossier's own adversarial audit (`docs/audit-adversarial.fr.md`, promoted to English in
   `LIMITATIONS.md`) and challenge rounds (`docs/challenges.fr.md`). The **Contested
   figures** table below names each one, its file, and what contests it. The caveat belongs
   in the same sentence as the number, not in a footnote.
3. **Keep the evidential markers.** Where the campaign reports and the article mark a claim
   `[D]` documented, `[R]` reported, `[U]` unverified or `[M]` measured, the marker travels
   with the claim. `findings_vector_rf3.json` is the one raw file that carries these markers
   inside the JSON itself (in `article_bearing` and `verdict`).
4. **Cite the measurement identifier.** The register of measurements M1–M19 lives in
   `docs/adr/ADR-001-modelling-policy.md` under *Evidence register*; it has no M9 entry, so
   the identifiers there run M1–M8 and M10–M19. **M20–M23 are not in the ADR** — they were
   assigned in this repository for campaign 7 and are registered in `RESULTS.md` §3 and
   reported in `docs/campaigns/07-aggregation.fr.md`. Each file below names the Mxx it backs,
   or says plainly that no Mxx has been assigned to it.

For how the measurements were taken, see `METHODOLOGY.md`; for what they do not establish,
`LIMITATIONS.md`; for the probes that wrote these files, `probes/README.md`.

---

## Common shape

Every probe that reports a latency emits the same distribution object:

| Key | Meaning |
|---|---|
| `n` | number of retained repetitions (warm-ups discarded separately) |
| `min_ms` | fastest observed operation, milliseconds |
| `p50_ms` | median |
| `p95_ms` | 95th percentile |
| `p99_ms` | 99th percentile |
| `max_ms` | slowest observed operation |
| `stdev_ms` | sample standard deviation of the observations |

**No mean is published for latency, by policy.** The dossier reports percentiles because a
mean of a closed-loop latency series hides exactly the tail that decides whether a system is
usable. `stdev_ms` is present as a spread indicator only; it is not a licence to reconstruct
a mean.

Four documented departures from that shape exist in the raw files, and they are departures
in the data, not in the policy:

| File | Departure |
|---|---|
| `findings.json`, `findings_rf3.json`, `findings_rf3_rate50.json`, `findings_rf3_rate50_rep2.json`, `control_read_A_run1.json`, `control_read_A_run2.json` | additionally carry `p999_ms` |
| `rmw_postflush.json` | `by_size.*` omits `min_ms` |
| `findings_mongot_freshness.json`, `findings_mongot_floor.json`, `findings_hcd_vec_freshness.json` | carry `mean_ms`, emitted by the freshness probes. `findings_mongot_floor.json` further carries `p10_ms`/`p90_ms` and omits `p95_ms`/`p99_ms`; `findings_hcd_vec_freshness.json` omits `p99_ms` and `stdev_ms`. The dossier's prose does not quote these means as latency results; the keys are documented here because they are in the files |
| `vector_freshness_idle.json`, `vector_freshness_loaded.json`, `findings_vector_rf3.json` | `insert_to_vector_visible_ms` uses unsuffixed keys `n`, `p50`, `p95`, `p99`, `max` — no `min`, no `stdev` |

Slope objects, where a probe fits a line across document sizes, have the shape
`{ms_per_KiB, r2, endpoint_ratio, y_range_ms}` (`comparison.json`, `comparison_v2.json`) or
`{slope_ms_per_unit, r2, endpoint_ratio, x_range, y_range_ms}` (`findings_fieldbyte.json`).
Read `r2` before quoting a slope: the MongoDB arms fit at r² 0.78 and 0.88 because their
slopes are near zero and largely noise, which is itself the finding.

---

## Host fingerprint

One shared host throughout: `alphadebunker`, Intel Xeon Gold 6148 @ 2.40GHz, 80 vCPU,
220.2 GiB RAM, `Linux-6.8.0-136-generic-x86_64-with-glibc2.39`, Python 3.12.3. It is a
shared, already-loaded production-demo VM, not a clean bench — see finding I1 of the
adversarial audit. Files record it in four different shapes:

| Shape | Files |
|---|---|
| `conditions.host` = `{hostname, cpu_model, cpu_count, mem_gib, platform}` | `cmp_hcd.json`, `cmp_hcdcql.json`, `cmp_mongo.json`, `smoke_hcd.json`, `smoke_mongo.json` |
| `hosts[]` = array of the above, one per merged record (the `--compare` same-host gate) | `comparison.json` (2 entries), `comparison_v2.json` (3 entries) |
| `host` = `{hostname, cpu_model, cpu_count, platform}` or `{hostname, cpu_model, cpu_count}` | `findings_rs_hcd.json`, `findings_rs_mongo.json`; `findings_agg_hcd.json`, `findings_agg_mongodb.json` |
| `conditions` = `{endpoint, keyspace, collection, cql_available, client_platform, python}` — platform but no hostname | `findings.json`, `findings_fieldbyte.json`, `findings_rf3_rate50.json`, `findings_rf3_rate50_rep2.json`, `findings_tier.json` |
| `target` = `{product, ring, keyspace, durability, …}` — the ring rather than the client | `findings_rf3.json`, `findings_vector_rf3.json` |

The remaining files identify their run by keyspace/collection only (`disk_state.json`,
`disk_state_c4.json`, `vector_freshness_idle.json`, `vector_freshness_loaded.json`,
`control_read_A_run1.json`, `control_read_A_run2.json`) or by probe name and timestamp only
(`findings_disk_rf3.json`, `probe4_rf3_supplementary.json`, `rmw_postflush.json`,
`tier_comparison.json`, `findings_tier_method2.json`, `findings_agg_cqlref.json`,
`findings_turn_hcd.json`, `findings_turn_mongodb.json`, `findings_mongot_floor.json`,
`findings_hcd_vec_freshness.json`, `findings_mongot_freshness.json`). Their host is
established by the campaign report that owns them, not by the file.

Twelve files carry no `run_at_utc` at all: `cmp_hcdcql.json`, `control_read_A_run1.json`,
`control_read_A_run2.json`, `findings_hcd_vec_freshness.json`, `findings_tier_method2.json`,
`findings_turn_hcd.json`, `findings_turn_mongodb.json`, `probe4_rf3_supplementary.json`,
`rmw_postflush.json`, `tier_comparison.json`, `vector_freshness_idle.json`,
`vector_freshness_loaded.json`. One more carries a hand-written, imprecise one:
`findings_vector_rf3.json` records `"run_at_utc": "2026-09-17T16:5x (p16 ring)"`. That is
how it was written and that is how it stays.

---

## Campaign index

| Campaign | Report | Raw files |
|---|---|---|
| 1 — verification, RF = 1 | `docs/campaigns/01-verification.fr.md` | `findings.json` |
| 2 — replication, RF = 3 | `docs/campaigns/02-replication-rf3.fr.md` | `findings_rf3.json`, `findings_rf3_rate50.json`, `findings_rf3_rate50_rep2.json`, `probe4_rf3_supplementary.json`, `control_read_A_run1.json`, `control_read_A_run2.json` |
| 2 addendum — vector freshness | ADR rev. 3 (no campaign report) | `findings_vector_rf3.json`, `vector_freshness_idle.json`, `vector_freshness_loaded.json` |
| 3 — disk regime, field vs byte | `docs/campaigns/03-disk-regime.fr.md` | `disk_state.json`, `findings_disk_rf3.json`, `findings_fieldbyte.json` |
| 3 reopened — post-flush read path | `docs/challenges.fr.md` (C2 resolution) | `rmw_postflush.json` |
| 4 — tier vs storage | `docs/campaigns/04-tier-vs-storage.fr.md` | `disk_state_c4.json`, `findings_tier.json`, `findings_tier_method2.json`, `tier_comparison.json` |
| 5 — mutation comparison | `docs/campaigns/05-mutation-comparison.fr.md` | `smoke_hcd.json`, `smoke_mongo.json`, `cmp_hcd.json`, `cmp_mongo.json`, `comparison.json`, `cmp_hcdcql.json`, `comparison_v2.json` |
| 6 — freshness, read, search | `docs/campaigns/06-freshness-read-search.fr.md` | `findings_rs_hcd.json`, `findings_rs_mongo.json`, `findings_mongot_freshness.json`, `findings_hcd_vec_freshness.json`, `findings_mongot_floor.json`, `findings_turn_hcd.json`, `findings_turn_mongodb.json` |
| 7 — aggregation | `docs/campaigns/07-aggregation.fr.md` | `findings_agg_mongodb.json`, `findings_agg_hcd.json`, `findings_agg_cqlref.json` |

---

## Campaign 1 — verification at RF = 1

Node `rh-hcd`, one node, RF = 1, memtable-resident, 17 September 2026. Per ADR-001's
*Evidence base* line, on `alphadebunker`.

### `findings.json`
- **Probe:** `probes/verify_storage_claims.py`, version `1.0 + 2 mechanical fixes`.
- **Backs:** M1, M2, M3, M4.
- **Read first:** `findings[]` — four probe records, each with `probe`, `claim`, `verdict`,
  `evidence`; `harness_modifications` — the two fixes, each declaring
  `"effect_on_protocol": "none"`; `what_this_experiment_does_not_establish` — seven
  disclaimers written before the results were known.
- **Where the numbers are:** `findings[0].evidence.column_count` = 12 and `index_count` = 9
  (M1). `findings[2].direct_observation_by_query_trace.sequence_per_updateOne` — the
  `SELECT` then `UPDATE … IF tx_id = ?` pair, 10 of 10 (M2). `findings[2].
  variant_B_indexed_chunks` — the ×7.50 growth, p50 12.1 ms at 1 KB to 90.8 ms at 128 KB
  (M3). `findings[3].per_statement_consistency` — 70/70 `LOCAL_QUORUM`, 30/30
  `LOCAL_SERIAL` (M4).
- **Against the author, in the file:** `findings[2].verdict` is `INCONCLUSIVE` — by the
  harness's own pre-registered read-control rule, update growth (×1.92) is not separable
  from same-size read growth (×1.86). The claim is carried by the trace, not by the curve.
  `findings[1].verdict` (freshness) is `INCONCLUSIVE` too, against the harness's own 50 ms
  rule.
- `findings[2].read_control_pre_registered_rule` states the rule, both runs' growth pairs
  (update ×1.92 / ×2.21 against read ×1.86 / ×1.94) and the caveat the rule does not capture:
  the `updateOne` request payload is constant at 122–124 bytes, so the update's growth cannot
  be HTTP transfer. `run_1.read_source` also records, unprompted, that run 1's full read
  distribution was overwritten by run 2 because the control script wrote a fixed filename —
  the p50 values there are transcribed from the run log. The gap is left standing rather than
  back-filled.
- `replication_2` holds the second run's four verdicts and its 0.055 s schedule slip.

---

## Campaign 2 — replication at RF = 3

Six-node `presto-hcd-v16-cluster`, probe keyspace `{dc1: 3}`, two passes at
`--rate 50 --duration 120`, 17 September 2026.

### `findings_rf3.json`
- **Probe:** `probes/verify_storage_claims_rf3.py` (`verify_storage_claims.py` 1.0 + 3
  mechanical fixes). Consolidated record for the campaign.
- **Backs:** M5; re-runs A2/A3/freshness at RF = 3.
- **Read first:** `target` — product, ring, keyspace, durability, isolation note;
  `probe4_A5` — `MULTI_REPLICA_CONSENSUS_OBSERVED`, `paxos_phase_counts`,
  `coordinator_duration_p50_ms`; `probe3_A3` — `verdict_latency_by_control_rule`
  (`INCONCLUSIVE`) beside `verdict_by_trace` (`SUPPORTED`).
- **Numbers:** coordinator-side p50 `SELECT` 6.582 ms against `UPDATE … IF` 13.738 ms.
  These are coordinator durations from `system_traces.sessions`, not client latency.
- **Caveat that must travel:** the three dc1 replicas share one host, so the Paxos round is
  measured where inter-replica latency is sub-millisecond — challenge C3. The structure is
  established; the magnitude is not representative of a multi-host deployment.
- Note `verdicts_run1` and `verdicts_run2` both record `["A5", "INCONCLUSIVE"]`: that is the
  harness's latency-based verdict. The `SUPPORTED` verdict for A5 comes from `probe4_A5`,
  which is trace-based. Both are in the file.

### `findings_rf3_rate50.json` and `findings_rf3_rate50_rep2.json`
- **Probe:** the same harness, `--out` default shape (`harness`, `run_at_utc`, `conditions`,
  `findings[]`, `publication_note`) — the two individual passes that `findings_rf3.json`
  consolidates.
- **Read first:** `findings[]`, `conditions`. `findings_rf3_rate50.json` shares
  `run_at_utc` with `findings_rf3.json` (`2026-09-17T16:21:37Z`); the repeat is at
  `16:26:59Z`.

### `probe4_rf3_supplementary.json`
- **Probe:** CQL trace extraction from `system_traces` during the RF = 3 run.
- **Backs:** the M5 detail.
- **Read first:** `statements[]` — per statement family: `cl`, `serial_cl`, `n`,
  `coordinator_duration_ms_p50`, and the verbatim `query`; `paxos_phase_counts`;
  `coordinators` (224 sessions each on 172.23.0.2 and .3). `per_session[]` holds 30 raw
  sessions.

### `control_read_A_run1.json` and `control_read_A_run2.json`
- **Probe:** the variant-A read control of the same harness, on `storage_probe_rf3`.
- **Backs:** the read-control half of A3 at RF = 3 — this is the pre-registered rule that
  makes the latency verdict `INCONCLUSIVE`.
- **Read first:** `read` — the four size distributions; `read_p50_growth_factor` (1.86 and
  1.85); `wire_bytes` — `updateOne_req` stays at 122–124 bytes across 1 KB to 128 KB while
  `findOne_resp` grows from 1 135 to 131 185 bytes. That constant request payload is the
  evidence that the growth is server-side, not wire-side.

---

## Campaign 2 addendum — vector-search freshness at RF = 3

### `findings_vector_rf3.json`
- **Probe:** `probes/vector_freshness_rf3.py`, two regimes.
- **Backs:** M7.
- **Read first:** `verdict` — `NOT DETECTABLE on this topology (neither confirms nor refutes
  the article's section-4 [D] claim)`; `idle` and `loaded_40ps`; `what_this_does_not_establish`.
- **Numbers:** 120/120 cycles (60 idle + 60 at 40 vector-writes/s) returned the just-written
  vector top-1 on the first `LOCAL_ONE` search; 0 cycles where the `LOCAL_QUORUM` key read
  hit and the vector search missed; `insert_to_vector_visible_ms.p50` 74.735 ms idle,
  74.406 ms loaded.
- **Against the author, in the file:** this is a negative result for the article's most
  HCD-favourable section. The window, if any, is bounded *below* the ~74 ms HTTP measurement
  floor — the probe cannot show a lag it is too slow to see. This is the one raw file
  carrying the `[D]`/`[M]`/`[U]` markers inside the JSON.

### `vector_freshness_idle.json` and `vector_freshness_loaded.json`
- **Probe:** same, raw output.
- **Read first:** `summary` — including `vector_attempts_histogram` (`{"1": 60}` in both) and
  `interpretation`; `cycles[]` — 60 per-cycle records of
  `{vec_hit_first, key_hit_first, vec_attempts, insert_to_vec_visible_ms}`.

---

## Campaign 3 — disk regime and field-vs-byte

### `disk_state.json`
- **Probe:** `probes/disk_regime_driver.py`.
- **Backs:** the disk-regime precondition of M10 and M11.
- **Read first:** `evidence.checks` — the four proof checks, all `true`; `evidence.disk_bound`
  (`true`); `evidence.page_cache_note`.
- **Numbers:** 0 → 40 SSTables, 0 → 6 491 369 675 bytes on disk, compactions completed
  651 → 729 (78 crossed), 24 576 documents in 1 137.8 s.
- **Against the author, in the file:** `honesty_note` reads *"disk_bound=false means the
  regime was not reached. Do not report the run as disk-bound on the strength of intent."*
  And `page_cache_note` records that the OS page cache was **not** dropped — no root on the
  host. The regime is proven for the *dataset*; challenge C2 establishes it was never proven
  for the *probed read*.

### `findings_disk_rf3.json`
- **Probe:** `probes/verify_storage_claims.py` plus the variant-B probe, run against the
  filled keyspace without restarting the node.
- **Backs:** M10.
- **Read first:** `disk_regime_proof` (a copy of the `disk_state.json` evidence block);
  `variantB_indexed_chunks` — `update_p50` 20.389 ms at 1 KB to 121.189 ms at 128 KB;
  `comparison` — ×5.94 here against ×7.50 in campaign 1.
- **Caveat that must travel:** `variantA_rmw.verdict_by_control_rule` is
  `INCONCLUSIVE (update grows with read)`. And the ×5.94-vs-×7.50 comparison mixes regime
  with a topology and hardware confound (RF 1 / 3 GiB against RF 3 / 8 GiB), so it cannot be
  attributed to disk alone. The label "the coefficient holds under disk" is retracted by
  `rmw_postflush.json`.

### `findings_fieldbyte.json`
- **Probe:** `probes/probe_field_vs_byte.py`, unmodified, two series, two passes.
- **Backs:** M11 — the most robust derived measurement in the dossier.
- **Read first:** `verdict_per_pass` — `["BYTES DOMINATE", "INCONCLUSIVE"]`;
  `analysis.pass1`/`pass2` — the two series' slopes and r²;
  `internal_control_same_config_in_both_series` — the 16×4096 B configuration present in both
  series, spread 2.0 % and 0.65 %.
- **Numbers:** at fixed 64 KiB indexed volume, raising field count 9 → 128 moved update p50
  by endpoint ratio 1.128 and 1.187 (r² 0.5745 and 0.9154); at fixed 16 fields, raising
  bytes per field 512 → 8000 moved it by 4.556 and 4.738 with r² 0.9999 on both passes.
- **Against the author, in the file:** the pre-registered rule
  (`verdict_rule`: ≤ 1.15 → bytes dominate, ≥ 1.5 → field count is an independent driver)
  straddles its own boundary — 1.128 on pass 1, 1.187 on pass 2 — so the strict two-pass
  verdict is `INCONCLUSIVE`, even though neither pass approaches 1.5. The file publishes both.

### `rmw_postflush.json`
- **Probe:** `probes/rmw_postflush.py`, written by the author to close his own challenge C2.
- **Backs:** M15.
- **Read first:** `by_size` — the four distributions (no `min_ms`); `p50_growth_factor`
  (1.52); `comparison` — 5.94 (M10), 7.5 (campaign 1), 1.52 (here).
- **Numbers:** 1 KB p50 107.765 ms, 128 KB p50 163.402 ms.
- **What this cost the author:** it is the file that demotes the dossier's headline
  coefficient. Forcing the cycle's `SELECT` onto SSTables collapses the per-byte growth from
  ×5.94 to ×1.52 and replaces it with a fixed read-path cost of roughly 100 ms. The
  0.77 ms/KiB rate is therefore a memtable phenomenon, not a property of the engine.
- **Caveat that must travel:** `regime` records `page-cache-warm; no root to drop page
  cache`, and flushing before *every* update fragments the table into many small SSTables, so
  the ~100 ms absolute is inflated by fragmentation a normal compaction would not leave. The
  true disk-bound cost lies between the memtable figures and this worst case.

---

## Campaign 4 — Data API tier versus storage engine

### `disk_state_c4.json`
- **Probe:** `probes/disk_regime_driver.py`, second fill, for campaign 4's keyspace.
- **Read first:** `evidence.checks`, `evidence.disk_bound`, `keyspace`
  (`verif_tier_20260917`).
- **Numbers:** 0 → 40 SSTables, 6 491 383 676 bytes, compactions 875 → 951 (76 crossed),
  24 576 documents in 1 207.4 s. Same `page_cache_note` and same `honesty_note` as
  `disk_state.json`.

### `findings_tier.json`
- **Probe:** `probes/probe_tier_vs_storage.py` (arm A = Data API `updateOne`, arm B = the
  identical CQL statement pair on the same row), plus the method-2 trace figures.
- **Backs:** M12.
- **Read first:** `VERDICT` — `where_the_rate_lives`, `tier_dominates` (`false`),
  `methods_agree`; `tier_slopes_ms_per_KiB` — method 1 combined 0.219 (r² 0.983) against
  method 2 0.145 (r² 0.992); `known_confounds` — three of them, stated by the probe.
- **Numbers:** storage 0.547 ms/KiB (method 1), tier 0.219 ms/KiB; `rate_reconstruction`
  records 0.219 + 0.547 = 0.766 ms/KiB, reproducing campaign 3's ~0.77.
- **Caveat that must travel, and the file says so itself:** the two methods agree within 25 %
  at 8, 16 and 32 KiB but diverge by 34 % at 64 KiB and 28 % at 125 KiB, and their tier
  slopes differ by about 50 %. **No single precise split is published** — a range, and the
  divergence. `known_confounds` further records that arm B reuses already-shredded values and
  so never exercises the shredding code path: it is "a subtraction instrument only", not a
  benchmark.
- **Contested downstream:** `comparison_v2.json` puts the tier share at ~9 % in a matched
  cache regime. Audit finding I3 records the share as an unpinned 9–29 % range.

### `findings_tier_method2.json`
- **Probe:** `probes/method2_trace.py` — written by the author, which audit finding I2 counts
  against it.
- **Read first:** `sizes` — per size, `client_p50_ms`, `coord_select_p50_ms`,
  `coord_update_p50_ms`, `coord_sum_p50_ms`, `tier_method2_p50_ms`, and the trace counts
  `n_select_traces`/`n_update_traces`; `tracing_reset_verified`.

### `tier_comparison.json`
- **Probe:** derived comparison table, one row per size.
- **Read first:** `tier_share_pct`, `divergence_pct`, `within_25pct`.
- **Numbers as measured:** 8 KiB 39.7 % / 0.5 % / true; 16 KiB 29.9 % / 8.0 % / true;
  32 KiB 31.1 % / 11.3 % / true; 64 KiB 33.8 % / **34.0 % / false**; 125 KiB 29.8 % /
  **28.0 % / false**. The two `false` rows are the reason no point estimate is published.

---

## Campaign 5 — single-field mutation, HCD against MongoDB

Same host, same session, same 16-field series from 512 B to 8000 B, 30 repetitions, two
passes, cache-resident on both sides, durability matched by a declared judgement.

### `smoke_hcd.json` and `smoke_mongo.json`
- **Probe:** `probes/probe_comparative.py` with `smoke_test: true`.
- **Backs:** nothing. `publication_note` says so: *"SMOKE TEST. Five repetitions on an
  unqualified machine. This validates that the instrument runs; it measures nothing."*
- **Read first:** `smoke_test`, `publication_note`, `conditions.reps` (5).

### `cmp_hcd.json`, `cmp_mongo.json`, `cmp_hcdcql.json`
- **Probe:** `probe_comparative.py` (`cmp_hcd`, `cmp_mongo`) and `probes/hcd_cql_arm.py`
  (`cmp_hcdcql`).
- **Backs:** the per-engine halves of M13 (`cmp_hcd`, `cmp_mongo`) and M14 (`cmp_hcdcql`).
- **Read first:** `arms.<arm>.results` — keyed `<size>|<pass>`, each with `size`,
  `total_bytes` and an `update` distribution; `durability_mapping`; `conditions.
  TO_BE_COMPLETED_BY_HAND` — the deployment shape, regime, resource limits and colocation,
  filled in by hand for these files.
- **The files refuse to be misread:** `cmp_hcd.json` and `cmp_mongo.json` each carry a
  `warning` key — *"A single-record file is not a comparison. Merge with `--compare`, which
  refuses to emit a ratio unless both engines were measured on the same host."*
  `cmp_hcdcql.json` carries no `warning` and no `run_at_utc`; its
  `conditions.TO_BE_COMPLETED_BY_HAND` is the short two-field form.
- `cmp_mongo.json` holds two arms, `mongo-default` and `mongo-wildcard`. Both are the
  finding; the reading guide in the merge files requires both or neither.

### `comparison.json`
- **Probe:** `probe_comparative.py --compare` merge of `cmp_mongo` and `cmp_hcd`.
- **Backs:** M13.
- **Read first:** `arms.<arm>.slope.ms_per_KiB` with its `r2`; `VERDICT`;
  `cross_engine_comparison_permitted` with `same_host` and `same_series_shape` — the gate
  that refuses a ratio across hosts; `reading_guide`.
- **Numbers as measured:** HCD 0.7775 ms/KiB (r² 0.997), `mongo-wildcard` 0.0176 (r² 0.8794),
  `mongo-default` 0.0098 (r² 0.7809) — 44× and 79×. Absolute update p50: HCD rises 40.9 →
  130.787 ms across the series, while the two MongoDB arms stay essentially flat within
  5.67–6.484 ms (default) and 5.544–7.621 ms (wildcard).
- **Caveats that must travel:** these are *cache-resident (memtable)* rates — see
  `rmw_postflush.json`. They are *stack against stack*, HCD driven through HTTP, JSON
  parsing, shredding and a Paxos round, MongoDB through its native driver — challenge C1,
  answered by `comparison_v2.json`. And `VERDICT.durability_matched` names the mapping as *a
  declared judgement*, with the Paxos-versus-document-atomicity asymmetry not aligned.
  Challenge C6 notes that the mapping actually favoured HCD — MongoDB's `j:true` waits for
  the journal fsync, HCD's `commitlog_sync periodic 10 s` acknowledges before it — and HCD
  lost anyway, which strengthens rather than weakens the result.

### `comparison_v2.json`
- **Probe:** the same merge, re-run with the `hcd-cql-direct` arm added.
- **Backs:** M14.
- **Read first:** `arms` — four arms now; `hosts` — three entries; note there is **no
  `VERDICT` key** in this file, unlike `comparison.json`.
- **Numbers as measured:** `hcd-cql-direct` 0.7037 ms/KiB (r² 0.9959), against the Data API
  stack's 0.7775. Removing the tier lowers the slope by about 9 %.
- **What this cost the author:** this file refutes the author's own challenge C1. He had
  extrapolated from M12 that the tier was ~29 % of the rate and that an honest
  engine-against-engine ratio would be ~31×. Measured, it is ~9 % and the ratio is 40×
  against `mongo-wildcard`, 72× against `mongo-default`. MongoDB's advantage is an engine
  result, not a Data-API artefact — a harder result for HCD than the challenge claimed.
  The 9 %-versus-29 % gap with `findings_tier.json` is audit finding I3 and is unresolved.

---

## Campaign 6 — the axes the article claims for HCD

1 000 000 documents, same host. Read and search on a 3-member MongoDB replica set against an
HCD `{dc1: 3}` ring; search freshness on a separate single-node `mongodb-atlas-local`
deployment — two different MongoDBs in one campaign, which is challenge C15.

### `findings_rs_hcd.json` and `findings_rs_mongo.json`
- **Probe:** `probes/probe_read_search.py`.
- **Backs:** M16.
- **Read first:** `arms.<arm>.A_filtered_read_qcol` (filtered read on an undeclared field),
  `B_point_read_id` (point read by `_id`), `C_freshness_secondary` (with
  `insert_to_found_ms` and `find_attempts_histogram`).
- **Numbers as measured:** A — `mongo-default` p50 376.698 ms (collection scan), HCD 17.376 ms
  (automatic SAI), `mongo-wildcard` 0.732 ms. B — `mongo-wildcard` 0.530 ms,
  `mongo-default` 0.616 ms, HCD 10.382 ms. C — `find_attempts_histogram` is `{"1": 40}` on all
  three arms: every engine returned the just-written document on the first query.
- **Against the author, in the files:** two of the three axes the article claims for HCD do
  not favour HCD here. The point read goes to MongoDB by roughly 20× (the Data API tier hop),
  and ordinary secondary-index freshness is a tie. The 22× advantage on axis A is over
  *default* MongoDB; a wildcard-indexed MongoDB is 23.7× faster than HCD on the same query —
  challenge C12. What HCD buys is the dispensation from index design, not speed.
- Note `C_freshness_secondary.insert_to_found_ms.p50` on `mongo-default` is 894.213 ms with
  `find_attempts_histogram` `{"1": 40}`: found on the first query, but that first query was a
  collection scan. The attempts histogram, not the interval, is what carries the freshness
  verdict here.

### `findings_mongot_freshness.json`
- **Probe:** `probes/mongot_freshness.py`, `mongodb-atlas-local` 8.3.11 with `mongot`.
- **Backs:** the MongoDB half of M17.
- **Read first:** `search_write_to_visible_ms`, `search_poll_attempts` (min 22, median 34,
  max 36), `regular_find_by_id_ms`, `contrast`.
- **Numbers as measured:** `$search` write-to-visible p50 1015.201 ms, stdev 35.172; ordinary
  `find({_id})` p50 1.306 ms.
- **This number must never be quoted alone.** `findings_mongot_floor.json` establishes that
  the ~1015 ms was the worst phase of a periodic refresh cycle, inflated ×1.53 on the medians
  (p50 1015.201 → 664.3 ms) by a self-synchronised probe. The "~1.6×" in ADR-001 rev. 12 is the
  ratio of the `mean_ms` fields (1021.553 / 646.3 = ×1.58), which this dossier does not publish
  for latency. The tight stdev of 35 ms is the signature of that self-synchronisation,
  not of a stable system property. The file is kept unedited.
- **Scope:** `deployment` records a single-node replica set, so `w:majority` is trivial. It is
  not the 3-member replica set used for the read and search halves.
- **Edition, pinned after the fact:** see `findings_mongot_provenance.json` below. The `mongot`
  that produced this number is edition **`localDev`**, not the build that serves Atlas, so the
  magnitude does not transfer to MongoDB the product at all.

### `findings_mongot_provenance.json`
- **Probe:** none — this is a direct interrogation of the `mongodb/mongodb-atlas-local` image
  (labels, plus two files read inside it), performed on 18 September 2026, after the freshness
  campaigns had run. No container from those runs survived; the image did.
- **Backs:** the scope of M17, M18 and M19. It adds no latency measurement; it names what was
  measured.
- **Read first:** `versions.mongot_edition` (**`localDev`**), `versions.mongot_version`
  (**1.75.1**), `consequence.statement`, `commit_interval.value` (**null**).
- **Why it exists.** Until the build was identified, the three freshness measurements carried an
  unnamed reserve — "some `mongot`". This names it, and the naming makes the reserve **worse**,
  not better: `localDev` is the edition MongoDB ships for local development.
- **Two sources per fact, deliberately.** Version and edition are each corroborated twice — an
  image label and an on-image artefact (`/opt/mongot/mongot --version`, and the literal contents
  of `/etc/mongodb-atlas-local/mongot-edition`) — because a label alone can be stale.
- **What it does NOT establish.** `commit_interval.value` is `null`. The interval is internal to
  the `mongot` jar and appears in no launch script, README or environment variable, so the
  ~1015 ms of M17 and the ~1.1 s interval of M18 remain empirical observations of this build
  rather than a documented default that was read off. Recorded as `null` rather than guessed.

### `findings_hcd_vec_freshness.json`
- **Probe:** HCD JVector vector-search freshness, same session as the `mongot` run.
- **Backs:** the HCD half of M17.
- **Read first:** `search_poll_attempts` (`min` 1, `median` 1, `max` 1) — this, not the
  interval, is the finding; `search_write_to_visible_ms`; `note`.
- **Numbers as measured:** p50 44.972 ms, min 31.9 ms, p95 84.827 ms, max 573.598 ms.
- **Caveat that must travel:** "synchronous, zero lag" overstates it. `attempts = 1` means the
  document was searchable on the first query, and that query arrived ~45 ms after the write.
  Any HCD index lag between 0 and ~45 ms is *undetectable by this instrument*. The honest
  statement is "HCD lag below the ~45 ms measurement floor" — challenge C11.

### `findings_mongot_floor.json`
- **Probe:** `probes/mongot_floor.py` — random 0–1200 ms pre-insert sleep to sample all
  commit-cycle phases, then 5 ms polling.
- **Backs:** M18.
- **Read first:** `de_synchronised_lag_ms`, `verdict`, `first_measurement_was`.
- **Numbers as measured:** n 60, min 89.1 ms, p10 254.5 ms, p50 664.3 ms, p90 988.7 ms,
  max 1170.2 ms, stdev 290.8 ms (and a `mean_ms` of 646.3, emitted by the probe).
- **What this cost the author:** it corrects his own M17. `first_measurement_was` records
  *"~1015 ms tight (self-synchronised, worst phase)"*. The lag is a Lucene-style refresh
  interval, not a fixed delay.
- **Caveats the file does not fully carry, from challenge round D:** the floor is ~89 ms, not
  ~0, so `verdict`'s phrase "the minimum approaches zero" is imprecise (D3); `atlas-local` is
  not production Atlas and the interval is not user-tunable there (D2); this measures MongoDB
  *text* `$search` against HCD *vector* JVector, so the two halves do not exercise the same
  path (C14/D4); n = 60, one pass, and the refresh-interval classification is a threshold in
  the author's own code, not a statistical test (D5).

### `findings_turn_hcd.json` and `findings_turn_mongodb.json`
- **Probe:** `probes/turn_latency.py`, 30 cycles per τ.
- **Backs:** M19.
- **Read first:** `miss_rate_by_tau_ms` — keyed by τ in ms, each `{miss, n, miss_rate}`;
  `tau_ms`; `reading`.
- **Numbers as measured:** HCD 0.0 miss rate at every τ from 0 to 3000 ms. MongoDB `$search`
  1.0 at τ = 0, 0.933 at 100 ms, 0.833 at 250 ms, 0.5 at 500 ms, 0.333 at 750 ms, 0.0 at
  τ ≥ 1000 ms.
- **What this cost the author:** it confirms challenge D1 against the article's own framing.
  HCD's freshness edge is decisive for sub-second write-then-search — MongoDB misses 50–100 %
  of documents below 500 ms — and **moot for conversational RAG**, where an LLM turn exceeds
  one second and MongoDB misses nothing. The one axis clearly favourable to HCD is favourable
  for a narrower class of workloads than the article claims.

---

## Campaign 7 — aggregation

Run 18 September 2026, 200 000 documents, ten categories of 20 000. These three files back
**M20–M23**, assigned in this repository: their register entries are in `RESULTS.md` §3 and
their report is `docs/campaigns/07-aggregation.fr.md`. **No Mxx has been assigned to them in
the ADR-001 evidence register**, which stops at M19, and the adversarial audit — which covers
M1–M17 — never saw them.

### `findings_agg_mongodb.json`
- **Probe:** `probes/probe_aggregation.py --engine mongodb`.
- **Read first:** `result.counts` (all `*_correct` true), `result.C1_groupby_sum_serverside_ms`,
  `result.ground_truth` — the correctness check every arm is scored against.
- **Numbers as measured:** `countDocuments` p50 115.009 ms; `estimatedDocumentCount` p50
  0.408 ms; filtered count by collection scan p50 157.177 ms, by `cat_idx` p50 12.659 ms;
  server-side `$group` sum p50 222.711 ms over n = 15, `C1_rows` 10, `C1_correct` true.

### `findings_agg_hcd.json`
- **Probe:** `probes/probe_aggregation.py --engine hcd`.
- **Read first:** `result.counts` — including `count_all_error` and `filtered_error`
  (`TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the
  server`) and `count_all_correct: false`, `filtered_correct: false`; `structural`;
  `result.C2_client_scan_aggregate_ms`.
- **Numbers as measured:** `A_count_all_ms` and `B_filtered_count_saidx_ms` are **empty
  objects** — the operations errored, so there is no distribution to report, and the probe
  did not invent one. `A_estimated_count_ms` p50 6.875 ms, but `counts.estimated` is `0`
  against a true 200 000 (`estimated_note`: SSTable-metadata estimate, reads 0 until memtable
  flush). The client-side scan-and-aggregate, n = 3, p50 133 984.229 ms — about 134 seconds —
  scanning 200 000 documents, `C2_correct` true.
- **Against HCD, in the file:** `structural` records that the HCD Data API has no server-side
  aggregation pipeline (`aggregate`/`$group`/`distinct` return `COMMAND_UNKNOWN`), that
  `countDocuments` refuses above 1 000 documents, and that the only correct aggregate
  available is to pull every document to the client. This is an unfavourable structural
  finding, published with the two empty distributions that prove the operations failed.

### `findings_cql_groupby_expressibility.json`
- **Probe:** `probes/cql_groupby_expressibility.py`.
- **Not a latency measurement.** It carries no percentile and answers one structural question:
  whether a CQL `GROUP BY` on the group key is expressible at all against a table that is not
  partitioned by it. Read `result` and `verdicts`, not timings — the `elapsed_ms` fields are
  incidental and must not be quoted.
- **Why it exists:** the annulment of challenge D12 rested on this fact, and the fact had been
  published in `RESULTS.md`, `LIMITATIONS.md` and the challenge document as "measured on the ring"
  with **no file to cite** — which reading rule 9 of this repository forbids. The probe repairs
  that by putting the measurement where every other claim's evidence lives.
- **Rules R1–R3 were fixed before execution** and are written into the file. **R1 did not fire**:
  `GROUP BY cat` against `PRIMARY KEY (id)` is refused, `code=2200`, with and without
  `ALLOW FILTERING`, so the structural argument holds. **R2 passed**: the aligned table's result
  matches the Python ground truth exactly. **R3 fired**, and narrows the argument — C3a's sweep
  shape, `SELECT SUM(amt) … WHERE cat='c3'`, *is* accepted against the unaligned table once
  `ALLOW FILTERING` is added, and C3a is the arm behind campaign 7's headline 2 011.399 ms.
- **Ring hygiene:** no SAI index is created, so the node's SAI budget is untouched, and the
  keyspace is dropped on exit. Verified after the run: 101 indexes on each of the three nodes,
  no residual keyspace, no snapshot.

### `findings_agg7bis_hcd.json` and `findings_agg7bis_mongodb.json`
- **Probe:** `probes/probe_agg_7bis.py --engine hcd` and `--engine mongodb` (campaign 7bis,
  the re-run of the aggregation axis).
- **Read first:** `result.D9_estimate_by_phase` on the HCD side, and the `raw_ms` arrays
  everywhere.
- **These two files are the only ones in the corpus that keep their observations.** Every
  timed distribution carries `raw_ms`, the full series in execution order, plus a `raw_note`
  saying why. The rest of `data/raw/` retains summaries only, and `docs/STATISTICS.md`
  records that as the dossier's central statistical defect. Because these two do not, they
  carry the first bootstrap intervals and the first rank test in the repository — on both
  arms, which no earlier comparison could support.
- **Against the dossier, in the files:** `D9_estimate_by_phase` records
  `estimatedDocumentCount()` as `0` before flush, **171 267** after `nodetool flush` and
  **172 132** after major compaction, against a true 200 000. That refutes challenge D9,
  which this repository had published: the estimator is wrong in steady state, not only at
  cold start, so M22 was understated here rather than overstated. The MongoDB file records
  `200000` exactly for the same call on the same corpus.
- **Also against the dossier:** the ingest section measures both arms at a batch of 100, the
  Data API's own per-call ceiling — HCD 206.961 s against MongoDB 29.85 s, **6.9×**, which
  withdraws the 46.3× campaign 7 reported by comparing that ceiling with MongoDB's native
  10 000-document batch.
- **`verdict_rules_preregistered`** holds the five rules R1–R5, fixed before execution, that
  would have refuted the campaign. They are in the evidence file, not only in the report.
- **Reserve the author owes:** the HCD scan series opens at 147 138.527 ms against a median of
  132 896.7 ms for the other fourteen — a warm-up the protocol had declared absent without
  measuring it. Both readings are published in `docs/campagne7bis.fr.md`.

### `findings_agg_cqlref.json`
- **Probe:** `probes/agg_cql_arm.py`.
- **Read first:** `LABEL` — *"APPLES-TO-ORANGES REFERENCE — native CQL, NOT the HCD document
  model / Data API. Requires abandoning the document model and pre-designing a table
  partitioned by the group key."*; `table`; `C3a_per_partition_sweep_10q_ms`;
  `C3b_full_groupby_cat_ms`; `ground_truth`.
- **Numbers as measured:** per-partition sweep of 10 queries p50 2 011.399 ms (n = 15,
  correct); full cross-partition `GROUP BY` p50 2 568.372 ms, described by `C3b_is` as the
  coordinator full-scan anti-pattern.
- **Caveat that must travel:** the `LABEL` is the caveat. This arm is not comparable to the
  document-model arms; it is a reference point that costs the document model to obtain.

---

## Contested figures

Every row here is a number a reader might lift out of this directory. The middle column is
the file it is in; the right column is what contests it, inside this same dossier.

| Figure | File | What contests it, in the same breath |
|---|---|---|
| 0.7775 ms/KiB; 44× and 79× | `comparison.json` | Cache-resident/memtable regime (`rmw_postflush.json`, audit I4). Stack against stack, not engine against engine — but see the next row, which makes it *worse* for HCD, not better |
| Engine-against-engine 40× / 72×; tier ≈ 9 % | `comparison_v2.json` | Refutes the author's own challenge C1 estimate of ~31 %. Conflicts with the 29 % in `findings_tier.json`; audit I3 records an unpinned 9–29 % range |
| Tier 0.219 ms/KiB, storage 0.547 ms/KiB, tier ≈ 29 % | `findings_tier.json` | The file's own `VERDICT.methods_agree`: methods diverge 34 % at 64 KiB and 28 % at 125 KiB; arm B is a subtraction instrument, not a benchmark. No point estimate is published |
| ×7.50 growth | `findings.json` (`findings[2].variant_B_indexed_chunks`) | RF = 1, memtable-resident, and `findings[2].verdict` is `INCONCLUSIVE` by the file's own read-control rule |
| ×5.94 growth "holds under disk" | `findings_disk_rf3.json` | The dataset was on disk; the probed read never left the memtable. `rmw_postflush.json` collapses it to ×1.52. ADR action 1 was reopened over this (audit I5) |
| ×1.52 growth, ~100 ms fixed cost | `rmw_postflush.json` | Flush-per-update fragments SSTables and inflates the absolute; the page cache was never dropped, so "SSTable" is not "cold" |
| Bytes dominate field count | `findings_fieldbyte.json` | Strict two-pass verdict is `INCONCLUSIVE` at the 1.15 boundary (1.128, 1.187), though neither pass approaches 1.5 |
| `UPDATE … IF` p50 13.738 ms | `findings_rf3.json`, `probe4_rf3_supplementary.json` | Three replicas share one host: sub-millisecond inter-replica latency, so Paxos is measured where it hurts least (challenge C3). Coordinator-side, not client latency |
| Vector freshness 120/120 first-try hits | `findings_vector_rf3.json` | The file's own verdict: `NOT DETECTABLE`. Bounded below the ~74 ms HTTP floor; neither confirms nor refutes |
| `$search` lag p50 1015.201 ms | `findings_mongot_freshness.json` | Superseded by `findings_mongot_floor.json`: worst phase of a refresh cycle, inflated ×1.53 on the medians (p50 1015.201 → 664.3 ms) by a self-synchronised probe; the "~1.6×" of ADR-001 rev. 12 is the mean-to-mean ratio (1021.553 / 646.3 = ×1.58) |
| `$search` lag p50 664.3 ms, floor 89.1 ms | `findings_mongot_floor.json` | `atlas-local`, single node, interval not user-tunable there; text `$search` against HCD *vector* search; n = 60, one pass, author-written classification threshold |
| HCD "synchronous", `attempts` median 1 | `findings_hcd_vec_freshness.json` | Means "below the ~45 ms HTTP floor", not "zero" (challenge C11) |
| HCD 22× faster filtered read | `findings_rs_hcd.json` vs `findings_rs_mongo.json` | Against *default* MongoDB. Wildcard-indexed MongoDB is 23.7× faster than HCD on the same query (challenge C12) |
| HCD 0 % miss at τ = 0 | `findings_turn_hcd.json` | Decisive below ~1 s; at τ ≥ 1000 ms MongoDB also misses 0 %, so the edge is moot for conversational RAG (challenge D1) |
| Server-side aggregation absent on HCD | `findings_agg_hcd.json` | Reported as M20–M23 in `docs/campaigns/07-aggregation.fr.md`, but **never adversarially challenged**: the audit covers M1–M17 and the challenges M1–M13, and neither examines the aggregation axis. The two empty distributions are failures, not zero-cost operations |
| Aggregation 602× — Data API client scan-and-aggregate p50 133 984.229 ms against MongoDB server-side `$group` p50 222.711 ms | `findings_agg_hcd.json` vs `findings_agg_mongodb.json` (M23) | A Data API **tier** gap, not an engine result: the same engine, on the same host and corpus, aggregates in p50 2 011.399 ms through native CQL (`findings_agg_cqlref.json`), 66.6× faster than the Data API path — and that arm's own `LABEL` disqualifies it as like-for-like, because reaching it means abandoning the document model. HCD arm **n = 3**, so its p95/p99 carry no information; `counts.estimated` 0 against a true 200 000 proves the corpus was still memtable-resident (M22), so campaign 7 ran in a cache regime. **That reserve is discharged**: campaign 7bis re-measured this axis after flush and major compaction at 130 127.0 ms, **2.1 % faster** than in cache, so the regime was not what carried the result — the cost is transport (`findings_agg7bis_hcd.json`) |

Standing limits that apply to every file without exception: one shared, already-loaded host;
one build of each engine; single-client closed-loop sequential load, so nothing here says
anything about concurrency; percentiles from n = 30–50 with no confidence intervals and no
significance testing outside campaign 7bis (audit I7); and five of the probes were written by the measurer himself
(audit I2), which weighs against the measurements that rest on them.

---

## Evidence held back from this directory

This directory is not the whole of the run's raw evidence, and a reader should not take it
for a complete record. An archive, `verif-storage-20260917/raw_evidence.tar.gz`, exists
outside this repository and holds **13 files, none of them byte-identical to anything
published here**: two scripts — `probe3_variant_b.py` and `control_read.py` — and eleven
evidence files — `findings_rate50.json`, `findings_rate50_rep2.json`,
`control_read_A_rep2.json`, `control_read_B.json`, `probe3_variant_b.json`,
`probe4_traced.json`, `probe4_supplementary_cl.json`, `probe4_traced_statements.json`,
`freshness_attempts.json`, `stats_run50.log` and `stats_run50_rep2.log`. Most are the
RF = 1 counterparts of files published here for RF = 3, and they are not redundant with
them.

One consequence stated plainly, because it bears on a number this dossier already
publishes: **the ×1.56 variant-B read control quoted in `RESULTS.md` M3 — p50
7.390 → 11.523 ms — is recorded in `control_read_B.json`, which is in that archive and
not in this directory.** The two files M3 cites for its controls,
`control_read_A_run1.json` and `control_read_A_run2.json`, carry the variant-A control for
the RF = 3 collection `storage_probe_rf3` (p50 9.748 → 18.179 ms and 8.671 → 16.059 ms)
and do not contain those figures.

This repository records no decision to withhold the archive and no reason for it. The fact
is set down here rather than left silent, because the alternative is a reader concluding
that `data/raw/` is everything the run produced. `probes/README.md`, gap 8, lists the
archive file by file.

---

## Licence

Raw data and documentation in this directory: CC BY 4.0 (`LICENSE-docs`). Probe source under
`probes/`: Apache-2.0 (`LICENSE`).
