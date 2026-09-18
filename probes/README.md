# `probes/` — probe index and provenance register

This directory holds every script that produced a number in this dossier. It is
both an index (what each probe measures, which measurement it backs, which file
in `data/raw/` it wrote) and a **provenance register**: for each probe, who wrote
the code that produced the evidence.

The provenance column is the point of this file. It exists as a direct response
to finding **I2** of the adversarial audit (`docs/audit-adversarial.fr.md`),
which states that "the measurer wrote and modified the instruments", that five
scripts were written entirely by the measurer, and that — in the auditor's own
words — *"the verdicts that matter most rest most on the measurer's code."*

That finding is not softened here. It is tabulated.

## Reading the evidence classes

| Class | Meaning | Strength |
|---|---|---|
| **vendor-supplied, unmodified** | A pre-registered harness, supplied with the campaign brief, executed as received. The measurer could not tune it to produce a preferred answer without leaving a trace. | Strongest |
| **vendor-supplied, patched** | The same, with declared changes. Each patch is listed below with the mechanical failure it repaired. No patch touched a size, a threshold, a repetition count or a verdict rule. | Middle |
| **written by the measurer** | Code the measurer wrote to answer a question the supplied harnesses did not cover. Nothing in the code prevented the measurer from choosing a design that flattered a preferred conclusion. | Weakest |

## Marker legend

The dossier marks every claim with its epistemic status: **[D]** documented by
the vendor, **[R]** reported in practitioner literature but not documented,
**[U]** unverified structural inference, **[M]** measured on one named build
under stated conditions. `[M]` is stronger than `[U]` and weaker than `[D]`: it
establishes what one build did on one day, not what a vendor commits to.
Everything in the table below is `[M]` evidence. (`[R]` is defined in the
epistemic legend but does not currently appear in the documents in `docs/`.)

---

## The register

