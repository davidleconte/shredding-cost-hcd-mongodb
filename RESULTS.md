# RESULTS — master register

Seven campaigns, 17–18 September 2026, on one shared lab host (`alphadebunker`, Intel Xeon Gold 6148,
80 vCPU, 220 GiB RAM), against IBM DataStax HCD 2.0.6 (release `5.0.7.0-ea50e91ba01f`) with Data API
v1.0.33, and MongoDB 8.x. Percentiles only: this dossier publishes no means for latency.

Evidence markers used throughout: **[D]** documented by a vendor or upstream source · **[R]** reported
by a third party · **[U]** unverified at the time of writing · **[M]** measured here.

---

## 1. What this dossier set out to test, and what it found

The dossier began as an attempt to verify, on a build the author controls, four claims he had marked
**[U]** in his own article about how HCD's Data API stores a JSON document — and it ended as a
side-by-side measurement of HCD against MongoDB on ten axes. It confirmed the mechanism the article
describes: a document is shredded into one row of twelve physical columns with nine automatically
created SAI indexes ([findings.json](data/raw/findings.json)), and a single-field `updateOne` is a
read-modify-write cycle that rewrites the whole document plus every derived column under a Paxos-guarded
conditional, observed directly in 10 of 10 CQL traces. It then contradicted the article's own step 4:
mutation cost tracks *unchanged* indexed content. **MongoDB won five of the ten measured axes, HCD two;
three named no winner.** MongoDB's five: single-field mutation (44× to 79× on the stack, 40× to 72×
engine-to-engine), point read by `_id` (≈19.6×), filtered search on a field it was given an index
for (23.7×), aggregation (602× against HCD's Data API path **at ten groups** — campaign 7bis bounds it to its query shape: 584× at ten groups and 151× at a hundred thousand, because MongoDB's cost scales with group cardinality and HCD's does not — a tier gap, not an engine gap: the same
engine, same host, same corpus aggregates
in ~2 s through native CQL ([findings_agg_cqlref.json](data/raw/findings_agg_cqlref.json)), at the price
of abandoning the document model and pre-designing a table partitioned by the group key), and exact
counting, which HCD's Data API simply refuses above 1 000 documents.
HCD's two: filtered search on a field nobody declared an index on, against a MongoDB that was never
given one (21.7×), and search-index freshness, where its index sits on the write path while MongoDB's
`$search` indexer has a refresh interval. Two of the campaigns' headline numbers did not survive later
measurement by the same author: the ×7.50 mutation growth coefficient is a memtable artefact that
collapses to ×1.52 once the read half of the cycle is forced onto SSTables
([rmw_postflush.json](data/raw/rmw_postflush.json)), and the Data API tier's share of the per-byte cost
was measured at 29 % in one campaign and 9 % in another and has never been reconciled. Every number
below is cache- or memtable-resident, single-client, sequential, on one shared and already-loaded host,
one build of each engine, with no concurrency and no multi-host topology — conditions under which the
article's own Part II §4 standard would disqualify somebody else's benchmark, and which disqualify these
figures as a purchasing argument. What the dossier establishes is mechanism and direction. It does not
establish production magnitudes.

---

## 2. The headline table

One row per measured axis. The margin column is quoted as measured, never rounded toward a conclusion.
The last column is not a footnote: a margin quoted without it is a misquote.

| Axis | MongoDB | HCD | Winner | Margin | The caveat that must travel with the margin |
|---|---|---|---|---|---|
| **Single-field mutation cost** (per indexed KiB, 16 fields × 512→8000 B) | 0.0098 ms/KiB default (r² 0.78); 0.0176 ms/KiB wildcard (r² 0.88); p50 5.5–7.6 ms, flat | 0.7775 ms/KiB through Data API (r² 0.997), p50 40.9→130.8 ms; 0.7037 ms/KiB CQL-direct (r² 0.996), p50 18.4→101.6 ms | MongoDB, decisively | 44× wildcard / 79× default as stacks; 40× / 72× engine-to-engine with the tier removed | Cache-resident (memtable) rate only. The per-byte coefficient it rests on collapses from ×5.94 to ×1.52 once the RMW read is forced onto SSTables ([rmw_postflush.json](data/raw/rmw_postflush.json)) — the mechanism transfers, the rate does not. Durability was matched by a declared judgement that *favoured HCD* (`j:true` waits for fsync, `commitlog_sync periodic 10 s` does not); HCD lost anyway. Closed-loop sequential single client. HCD ring carried ~13 GiB/node of unpurged `system.paxos` — an unquantified drag, so HCD's absolutes are a noisy ceiling. [comparison.json](data/raw/comparison.json), [comparison_v2.json](data/raw/comparison_v2.json) |
| **Where the per-byte cost is charged** (stateless tier vs stateful engine) | No equivalent tier in this rig — not comparable | Method 1 (bypass, disk regime): storage 0.547 ms/KiB (r² 0.997) + tier 0.219 ms/KiB (r² 0.98) = 0.766; tier 29 %. Method 2 (coordinator-trace): tier 0.145 ms/KiB, 19 %. Matched cache regime, separated arms: tier ~9 % | HCD-internal, no winner | Tier share **9–29 %, unpinned**; majority (71–91 %) sits in the stateful engine | The 9 % and the 29 % are a 3× disagreement on the same quantity, in different regimes with different arm scheduling, **never reconciled** (audit I3). The two methods of campaign 4 themselves diverge 34 % at 64 KiB and 27.7 % at 125 KiB. No single split is publishable; quote the range with its regime. The rate being split is itself a memtable figure. [findings_tier.json](data/raw/findings_tier.json), [findings_tier_method2.json](data/raw/findings_tier_method2.json), [tier_comparison.json](data/raw/tier_comparison.json), [comparison_v2.json](data/raw/comparison_v2.json) |
| **Point read by `_id`** (1 M documents) | p50 0.530 ms wildcard; 0.616 ms default | p50 10.382 ms | MongoDB | ≈19.6× (wildcard arm) | Stack versus stack. HCD's ~10 ms is the Data API tier HTTP hop, charged on every read and not only on every write; a CQL-direct read arm, which would shrink the gap, was **not run** (challenge C15). Cache-resident, 50 reps, single client. [findings_rs_mongo.json](data/raw/findings_rs_mongo.json), [findings_rs_hcd.json](data/raw/findings_rs_hcd.json) |
| **Filtered search, undeclared field** (1 M documents) | p50 376.698 ms — collection scan, no index on the queried field | p50 17.376 ms — automatic SAI, nothing declared | HCD | 21.7× | This is a win over a MongoDB that was never given the index (challenge C12). What HCD buys on this axis is the **dispensation from index design**, an operational property — not engine speed. The same MongoDB with a wildcard index answers in 0.732 ms (next row). [findings_rs_hcd.json](data/raw/findings_rs_hcd.json), [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) |
| **Filtered search, declared (wildcard) index** (1 M documents) | p50 0.732 ms | p50 17.376 ms (same HCD measurement as the row above — HCD has one path) | MongoDB | 23.7× | Same run, same corpus. HCD's figure includes the Data API tier hop and was not re-measured CQL-direct (C15). A wildcard index is MongoDB doing HCD's job; it is not free at write time, which is the axis of row 1. [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) |
| **Secondary-index freshness** (read-your-writes on an ordinary index) | Found on first query, attempts `{1: 40}` both arms; insert→found p50 7.072 ms wildcard, 894.213 ms default | Found on first query, attempts `{1: 40}`; insert→found p50 33.240 ms | Tie | No margin — both engines synchronous on regular indexes | The tie is on **attempts, not latency**: mongo-default's single successful find still took p50 894.213 ms because it scanned. This result bounds HCD's freshness advantage to the search/vector path; it is not a general read-your-writes edge. [findings_rs_hcd.json](data/raw/findings_rs_hcd.json), [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) |
| **Search-index freshness** (write → searchable) | `$search` via mongot: self-synchronised probe p50 1015.201 ms, poll attempts median 34; de-synchronised p50 664.3 ms, floor 89.1 ms, max 1170.2 ms — a refresh interval, not a fixed delay | JVector search: p50 44.972 ms, poll attempts min = median = max = 1, 0 cycles never visible | HCD, in direction | Miss rate of one search issued τ ms after the write: **HCD 0/30 at every τ; MongoDB 30/30 (100 %) at τ=0, 15/30 at 500 ms, 0/30 at τ ≥ 1000 ms** | Three reserves, all of which cut against the headline. (a) The mongot measured is **1.75.1 `localDev` edition** on a single-node `atlas-local` container — it may **not** be quoted as "MongoDB Atlas Search lag" or as a property of MongoDB the product; the commit interval is internal to the jar and was never read ([findings_mongot_provenance.json](data/raw/findings_mongot_provenance.json)). (b) HCD's "synchronous" is only **bounded below the ~45 ms HTTP round-trip floor**, never shown to be zero, and its max was 573.598 ms. (c) Not like-for-like: MongoDB `$search` is lexical, HCD JVector is vector (C14). The 1015.2 ms figure was the worst phase of the cycle and is corrected by M18. [findings_mongot_freshness.json](data/raw/findings_mongot_freshness.json), [findings_mongot_floor.json](data/raw/findings_mongot_floor.json), [findings_hcd_vec_freshness.json](data/raw/findings_hcd_vec_freshness.json), [findings_turn_hcd.json](data/raw/findings_turn_hcd.json), [findings_turn_mongodb.json](data/raw/findings_turn_mongodb.json) |
| **Vector freshness at RF = 3 under `vector-search = LOCAL_ONE`** | Not measured | 120/120 cycles (60 idle + 60 at 40 vector-writes/s) had the just-written vector top-1 on the first `LOCAL_ONE` search; 0 cycles where the `LOCAL_QUORUM` key read hit and the vector search missed; insert→visible p50 74.735 ms idle / 74.406 ms loaded | No comparison — verdict **NOT DETECTABLE** | None quotable | The `LOCAL_ONE` vector read against `LOCAL_QUORUM` writes is a real design asymmetry ([M6]), but on a co-located ring inter-replica latency is sub-millisecond, so any window is **bounded below the ~74 ms HTTP measurement floor**. This neither confirms nor refutes the article's Part II §1 claim; a WAN topology is where it would surface and this bench cannot produce one. [findings_vector_rf3.json](data/raw/findings_vector_rf3.json) |
| **Aggregation** (`GROUP BY cat`, `SUM(amt)`, 200 000 docs, 10 groups, all arms exact against ground truth) | Server-side `$group` p50 222.711 ms | Data API client scan-and-aggregate p50 133 984.229 ms (n = 3), 200 000 docs pulled to the client at the Data API's default ~20 docs/page; native CQL per-partition sweep p50 2 011.399 ms; native CQL cross-partition `GROUP BY` p50 2 568.372 ms | MongoDB | **602× vs HCD's Data API; 9.0× vs HCD's best CQL path; 66.6× between HCD's own two paths** | This is a **capability gap, not a latency race**, and the 602× must never be quoted as "HCD is 602× slower". The same storage engine, same host, same corpus, aggregates in ~2 s through native CQL — the 134 s belongs to a tier that exposes no aggregation surface and therefore forces the whole collection through the client. **And** the CQL arm is a labelled apples-to-oranges reference: reaching it means abandoning the document model — which is structural and needs no percentile. An earlier revision added "and pre-designing a table partitioned by the group key"; ~~**D12 withdrew that clause**, because the aligned table and a cross-partition `GROUP BY` against it differ by ×1.28 at the median, their supports overlap, and the ratio interval [0.966, 1.421] contains 1.0 — at this scale the partitioning choice does not separate from noise.~~ **⚠ That withdrawal is annulled (18 September 2026) and the clause is reinstated; the struck sentence is kept as written so the error stays legible.** D12 mistook its object, and the struck sentence contains its own refutation: the cross-partition `GROUP BY` runs *against it* — against the aligned table. `agg_cql_arm.py` creates exactly one table, `PRIMARY KEY (cat, id)`, and both arms query it, so they differ by query shape, not by schema, and their ratio prices a query shape rather than a partitioning choice. Measured on the ring, the same `GROUP BY cat` against a `PRIMARY KEY (id)` table is **refused** (`InvalidRequest code=2200`, `ALLOW FILTERING` included), so that arm is expressible only because the table is pre-partitioned by the group key. What survives of D12: the ×1.28 **between the two query shapes** is not established, `agg_cql` retains no per-observation series, and its scale reserve stands — 200 000 rows on ten partitions bounds nothing at 10⁸ rows or 10⁵ partitions. HCD arm is n = 3; its p95/p99 carry no information. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row. [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json), [findings_agg_hcd.json](data/raw/findings_agg_hcd.json), [findings_agg_cqlref.json](data/raw/findings_agg_cqlref.json) |
| **Exact count** (200 000 documents) | `count_documents({})` p50 115.009 ms → 200000 exact; filtered collscan p50 157.177 ms → 20000 exact; filtered with a declared `cat` index p50 12.659 ms; `estimated_document_count()` p50 0.408 ms → 200000 | `countDocuments({})` and `countDocuments({cat:"c3"})` both **impossible**: `TooManyDocumentsToCountException — Document count exceeds 1000, the maximum allowed by the server`, on a stock container with no count-limit env var. `estimatedDocumentCount()` p50 6.875 ms → returned **0** while the true count was 200 000 | MongoDB, by capability | Not a ratio — HCD has no answer at this cardinality | MongoDB wins this axis because it **answers**, not because it answers cheaply: its exact count is a scan (115 ms / 157 ms) and only reaches 12.659 ms after a declared index, so MongoDB too pays index design here. HCD's estimate is not approximate, it is **wrong** — pre-flush it returns 0, and campaign 7bis shows it still returns 171 267 after flush and 172 132 after major compaction against a true 200 000, an error of ~14 % that does not decay. Nothing in the API signals the condition — an application testing `if count == 0` on a freshly loaded collection concludes it is empty, and one testing `if count < threshold` in steady state is also wrong. That zero is also direct proof this campaign ran in a **cache regime**, not a proven disk regime. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row. [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json), [findings_agg_hcd.json](data/raw/findings_agg_hcd.json) |

