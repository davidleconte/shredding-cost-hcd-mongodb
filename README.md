# Shredding cost: what physical storage layout does to write cost, index freshness and concurrency in document databases

IBM DataStax HCD 2.0.6 (release `5.0.7.0-ea50e91ba01f`, Data API v1.0.33) measured against MongoDB 8.0.32
(replica set) and — for search freshness only — `mongodb-atlas-local` 8.3.11 with mongot 1.75.1 `localDev`.

---

**MongoDB won five of the ten measured axes, HCD two; three named no winner.** MongoDB's five:
single-field mutation (44× to 79× stack-to-stack, 40× to 72× engine-to-engine), point read by `_id`
(≈19.6×), filtered search on a field it was given an index for (23.7×), aggregation (602× against
HCD's Data API path — a tier gap, not an engine gap: the same engine, same host, same corpus
aggregates in ~2 s through native CQL
([`findings_agg_cqlref.json`](data/raw/findings_agg_cqlref.json)), at the price of abandoning the document
model and pre-designing a table partitioned by the group key) and exact counting, which HCD's Data API
refuses above 1 000 documents. HCD's two: filtered search on a field nobody declared an index on,
against a MongoDB that was never given one (21.7×), and search-index freshness, where its index sits on
the write path.

**Two of the dossier's own headline numbers did not survive later measurement by the same author.**
The ×7.50 mutation-growth coefficient is a memtable artefact that collapses to **×1.52** once the read
half of the read-modify-write cycle is forced onto SSTables
([`rmw_postflush.json`](data/raw/rmw_postflush.json)). The Data API tier's share of the per-byte cost was
measured at **29 %** in one campaign and **~9 %** in another, a 3× disagreement on the same quantity that
has **never been reconciled**.

Every figure here is cache- or memtable-resident, single-client, sequential, on one shared and
already-loaded host, one build of each engine, with no concurrency and no multi-host topology. The
dossier establishes **mechanism and direction**. It does not establish production magnitudes.

**The raw evidence is in [`data/raw/`](data/raw/)** — byte-identical to the runs, including the runs
that went against the author. **Before quoting anything: [LIMITATIONS.md](LIMITATIONS.md).**

---

## What this is

An adversarial self-verification of the author's own technical article. Seven measurement campaigns over
two days produced the numbered measurements M1–M23 against two document databases on one host, with the probe
source, the untouched raw JSON, an ADR evidence register, and an adversarial audit written *against* the
campaigns rather than for them.