| Probe file | What it measures | Backs | Output in `data/raw/` | Provenance |
|---|---|---|---|---|
| `verify_storage_claims.py` | The four pre-registered probes against one HCD build: schema introspection (probe 1), write-to-searchable interval at idle and under a fixed offered rate (probe 2), mutation cost vs document size with a same-size read control (probe 3), CQL query tracing of the statement pair the Data API issues (probe 4). | M1, M2, M3, M4 | `findings.json`; the campaign-3 re-run is folded into `findings_disk_rf3.json` | **vendor-supplied, patched** (2 patches, diffable against the `.orig`) |
| `verify_storage_claims.py.orig` | Nothing — never executed. The unmodified original, kept so the two patches above can be diffed byte for byte. | — | — | **vendor-supplied, unmodified** (reference copy) |
| `verify_storage_claims_rf3.py` | The same four probes at RF = 3 on a six-node, two-datacentre ring with tracing raised to 1.0 on the three dc1 replicas. This is where the three-replica Paxos round is observed message by message. | M5 (and the RF = 3 re-check of A2, A3, A5, freshness) | `findings_rf3.json`, `findings_rf3_rate50.json`, `findings_rf3_rate50_rep2.json`; `probe4_rf3_supplementary.json` accompanies that run as a trace extract but names no producing script in the file itself | **vendor-supplied, patched** (the 2 above plus a third) |
| `disk_regime_driver.py` | Measures nothing by design. It forces a disk-bound state and refuses to report success unless it can evidence four obligations: on-disk data exceeds the memtable budget, SSTables exist, at least one compaction completed, caches were invalidated. Measurement is then a separate harness run against that state. | The disk-regime precondition of M10, M11, M12 | `disk_state.json` (campaign 3), `disk_state_c4.json` (campaign 4) | **vendor-supplied, patched** (3 patches) |
| `probe_field_vs_byte.py` | Separates the two terms campaign 1 grew together. Series 1 holds field count fixed at 16 and varies bytes per field (512 → 8000); series 2 holds indexed volume fixed at 64 KiB and varies field count (9 → 128). An internal control (16 × 4096 B) appears in both series. | M11 | `findings_fieldbyte.json` | **vendor-supplied, unmodified** |
| `probe_tier_vs_storage.py` | Method 1 (bypass): the same logical mutation run (a) through the Data API and (b) as the identical CQL statement pair against the same row, with shredded values read back rather than recomputed. The difference is the stateless-tier term. | M12 (method 1) | `findings_tier.json` | **vendor-supplied, patched** (1 patch) |
| `probe_tier_vs_storage.py.orig` | Nothing — never executed, and not an artefact of the run. It was **reconstructed during the documentation pass** by reverting the declared campaign-4 prepared-statement patch in the patched script: no pre-patch copy of this probe survives in the evidence snapshot (which does retain `verify_storage_claims.py.orig`) or in `raw_evidence.tar.gz`, and its mtime (2026-09-18 10:03) is later than the patched probe it is supposed to predate (09:35). It is a convenience for reading the diff, not independent evidence of what the original contained. | — | — | **reconstructed after the fact** (derived from the patched file, not a retained original) |
| `method2_trace.py` | Method 2 (trace): the second, independent estimate of the same tier term — client-observed Data API latency minus the coordinator-side duration of the CQL statements it issued, read from `system_traces.sessions`. | M12 (method 2) | `findings_tier_method2.json` | **written by the measurer** |
| `probe_comparative.py` | The identical sixteen-field mutation series against HCD's Data API and against MongoDB, with MongoDB run **twice** (no ballast index, and a `$**` wildcard index matching HCD's automatic indexing). Refuses to emit a cross-engine ratio unless both engines ran on the same host, in the same session, with the same series shape and repetition counts. | M13 | `cmp_hcd.json`, `cmp_mongo.json`, `comparison.json`, `comparison_v2.json`, `smoke_hcd.json`, `smoke_mongo.json` | **vendor-supplied, unmodified** |
| `hcd_cql_arm.py` | The same single-field mutation driven straight through the CQL driver — the same `SELECT` + conditional `UPDATE` the Data API issues (M2) — with the stateless tier removed, so the MongoDB comparison becomes engine-vs-engine rather than stack-vs-stack. | M14 | `cmp_hcdcql.json` (merged into `comparison_v2.json`) | **written by the measurer** (the file says so in its own docstring) |
| `rmw_postflush.py` | Variant B with `nodetool flush` on the three dc1 nodes **before each timed update**, so the read half of the read-modify-write cycle lands on the SSTable path instead of the memtable. The flush is not timed. | M15 | `rmw_postflush.json` | **written by the measurer** |
| `probe_read_search.py` | The three axes the article claims for HCD, at 1 000 000 documents on both engines: (A) filtered read on an **undeclared** field, (B) point read by `_id`, (C) freshness on a regular secondary index. | M16 | `findings_rs_hcd.json`, `findings_rs_mongo.json` | **written by the measurer** |
| `vector_freshness_rf3.py` | Vector-search freshness at RF = 3, where the Data API reads vectors at `LOCAL_ONE` while writes commit at `LOCAL_QUORUM`. Each cycle contrasts, on the same first attempt, a `LOCAL_ONE` vector search against a `LOCAL_QUORUM` key read, so a stale-replica window would be attributable. | M7 | `vector_freshness_idle.json`, `vector_freshness_loaded.json`, `findings_vector_rf3.json` | **vendor-supplied, unmodified** — see the classification caveat below |
| `mongot_freshness.py` | MongoDB's write-to-searchable lag on `$search` (mongot ingests asynchronously off the change stream), contrasted against a synchronous `find({_id})` in the same cycles. | M17 (the MongoDB half) | `findings_mongot_freshness.json` | **written by the measurer** |
| `mongot_floor.py` | The true floor of that lag. Sleeps a random 0–1200 ms before each insert so inserts land at uniformly random phases of the commit cycle, then polls at 5 ms. Distinguishes a refresh interval from a fixed pipeline delay. | M18 | `findings_mongot_floor.json` | **written by the measurer** |
| `turn_latency.py` | Miss-rate of a search issued τ ms after the write, swept over τ = 0…3000 ms, 30 cycles per point. Answers whether the freshness lag survives a realistic RAG turn latency. | M19 | `findings_turn_hcd.json`, `findings_turn_mongodb.json` | **written by the measurer** |
| `probe_aggregation.py` | The aggregation axis: count-all, filtered count, and `GROUP BY cat / SUM(amt)` at 200 000 documents, with a deterministic ground truth so every arm is checked for **correctness**, not only for speed. | M20–M23 — assigned in this repository, not in ADR-001; see gaps | `findings_agg_hcd.json`, `findings_agg_mongodb.json` | **written by the measurer** |
| `cql_groupby_expressibility.py` | Not a latency probe. Answers one structural question — is a CQL `GROUP BY` on the group key expressible against a table not partitioned by it? — with rules R1–R3 fixed before execution and written into the output. Written 18 September 2026 to put behind a citation a fact that had been published without one. | `findings_cql_groupby_expressibility.json` |
| `agg_cql_arm.py` | The labelled apples-to-oranges reference for the same aggregation: a purpose-built **native CQL** table pre-partitioned by the group key. Not the document model, not the Data API. Shows what the storage engine can do once the document model is abandoned. | M23, CQL arms — assigned in this repository, not in ADR-001; see gaps | `findings_agg_cqlref.json` | **written by the measurer** |