---

## 3. Measurements M1–M23

The register is M1–M8 and M10–M23. **No M9 was ever assigned** — the identifier is absent from the
evidence register in [ADR-001](docs/adr/ADR-001-modelling-policy.md) and from every campaign report.
It is listed here as missing rather than silently skipped.

The ADR's own evidence register stops at M19: it holds M1–M8 and M10–M19 and nothing above.
**M20–M23 were assigned in this repository for campaign 7, after the ADR's last revision, and were
never entered in it** — this section and [the campaign 7 report](docs/campaigns/07-aggregation.fr.md)
are their only register. The adversarial audit, which covers M1–M17, never saw them either.

Two entries, **M6 and M8, have no raw JSON file** under `data/raw/`: their evidence is a Data API
startup configuration log and a raw CQL row read, recorded in the ADR evidence register but not
captured as a machine-readable artefact. They are weaker on traceability than every other row and are
marked as such. **M20 and M21 each carry one sub-claim with the same weakness** — the nineteen-command
allow-list and the absence of a count-limit environment variable are transcribed from the campaign
report, not captured under `data/raw/`; their rows say so and cite the report rather than a raw file.

### Campaign 1 — verification at RF = 1 ([01-verification.fr.md](docs/campaigns/01-verification.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M1** | The shredded collection row carries 12 physical columns. All 9 predicted generic columns present under the predicted names (`doc_json`, `exist_keys`, `array_contains`, `array_size`, `query_text_values`, `query_dbl_values`, `query_bool_values`, `query_null_values`, `query_timestamp_values`), plus 3 the practitioner literature omits: `key frozen<tuple<tinyint,text>>`, `tx_id timeuuid`, `query_lexical_value text`. 9 SAI indexes created automatically on a collection declaring no vector option. Second pass identical | SUPPORTED — claim A2, **[U] → [M]** | [findings.json](data/raw/findings.json) | One build, one collection, one day. The vendor documents none of these names: an observation of a build, not an interface. The upstream **[D]** "ten indexes per collection" is the budget checked at creation, not the count created (9 here). Rated by the adversarial audit as one of two unattackable results, because it is a direct schema read independent of any code the measurer wrote |
| **M2** | Read-modify-write cycle observed directly: each `updateOne` with one `$set` produced `SELECT key, tx_id, doc_json … LIMIT 1` then a single `UPDATE` rewriting 11 assignments (`tx_id = now()`, 9 derived columns, whole `doc_json`) guarded by `IF tx_id = ?`. 10 of 10 traced operations. Statement counts: `insertOne` = 1, `updateOne` = 2, `deleteOne` = 2 | SUPPORTED by trace — claim A3, **[U] → [M]** | [findings.json](data/raw/findings.json) | Established **by trace, not by latency**. Tracing was off during the main run (empty `system_traces`), so the probe was re-run at `settraceprobability 1.0`. A reader who rejects trace evidence must hold A3 INCONCLUSIVE, because the latency probe is inconclusive by the campaign's own control rule. One node, RF = 1 |
| **M3** | Mutation cost scales with **unchanged** indexed content. Variant B (indexed chunks ≤ 8000 B, 2/5/17 fields at 8/32/128 KB), mutation held at one scalar `$set`: p50 12.104 → 15.718 → 32.108 → 90.783 ms = **×7.50** for ×128 document size, against a same-size read control of ×1.56 (7.390 → 11.523 ms) and an `updateOne` HTTP payload constant at 122–124 B request / 47 B response. Variant A (ballast not indexed): update ×1.92 / ×2.21 against read ×1.86 / ×1.94 | Step 4 of the article's five-operation model **CONTRADICTED**; variant A INCONCLUSIVE by the pre-registered control rule | [findings.json](data/raw/findings.json), [control_read_A_run1.json](data/raw/control_read_A_run1.json), [control_read_A_run2.json](data/raw/control_read_A_run2.json) | **×7.50 is a memtable-regime coefficient** and must never be quoted as an engine property: zero SSTables flushed, no compaction crossed, RF = 1, loopback client. ×5.94 on disk at RF 3 (M10); **×1.52** once the cycle's `SELECT` is forced onto SSTables (M15). The Data API refuses indexed strings > 8000 B, which forced the chunking. n = 30 per size, medians only, no confidence intervals, closed-loop sequential — requirement 1 of the article's own Part II §4 violated; requirement 6 explicitly not met |
| **M4** | Consistency levels read from `system_traces`: 70 of 70 statements on the target table at `LOCAL_QUORUM` (40 SELECT, 10 INSERT, 10 UPDATE, 10 DELETE); `LOCAL_SERIAL` the serial level on all 30 conditionals. Not configured by the client — Data API tier defaults | SUPPORTED — claims A5a/A5b, **[U] → [M]** | [findings.json](data/raw/findings.json) | On one node at RF = 1 both levels are satisfied by a **single replica**: the *name* is established, the cost of a real quorum or Paxos round is not (supplied later by M5). The harness's own raw counter mixes all 200 traced sessions (`{ONE: 42, LOCAL_QUORUM: 70, LOCAL_ONE: 2}`); the 70/70 and 30/30 come from a supplementary read-only per-statement query. First invocation INCONCLUSIVE (tracing off) |