The experiment was built so that it could prove its own author wrong, and in several places it did.
[RESULTS.md §4](RESULTS.md#4-where-the-dossier-proved-its-own-author-wrong) lists **52 numbered points at
which the measurements contradicted the article they were written to support** — including the
contradiction of the article's own step 4, the finding that the article names the wrong mechanism-lever
(field *count*, where bytes dominate), and the finding that the article's freshness argument is
*overstated for the conversational-RAG use case it invokes*, because MongoDB's miss rate reaches 0/30 once
the write-to-search gap reaches 1 000 ms.

Evidence markers are carried throughout: **[D]** documented by a vendor · **[R]** reported by a third
party · **[U]** unverified · **[M]** measured here. **No performance figure in this repository is [D].**

## At a glance

| | |
|---|---|
| **HCD** | IBM DataStax HCD 2.0.6, `nodetool version` = `5.0.7.0-ea50e91ba01f`, Data API `stargateio/data-api` v1.0.33; RF = 1 (campaign 1) and `{dc1:3}` thereafter |
| **MongoDB — mutation, read, search, aggregation** | MongoDB 8.0.32, three-member replica set `rs0`, `w:majority` + `j:true` |
| **MongoDB — search freshness only** | MongoDB 8.3.11, image `mongodb/mongodb-atlas-local`, single-node replica set, mongot **1.75.1 `localDev` edition**. A different deployment from the one above (audit finding I8) |
| **Host** | One QEMU virtual machine, `alphadebunker`: Intel Xeon Gold 6148 @ 2.40 GHz, 80 vCPU, 220 GiB RAM, Linux 6.8.0-136. Shared, carrying unrelated workloads at load average 14–16 throughout. No root, so the OS page cache was never dropped |
| **Dates** | 17–18 September 2026, `run_at_utc` stamped in every raw file |
| **Measurements** | Numbered **M1–M23** across 7 campaigns. The register holds M1–M8 and M10–M23: no M9 was ever assigned, and it is listed as missing rather than silently skipped. Of those, only M1–M8 and M10–M19 are entered in ADR-001's evidence register; **M20–M23 (campaign 7) were assigned in this repository, after the ADR's last revision, and were never entered in it** — their entries live in [RESULTS.md §3](RESULTS.md#3-measurements-m1m23) |
| **Statistics** | Percentiles only. This dossier publishes **no means for latency**. n = 30 per point, two passes at most, **no confidence intervals** |
| **Licence** | Apache-2.0 for `probes/`; CC BY 4.0 for `docs/`, `data/` and the root Markdown |

## The headline, abbreviated

Seven of the ten measured axes. The full table, with every arm and every raw-file reference, is
[RESULTS.md §2](RESULTS.md#2-the-headline-table); the measurement register is
[RESULTS.md §3](RESULTS.md#3-measurements-m1m23). **The last column is not a footnote: a margin quoted
without it is a misquote.**

| Axis | MongoDB | HCD | Winner | Margin | The caveat that must travel with the margin |
|---|---|---|---|---|---|
| **Single-field mutation cost** (per indexed KiB, 16 fields × 512→8000 B) — [M13, M14](RESULTS.md#3-measurements-m1m23) | 0.0098 ms/KiB default (r² 0.78); 0.0176 ms/KiB wildcard (r² 0.88); p50 5.5–7.6 ms, flat | 0.7775 ms/KiB through the Data API (r² 0.997), p50 40.9→130.8 ms; 0.7037 ms/KiB CQL-direct (r² 0.996), p50 18.4→101.6 ms | MongoDB, decisively | 44× wildcard / 79× default as stacks; 40× / 72× engine-to-engine with the tier removed | Cache-resident (memtable) rate only. The per-byte coefficient it rests on collapses from ×5.94 to **×1.52** once the RMW read is forced onto SSTables ([rmw_postflush.json](data/raw/rmw_postflush.json)) — the mechanism transfers, the rate does not. Durability was matched by a declared judgement that *favoured HCD* (`j:true` waits for the fsync, `commitlog_sync periodic 10 s` does not); HCD lost anyway. Closed-loop sequential single client. The HCD ring carried ~13 GiB/node of unpurged `system.paxos`, an unquantified drag, so HCD's absolutes are a noisy ceiling. [comparison.json](data/raw/comparison.json), [comparison_v2.json](data/raw/comparison_v2.json) |
| **Point read by `_id`** (1 M documents) — [M16](RESULTS.md#3-measurements-m1m23) | p50 0.530 ms wildcard; 0.616 ms default | p50 10.382 ms | MongoDB | ≈19.6× (wildcard arm) | Stack versus stack. HCD's ~10 ms is the Data API tier HTTP hop, charged on every **read** and not only on every write; a CQL-direct read arm, which would shrink the gap, was **not run** (challenge C15). Cache-resident, 50 reps, single client. [findings_rs_mongo.json](data/raw/findings_rs_mongo.json), [findings_rs_hcd.json](data/raw/findings_rs_hcd.json) |
| **Filtered search, undeclared field** (1 M documents) — [M16](RESULTS.md#3-measurements-m1m23) | p50 376.698 ms — collection scan, no index on the queried field | p50 17.376 ms — automatic SAI, nothing declared | HCD | 21.7× | This is a win over a MongoDB that was **never given the index** (challenge C12). What HCD buys on this axis is the **dispensation from index design**, an operational property — not engine speed. The same MongoDB with a wildcard index answers in 0.732 ms (next row). [findings_rs_hcd.json](data/raw/findings_rs_hcd.json), [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) |
| **Filtered search, declared (wildcard) index** (1 M documents) — [M16](RESULTS.md#3-measurements-m1m23) | p50 0.732 ms | p50 17.376 ms — the same HCD measurement as the row above; HCD has one path | MongoDB | 23.7× | Same run, same corpus. HCD's figure includes the Data API tier hop and was not re-measured CQL-direct (C15). A wildcard index is MongoDB doing HCD's job; it is not free at write time, which is the axis of row 1. [findings_rs_mongo.json](data/raw/findings_rs_mongo.json) |
| **Search-index freshness** (write → searchable) — [M17, M18, M19](RESULTS.md#3-measurements-m1m23) | `$search` via mongot: self-synchronised probe p50 1015.201 ms, poll attempts median 34; de-synchronised p50 **664.3 ms**, floor **89.1 ms**, max 1170.2 ms — a refresh interval, not a fixed delay | JVector search: p50 44.972 ms, poll attempts min = median = max = 1, 0 cycles never visible | HCD, in direction | Miss rate of one search issued τ ms after the write: **HCD 0/30 at every τ; MongoDB 30/30 (100 %) at τ = 0, 15/30 at 500 ms, 0/30 at τ ≥ 1000 ms** | Three reserves, all cutting against the headline. (a) The mongot measured is **1.75.1 `localDev` edition** on a single-node `atlas-local` container — it may **not** be quoted as "MongoDB Atlas Search lag" or as a property of MongoDB the product; the commit interval is internal to the jar and was never read ([findings_mongot_provenance.json](data/raw/findings_mongot_provenance.json)). (b) HCD's "synchronous" is only **bounded below the ~45 ms HTTP round-trip floor**, never shown to be zero, and its max was 573.598 ms. (c) Not like-for-like: MongoDB `$search` is lexical, HCD JVector is vector (C14). The 1015.2 ms figure was the worst phase of the cycle and is corrected by M18. [findings_mongot_freshness.json](data/raw/findings_mongot_freshness.json), [findings_mongot_floor.json](data/raw/findings_mongot_floor.json), [findings_hcd_vec_freshness.json](data/raw/findings_hcd_vec_freshness.json), [findings_turn_hcd.json](data/raw/findings_turn_hcd.json), [findings_turn_mongodb.json](data/raw/findings_turn_mongodb.json) |
| **Aggregation** (`GROUP BY cat`, `SUM(amt)`, 200 000 docs, 10 groups, every arm exact against ground truth) — [M23](RESULTS.md#3-measurements-m1m23) | Server-side `$group` p50 222.711 ms | Data API client scan-and-aggregate p50 133 984.229 ms (n = 3), 200 000 docs pulled to the client at the Data API's default ~20 docs/page; native CQL per-partition sweep p50 2 011.399 ms; native CQL cross-partition `GROUP BY` p50 2 568.372 ms | MongoDB | **602× vs HCD's Data API; 9.0× vs HCD's best CQL path; 66.6× between HCD's own two paths** | This is a **capability gap, not a latency race**, and the 602× must never be quoted as "HCD is 602× slower". The same storage engine, same host, same corpus aggregates in ~2 s through native CQL — the 134 s belongs to a tier that exposes no aggregation surface and therefore forces the whole collection through the client. **And** the CQL arm is a labelled apples-to-oranges reference: reaching it means abandoning the document model and pre-designing a table partitioned by the group key — exactly the index-design work the Data API's pitch is to avoid. Both halves of that sentence are required. The HCD arm is n = 3; its p95/p99 carry no information. **No adversarial verdict:** campaign 7 sits outside the adversarial audit (M1–M17) and the challenge rounds (M1–M13); no figure in it has been challenged. [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json), [findings_agg_hcd.json](data/raw/findings_agg_hcd.json), [findings_agg_cqlref.json](data/raw/findings_agg_cqlref.json) |
| **Exact count** (200 000 documents) — [M21, M22](RESULTS.md#3-measurements-m1m23) | `count_documents({})` p50 115.009 ms → 200000 exact; filtered collscan p50 157.177 ms → 20000 exact; filtered with a declared `cat` index p50 12.659 ms; `estimated_document_count()` p50 0.408 ms → 200000 | `countDocuments({})` and `countDocuments({cat:"c3"})` both **impossible**: `TooManyDocumentsToCountException — Document count exceeds 1000, the maximum allowed by the server`, on a stock container with no count-limit env var. `estimatedDocumentCount()` p50 6.875 ms → returned **0** while the true count was 200 000 | MongoDB, by capability | Not a ratio — HCD has no answer at this cardinality | MongoDB wins this axis because it **answers**, not because it answers cheaply: its exact count is a scan (115 ms / 157 ms) and only reaches 12.659 ms after a declared index, so MongoDB too pays index design here. HCD's estimate is not approximate, it is **wrong** pre-flush, and nothing in the API signals the condition — an application testing `if count == 0` on a freshly loaded collection concludes it is empty. That zero is also direct proof this campaign ran in a **cache regime**, not a proven disk regime. **No adversarial verdict:** campaign 7 sits outside the adversarial audit (M1–M17) and the challenge rounds (M1–M13); no figure in it has been challenged. [findings_agg_mongodb.json](data/raw/findings_agg_mongodb.json), [findings_agg_hcd.json](data/raw/findings_agg_hcd.json) |

Three further axes are in the full table and are omitted here only because they name no winner: **where
the per-byte cost is charged** (the Data API tier is 9–29 % of it, unpinned and unreconciled, so 71–91 %
sits in the stateful engine), **secondary-index freshness on an ordinary index** (a tie — both engines
found the document on the first query, attempts `{1: 40}` on every arm), and **vector freshness at RF = 3
under `vector-search = LOCAL_ONE`** (120/120 cycles hit on the first `LOCAL_ONE` search; verdict **NOT
DETECTABLE**, because any window is bounded below the ~74 ms HTTP measurement floor on a co-located ring).

## The three findings worth your time if you read nothing else

**1. The Data API read-modify-write cycle: mutation cost scales with indexed content the mutation never
touches.** Every `updateOne` with a single `$set` was observed, in 10 of 10 CQL traces, to be a
`SELECT key, tx_id, doc_json … LIMIT 1` followed by one `UPDATE` carrying **11 assignments** — `tx_id =
now()`, nine derived columns, and the whole `doc_json` — guarded by `IF tx_id = ?` under Paxos
([`findings.json`](data/raw/findings.json), M2). The consequence is the finding: a constant one-field
mutation grew **×7.50** (p50 12.104 → 90.783 ms) across a ×128 document size, against a same-size read
control of ×1.56 and an `updateOne` HTTP payload constant at 122–124 B. The cost is charged against the
**indexed content the document carries**, not against what changed. This contradicts step 4 of the
article's own five-operation model (M3, [RESULTS.md §4](RESULTS.md#4-where-the-dossier-proved-its-own-author-wrong)).

**2. That cost is a regime artefact, and this is the dossier correcting itself.** ×7.50 is memtable-resident
at RF = 1. On disk at RF = 3 it is ×5.94 (M10). Once the cycle's `SELECT` is forced onto the SSTable read
path by flushing before every update, it flattens to **×1.52**, and a fixed read-path cost of roughly
90–100 ms takes over ([`rmw_postflush.json`](data/raw/rmw_postflush.json), M15). The mechanism transfers;
the coefficient does not. Every per-KiB rate in the dossier — M3, M10, M11, M12, M13 — was relabelled a
memtable/cache figure as a result, and the ADR's action item 1 was reopened from `[x]` to `[~]`. M15
carries its own reserve in the other direction: flushing before each update fragments the table into ~35
small SSTables, so its ~100 ms absolute is inflated and the true disk-bound value sits between the two.
**No genuinely disk-bound RMW read exists anywhere in this dossier.**

**3. The aggregation capability gap.** The HCD Data API command allow-list contains nineteen commands;
`aggregate`, `$group` and `distinct` all return `COMMAND_UNKNOWN` — there is **no server-side aggregation
pipeline** (M20). Exact counting is capped at 1 000 documents on a stock container
(`TooManyDocumentsToCountException`, M21), and `estimatedDocumentCount()` returned **0** on a collection
holding 200 000 documents, because it reads SSTable metadata and the memtable had not been flushed — not
approximate, wrong, with nothing in the API signalling the condition (M22). This is the one family of
findings that is independent of hardware, load, regime and percentile. Its reserve is different in kind:
an allow-list is a **product decision** and can change between builds, so what resists time is the
mechanism — no pipeline means the corpus crosses the client — not the list.

## How to read this repository

| Path | What it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | The master register: the full headline table, M1–M23 grouped by campaign, the 52 points of self-refutation, the measurements that did not survive a later campaign, the 16 axes never measured, and the eight quoting rules. |
| [`LIMITATIONS.md`](LIMITATIONS.md) | The adversarial half, in English: integrity findings I1–I9, challenges C1–C15 and meta-challenges D1–D5, what survives without a scratch, and what this repository cannot tell you. |
| [`METHODOLOGY.md`](METHODOLOGY.md) | Pre-registered verdict rules, evidence markers, instrument provenance, durability matching and which way it leans, the regime taxonomy, statistical policy, and self-compliance against the article's own six conditions (about 2.5 of 6 met). |
| [`REPRODUCING.md`](REPRODUCING.md) | How to stand up both engines and point each probe at them — written so a reader can contradict us. It states up front that you will not reproduce these numbers and are not supposed to. |
| [`DISCLAIMER.md`](DISCLAIMER.md) | Personal research, not an employer position; exactly what was measured; why this is not a benchmark, a product comparison or advice. |
| [`data/raw/`](data/raw/) | The untouched JSON the probes wrote, byte-identical to the runs, including the files a later measurement refuted. |
| [`data/README.md`](data/README.md) | The data dictionary: one entry per raw file, its host fingerprint, and how to quote a number out of the directory. |
| [`probes/`](probes/) | Every script that produced a number here. |
| [`probes/README.md`](probes/README.md) | The probe index **and provenance register**: for each probe, whether it was vendor-supplied and unmodified, vendor-supplied and patched (with each patch listed), or written by the measurer. This exists because audit finding I2 says the verdicts that matter most rest most on the measurer's own code, and it tabulates that rather than softening it. |
| [`docs/campaigns/`](docs/campaigns/) | The seven campaign reports, 01–07, in French, as written at the time — except [06](docs/campaigns/06-freshness-read-search.fr.md), which was amended on 18 September 2026, after the report was written, by three additive changes: a dated warning inside reserve (1), a warning in the verdict table, and an appended section, *Provenance de `mongot`*, which retracts that report's own claim that the ~1 s lag is representative. Nothing was deleted and nothing was reworded. |
| [`docs/adr/ADR-001-modelling-policy.md`](docs/adr/ADR-001-modelling-policy.md) | The modelling policy, and the evidence register for M1–M8 and M10–M19 — the identifiers that existed when it was last revised. **M20–M23 are not in it**: they were assigned in this repository for campaign 7 and are registered in [`RESULTS.md` §3](RESULTS.md#3-measurements-m1m23) only. The sole evidence for M6 and M8 lives here rather than in a raw file — the weakest traceability in the register. |
| [`docs/audit-adversarial.fr.md`](docs/audit-adversarial.fr.md) | The adversarial audit of the dossier's own integrity, in French. Promoted to English in `LIMITATIONS.md`. |
| [`docs/challenges.fr.md`](docs/challenges.fr.md) | The challenge rounds C1–C15 and D1–D5, in French, with the measured resolutions of C1, C2, C10 and D1. |
| [`docs/article/`](docs/article/) | The article under verification, as corrected, plus the wording insertions made in response to the campaigns. |
| [`env/`](env/) | `requirements.txt` (pinned to what ran, with pymongo deliberately unpinned because no file records the version) and the MongoDB replica-set compose file. |
| [`CITATION.cff`](CITATION.cff) | Citation metadata. |

## Honesty statement

This repository publishes its own adversarial audit. [LIMITATIONS.md](LIMITATIONS.md) contains the nine
integrity findings and twenty challenges written against these campaigns — including that the measurer
wrote or patched most of the instruments that carry the decisive verdicts, that the host was never
isolated, that two headline quantities were never reconciled, and that the dossier satisfies about two
and a half of the six conditions the article imposes on other people's benchmarks. The author is an IBM
employee measuring an IBM product, and the result is unflattering to that product on most of the axes
measured; where the axes themselves are skewed toward HCD's expected weakness, [DISCLAIMER.md](DISCLAIMER.md)
and challenge C9 say so rather than leaving it for a reader to notice. No figure in
[`data/raw/`](data/raw/) has been edited after the fact, including the figures a later run refuted —
`findings_mongot_freshness.json` still reads `p50_ms: 1015.201` even though `findings_mongot_floor.json`
proved that was the worst phase of a refresh cycle. Corrections, contradictions and reproductions that
disagree with these results are the point of publishing, and are welcome as issues.

## Licence

| Scope | Licence |
|---|---|
| Everything under `probes/` | **Apache-2.0** — see [`LICENSE`](LICENSE) |
| Everything under `docs/` and `data/`, and the Markdown files at the repository root | **CC BY 4.0** — see [`LICENSE-docs`](LICENSE-docs) |

If you redistribute the JSON under `data/raw/` in modified form, say so. The value of that dataset is
that it has not been edited after the fact.

## Cite this

> Leconte, David (2026). *Shredding cost: what physical storage layout does to write cost, index
> freshness and concurrency in document databases.* Dataset.
> https://github.com/davidleconte/shredding-cost-hcd-mongodb

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff). **Cite the measurement identifier (Mxx)
alongside the number**, so that the regime the number belongs to travels with it, and read
[LIMITATIONS.md](LIMITATIONS.md) first. The eight rules at the end of
[RESULTS.md](RESULTS.md#reading-rules-for-anyone-quoting-this-dossier) state the specific misquotations
this dossier is most likely to suffer.