---

## The patches, in full

Four scripts are patched. Each patch repaired a mechanical failure — the probe
could not run at all, or could not satisfy its own proof obligation — and none
changed a document size, a threshold, a repetition count, a warm-up count or a
verdict rule.

### `verify_storage_claims.py` (2 patches; diffable against `verify_storage_claims.py.orig`)

| Where | Change | Why it is mechanical |
|---|---|---|
| `connect_data_api()` | `DataAPIClient(token)` → `DataAPIClient(token, environment=Environment.HCD)` | Self-hosted HCD serves `/v1`; without `environment`, astrapy 2.3.1 targets Astra's `/api/json/v1` and returns **HTTP 404 on every command**. Reproduced read-only before the change. Effect on protocol: none. |
| `main()`, `create_collection` | added `definition={"indexing": {"deny": ["ballast"]}}` | The Data API refuses any **indexed** string over 8000 bytes (`SHRED_DOC_LIMIT_VIOLATION` at 8192 B), so probe 3's single-string 8/32/128 KB ballast cannot be indexed at all. Excluding only `ballast` from indexing leaves sizes, mutation, 5 warm-ups, 30 repetitions and the 1.2/1.6 thresholds untouched; the ballast still lives in `doc_json`. Declared and approved before the run (`findings.json → harness_modifications`). |

### `verify_storage_claims_rf3.py` (the two above, plus one)

| Where | Change | Why it is mechanical |
|---|---|---|
| `connect_cql()` | `session.default_consistency_level = ConsistencyLevel.ONE` | `system_traces` is `SimpleStrategy RF=2` on a **two-datacentre** ring, so the driver's default `LOCAL_ONE` read fails with `alive_replicas: 0` for partitions whose two replicas both sit in dc2. Queries, thresholds and verdict logic untouched. Applies to the RF = 3 run only. |

### `disk_regime_driver.py` (3 patches, carried as in-code `Mechanical fix` comments)

| Where | Change | Why it is mechanical |
|---|---|---|
| `fill()` | Ballast changed from constant bytes (`"x" * n`) to **incompressible** random base64, a fresh value per document | A constant-byte payload compressed roughly 120:1 under the table's `LZ4Compressor`: 6 GiB of logical data occupied about 50 MiB on disk, and the driver's own on-disk-size proof **correctly refused the run**. The patch makes on-disk size track logical size. It repairs the proof, it does not relax it. |
| `count_sstables()` | SSTable evidence read via `docker exec` instead of an in-process host walk | The node is a container and the host volume is root-only. The proof obligation and its threshold (`Data.db` count > 0) are unchanged; the count still comes from the real node's data directory. |
| `dir_bytes()` | On-disk size read via `docker exec … du -sb` | Same root-only host volume. |