### Campaign 2 — replication factor 3 ([02-replication-rf3.fr.md](docs/campaigns/02-replication-rf3.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M5** | Every conditional write on an RF = 3 keyspace runs a full three-replica Paxos round, traced message by message (`PAXOS2_PREPARE_REQ` 370 B → `PAXOS2_PREPARE_RSP` ≈263 KB → `PAXOS2_PROPOSE_REQ` ≈131 KB → commit; 448 statements traced, 232 `PAXOS_COMMIT` events over 30 sessions, 0 read-repair). Coordinator-side p50: non-conditional `SELECT` 6.582 ms, `UPDATE … IF` **13.738 ms** (n = 124), `INSERT … IF NOT EXISTS` 11.174 ms, `DELETE … IF` 10.207 ms | SUPPORTED — the consensus cost RF = 1 hid entirely | [findings_rf3.json](data/raw/findings_rf3.json), [probe4_rf3_supplementary.json](data/raw/probe4_rf3_supplementary.json) | Contested in the same breath by challenge C3: the three dc1 replicas **share one host**, inter-replica latency sub-millisecond, so the Paxos cost is measured exactly where it hurts least — structure established, magnitude not representative. Durations are coordinator-side, not client latency. Memtable-resident, no flush, no compaction. Shared demo ring at load average 14–16. The supplementary trace analysis is the measurer's own instrument (audit I2) |
| **M1 (re-run)** | Shredded layout identical at RF = 3: 12 columns, 9 SAI, same three unpredicted columns. Identical across both passes — shredding does not depend on the replication factor | SUPPORTED, RF-independence established | [findings_rf3.json](data/raw/findings_rf3.json), [findings_rf3_rate50.json](data/raw/findings_rf3_rate50.json), [findings_rf3_rate50_rep2.json](data/raw/findings_rf3_rate50_rep2.json) | Collection created with `indexing.deny=['ballast']` and no vector option; different options would not necessarily give 9 indexes |
| **M2 (re-run)** | The RMW cycle is present at RF = 3 exactly as at RF = 1, both statements at `LOCAL_QUORUM`, the conditional at `LOCAL_SERIAL`. `updateOne` HTTP payload constant at 122–124 B / 47 B across 1, 8, 32 and 128 KB, so the growth cannot be HTTP transfer | SUPPORTED by trace only | [findings_rf3.json](data/raw/findings_rf3.json) | The latency probe is INCONCLUSIVE at RF = 3 as at RF = 1: update growth ×1.72 / ×1.91 against a read control of ×1.86 / ×1.85 — the same slope. n = 30, medians only (audit I7) |
| **M3 (not re-run)** | Variant B — the ×7.50 coefficient that carries the article's step-4 correction — recorded `NOT_ATTEMPTED` at RF = 3. Creating a second default-indexed collection on the shared ring was blocked twice by the session's safety classifier | Capability gap: the campaign could not test its own load-bearing measurement | [findings_rf3.json](data/raw/findings_rf3.json) | ×7.50 may therefore never be quoted as an RF = 3 property. Independently shown to be a regime artefact: ×7.50 memtable RF 1, ×5.94 disk RF 3, ×1.52 post-flush — a 5× interval across regimes (audit I4) |
| **M4 (re-run)** | Same levels, now satisfied by 2 of 3 real replicas: 100 % of collection statements at `LOCAL_QUORUM`, every conditional at `LOCAL_SERIAL`. Schema DDL at `LOCAL_ONE` with serial `LOCAL_QUORUM`, coordinator p50 1.94 ms | SUPPORTED — but see caveat | [probe4_rf3_supplementary.json](data/raw/probe4_rf3_supplementary.json), [findings_rf3.json](data/raw/findings_rf3.json) | **The unmodified harness returned INCONCLUSIVE in both passes**, with `consistency_levels_observed = {}` over 200 traces examined, and `findings_rf3.json` records A5 = INCONCLUSIVE in both `verdicts_run1` and `verdicts_run2`. SUPPORTED rests on the measurer's own supplementary analysis — precisely the dependency audit finding I2 flags |
| **M6** | Data API consistency levels are configuration properties, not fixed: `consistency.writes`/`reads`/`schema-changes = LOCAL_QUORUM`, `consistency.vector-search = LOCAL_ONE`, `serial-consistency = LOCAL_SERIAL`, `lwt.retries = 3`, settable through the `STARGATE_JSONAPI_OPERATIONS_QUERIES_*` environment surface | SUPPORTED | **No raw JSON.** Data API v1.0.33 startup configuration log, recorded in [ADR-001](docs/adr/ADR-001-modelling-policy.md) | Weakest traceability in the register: a log read transcribed into the ADR, not a captured artefact. Its consequence — `vector-search = LOCAL_ONE` means a vector read at RF = 3 can hit a replica the `LOCAL_QUORUM` write has not reached — was tested separately as M7 |
| **M7** | Vector-search freshness at RF = 3 under `vector-search = LOCAL_ONE`: 120/120 cycles (60 idle + 60 at 40 vector-writes/s) had the just-written vector top-1 on the first `LOCAL_ONE` search; 0 cycles where the key read hit and the vector search missed; insert→visible p50 74.735 ms idle / 74.406 ms loaded. Validity: marker at cosine similarity 1.0 rank-1, background ≤ 0.83 | **NOT DETECTABLE** — neither confirms nor refutes the article's Part II §1 | [findings_vector_rf3.json](data/raw/findings_vector_rf3.json) | The window is bounded below the ~74 ms HTTP measurement floor, not shown to be absent. Co-located ring, sub-millisecond inter-replica latency; a WAN deployment is where `LOCAL_ONE` could surface a stale vector, and this bench cannot make a replica lag longer than an HTTP round trip |

### Follow-up to campaign 1 — nested shredding

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M8** | Nested JSON is flattened to dotted paths: every scalar lands in its typed value map keyed by the full path (`payer.account.id`, `lines.0.qty`), `exist_keys` enumerates every path including array indices, `array_contains` carries scalar-array membership and whole encoded array-objects, `array_size` per-path lengths, `doc_json` the original verbatim. Any nested scalar is filterable with no index declaration. Two traps: (a) inside an array of objects only positional paths exist — `lines.0.sku` filters, `lines.sku` across elements does not, there is no `$elemMatch`-by-path; (b) hard shape limits — nesting depth ≤ 16, ≤ 1000 properties per indexable object, indexed string ≤ 8000 bytes | SUPPORTED (mechanism); limits documented | **No raw JSON.** Raw CQL row read on `rh-hcd` (RF = 1) after a Data API insert, plus filter and depth/width stress probes, recorded in [ADR-001](docs/adr/ADR-001-modelling-policy.md) | Same traceability weakness as M6. Compounds M3: one nested-field update still rewrites `doc_json` plus every derived map, so the indexed-content coefficient grows with nesting breadth and depth |

*(No M9 exists — see the note above the register.)*

### Campaign 3 — disk regime and the field-versus-byte separation ([03-disk-regime.fr.md](docs/campaigns/03-disk-regime.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M10** | Disk regime proven rather than assumed: 24 576 incompressible documents of 262 144 B (fill 1 137.8 s), flush → 82 SSTables, major compaction → 40, compaction counter 651 → 729 (78 crossed), 6 491 369 675 B = 6.05 GiB on disk against a 2 048 MiB memtable budget, caches invalidated. Against that state, variant B grew 20.389 → 25.127 → 44.314 → 121.189 ms = **×5.94** (read control ×2.10, SUPPORTED); variant A ×1.78 against read ×1.89 (INCONCLUSIVE) | SUPPORTED — the indexed-content coefficient does not collapse on disk | [findings_disk_rf3.json](data/raw/findings_disk_rf3.json), [disk_state.json](data/raw/disk_state.json); **contested by** [rmw_postflush.json](data/raw/rmw_postflush.json) | Four limits, none droppable. (1) "Disk-bound" describes the **dataset, not the probed read**: the RMW probe re-reads the row it just wrote, memtable-resident whatever the dataset size. (2) The OS page cache was never dropped (no root); 6.05 GiB fits in 220 GiB of host RAM. (3) The ×7.50 → ×5.94 difference **mixes regime with a topology/hardware confound** (RF 1 on 3 GiB/2 G heap versus RF 3 on 8 GiB/4 G heap) and must not be attributed to disk. (4) Partly overturned within the dossier by M15; ADR-001 action 1 was reopened from `[x]` to `[~]`. A ~6 GiB/node `system.paxos` residue was left on the shared ring by the LWT fill and could not be reclaimed |
| **M11** | Two series, each holding one term fixed, two passes, n = 30 per point. **S2** (field count 9 → 128 at constant 64 KiB indexed volume): endpoint ratio 1.128 (slope 0.0774 ms/field, r² 0.5745) and 1.187 (slope 0.1112, r² 0.9154). **S1** (bytes per field 512 → 8000 at constant 16 fields): 25.163 → 114.649 ms, ratio **4.556**, slope 0.011926 ms per byte-per-field, r² **0.9999**; pass 2 ratio 4.738, r² 0.9999. Internal control (16 × 4096 B measured in both series): 2.0 % and 0.65 % spread | **Indexed byte volume dominates**; field count a weak secondary factor | [findings_fieldbyte.json](data/raw/findings_fieldbyte.json) | The pre-registered rule (S2 ratio ≤ 1.15 → bytes dominate; ≥ 1.5 → field count independent) returns **no clean verdict**: the two passes straddle 1.15, giving "BYTES DOMINATE" and "INCONCLUSIVE". The strict answer is inconclusive; only the direction is unambiguous, neither pass approaching 1.5. The intended three-arm design was not executable (the 8 000-byte indexed-string cap makes 17 the minimum field count at 128 KB). Ran only in the disk regime, and by the audit's later finding the probed read never left memtable anyway — these are memtable-under-pressure rates. S2 r² weak in pass 1 (0.5745). Rated among the most robust derived measurements because `probe_field_vs_byte.py` ran **unmodified** |

### Campaign 4 — tier versus storage ([04-tier-vs-storage.fr.md](docs/campaigns/04-tier-vs-storage.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M12** | In the proven disk regime the ~0.77 ms/KiB rate decomposes by method 1 (bypass) into **storage 0.547 ms/KiB (r² 0.997)** and **tier 0.219 ms/KiB (r² 0.983)**, summing to 0.766 and reproducing campaign 3's rate. Tier share 29 % by method 1, 19 % by method 2 (coordinator-trace, tier slope 0.145 ms/KiB, r² 0.992). Tier share of absolute p50 by size: 39.7 % at 8 KiB, 29.9 % at 16, 31.1 % at 32, 33.8 % at 64, 29.8 % at 125 KiB. Third indicator: Data API container CPU alternated 0.52 % (arm B) to 230.33 % (arm A), median 29.73 % — the tier spends real CPU, it is not merely a network hop | MAJORITY STORAGE (~71 %), substantial minority tier. Pre-declared trigger `tier_dominates` = **false**, so no article claim was replaced | [findings_tier.json](data/raw/findings_tier.json), [findings_tier_method2.json](data/raw/findings_tier_method2.json), [tier_comparison.json](data/raw/tier_comparison.json), [disk_state_c4.json](data/raw/disk_state_c4.json) | (1) **No single precise split is published**: methods agree within 25 % at 8/16/32 KiB but diverge 34 % at 64 KiB and 27.7 % at 125 KiB, tier slopes differing ~50 %, because they subtract different "storage". Only the direction is robust. (2) Data API container: 2 GiB, **no CPU cap**, co-located — the slope answers the location question, the absolute does not transfer. (3) The tier term is parse + shred + serialisation together, never separated; arm B reuses already-shredded values, so it never exercises the shredding code and its "storage" term is an optimistic floor (C7). (4) Contradicted by M14's ~9 % and never reconciled (audit I3). The rate being split is itself a memtable coefficient |