### `probe_tier_vs_storage.py` (1 patch)

| Where | Change | Why it is mechanical |
|---|---|---|
| arm B statement binding | Simple statements with `%s` → **prepared statements** with `?` | The collection primary key is a `frozen<tuple<tinyint,text>>`. Binding it in a simple statement is rejected server-side (`Unexpected receiver type 'tuple<tinyint,text>'; only list and vector are expected`); a prepared statement carries the column type and binds the tuple correctly. This is how a real client binds a typed key. No threshold, size or repetition changed. |

**Auditability caveat, stated plainly.** One probe — `verify_storage_claims.py`
— ships a genuinely retained original in this directory, byte-identical to the
copy in the evidence snapshot, so its patches can be machine-checked rather than
taken on trust. The second `.orig` is weaker, and the register above says why:
it was reconstructed after the run by reverting the patch it is used to show.
Both diffs are still worth running:

```bash
diff probes/verify_storage_claims.py.orig  probes/verify_storage_claims.py    # 14 changed lines, 2 patches
diff probes/probe_tier_vs_storage.py.orig  probes/probe_tier_vs_storage.py    # 21 changed lines, 1 patch
```

Both diffs consist only of the declared changes and their in-code `Mechanical fix`
rationale. Neither touches a document size, a threshold, a repetition count, a
warm-up count or a verdict rule — which is the property a reader should actually
check. For `verify_storage_claims.py` that check is independent evidence. For
`probe_tier_vs_storage.py` it is true by construction, since the `.orig` was made
by reverting exactly that patch, and it therefore cannot rule out an undeclared
change made before the file was first saved.

The patches to `verify_storage_claims_rf3.py` and `disk_regime_driver.py` are
documented in-code as `Mechanical fix` comments and in the campaign reports, but
**this repository does not ship an unmodified original for those two**, so their
diffs cannot be machine-checked here. A hostile reader should treat those two as
declared but not independently diffable.

---

## What rests on code the measurer wrote

Stated without hedging, because the audit states it without hedging.

**Five of the decisive measurements rest on measurer-written code**:
M12 (half of it — the trace method), M14, M15, M16, M17. Audit finding I2 names
the five scripts: `method2_trace.py`, `hcd_cql_arm.py`, `rmw_postflush.py`,
`mongot_freshness.py`, `probe_read_search.py`.

**Both measurements in which HCD comes out ahead are among them.** There are
exactly two, and neither rests on a script the measurer did not write:

| HCD wins | Measured by | Provenance | The number, with its caveat in the same breath |
|---|---|---|---|
| Filtered search on an **undeclared** field (M16, axis A) | `probe_read_search.py` | written by the measurer | HCD p50 **17.376 ms** against mongo-default's **376.698 ms** collection scan at 1 M documents — a factor of about 22 (`findings_rs_hcd.json`, `findings_rs_mongo.json`). **In the same breath:** mongo-wildcard answers the same query at p50 **0.732 ms**, about 24× faster than HCD. What HCD buys is the dispensation from index design, not speed. |
| Search freshness (M17) | `mongot_freshness.py` (MongoDB half) | written by the measurer | MongoDB `$search` p50 **1015.201 ms** write-to-searchable, poll attempts median 34 (`findings_mongot_freshness.json`), against HCD searchable on the first query, p50 **44.972 ms** (`findings_hcd_vec_freshness.json`). **In the same breath:** the measurer's own follow-up M18 (`mongot_floor.py`, `findings_mongot_floor.json`) established that the 1015 ms was the **worst phase of a periodic refresh interval**, inflated by a self-synchronised probe — de-synchronised, the lag is p50 **664.3 ms**, min **89.1 ms**, max **1170.2 ms**. And HCD's 44.972 ms is the HTTP round-trip floor, not a measured zero: any HCD index lag below about 45 ms is undetectable by this instrument, so "synchronous, zero lag" is an overstatement of "below the measurement floor". M19 (`turn_latency.py`) then bounds the advantage: MongoDB's miss rate is 100 % at τ = 0 and **0 % at τ ≥ 1000 ms** (`findings_turn_mongodb.json`), so the edge is total below one second and absent above it. |

By contrast, the measurements the audit calls hardest to dismiss come from
supplied scripts:

- **M1** (12 physical columns, 9 SAI indexes) and **M2** (the `SELECT` →
  `UPDATE … IF` cycle, 10 of 10 traced operations) — direct engine reads through
  the patched `verify_storage_claims.py`, two passes. The audit calls them
  *"unattackable"*.
- **M11** (indexed **bytes** dominate field count) — `probe_field_vs_byte.py`,
  **unmodified**. Series 1 (bytes vary, fields fixed) fits at r² **0.9999** in
  both passes; series 2 (fields vary, volume fixed) moves the update p50 by an
  endpoint ratio of only **1.128** and **1.187** across the two passes
  (`findings_fieldbyte.json`; the campaign report rounds these to ×1.13 and
  ×1.19). The audit calls this the most robust of the derived measurements.
  **In the same breath:** the pre-registered strict rule — *≤ 1.15 → bytes
  dominate; ≥ 1.5 → field count is an independent driver; between → inconclusive*
  — returns no clean verdict, because the two passes straddle its 1.15 line. One
  pass says "bytes dominate", the other says "inconclusive". Neither approaches
  the 1.5 that would make field count an independent driver.
- **M13** (MongoDB wins single-field mutation decisively) — `probe_comparative.py`,
  **unmodified**, with its own cross-engine gate. HCD 0.7775 ms/KiB (r² 0.997)
  against mongo-wildcard 0.0176 (r² 0.8794) and mongo-default 0.0098 (r² 0.7809)
  — 44× and 79× (`comparison.json`). **In the same breath:** these are
  cache-resident (memtable) rates. M15 (`rmw_postflush.json`) shows the per-byte
  growth collapsing from ×5.94 to ×1.52 once the read half of the cycle is forced
  onto SSTables, so 0.7775 ms/KiB characterises a regime, not "the" mutation
  cost of HCD. The low MongoDB r² values are themselves the finding: the slope is
  so near zero that noise dominates.

---

## Gaps in this register

A provenance register that hid its own holes would defeat its purpose.

1. **`probe3_variant_b.py` is referenced but absent.** ADR-001 names it as an
   instrument of M10, alongside `disk_regime_driver.py` and
   `verify_storage_claims.py`. It is not in this directory — and it was not lost: it
   survives, unpublished, in the off-repository archive listed in gap 8. The variant-B
   numbers it produced survive in `findings_disk_rf3.json`
   (`variantB_indexed_chunks`, update p50 20.389 → 121.189 ms, growth ×5.94) and
   in `findings_rf3.json`, but **the code that produced them is not published
   here**, so their provenance class cannot be established from this repository.
2. **The HCD half of M17 has no script here.** `findings_hcd_vec_freshness.json`
   records its own producer only as *"hcd vector-search freshness (same session
   as mongot)"*. No file in this directory writes that filename.
3. **`control_read_A_run1.json` and `control_read_A_run2.json` have no producing
   script in this directory.** They carry the variant-A read control for the
   RF = 3 collection (`storage_probe_rf3`). Related: campaign 1 records that the
   pass-1 read-control JSON was **overwritten by pass 2** because the filename was
   fixed, and that its p50 values and wire sizes were transcribed from the run log
   and marked as transcribed in `findings.json`. The script `RESULTS.md` names for that
   overwrite, `control_read.py`, is real and not an invented filename: it is one of the
   two scripts in the archive of gap 8, and the archived copy already carries the repair
   — a `RUN` argument that labels the output per pass, under an inline comment recording
   that a fixed name overwrote run 1 on 2026-09-17.