### Campaign 5 — HCD versus MongoDB on mutation ([05-mutation-comparison.fr.md](docs/campaigns/05-mutation-comparison.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M13** | Per indexed KiB: HCD through the Data API **0.7775 ms** (r² 0.997); MongoDB with a wildcard `$**` index **0.0176 ms** (r² 0.8794); MongoDB with nothing indexed on the ballast **0.0098 ms** (r² 0.7809). Ratios 44× and 79×. Absolute update p50 over 8 → 125 KiB: HCD 40.9 → 130.787 ms (endpoint ratio 3.198); mongo-wildcard 5.544 → 7.621 (1.375); mongo-default 5.67 → 6.484 (1.144) | **MongoDB, decisively, on this axis** | [comparison.json](data/raw/comparison.json), [cmp_hcd.json](data/raw/cmp_hcd.json), [cmp_mongo.json](data/raw/cmp_mongo.json) — `probe_comparative.py` run **unmodified** | A cache-resident rate whose coefficient is a memtable phenomenon (M15). A **stack-vs-stack** ratio: HCD carries a Data API tier MongoDB has no equivalent of. The durability mapping is a declared judgement that **favoured HCD** (C6) and HCD still lost 44×. Paxos-vs-document-atomicity is named, not aligned. One host, one build of each engine, closed-loop sequential single client — nothing about concurrency or scaling; §10 requirement of a fixed offered load violated. Ring carried ~13 GiB/node of `system.paxos` residue at load average 14–16, never quantified (C8, audit I6). Says nothing about read, search, aggregation or freshness. **Both MongoDB arms are the finding**: quoting the default arm alone overstates MongoDB, quoting the wildcard arm alone understates how it is deployed |
| **M14** | The same mutation driven straight over CQL (same nine SAI, same conditional write, tier bypassed): **0.7037 ms/KiB** (r² 0.9959) against 0.7775 through the Data API — removing the tier lowers the slope by only **~9 %**. Engine versus engine: 40× mongo-wildcard, 72× mongo-default. Absolute p50 18.407 → 101.645 ms (endpoint ratio 5.522) | MongoDB — and the win is an **engine** result, not a tier artefact. Refutes the author's own challenge C1 | [cmp_hcdcql.json](data/raw/cmp_hcdcql.json), [comparison_v2.json](data/raw/comparison_v2.json) — `hcd_cql_arm.py` | Two specific weaknesses. (1) `hcd_cql_arm.py` was **written by the measurer**; the audit lists it among the five measurer-written instruments carrying decisive verdicts (I2), in contrast with M13's unmodified probe. (2) Its ~9 % tier share contradicts M12's ~29 % by 3× on the same quantity, never reconciled (I3). Arms separated in time rather than interleaved; arm B's storage work is *asserted* identical to the Data API path (M2), not proven identical |

### Challenge resolutions — the author measuring against himself

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M15** | Flushing before every update forces the RMW `SELECT` onto the SSTable read path. Variant B post-flush: p50 107.765 ms at 1 KB → 112.086 → 119.220 → **163.402 ms** at 128 KB, growth **×1.52**, against ×5.94 (M10, memtable under disk-regime pressure) and ×7.50 (M3, memtable RF 1). A fixed read-path cost of roughly 90–100 ms takes over | The 0.77 ms/KiB per-byte rate is a **MEMTABLE phenomenon**. Challenge C2 CONFIRMED | [rmw_postflush.json](data/raw/rmw_postflush.json) | Carries its own reserve: flushing before each update fragments the table into ~35 small SSTables, so its ~100 ms absolute is **inflated** and the true disk-bound value sits between the memtable and post-flush figures. Page-cache-warm; no root to drop the OS cache. Consequence recorded in the ADR: action item 1 reopened from `[x]` to `[~]` (audit I5), and every per-KiB rate — M3, M10, M11, M12, M13 — relabelled memtable (audit I4) |

### Campaign 6 — freshness, read and search ([06-freshness-read-search.fr.md](docs/campaigns/06-freshness-read-search.fr.md))

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M16** | At 1 M documents, same host. **(A)** Filtered read on an undeclared field: mongo-default p50 376.698 ms (scan), HCD p50 17.376 ms (automatic SAI) = 21.7× faster than default; mongo-wildcard p50 0.732 ms = 23.7× faster than HCD. **(B)** Point read by `_id`: mongo-wildcard 0.530 ms, mongo-default 0.616 ms, HCD 10.382 ms = MongoDB 19.6×. **(C)** Freshness on an ordinary secondary index: all three arms returned the just-written document on the first query, attempts `{1: 40}` each; insert→found p50 HCD 33.240 ms, mongo-wildcard 7.072 ms, mongo-default 894.213 ms | Split — MongoDB on two of three axes; HCD on the undeclared-field axis; tie on secondary-index freshness | [findings_rs_hcd.json](data/raw/findings_rs_hcd.json), [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) | Cache-resident, single-client sequential, shared host at load average 14–16, HCD ring carrying ~13 GiB/node of `system.paxos`, 8 GiB / 4 vCPU per side, 50 reps. The 21.7× is against a MongoDB **never given an index on the queried field** (C12). The axis-C tie is a tie on attempts, not latency. HCD's ~10 ms is the tier hop, not re-measured CQL-direct (C15). `probe_read_search.py` written by the measurer (audit I2) |
| **M17** | HCD JVector, 40 cycles: write-to-searchable p50 **44.972 ms** (min 31.900, p95 84.827, max 573.598), poll attempts min = median = max = 1, 0 cycles never visible. MongoDB `$search` through mongot, 40 cycles: write-to-visible p50 **1015.201 ms** (min 978.641, p95 1042.295, p99 1154.313, max 1224.720), poll attempts min 22 / median 34 / max 36, while `find({_id})` on the same document was p50 1.306 ms | HCD, decisively **in direction**. Magnitude corrected downward by this campaign's own M18 | [findings_mongot_freshness.json](data/raw/findings_mongot_freshness.json), [findings_hcd_vec_freshness.json](data/raw/findings_hcd_vec_freshness.json) | The 1015.2 ms **must never be quoted alone**: it is the worst phase of a periodic refresh interval, inflated by a probe that self-synchronised with the commit cycle. mongot ran on a single-node `atlas-local` — a different MongoDB deployment from M16's 3-member replica set (C15). HCD's 45.0 ms is the HTTP floor: attempts = 1 bounds HCD's lag **below ~45 ms**, it does not prove zero (C11). Not like-for-like: `$search` lexical versus JVector vector (C14). HCD's max 573.598 ms shows a tail the p50 does not carry |
| **M18** | With the probe de-synchronised (random 0–1200 ms pre-insert delay, then 5 ms polling), n = 60: mongot `$search` lag min **89.1 ms**, p10 254.5, p50 **664.3 ms**, p90 988.7, max **1170.2 ms**. Broad and phase-uniform — a Lucene-style refresh interval of ~1.1 s, not a fixed per-write delay | Narrows HCD's own favourable margin — the author refuting his own pro-HCD magnitude. Direction unchanged | [findings_mongot_floor.json](data/raw/findings_mongot_floor.json) | n = 60, one pass, no replication. The "refresh interval versus fixed delay" classification is a threshold in the measurer's own code, not a statistical test (D5). The interval is not user-tunable in `atlas-local`, and `atlas-local` is a development container nobody runs in production (D2). The floor is **89.1 ms, not zero** — a fixed ingestion component on top of the refresh phase, which cuts in HCD's favour and was omitted from the first verdict (D3). The dossier's challenges document states this headline as an arithmetic mean; percentiles are quoted here because this dossier publishes no means for latency |
| **M19** | Miss rate of a single search issued τ ms after the write, 30 cycles per point. **HCD: 0/30 at every τ** (0, 100, 250, 500, 750, 1000, 1500, 2000, 3000 ms). **MongoDB `$search`: 30/30 at τ = 0 (100 %), 28/30 at 100 ms, 25/30 at 250 ms, 15/30 at 500 ms, 10/30 at 750 ms, 0/30 at τ ≥ 1000 ms.** Crossover at ~1 s | HCD totally (0 % vs 100 % at τ = 0) for write-then-search gaps under ~1 s; neutral at τ ≥ 1000 ms, which is where a conversational RAG turn sits | [findings_turn_hcd.json](data/raw/findings_turn_hcd.json), [findings_turn_mongodb.json](data/raw/findings_turn_mongodb.json) | The premise that makes the τ ≥ 1000 ms column decisive — that an LLM-driven turn takes 1–10 s — is an **assumption stated by the challenge author**, not measured against a real workload. Single-node `atlas-local` against HCD `{dc1:3}`, one pass, same text-versus-vector asymmetry as M17. The crossover is this deployment's own refresh interval; a differently configured mongot moves it. This bounds the workload class in which HCD's edge bites; it does not measure how common that class is |
| **Provenance note on M17–M19** | The mongot measured is **version 1.75.1, `localDev` edition** (image label and `/opt/mongot/mongot --version`; `/etc/mongodb-atlas-local/mongot-edition` contains exactly `localDev`), alongside mongod 8.3.11 community. The commit/refresh interval is **not** exposed in the launch script, the README or any image environment variable — it is internal to the jar | **Raises** the reserve on M17, M18 and M19 rather than lowering it | [findings_mongot_provenance.json](data/raw/findings_mongot_provenance.json) | The measured lag is a property of mongot 1.75.1 `localDev` beside a single-node replica set on a loaded shared host. It may **not** be quoted as "MongoDB Atlas Search lag", as "MongoDB's search freshness", or as a property of MongoDB the product. The direction survives — mongot indexes asynchronously off the change stream by construction — because that is architectural, not a build artefact. Closing this would require repeating M17–M19 against a production-edition mongot, which is not possible on this host |

### Campaign 7 — aggregation ([07-aggregation.fr.md](docs/campaigns/07-aggregation.fr.md))

Corpus: 200 000 documents, 10 categories × 20 000, fields `cat` (string) and `amt` (double), same host.
MongoDB 8.0.32 three-member replica set `rs0` at `w:majority`+`j:true`; HCD 2.0.6 keyspace `cmp` at
`{dc1:3}`. All group-by arms verified exact against precomputed ground truth.

| ID | What was established | Verdict | Raw evidence | Regime / caveat |
|---|---|---|---|---|
| **M20** | The HCD Data API command allow-list contains exactly nineteen commands: `alterTable`, `countDocuments`, `createIndex`, `createTextIndex`, `createVectorIndex`, `deleteMany`, `deleteOne`, `estimatedDocumentCount`, `find`, `findAndRerank`, `findOne`, `findOneAndDelete`, `findOneAndReplace`, `findOneAndUpdate`, `insertMany`, `insertOne`, `listIndexes`, `updateMany`, `updateOne`. `aggregate`, `$group` and `distinct` all return `COMMAND_UNKNOWN`. **There is no server-side aggregation pipeline**. The `COMMAND_UNKNOWN` result is a captured artefact; **the nineteen-command list itself is report-transcribed**, not captured — see Raw evidence | Structural — a capability gap, not a latency result | **Split.** `COMMAND_UNKNOWN` and “no server-side aggregation pipeline”: [findings_agg_hcd.json](data/raw/findings_agg_hcd.json) (`structural` field). **The nineteen-command list appears in no raw file**; its only source is [07-aggregation.fr.md](docs/campaigns/07-aggregation.fr.md), transcribed from the campaign report — the same traceability weakness as M6 and M8 | Independent of hardware, load, regime and percentile; it survives every method challenge in the dossier and transposes intact to a production-sized Data API. But an allow-list is a **product decision** and can change between builds: what resists time is the mechanism ("no pipeline ⇒ the corpus crosses the client"), not the list. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row |
| **M21** | Exact counting is capped at 1 000 documents on a stock container: `countDocuments({})` and `countDocuments({cat:"c3"})` both failed with `TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the server`, despite a client `upper_bound` of 400 000. **Report-transcribed, not captured:** the `data-api` container is stated to carry no count-limit environment variable — that statement is in no raw file and the French source hedges it as *d’après le rapport de campagne*. The cap is the server's own **default** on a stock container; whether it is server-configurable was never established — the campaign showed only that the client's `upper_bound` does not move it. On this build as it ships, there is no way in the Data API document model to obtain the exact cardinality of a 200 000-document collection | Structural | **Split.** The two exception strings and the empty count distributions: [findings_agg_hcd.json](data/raw/findings_agg_hcd.json); the client `upper_bound` of 400 000 is `max(n*2,1000)` at [probe_aggregation.py:156](probes/probe_aggregation.py) applied to the `n_loaded` = 200 000 recorded in that JSON. **The “no count-limit environment variable” statement is in neither**; its only source is [07-aggregation.fr.md](docs/campaigns/07-aggregation.fr.md) | The counterpoint, which is unfavourable to MongoDB and belongs in the same breath: MongoDB's exact count is **not cheap either** — p50 115.009 ms unfiltered and 157.177 ms filtered without an index, both scans, dropping to 12.659 ms only after `cat_idx` was declared. MongoDB wins this axis because it answers, not because it answers fast, and it too pays index design here. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row |
| **M22** | `estimatedDocumentCount()` answered in p50 **6.875 ms** and returned **0** while the collection held 200 000 documents. It reads SSTable metadata; before the memtable is flushed there is nothing in the metadata, so the estimate is zero. Not approximate — **wrong**, with nothing in the API signalling the condition. **Campaign 7bis closes the condition this row left open:** after `nodetool flush` the estimate is **171 267**, and after major compaction **172 132**, against a true 200 000 — the metadata explanation accounts for the zero but not for a residual ~14 % error that survives both flush and compaction, so the defect is steady-state and not a start-up window. MongoDB's `estimated_document_count()` returned 200 000 exactly in p50 0.408 ms on the same corpus | Structural defect on this build | [findings_agg_hcd.json](data/raw/findings_agg_hcd.json), [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json) | An application testing `if count == 0` on a freshly loaded collection concludes it is empty. MongoDB's correct answer here proves it was correct *here*, not that it is always correct. **Methodological corollary against the author:** that zero is direct proof the HCD corpus was still memtable-resident, so campaign 7 is a **cache regime**, not a proven disk regime — the same reserve that attaches to the per-KiB rates of campaigns 1, 3 and 5. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row |
| **M23** | `GROUP BY cat` with `SUM(amt)`, 10 groups, every arm exact: MongoDB server-side `$group` p50 **222.711 ms**; native CQL per-partition sweep of ten queries p50 **2 011.399 ms**; native CQL cross-partition `GROUP BY cat` p50 **2 568.372 ms**; HCD Data API client scan-and-aggregate p50 **133 984.229 ms**, pulling all 200 000 documents to the client at ~20 docs/page (≈10 000 HTTP round trips). Ratios: MongoDB / HCD-Data-API = **602×**, MongoDB / CQL-best = **9.0×**, CQL-best / HCD-Data-API = **66.6×**. Load times for the same 200 000 rows: MongoDB 4.0 s, CQL 68.9 s, HCD Data API 185.3 s | MongoDB — and the reading must not be flattened | [findings_agg_hcd.json](data/raw/findings_agg_hcd.json), [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json), [findings_agg_cqlref.json](data/raw/findings_agg_cqlref.json) | **The storage engine can aggregate**: native CQL does it in ~2 s, so the 134 s belongs to the Data API tier, which exposes no aggregation surface and therefore forces the whole collection through the client. This is an API gap, not a hard engine limit. **And** the CQL arm carries its own disqualifying label in its result file — *"APPLES-TO-ORANGES REFERENCE — native CQL, NOT the HCD document model / Data API. Requires abandoning the document model and pre-designing a table partitioned by the group key."* The table `agg_cql(cat, id, amt)` with `PK(cat, id)` was designed for this query. Both halves must survive together. HCD arm **n = 3**: its p95/p99 carry no information. The 134 s was decomposed only after the fact, by D7 and from this dossier's own figures rather than by the campaign: 200 000 documents at the vendor's documented page size of 20 is 10 000 round trips, and 133 984.229 ms over 10 000 pages is **13.398 ms per page** — against 10.382 ms for a single-document point read (M16), the +29 % being twenty documents' payload rather than one. No residue remains to attribute. The campaign itself measured no such decomposition. The ~20 docs/page is the Data API's **default** page size and the probe never varied it — `probe_aggregation.py` calls `find()` with no page-size option — so part of the 134 s is a client-pagination default rather than a fixed property of the tier. Load times are single readings, not instrumented write-path measurements — **and campaign 7bis replaced them**: re-measured at a batch size of 100 on both arms, MongoDB takes 29.85 s against HCD's 206.96 s, so the 46.3× implied by this row's 4.0 s / 185.3 s is **withdrawn** and reads **6.9×**. The 602× likewise holds only for this row's ten-group shape: at 100 000 groups the same comparison gives **151×** (MongoDB 878.206 ms against HCD 132.9 s), and 609× with a filter, all three with disjoint supports and bootstrap intervals [577, 592], [148, 153], [599, 617]. The n = 3 reserve is also discharged: at n = 15 the HCD median is 132 985.311 ms, −0.7 % from this row's figure. **Adversarial pass, added 18 September 2026:** campaign 7 sits outside the audit (M1–M17) and the challenge rounds (M1–M13), but now carries its own — [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md), nine challenges D6–D14, **no conclusion reversed at that point**. Two measurements came out stronger (D7 decomposes the 134 s to 13.398 ms × 10 000 pages with no residue; D8 shows the 1 000 cap is documented vendor behaviour), one was narrowed to a cold-start property (D9), one resolved against the challenger (D10). **Campaign 7bis then reversed three of these — see [`docs/campagne7bis.fr.md`](docs/campagne7bis.fr.md):** D9's narrowing is **withdrawn** (the estimator returns 171 267 after flush and 172 132 after major compaction against a true 200 000, so the defect is steady-state, not cold-start); the **46.3× ingest ratio is withdrawn** (6.9× once the batch size is matched to the Data API's 100-document ceiling on both arms); and the **602× is bounded to its query shape** (584× at 10 groups, 151× at 100 000 groups, 609× filtered — MongoDB's cost scales with group cardinality and HCD's does not). Being challenged does **not** lift the reserves in this row |

---

## 4. Where the dossier proved its own author wrong

This section is the reason the repository is worth publishing. Every campaign was built so that it could
fail its own hypothesis, and the entries below are the places where it did. They are reproduced in full
rather than summarised, because a summary would be a softening.

### Campaign 1 — verification

1. **Step 4 of the five-operation model is contradicted.** The article's Part I §4 numbered list and its
   Figure 1 promise that HCD will "maintain the indexes covering the fields that changed". On this
   build the `UPDATE` rewrites **every** derived column, and a constant one-field `$set` grew **×7.50**
   (p50 12.104 → 90.783 ms) against *unchanged* indexed content, with a read control of ×1.56 and a
   constant `updateOne` HTTP payload ([findings.json](data/raw/findings.json)). Quoted with its regime
   caveat in the same breath: ×7.50 is memtable-resident at RF = 1; ×5.94 on disk at RF 3 (M10);
   ×1.52 once the cycle's `SELECT` is forced onto SSTables (M15).
2. **The article points readers at the wrong measurement.** Its §3 sentence promising that "the
   measurement in section 6 answers empirically … for your build in a quarter of an hour" is
   contradicted **as a cross-reference**: §6.3 measures write-to-searchable freshness, not the
   read-modify-write cycle. What settled the cycle was a query trace, not a latency curve, and the
   article's own harness cannot deliver what that sentence promises.