4. **`tier_comparison.json` is a derived merge with no producing script here.**
   It joins the method-1 and method-2 tier estimates size by size — including the
   `divergence_pct` and `within_25pct` fields that carry M12's cardinal caveat
   (agreement within 25 % at 8, 16 and 32 KiB; **34.0 %** divergence at 64 KiB and
   **27.7 %** at 125 KiB). Neither `probe_tier_vs_storage.py` nor
   `method2_trace.py` writes it.
5. **The aggregation axis carries M20–M23, which ADR-001 does not.**
   `probe_aggregation.py` and `agg_cql_arm.py` post-date the M1–M19 register in
   ADR-001 and are not entered in it; their measurements were numbered M20–M23 in
   this repository, in `RESULTS.md` §3. Their findings are in `data/raw/` and are real
   (`findings_agg_hcd.json` records HCD's `countDocuments` failing outright with
   `TooManyDocumentsToCountException` above 1000 documents, and a client
   scan-and-aggregate p50 of **133 984.229 ms** over 200 000 documents against
   MongoDB's server-side `$group` at p50 **222.711 ms** in
   `findings_agg_mongodb.json` — and, on the same engine, same host, same corpus,
   against native CQL's per-partition sweep at p50 **2 011.399 ms** in
   `findings_agg_cqlref.json`, the arm `agg_cql_arm.py` listed above — which
   locates the 134 s in the Data API tier rather than in the storage engine, at
   the price of abandoning the document model and pre-designing a table
   partitioned by the group key), but they were never folded into the ADR's
   register, and the adversarial audit — which covers M1–M17 — never saw them.
6. **`mongot_floor.py` (M18) and `turn_latency.py` (M19) post-date the audit.**
   The audit counts **five** measurer-written scripts. These two are measurer-written
   by the same pattern as the others (each closes a self-issued challenge, C10 and
   D1 respectively), which would make the true count **seven**, but the audit's own
   text is quoted above as it stands.
7. **`vector_freshness_rf3.py` is classified vendor-supplied by inference, not by
   diff.** No `.orig` exists for it, and no patch is declared in it. It is placed
   in the vendor-supplied class because audit finding I2 enumerates exactly five
   measurer-written scripts and this is not among them, and because it carries the
   supplied harnesses' structure (a pre-declared verdict rule, an explicit refusal
   to adjust sizes or thresholds to agree with the article). A reader who rejects
   that inference should read M7 as measurer-written. M7's verdict is **NOT
   DETECTABLE** either way: 120 of 120 cycles had the just-written vector top-1 on
   the first `LOCAL_ONE` search, insert-to-visible p50 **74.735 ms**
   (`vector_freshness_idle.json`) — which bounds the window below the measurement
   floor rather than proving it is zero.