3. **Claim A3 is downgraded as a latency result.** By the author's own pre-registered read-control rule
   the cost-versus-size probe is INCONCLUSIVE: update growth ×1.92 / ×2.21 is not separable from
   same-size read growth ×1.86 / ×1.94. The claim survives only on the trace, so a reader who refuses
   trace evidence must hold A3 INCONCLUSIVE — the report states this explicitly rather than burying it.
4. **The [D] "ten indexes per collection" figure is narrowed.** Ten is the budget the API checks at
   creation time; only **nine** indexes were actually created on a collection declaring no vector option.
5. **Figure 1's storage box is incomplete as drawn.** It omits three columns that exist on the build:
   `key` (the partition key), `tx_id` (the LWT guard) and `query_lexical_value`.
6. **Figure 1's "consistency levels: not established by any source consulted here" is superseded** —
   they were measured (70/70 `LOCAL_QUORUM`, 30/30 `LOCAL_SERIAL`). The narrowing runs in both
   directions: the author had removed a `LOCAL_SERIAL` assertion from earlier drafts rather than defend
   it from memory, and the measurement restores it — but only as a *name* satisfied by one replica at
   RF = 1.
7. **The Disclosure sentence "no benchmark figures appear anywhere above" becomes false** the moment any
   appendix figure is lifted into the body. The campaign forces a choice: keep every number confined to
   the appendix with its conditions, or reword the sentence. The adversarial audit later reads this as
   the Disclosure being vindicated a posteriori — these numbers were never publishable outside an appendix.
8. **The [D] quotation "searchable as soon as it is written" is NOT supported by this campaign** and
   must not be cited as if it were. The freshness probe is INCONCLUSIVE against the harness's own 50 ms
   rule (p99 under load 59.178 ms and 53.849 ms), and what it exercised was SAI equality on a scalar
   field, not the JVector graph the quotation concerns. The idle result is dominated by two HTTP round
   trips and cannot resolve index lag below ~40 ms; the attempt count under load was not recorded at all.
9. **The campaign fails the standard the article imposes on other people's benchmarks.** Requirement 6
   of §10 (cross the background maintenance cycles) is explicitly **not met** — zero SSTables flushed,
   no compaction crossed — and requirement 1 (fixed offered rate rather than a closed loop) is met only
   by the freshness probe. Every latency figure in campaign 1 is therefore a memtable/in-cache figure
   by the article's own criteria.
10. **A record-keeping defect declared against the campaign itself.** The full distribution JSON of the
    run-1 read control was overwritten by run 2 (`control_read.py` writes a fixed filename), so run 1's
    read p50 values and wire sizes are transcribed from the run log and marked as transcribed. The
    ×1.86 read-growth figure that makes probe 3 INCONCLUSIVE rests on that transcription, not on a
    surviving distribution file.

### Campaign 2 — replication factor 3

11. **The latency probe still does not answer the question the article points at.** At RF = 3 as at
    RF = 1, the A3 probe is INCONCLUSIVE in both passes — update growth ×1.72 / ×1.91 against a read
    control of ×1.86 / ×1.85, the same slope. The campaign repeats campaign 1's reversal instead of
    rescuing the article's suggested method.
12. **The RF = 1 figures understate the conditional-write path.** The article's appendix said the
    multi-replica cost was not established; it is worse than the RF = 1 record implied — coordinator-side
    p50 **13.738 ms** for the conditional `UPDATE` against **6.582 ms** for a non-conditional `SELECT`,
    about 2×, "in a direction none of these options improves".
13. **Freshness degrades under replication rather than improving.** The verdict stays INCONCLUSIVE and
    the numbers move the wrong way: idle p50 45.431 / 28.372 ms against 25.5 / 18.7 ms at RF = 1; loaded
    p50 47.872 / 45.903 against 42.5 / 42.3; and the second pass's loaded p99 reaches 127.346 ms with a
    maximum of 238.219 ms against roughly 54 ms at RF = 1. The acknowledgement-to-searchable window
    widens with a replication factor the article never qualifies.
14. **The campaign refuses to extend its own headline coefficient.** Variant B — the measurement that
    carries the step-4 correction — is recorded `NOT_ATTEMPTED`, blocked twice by the session's safety
    classifier on the shared ring. ×7.50 remains an RF = 1, memtable-resident figure.
15. **The campaign refuses to credit its own headline to replication.** The roughly doubled end-to-end
    latencies mix the replication effect with an uneliminated hardware confounder (p16 nodes at
    8 GiB / 4 GiB heap against `rh-hcd`'s 3 GiB / 2 GiB), so "RF = 3 doubles the latency" is not a claim
    this run licenses. Only the Paxos trace is structural and independent of sizing.
16. **The A5 verdict did not reproduce on the unmodified instrument.** The supplied harness returned
    INCONCLUSIVE with `consistency_levels_observed = {}` over 200 traces examined, in both passes, and
    `findings_rf3.json` records A5 = INCONCLUSIVE in both verdict blocks. SUPPORTED rests on a
    supplementary analysis written by the measurer — the dependency the audit flags as I2. The report's
    opening claim that "the four RF = 1 verdicts hold identically" holds only once the measurer's own
    instrument is admitted as evidence.
17. **The Paxos number cannot support a production-scale cost argument, and says so.** Because the three
    dc1 replicas share one host with sub-millisecond inter-replica latency, the consensus cost is
    measured where it hurts least. Any wide-area quotation of 13.7 ms **understates** HCD's real exposure.

### Campaign 3 — disk regime and field-versus-byte

18. **The article's classification lever is named wrong.** Its §3.1 resolution paragraph and ADR-001's
    design-review test attribute crept-up write latency to the **count** of added indexed fields. M11
    shows the count is a weak secondary factor (×1.13–1.19 for a 14× rise at constant volume) while the
    **byte volume** is the driver (×4.6 for a ~16× rise at constant field count, r² 0.9999). The
    direction of the article survives; its stated mechanism-lever does not.
19. **The campaign refuses itself the clean verdict it was designed to win.** The pre-registered rule
    returns "BYTES DOMINATE" on one pass (1.128) and "INCONCLUSIVE" on the other (1.187) — straddling
    the 1.15 threshold. Both are published and the strict verdict is declared inconclusive, rather than
    quoting the favourable pass.
20. **The ×7.50 → ×5.94 difference is explicitly not credited to the disk regime.** The campaign existed
    to test whether disk changes the coefficient, then declared the answer unattributable: the
    comparison mixes regime with a topology and hardware confound.
21. **The campaign's own title is narrowed by its own limitations section.** "Disk-bound" means only
    that the *dataset* exceeds the memtable budget and lives in SSTables — not that any read missed RAM.
    The page cache could not be dropped (no root), the 6.05 GiB set fits in 220 GiB, and the RMW probe
    re-reads its own memtable-resident row. The campaign concedes in-report that it did **not** measure
    a disk-bound read, which is exactly what the coefficient claim needed.
22. **Variant A is INCONCLUSIVE again.** The arm that would carry A3 by latency alone grew ×1.78 against
    a read control of ×1.89. The disk regime did not rescue the latency probe; the cycle remains
    established by trace.
23. **The campaign's own proposed edit to the article was later reversed inside the dossier.** Its
    synthesis table proposed removing the "memtable-only" qualifier on the strength of M10; M15 then
    showed M10 never measured a disk-bound read at all. ADR-001 action 1 was reopened from `[x]` to
    `[~]`, the rate was relabelled memtable/cache, and **the qualifier has to stay**.
24. **The campaign downgrades its own instrument-independence guarantee.** The ballast had to be changed
    from constant bytes (LZ4-compressed ~120:1, 6 GiB logical → 50 MiB on disk, `disk_bound = false`) to
    incompressible random base64, and `nodetool` plus SSTable evidence had to be read through
    `docker exec`. Each patch is mechanically justified, but the audit counts them: M11 is rated among
    the strongest derived measurements **only because** `probe_field_vs_byte.py` ran unmodified.
25. **A cost was left on the shared ring and disclosed rather than hidden.** The ~24 600 fill inserts are
    LWTs, so `system.paxos` grew by ~6 GiB per dc1 node (~18 GiB on dc1) and could not be reclaimed
    (`paxos_state_purging = legacy`). Host disk went 507 GB → 525 GB used. The audit later cites this
    residue as an uncontrolled, never-quantified slowdown of HCD in campaigns 4–6, making those HCD
    absolutes a noisy ceiling rather than a clean measurement.
26. **The report refuses to act on a brief it cannot verify:** only one of the two HTML halves of the
    diptych was supplied, and the author declines to reconstitute the second or apply a correction to a
    document he does not have.

### Campaign 4 — tier versus storage

27. **The article's attribution is narrowed.** Its prose attributes the mutation cost to index
    maintenance, i.e. to the storage engine. The verdict table marks that "majoritairement juste
    (~71 % stockage) mais incomplet": roughly a quarter to a third of the per-byte rate is charged in
    the stateless Data API tier, a component the article's prose never separates from storage.
28. **The article's architectural criticism is partially softened by the author's own experiment.** A
    real fraction of the cost (29 % by method 1, 19 % by method 2) sits in a component that scales out
    behind a load balancer, so part of what the article presents as a structural, non-scalable write
    cost is elastic. The centre of gravity does not move, but the criticism is weaker than stated.
29. **The campaign denies the article any single precise split.** Because the two methods diverge 34 % at
    64 KiB and 27.7 % at 125 KiB, with tier slopes differing ~50 %, no single split is published.
    Quoting "29 %", or a clean "seventy–thirty", as *the* split quotes beyond what the measurement
    supports.
30. **The correction inserted into the article is itself an overclaim.** The added note names the tier's
    work as "the JSON parse, the shred and the response serialisation"; the campaign never separates
    those three — arm B skips all of them at once. The article's own new sentence is more specific than
    the measurement standing behind it.
31. **A pre-authorised correction was refused on the evidence.** The brief's trigger for replacing an
    article claim was "if the tier term dominates"; the measurement returned `tier_dominates = false`,
    and the report states that it will not invent a correction the measurement does not call for. The
    campaign was set up to contradict the article, could have, and declined.
32. **The 29 % was later measured at ~9 %, and the narrative changed value with need.** The dossier used
    29 % to estimate an engine-vs-engine ratio of ~31×, then 9 % to correct it to 40×. Each use was
    declared; the audit records the pair as a 3× disagreement on the same quantity, never reconciled (I3).

### Campaign 5 — HCD versus MongoDB on mutation

33. **The article's blanket limitation that nothing was measured on the MongoDB side falls for the
    mutation axis.** Three passages had to be rewritten: the appendix tail "Anything about … MongoDB" is
    replaced by a narrower exclusion, the Limitations paragraph concedes that the eleven-to-zero
    measurement asymmetry no longer holds for this axis, and the Disclosure's "none of them licenses a
    comparison with anything" is replaced by naming M13 as a deliberate exception. The correction is
    also **incomplete by the report's own admission** — it was applied to one HTML half only, so if the
    other carries the same limitation it stands uncorrected.
34. **The headline 44× is a stack ratio, not an engine ratio, and the report says so against its own
    first sentence.** HCD carries a Data API tier MongoDB has no equivalent of in this rig.
35. **The author's own red-team challenge C1 was measured and found wrong — in MongoDB's favour.** C1
    extrapolated an honest engine ratio of ~31×; M14 shows the tier is only ~9 % of the slope in the
    matched cache regime, so the engine ratio is 40× (wildcard) and 72× (default). The author's attempt
    to deflate his own number was **too generous to HCD**.
36. **"Matched durability" overstates what was done, and the mismatch favoured HCD.** MongoDB at
    `j:true` waits for the journal fsync before acknowledging; HCD under `commitlog_sync periodic 10 s`
    acknowledges before the fsync, with up to 10 s of acknowledged writes loseable. HCD was given a
    latency advantage inside the mapping and still lost 44×. The objection strengthens the MongoDB
    conclusion while downgrading the claim that the sides were equalised.
37. **The §3 numeric coefficient is requalified as a memtable/cache figure, not an engine property**
    (M15). The §3 mechanism holds; the rate does not transfer. ADR action item 1 reopened; every per-KiB
    rate — M3, M10, M11, M12, M13 — relabelled memtable.
38. **The campaign declines to support the axes the article claims for HCD.** Its own "what this
    campaign does not establish" states that it says nothing about read, search, aggregation or index
    freshness — the axis where HCD has its structural advantage. A dossier that measures only the axis
    where HCD is designed to lose is as skewed as a flattering one; the report declares the gap and does
    not close it.
39. **The article's own Part II §4 standard is not met by this comparison.** The adversarial audit scores the
    dossier at about **2.5 of §10's six requirements**; this campaign fails the first outright — every
    mutation probe is a closed-loop sequential single client, not a fixed offered load — and exercises
    only the cache regime where requirement 4 asks for cache *and* disk.

### Campaign 6 — freshness, read and search

40. **§4's first purchase is vindicated in mechanism and stripped of its speed claim.** HCD's automatic
    SAI answers an undeclared-field filter at p50 17.376 ms where default MongoDB scans 1 M documents in
    376.698 ms (21.7×) — but the same MongoDB given a wildcard index answers in 0.732 ms, **23.7× faster
    than HCD**. What decomposition purchases is the dispensation from index design; on absolute latency
    HCD loses the axis it is supposed to win.
41. **§4.1's correctness argument is moot for the use case it invokes.** The article grounds the whole
    freshness axis in retrieval-augmented applications: "an assistant that records a fact and cannot
    retrieve it on the following turn is producing wrong answers". M19 shows MongoDB `$search`'s miss
    rate is **0/30 once the write-to-search gap reaches 1000 ms**, and a conversational RAG turn exceeds
    that. The claim is right on mechanism and right for sub-second automated write-then-search (agentic
    loops, tight ingestion pipelines, where MongoDB misses 50–100 %), and **overstated where it invokes
    conversational RAG**. This is the campaign's sharpest reversal of its own author.
42. **The [U] the article deliberately refused to close is now closed for this deployment.** Figure 2 was
    drawn without a time axis because "supplying one would imply a magnitude nobody has published".
    M18 supplies one: a Lucene-style refresh interval with p50 664.3 ms, floor 89.1 ms, max 1170.2 ms.
    The refusal was sound as of writing; the [U] is now closed for mongot on `atlas-local` while
    remaining genuinely [U] for Atlas in production, which is what "MongoDB 8.x" actually denotes.
43. **The campaign cannot prove zero on HCD's side.** "Searchable at acknowledgement — no window" is not
    established: attempts = 1 means the document was found by the first query, but that query arrives
    ~45 ms after the write. Any HCD index lag between 0 and 45 ms is undetectable. The honest statement
    is "HCD lag < 45 ms, below the measurement floor".
44. **HCD's freshness advantage is narrower than §4 reads.** On an ordinary secondary index the campaign
    measured a **tie** — attempts `{1: 40}` on all three arms. MongoDB's b-tree indexes are synchronous
    too. The advantage is scoped to the `$search` / `$vectorSearch` path, not to read-your-writes in
    general.
45. **The article never prices the Data API tier on the read path, and it should.** A point read by `_id`
    costs HCD p50 10.382 ms against MongoDB's 0.530–0.616 ms — roughly a 10 ms tier hop charged to every
    single **read**, not only to every write. Measured stack-versus-stack; a CQL-direct read arm, which
    would shrink the gap, was not run.
46. **The article's own recommended probe has a method flaw that inflates the thing it measures.** Run
    back-to-back as §6.3 writes it, a probe of that shape self-synchronises with a periodic refresh
    interval and reports its worst phase. That is exactly what happened to this campaign's first
    measurement: p50 1015.2 ms tight, against p50 664.3 ms once the insert was de-synchronised with a
    random 0–1200 ms offset. The recommended probe needs a randomised pre-insert delay.
47. **Internal to the dossier:** the campaign-6 report's own closing table still reads "synchronous vs
    ~1 s of async lag", a figure the same author's M18 corrected. The prepended abstract carries the
    correction; the French body retains the uncorrected line as it was written.

### Campaign 7 — aggregation

48. **The 602× refutes itself in the same sentence, and both halves are required.** MongoDB aggregates
    200 000 documents into 10 groups in p50 222.711 ms; HCD's Data API takes p50 133 984.229 ms for the
    same exact result. That is **not** a statement that HCD's storage engine is 602× slower: the same
    engine, same machine, same corpus does the same aggregation in p50 2 011.399 ms in native CQL (9.0×
    MongoDB) and p50 2 568.372 ms by cross-partition `GROUP BY` (a recognised anti-pattern, still under
    three seconds). The 66.6× between HCD's own two paths is the cost of a tier that does not expose the
    function. **And** the CQL arm carries its own disqualifying label: reaching it means abandoning the
    document model and pre-designing a table partitioned by the group key — exactly the index-design
    work §4's "queryability without index design" argument, *favourably verified in campaign 6*, promises
    to avoid. The engine can aggregate, and reaching it costs the document model.
49. **The campaign proves against itself that it ran in a cache regime.** M22's zero is direct evidence
    the HCD memtable had not been flushed. No flush was forced, no compaction crossed — the same reserve
    that attaches to campaigns 1, 3 and 5.
50. **The axis unfavourable to MongoDB is stated at full strength.** MongoDB's exact count is a scan
    (p50 115.009 ms unfiltered, 157.177 ms filtered) and reaches 12.659 ms only after an index is
    declared. MongoDB wins the counting axis because it **answers**, not because it is cheap, and it too
    pays index design there.
51. **The campaign fills a gap the dossier had been declaring since campaign 5** — "nothing about
    aggregation" — and the filled cell turns out to be the most unfavourable axis to HCD in the whole
    dossier. It was measured anyway.
52. **The campaign refuses three extrapolations it could have made.** The 134 s was never decomposed
    into round-trip, deserialisation and engine terms, so the 66.6× locates the cost in the tier without
    apportioning it. The HCD arm is **n = 3**, so its p95/p99 are declared unquotable. And nothing was
    measured about what HCD might serve otherwise — `findAndRerank`, vector indexes, or an external
    analytic stack on the same ring: the finding is about the Data API as exposed, not about every way
    of querying HCD.

---

## 5. Measurements that did not survive contact with a later campaign

### 5.1 The ×7.50 growth factor is a memtable artefact

The dossier's most-quoted number was the ×7.50 growth of a constant single-field `$set` across a ×128
document size, measured in campaign 1 ([findings.json](data/raw/findings.json)). It was the evidence for
correcting step 4 of the article's five-operation model, and it is real — but it characterises a regime,
not an engine.

| Regime | Growth 1 KB → 128 KB | Absolute p50 at 1 KB → 128 KB | Source |
|---|---|---|---|
| Memtable-resident, RF = 1 (M3) | **×7.50** | 12.104 → 90.783 ms | [findings.json](data/raw/findings.json) |
| Dataset on disk, RF = 3, probed row still memtable-resident (M10) | **×5.94** | 20.389 → 121.189 ms | [findings_disk_rf3.json](data/raw/findings_disk_rf3.json) |
| RMW `SELECT` forced onto the SSTable read path (M15) | **×1.52** | 107.765 → 163.402 ms | [rmw_postflush.json](data/raw/rmw_postflush.json) |

Once the read half of the cycle actually leaves memory, the per-byte growth flattens to ×1.52 and a
fixed read-path cost of roughly 90–100 ms dominates instead. The consequences were recorded rather than
absorbed: ADR-001's action item 1 was reopened from `[x]` to `[~]` (audit finding I5), and every per-KiB
rate in the dossier — M3, M10, M11, M12, M13 — was relabelled a memtable/cache figure (audit finding I4).
The mechanism of §3 (read, rewrite, maintain indexes) survives intact; the coefficient does not transfer
to a disk-bound read. M15 carries its own reserve in the other direction: flushing before every update
fragments the table into ~35 small SSTables, so its ~100 ms absolute is inflated and the true
disk-bound value sits somewhere between the memtable and post-flush figures. **No genuinely disk-bound
RMW read exists anywhere in this dossier** (challenge C2, confirmed).

### 5.2 The Data API tier's share: 29 % or 9 %, never reconciled

| Measurement | Regime | Arm scheduling | Tier share of the per-KiB rate |
|---|---|---|---|
| M12, method 1 (bypass) | Disk regime | Interleaved | **29 %** (storage 0.547, tier 0.219 ms/KiB) |
| M12, method 2 (coordinator-trace subtraction) | Disk regime | Interleaved | **19 %** (tier 0.145 ms/KiB) |
| M14 (HCD-CQL-direct arm) | Matched cache regime | Separated in time | **~9 %** (0.7775 → 0.7037 ms/KiB) |

Three estimates spanning 9–29 % on the same quantity, a 3× disagreement, produced in different regimes
with different arm scheduling. **They have never been reconciled** (audit finding I3). Within M12 alone
the two methods already agree within 25 % at 8, 16 and 32 KiB but diverge 34 % at 64 KiB and 27.7 % at
125 KiB, with tier slopes differing ~50 %, because method 1 subtracts a full client-side CQL execution
while method 2 subtracts only the coordinator's internal duration. M12's arm B also reuses already-shredded
values, so it never exercises the shredding code and its "storage" term is an optimistic floor
(challenge C7). The dossier's narrative used 29 % to deflate the engine ratio to ~31×, then 9 % to
correct it to 40×; each use was declared, but the value changed with need. **The ADR now records the
share as an unpinned range, and no single split may be quoted.** What survives all three estimates is the
direction: the tier is a minority however it is measured, so 71–91 % of HCD's mutation cost sits in the
stateful storage engine, which does not scale out by adding instances.

### 5.3 The mongot lag is a `localDev` build, not MongoDB Atlas Search

M17's 1015.201 ms was first corrected by M18 to a refresh interval with p50 664.3 ms and a floor of
89.1 ms — the author refuting his own pro-HCD magnitude. A later provenance check
([findings_mongot_provenance.json](data/raw/findings_mongot_provenance.json)) then **raised** the reserve
on all three search-freshness measurements rather than lowering it: the mongot measured is version
**1.75.1, `localDev` edition**, the build MongoDB ships for local development, not the search tier that
serves Atlas, and the commit interval is internal to the jar and was never read. M17, M18 and M19 may not
be quoted as "MongoDB Atlas Search lag", as "MongoDB's search freshness", or as a property of MongoDB the
product. The architectural direction survives — mongot indexes asynchronously off the change stream by
construction — and so does the reserve on HCD's own half: "synchronous" was only ever bounded below the
~45 ms HTTP floor, never shown to be zero.

### 5.4 Smaller reversals, listed for completeness

- **A3 by latency** was INCONCLUSIVE in every regime it was tried — RF 1 memtable (×1.92 / ×2.21 vs
  ×1.86 / ×1.94), RF 3 memtable (×1.72 / ×1.91 vs ×1.86 / ×1.85), RF 3 disk (×1.78 vs ×1.89). It is
  carried by the CQL trace alone, in all three.
- **A5 at RF = 3** was INCONCLUSIVE on the unmodified harness in both passes
  ([findings_rf3_rate50.json](data/raw/findings_rf3_rate50.json),
  [findings_rf3_rate50_rep2.json](data/raw/findings_rf3_rate50_rep2.json)); the SUPPORTED verdict rests
  on the measurer's own supplementary analysis.
- **M11's pre-registered verdict rule** returned two different answers on two passes (1.128 and 1.187,
  straddling the 1.15 threshold). The strict verdict is inconclusive; only the direction stands.