8. **Thirteen files of this campaign's evidence exist and are not published.** The run
   left an archive, `verif-storage-20260917/raw_evidence.tar.gz`, outside this
   repository. It holds 13 files, **none of them byte-identical to anything in
   `data/raw/` or in this directory**:
   - **the two scripts this register and `RESULTS.md` name as unfindable** —
     `probe3_variant_b.py` (gap 1) and `control_read.py` (gap 3);
   - **nine further evidence files**, all from the RF = 1 keyspace
     `verif_stockage_20260917` — `findings_rate50.json` and `findings_rate50_rep2.json`
     (the RF = 1 fixed-rate passes, distinct from the published RF = 3
     `findings_rf3_rate50*.json`); `control_read_A_rep2.json` and `control_read_B.json`
     (the RF = 1 read controls); `probe3_variant_b.json` (the RF = 1 variant-B finding,
     verdict `SUPPORTED`); `probe4_traced.json`, `probe4_supplementary_cl.json` and
     `probe4_traced_statements.json` (the M4 consistency-level trace, the last being the
     raw per-statement dump; `probe4_traced.json` records `consistency_levels_observed`
     as `LOCAL_QUORUM` 70 **alongside `ONE` 42 and `LOCAL_ONE` 2** over 200 traces
     examined, where M4 is stated in ADR-001 as "70/70 statements at `LOCAL_QUORUM`");
     and `freshness_attempts.json` (the RF = 1 freshness histogram, 40/40 found on the
     first attempt);
   - **two container-stat logs**, `stats_run50.log` and `stats_run50_rep2.log`, which
     this repository's `.gitignore` would exclude by its `*.log` rule in any case.

   This is not a redundant copy of what is published. **The ×1.56 variant-B read control
   quoted in `RESULTS.md` M3 — p50 7.390 → 11.523 ms — is recorded in
   `control_read_B.json`, which is in that archive and not in `data/raw/`.** M3 cites
   `control_read_A_run1.json` and `control_read_A_run2.json`, which carry the variant-A
   control for the *RF = 3* collection (9.748 → 18.179 and 8.671 → 16.059 ms) and do not
   contain those figures. So a published number rests on an unpublished file.

   No filename in that archive appears anywhere in this repository's prose, and the
   archive itself is named nowhere in it. **This register records no decision to withhold
   these files and no reason for it**; the omission is stated here so that the gap reads
   as one of publication rather than of survival. Until the archive is published, gaps 1
   and 3 stand as written — a withheld file settles nothing a reader can check.

---

## How to read this register

A finding produced by an unmodified vendor-supplied script is harder to dismiss
than one produced by a script the measurer wrote. The reason is not that the
measurer is suspected of fraud. It is that an instrument written after the
question is known can be shaped — in its sizes, its thresholds, its arms, its
stopping rule — by what its author expects to find, and no amount of good faith
removes that degree of freedom. A pre-registered harness executed as received has
far fewer places to hide a thumb on the scale, and a patched one has exactly as
many as its patches, which is why every patch is listed above with the failure it
repaired.

So the classes are a ranking of how much a hostile reader has to take on trust:

- **vendor-supplied, unmodified** — trust the harness's author, and check that it
  ran on the stated build. M11 and M13 sit here.
- **vendor-supplied, patched** — the same, plus each declared patch. Four patches
  are diffable (three of them against the two `.orig` files in this directory); the rest are
  declared in-code and in the campaign reports, and are listed above so a reader
  can weigh them individually rather than accept them as a bundle.
- **written by the measurer** — trust the measurer's design judgement. Five of the
  decisive measurements sit here, including **both** measurements in which HCD
  comes out ahead. Two of those designs were later found flawed **by the measurer's
  own follow-up work**: M17's magnitude was overstated by a self-synchronised probe
  and corrected by M18, and M10's "the coefficient holds under disk" was an
  artefact of a probe that re-read its own memtable-resident row, corrected by M15.
  That is what this class costs.

This repository publishes the distinction instead of hiding it. The register is
not a defence of the weaker class; it is the information a reader needs to
discount it correctly. The experiment was built so that it could prove its own
author wrong, and in several places it did — which is only verifiable if you can
see which instrument produced which number, and who wrote that instrument.

**Do not modify anything under `data/raw/`.** Those files are untouched evidence,
byte-identical to the run that produced them. The Python files in this directory
are likewise the code as it ran.

## `disk_regime_rerun.py` — written, not yet run

Closes the two comparisons that `data/derived/inference.json` marks UNDETERMINABLE, which are the
comparisons carrying the dossier's strongest architectural claim. It exists because the original
records kept a median and nothing else: the shared `dist()` helper emits n / p50 / p95 / p99 / max
/ stdev and drops both the minimum and the series, and separation of support needs the minimum.
This probe does not call that helper. Rules R1–R4 are fixed in its docstring before execution;
record the verdict against them and not against what the data suggest afterwards.