- **The author's challenge C1 estimate of ~31×** was measured wrong by his own follow-up and corrected
  to 40× — in MongoDB's favour.

---

## 6. Axes never measured

Nothing below was measured. Each is listed because a reader who assumes otherwise would misread every
number above.

| Axis | Status | Why it matters |
|---|---|---|
| **Concurrency** | Never measured. Every probe in every campaign is a **single sequential closed-loop client**. | This violates requirement 1 of the article's own Part II §4 standard for a defensible benchmark. Contention, queueing and lock behaviour are entirely unknown on both engines; the audit scores the dossier at about 2.5 of §10's six requirements. |
| **Fixed offered-rate load** | Never measured except by campaign 1's freshness probe (50 writes/s) and campaign 2's rate-50 passes. All mutation, read, search and aggregation probes are closed-loop. | A closed loop measures service time under self-imposed pacing, not behaviour under load. Every latency figure here is a best case in that sense. |
| **Multi-host and WAN topology** | Never measured. All six HCD nodes and all MongoDB members share one host; inter-replica latency is sub-millisecond. | The Paxos round of M5 is therefore measured **where it hurts least** (C3): the structure is established, the magnitude is not representative, and a wide-area quotation of 13.738 ms understates HCD's exposure. It is also the only topology where M7's `LOCAL_ONE` vector-freshness window could surface. |
| **A genuinely disk-bound read** | Never achieved anywhere in the dossier. Campaign 3 proved a disk-bound **dataset**, not a disk-bound probed read; M15's post-flush pass fragments the table and inflates its absolute. The OS page cache could never be dropped — no root on the host. | This is challenge C2, confirmed. Every per-KiB rate in the dossier is a memtable/cache coefficient. |
| **Vector ANN search quality** | Never measured. M7 and M17 measure **freshness** — whether a just-written vector is retrievable — not recall, precision, or ranking quality at scale. | Nothing here says anything about how good JVector's results are, only about when they appear. M7's validity check confirms only that the marker is discriminated (cosine 1.0 rank-1 against a background ≤ 0.83). |
| **Lexical/BM25 freshness on HCD, and `$vectorSearch` freshness on mongot** | Never measured (C14, D4). The search-freshness comparison is MongoDB **lexical** `$search` against HCD **vector** JVector. | The two halves do not exercise the same path. The comparison is directional, not like-for-like. |
| **A production-sized or CPU-capped Data API tier** | Never measured. The Data API container ran with 2 GiB memory, **no CPU cap**, unpinned, co-located with the storage nodes. | The tier-share *slope* answers the location question; the absolute latency does not transfer to a tier sized for production. The capability gap of M20 does transfer intact. |
| **A production-edition mongot / MongoDB Atlas** | Never measured — `mongot 1.75.1 localDev` on single-node `atlas-local` only. | See §5.3. The article's subject is "MongoDB 8.x"; Atlas production search may be faster or slower and is untested. |
| **Sharded MongoDB** | Never measured. MongoDB ran as a 3-member replica set (campaigns 5–7) or single-node `atlas-local` (search freshness). | No statement here covers MongoDB's behaviour at scale-out. |
| **HCD's other query surfaces** | Never measured: `findAndRerank`, vector indexes as an aggregation substitute, or an external analytic stack (Presto, Spark) on the same ring. | M20's finding is about the Data API **as exposed**, not about every way of querying HCD. |
| **Decomposition of the 134 s aggregation** | Never measured. The ~10 000 HTTP round trips, client deserialisation, and engine time were never separated. | The 66.6× locates the cost in the tier; it does not apportion it. |
| **Write throughput** | Never measured as such. The load times quoted (MongoDB 4.0 s, CQL 68.9 s, Data API 185.3 s for 200 000 rows; 1 057.2 s for HCD's 1 M-document load) are **single readings with no percentiles**, different durability paths, sequential clients. | They are reported because they appear in the result files and run in the same direction as M13 — not because they are measurements of the write path. |
| **Reads, search and aggregation at RF = 3 versus RF = 1** | Only mutation and freshness were re-run under replication. | The replication cost of the read and search paths is unknown. |
| **Background maintenance in the mutation probes** | Requirement 6 of §10, explicitly not met in campaign 1: zero SSTables flushed, no compaction crossed. Campaign 3 crossed 78 compactions during the fill, not during the measured probes. | No probe in this dossier measures a mutation while compaction is running. |
| **Environmental isolation** | Never achieved. Shared host at load average 14–16 with third-party tenants; the HCD ring carried ~13 GiB/node of unpurged `system.paxos` from campaigns 3–4 through campaigns 4–7, never quantified. | Audit findings I1 and I6: HCD's absolute figures are a **noisy ceiling**, not a clean measurement. Every HCD number in campaigns 4–7 may be slower than a clean run would give. |
| **Reproducibility across days or hosts** | Never attempted. One host, one day per campaign, one build of each engine, two passes at most. | n = 30 per point, medians and percentiles only, **no confidence intervals**; the audit records that inter-pass variance is of the same order as some claimed effects (I7). |

---

## Reading rules for anyone quoting this dossier

1. **Never quote a per-KiB rate or a growth factor without its regime.** They are memtable/cache
   coefficients. ×7.50 becomes ×1.52 off the memtable.
2. **Never quote the 602× as "HCD is 602× slower", and never without its query shape.** The same
   engine aggregates in ~2 s in native CQL; the gap is an API surface, and reaching the CQL path costs
   the document model. Campaign 7bis measured the same comparison at three group cardinalities: 584×
   at ten groups, **151× at a hundred thousand**, 609× filtered. The 602× is the most favourable
   shape, not the engine's constant.
2b. **Never quote the 46.3× ingest ratio.** It is withdrawn: it compared the Data API's 100-document
   call ceiling against MongoDB's 10 000-document native batch. At a matched batch of 100 on both
   arms the ratio is **6.9×** (campaign 7bis). 50.9× is the figure for matched-corpus, unmatched
   batch, and must be labelled as such.
3. **Never quote the tier share as a single number.** It is 9–29 %, unreconciled.
4. **Never quote the mongot lag as MongoDB's or Atlas's.** It is mongot 1.75.1 `localDev`.
5. **Never quote HCD's search freshness as zero.** It is bounded below the ~45 ms HTTP floor.
6. **Never quote the 21.7× undeclared-field win as engine speed.** It is a win over a MongoDB that was
   never given the index; a declared index beats HCD by 23.7×.
7. **Report both MongoDB arms or neither.** Default alone overstates MongoDB; wildcard alone understates
   how it is deployed.
8. **Never quote 13.738 ms as the cost of Paxos.** Three replicas shared one host; on a real topology it
   is worse for HCD, not better.
