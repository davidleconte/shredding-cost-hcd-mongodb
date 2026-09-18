# Methodology

How the measurements in this repository were taken, what rules governed them, and
where those rules were broken or only partly met.

This document exists because the campaign it describes was designed to be able to
prove its own author wrong, and in several places it did. Everything below is
written to preserve that property. Readers looking for the numbers themselves
should go to `docs/campaigns/`, the evidence register in
`docs/adr/ADR-001-modelling-policy.md`, and the untouched JSON in `data/raw/`.
Readers looking for what the numbers may not be used for should read
`docs/audit-adversarial.fr.md` and `docs/challenges.fr.md`.

**System under test.** IBM DataStax HCD 2.0.6 (`nodetool version` =
`5.0.7.0-ea50e91ba01f`) with Data API v1.0.33, and MongoDB 8.0.32 (replica set) /
`mongodb-atlas-local` 8.3.11 (the `mongot` deployments — `mongot` **1.75.1**, edition
**`localDev`**, image digest `sha256:e118f5c1…986d8f1`; the edition string is read verbatim
from `/etc/mongodb-atlas-local/mongot-edition` inside the image and is recorded in
`data/raw/findings_mongot_provenance.json`), all on one host,
`alphadebunker`: Intel Xeon Gold 6148 @ 2.40 GHz, 80 vCPU, 220.2 GiB RAM,
Linux 6.8.0-136-generic, inside a QEMU VM whose physical storage class could not
be established from the guest (`data/raw/comparison.json`,
`data/raw/findings_fieldbyte.json → conditions.storage_class`).

---

## 1. The cardinal rule

**The protocol was fixed before the numbers, and was never retuned to make the
numbers converge on the article's claims.**

In practice this decomposed into four standing rules.

1. **Verdict rules were pre-registered.** Each probe carried its decision rule in
   its own source before it ran, and the rule was allowed to return a verdict the
   author did not want. Two examples, both of which did exactly that:
   - The **read-control rule** of campaign 1: a growth in update latency counts
     only if it is separable from the growth of a same-size *read* on the same
     document. Applied, it made the latency probe **INCONCLUSIVE** — update
     ×1.92 and ×2.21 over two passes against a read control of ×1.86 and ×1.94
     (`data/raw/findings.json → findings[2].read_control_pre_registered_rule`).
     The read-modify-write claim therefore rests on the CQL trace (M2), not on
     the latency curve.
   - The **field-versus-byte rule** of `probes/probe_field_vs_byte.py`
     (its `verdict_rule` field): endpoint ratio ≤ 1.15 means bytes dominate,
     ≥ 1.5 means field count is an independent driver, anything between is
     INCONCLUSIVE. The two passes returned 1.128 and 1.187 — straddling the
     boundary — so the strict verdict is **INCONCLUSIVE**, and the dossier
     reports "bytes dominate, field count a weak secondary factor" as a
     direction rather than as a passed test
     (`data/raw/findings_fieldbyte.json`).
2. **Script changes had to be mechanical, and declared before any number was
   read.** A mechanical fix is one that makes the instrument run at all, without
   touching a threshold, a document size, a repetition count or a verdict rule.
   Five were needed; all five are declared, and the unmodified original of the
   main harness is kept in the repository as
   `probes/verify_storage_claims.py.orig` so the diff can be audited.

   | # | Where | Change | Mechanical reason | Effect on protocol |
   |---|---|---|---|---|
   | 1 | `verify_storage_claims.py`, `connect_data_api()` | `DataAPIClient(token)` → `DataAPIClient(token, environment=Environment.HCD)` | self-hosted HCD serves `/v1`, not Astra's `/api/json/v1`; without it astrapy 2.3.1 returns HTTP 404 on every command | none |
   | 2 | `verify_storage_claims.py`, `create_collection` | added `definition={"indexing": {"deny": ["ballast"]}}` | the Data API refuses any *indexed* string above 8 000 bytes (`SHRED_DOC_LIMIT_VIOLATION` at 8 192), so probe 3's single-string ballast cannot be indexed | sizes, mutation, 5 warm-ups, 30 repetitions, thresholds 1.2/1.6 unchanged; ballast still lives in `doc_json` |
   | 3 | RF = 3 run, `connect_cql` | `session.default_consistency_level = ConsistencyLevel.ONE` | `system_traces` is `SimpleStrategy RF=2` on a two-datacentre ring, so the driver's default `LOCAL_ONE` read fails with `alive_replicas: 0` for partitions whose replicas both sit in dc2 | queries, thresholds and verdict logic unchanged (`docs/campaigns/02-replication-rf3.fr.md`) |
   | 4 | `disk_regime_driver.py` (campaign 3) | incompressible fill payload; evidence read host→container | constant-byte ballast compressed roughly 120:1 under LZ4, which defeated the on-disk-size proof the regime depends on | the proof becomes valid; probe parameters unchanged (`docs/campaigns/03-disk-regime.fr.md`) |
   | 5 | `probe_tier_vs_storage.py` (campaign 4) | arm B binds the `frozen<tuple>` key through prepared statements (`?`) | simple `%s` binding of that key is rejected server-side | none (`docs/campaigns/04-tier-vs-storage.fr.md`) |

3. **A finding unfavourable to the author is published at the same weight as one
   that supports him.** The record of the campaign contains, among others:
   - Step 4 of the article's own five-operation model — "maintain the indexes
     covering the fields that changed" — **CONTRADICTED** on this build: the
     `UPDATE` rewrites every derived column
     (`data/raw/findings.json`, M3 in the evidence register).
   - The article's own sentence promising that a measurement "answers
     empirically … in a quarter of an hour" was found to point at the wrong
     section (`docs/campaigns/01-verification.fr.md`).
   - The author's challenge C1 (that the 44× ratio was inflated by the Data API
     tier, and the honest engine-to-engine figure was ~31×) was **refuted by his
     own follow-up measurement**: removing the tier moved the slope only from
     0.7775 to 0.7037 ms/KiB, so the engine-to-engine ratio is 40×, not ~31×
     (`data/raw/comparison_v2.json`, M14).
   - The author's own headline freshness figure, ~1015 ms of `mongot` lag, was
     **overstated by roughly 1.6×** by a self-synchronised probe of his own
     design, and was corrected downward by his own re-measurement to a p50 of
     664.3 ms (`data/raw/findings_mongot_freshness.json` then
     `data/raw/findings_mongot_floor.json`, M17 then M18). A later provenance
     check cut against the author a second time: **both** figures were produced
     by mongot `localDev`, so neither is a MongoDB Atlas Search number at all
     (`data/raw/findings_mongot_provenance.json`).
   - The one axis clearly favourable to HCD — synchronous search freshness — was
     then shown to be **moot for the use case the article invokes to justify it**
     (conversational RAG), because MongoDB's miss rate reaches 0 % once the
     write-to-search gap passes 1000 ms
     (`data/raw/findings_turn_mongodb.json`, M19).
4. **A number never travels without its regime.** See §5. In this dossier a
   per-KiB or per-byte figure quoted without naming the regime it was taken in is
   a misquote, not an abbreviation.

---

## 2. Evidence markers

Every substantive claim in the source article carries one of four markers, and
the same markers are used throughout this repository. They are reproduced here
verbatim from `docs/article/article-corrected.html` and
`docs/article/wording-insertions.md`:

| Marker | Meaning |
|---|---|
| **[D] Documented** | Established by the vendor's own version-pinned documentation, by the project's source of record, or by peer-reviewed publication. Quoted verbatim in the appendix. |
| **[R] Reported** | Described publicly by the engineers who built the system, or by the upstream project, but not restated in the versioned documentation of the shipped product. Directionally reliable; not a contractual guarantee. |
| **[U] Unverified** | Asserted on structural grounds, or widely repeated in the practitioner literature, but not established by any source of acceptable rank that the author was able to consult. Treat as a hypothesis to be tested against your own build. |
| **[M] Measured** | Observed on a named build under stated conditions, by a harness reproduced in the appendix. Stronger than [U], weaker than [D]: it establishes what one build did on one day, not what the vendor commits to. Every [M] claim names its measurement and every measurement names its conditions. |

The marker ordering matters and is not decorative: **[M] does not outrank [D]**.
A measurement of one build on one day is weaker evidence than a vendor's
version-pinned commitment, and the campaign was explicitly forbidden from
promoting a [U] to [D] by measuring it. The campaign's whole output is [M].

Where a measurement came back **NOT DETECTABLE** rather than supported or
contradicted — M7, the `LOCAL_ONE` vector-freshness window, bounded below the
~74 ms HTTP floor of the co-located ring — the marker on the underlying claim was
left unchanged, because a measurement that cannot see an effect is not evidence
that the effect is absent.

---

## 3. Provenance of instruments

**Rule: a measurement resting on an instrument the measurer did not write is
stronger evidence than one resting on an instrument he wrote himself.** The
guarantee being invoked is narrow and worth stating plainly — an instrument you
did not write is one you cannot have shaped, consciously or not, around the
answer you expected.

This rule is applied against the dossier, not for it. It is the substance of
challenge C5 and of audit finding I2, and it is unflattering: the measurements
that produce the most quotable verdicts are, disproportionately, the ones that
rest on the measurer's own code.

| Provenance tier | Measurements | Note |
|---|---|---|
| Supplied harness, executed **unmodified** | M11 (`probe_field_vs_byte.py`), M13 (`probe_comparative.py`) | The strongest evidence in the corpus. M11 carries r² 0.9999 on the byte series. |
| Supplied harness, executed with **declared mechanical fixes** | M1, M2, M3 (`verify_storage_claims.py` + fixes 1–3 above) | Original retained as `probes/verify_storage_claims.py.orig`; the diff is two hunks. |
| Written **by the measurer** | M12 (half, via `method2_trace.py`), M14 (`hcd_cql_arm.py`), M15 (`rmw_postflush.py`), M16 (`probe_read_search.py`), M17 (`mongot_freshness.py`), M18 (`mongot_floor.py`), M19 (`turn_latency.py`) | Audit I2: five of the decisive measurements sit here, including **both** of the two that give HCD a win. M18 and M19 were written after the audit and are in the same tier. |

Two consequences the dossier accepts:

- The measurements a hostile reader should attack first are the measurer's own,
  and specifically the two HCD-favourable ones (M16's 22× auto-index advantage
  and M17's search-freshness advantage).
- `hcd_cql_arm.py` declares its own provenance in its docstring — *"This is the
  measurer's own code (declared, per challenge C5); the storage work it times is
  identical to the Data-API path's, only the tier is absent."* That declaration
  is the mitigation, not an exemption.

A related failure mode, visible in the raw files: a machine-written verdict
string is not a verified conclusion. `data/raw/findings_mongot_floor.json`
contains the verdict *"the true best-case freshness floor is near 0"*, while the
same record's own `min_ms` is **89.1**. Challenge D3 corrects it: the honest model
is a fixed ingestion floor of ~90 ms with a refresh phase on top. Where a raw
record's prose and its own numbers disagree, the numbers win.

---

## 4. Durability matching, and which way it leans

Cross-engine latency comparisons are most commonly rigged by running one engine
at a weaker durability setting than the other. `probes/probe_comparative.py`
names this in its own docstring as "Rigging 2" and records the mapping in every
output record it writes.

| | HCD | MongoDB |
|---|---|---|
| Write path | `LOCAL_QUORUM` (2-of-3) | `w: "majority"` (2-of-3) |
| Conditional path | `LOCAL_SERIAL` on every mutation (a Paxos round) | none — atomicity is per document |
| Journal / commitlog | `commitlog_sync = periodic`, period **10 000 ms** | `j: true` |
| Acknowledgement relative to fsync | **acknowledges before fsync** | **waits for fsync** |

Sources: `data/raw/cmp_hcd.json → durability_mapping`,
`data/raw/cmp_mongo.json → durability_mapping`,
`data/raw/findings.json → conditions` (the commitlog setting).

**State this plainly, because it is the single most important asymmetry in the
comparison and it runs in HCD's favour.** HCD acknowledges a write up to ten
seconds before that write is on stable storage; under `j: true` MongoDB does not
acknowledge until its journal fsync returns. In latency terms the pairing
therefore *gives HCD a head start*: HCD is allowed to answer without waiting for
the disk, and MongoDB is not.

HCD still lost this axis by 44× at the stack level and 40× at the engine level
(`data/raw/comparison.json`, `data/raw/comparison_v2.json`). The objection
consequently reverses: correcting the asymmetry would widen MongoDB's margin, not
narrow it. This is challenge C6, and it is the one challenge in the corpus that
*strengthens* the conclusion it was raised against.

Two further asymmetries are named and were **not** aligned, because they are
design differences rather than settings:

- Every HCD mutation carries a lightweight transaction (Paxos at
  `LOCAL_SERIAL`); MongoDB pays no such round. Recorded in both comparison
  records under `durability_asymmetry_not_covered_by_mapping`.
- The Paxos round was measured on three replicas that **share one host**, so
  inter-replica latency is sub-millisecond. Consensus is therefore measured where
  it hurts least; on a multi-host or WAN deployment it costs tens of
  milliseconds, which would widen the gap further against HCD (challenge C3).
  **No figure in this repository is valid for a multi-host topology.**

`probe_comparative.py` refuses to emit a cross-engine ratio at all unless both
engines were measured on the same host, in the same session, with the same series
shape and repetition counts; the record carries
`cross_engine_comparison_permitted: true` only when that held
(`data/raw/comparison.json`).

---

## 5. The regime taxonomy

This is the lesson the dossier learned the hard way, and the reason the word
"regime" appears beside nearly every number in it.

The mutation cost of HCD's Data API was originally characterised by a single
rate — about **0.77 ms per indexed KiB**, equivalently a growth factor of
**×7.50** from 1 KB to 128 KB of indexed content. That rate turned out to be a
property of a *regime*, not of the engine. Three distinct regimes were measured,
and they are not interchangeable:

| Regime | What it means | Variant-B growth, 1 KB → 128 KB | Source |
|---|---|---|---|
| **Memtable** | Working set entirely in memory; zero SSTables flushed; no compaction cycle crossed. One node, RF = 1. | p50 12.104 ms → 90.783 ms = **×7.50** | `data/raw/findings.json` (M3) |
| **Memtable under pressure** | The *dataset* is genuinely on disk — 6 491 369 675 B (6.05 GiB) ≥ 3× the 2 GiB memtable budget, 40 SSTables after a major compaction, 78 compactions crossed, caches invalidated — but the probe re-reads the row it has just written, which stays memtable-resident. RF = 3. | p50 20.389 ms → 121.189 ms = **×5.94** | `data/raw/findings_disk_rf3.json`, `data/raw/disk_state.json` (M10) |
| **SSTable read path** | `nodetool flush` before each timed update, so the cycle's internal `SELECT` must read an SSTable. | p50 107.765 ms → 163.402 ms = **×1.52** | `data/raw/rmw_postflush.json` (M15) |

**What changes between them is not a detail, it is the shape of the cost.** In
the memtable regimes the latency grows with the indexed byte volume. On the
SSTable read path it does not: a fixed read-path cost of roughly 100 ms dominates
and the per-byte growth nearly flattens. The per-byte rate that the article's
section 3 rests on is therefore **a memtable phenomenon**. The *mechanism* —
read, modify, rewrite the whole document plus every derived column — holds in all
three regimes; the *number* does not transfer.

**A single "cost per KiB" figure, quoted without its regime, is meaningless in
this dossier.** The same quantity spans ×1.52 to ×7.50, an interval of about 5×,
across the three regimes measured on one host in one week. That is audit finding
I4, and the ADR's action item 1 was **reopened from `[x]` to `[~]`** because of it
(audit finding I5).

Three caveats belong beside that table and must not be relegated:

- **The SSTable figure is inflated by its own method.** Flushing before every
  update creates one SSTable per flush, so a single `SELECT` may merge up to
  ~35 small SSTables — fragmentation a normal compaction would not leave. The
  true disk-bound cost lies *between* the memtable figures (12–91 ms) and this
  fragmented worst case (107.8–163.4 ms). Declared in
  `probes/rmw_postflush.py` and in `docs/challenges.fr.md`.
- **No page-cache-cold read was ever measured.** Dropping the OS page cache needs
  root, which was unavailable. Every raw record that claims a disk regime says so
  in its own `page_cache_note`: *"Reads may therefore still be served from RAM
  below the database. State this in any report that calls the regime
  disk-bound."* "SSTable-resident" in this repository never means "cold platter".
- **The regimes differ in hardware as well as in regime.** Campaign 1 ran on
  `rh-hcd` (RF = 1, 3 GiB container, 2 G heap); campaigns 3–6 on the `p16` ring
  (RF = 3, 8 GiB nodes, 4 G heap). A coefficient difference between them mixes
  regime with topology and hardware, and the raw record says so
  (`data/raw/findings_fieldbyte.json → conditions.hardware_confound_vs_campaign1`).

The same "name the regime" discipline applies to the **tier-versus-storage
split**, which is the other quantity the dossier refuses to publish as a point:

| Method | Regime / arm layout | Tier share of the per-KiB rate |
|---|---|---|
| Bypass (method 1) | disk regime, interleaved arms | **~29 %** (storage 0.547 ms/KiB, r² 0.997; tier 0.219 ms/KiB, r² 0.98; sum 0.766) |
| Coordinator trace (method 2) | same run | **~19 %** (tier slope 0.145 ms/KiB) |
| HCD-CQL-direct arm | cache regime, separated arms | **~9 %** (0.7775 → 0.7037 ms/KiB) |

Sources: `data/raw/findings_tier.json`, `data/raw/findings_tier_method2.json`,
`data/raw/comparison_v2.json` (M12, M14). The audit publishes this as an
**unpinned 9–29 % range** (finding I3) rather than any single figure, and notes
that the dossier's narrative used 29 % when estimating one ratio and 9 % when
correcting it. A further caveat that widens rather than narrows the range: the
per-size tier shares in `data/raw/tier_comparison.json` run from 29.8 % to
**39.7 %**, above the top of the published range, and the two methods diverge by
34.0 % at 64 KiB and 27.7 % at 125 KiB — which is why no precise split is
published at all. What survives across every method is only the direction: the
rate lives **majority in the stateful storage engine, minority in the stateless
tier**.

---

## 6. Statistical policy, and what was not done

**Percentiles only. No means for latency, by construction.**
`probes/verify_storage_claims.py` enforces this in code and says why:

> *"Percentiles only. No mean is computed anywhere in this file, on purpose: an
> average of a latency distribution conceals the behaviour that matters."*

The same `distribution()` shape — `n`, `min`, `p50`, `p95`, `p99`, `max`,
population standard deviation — recurs in `probe_comparative.py`,
`probe_field_vs_byte.py`, `hcd_cql_arm.py` and `rmw_postflush.py`. Comparisons
across the corpus are made on **p50**.

**Where the policy was broken.** The freshness probes are the exception and it is
declared here rather than hidden: `data/raw/findings_mongot_freshness.json`,
`data/raw/findings_hcd_vec_freshness.json` and
`data/raw/findings_mongot_floor.json` each carry a `mean_ms`, and the campaign
prose quotes the `mongot` mean (646.3 ms) in several places. Readers comparing
that axis against the rest of the corpus should use the percentiles in the same
records — for `mongot`, p50 **664.3 ms**, p10 254.5 ms, p90 988.7 ms, min 89.1 ms,
max 1170.2 ms, n = 60 — so that one axis is not quoted on a different statistic
from every other axis.

**Sample sizes and repetition.**

| Probe family | n per point | Warm-up | Passes |
|---|---|---|---|
| Latency series (mutation, field-vs-byte, comparative, CQL arm, post-flush) | 30 | 5, discarded | 2 (post-flush: 1) |
| Read / search (`probe_read_search.py`) | 50 | 5, discarded | 1 |
| Freshness cycles (secondary index, vector, `mongot`) | 40 | — | 1 |
| `mongot` floor (`mongot_floor.py`) | 60 | — | 1 |
| Turn-latency sweep (`turn_latency.py`) | 30 per τ, 9 values of τ | — | 1 |

**Offered rate versus closed loop.** Only the freshness probe of campaign 1 and
its RF = 3 repeat were driven at a **fixed offered rate** — 50 writes/s for 120 s,
open loop, with the measured slip recorded (0.056 s and 0.055 s at RF = 1;
0.066 s and 0.078 s at RF = 3). **Every other probe in this repository is a
sequential closed loop**: one operation, then the next. This is the first of the
six conditions in §8 and the dossier fails it.

**What was not computed, and this is not a footnote.**

- **No confidence intervals.** Anywhere.
- **No significance tests.** Anywhere. Verdicts come from pre-registered
  threshold rules on p50 ratios, not from statistics.
- **Inter-pass variance sometimes exceeds the claimed effect.** The clearest
  instance is campaign 1's variant A: update growth ×1.92 on pass 1 and ×2.21 on
  pass 2 — a spread of roughly 10–15 % between two passes of the same
  configuration — against effects elsewhere in the corpus that are of the same
  order (`data/raw/findings.json`). Audit finding I7.
- **Low r² on the MongoDB side.** The MongoDB slopes that the 44× and 79× ratios
  are computed from carry r² = **0.7809** (default) and **0.8794** (wildcard),
  against 0.997 for HCD (`data/raw/comparison.json`). MongoDB's slope is
  near-zero and substantially noise; the ratio's denominator is the weakest
  quantity in the comparison.
- **No concurrency.** A single sequential client throughout. Nothing in this
  repository says anything about behaviour under concurrent load, which is the
  regime production runs in.
- **The host was not quiet.** The ring carried unrelated production-demo
  workloads (Presto, streaming, Jupyter) at a load average of 14–16 throughout,
  and `system.paxos` grew from 0 to ~13 GiB per node across the campaigns. That
  pressure may have slowed HCD in M12, M13 and M16. It was never quantified and
  never subtracted, so **HCD's absolute latencies should be read as a noisy
  ceiling, not as a clean measurement** (audit findings I1 and I6).

Where a single figure is nevertheless irreducible, it is reported as a count
rather than dressed up as a statistic — for example the turn-latency sweep, whose
result is a miss count out of 30 at each τ: MongoDB 30/30 at τ = 0 ms, 15/30 at
500 ms, 0/30 at τ ≥ 1000 ms; HCD 0/30 at every τ from 0 to 3000 ms
(`data/raw/findings_turn_mongodb.json`, `data/raw/findings_turn_hcd.json`).

---

## 7. Ring restoration protocol

Every campaign ran on a shared, already-populated ring. The same restoration was
performed after each one, and verified rather than assumed:

1. **Drop the experiment keyspace** (`verif_stockage_*`, `verif_rf3_*`,
   `verif_disk_*`, `verif_tier_*`, `cmp`).
2. **Purge every snapshot on all six nodes** — a keyspace drop takes automatic
   snapshots, which are then cleared explicitly.
3. **Recreate the twenty borrowed SAI indexes verbatim.** The ring's 100-index
   SAI guardrail is not modifiable at runtime on this build
   (`nodetool setguardrailsconfig` does not know it; `system_views.settings` is
   read-only), so twenty `supply_chain_hcd` indexes were dropped to make room and
   recreated from captured definitions
   (`p16-sai-index-definitions-20260917.cql`). Verified by count: **101 indexes
   total, 20 on `supply_chain_hcd`**.
4. **Remove the temporary Data API container.**
5. **Reset tracing to 0.0 and verify it** on the three dc1 nodes — the trace
   probability is raised to 1.0 during the CQL-trace probes and must not be left
   there (`data/raw/findings_tier_method2.json → tracing_reset_verified`).
6. **Tear down MongoDB entirely** after the comparative campaigns: three
   containers plus the `cmpnet` network; likewise the `atlas-local` container
   after the `mongot` campaigns.

Sources: `docs/campaigns/02-replication-rf3.fr.md` through
`docs/campaigns/06-freshness-read-search.fr.md`, each of which ends with the
state of the ring.

**What was not restored, and is declared as a permanent residue.** The ~24 600
disk-fill inserts of campaigns 3 and 4 are lightweight transactions, so
`system.paxos` grew by roughly 6 GiB per dc1 node in campaign 3 and reached about
**13 GiB per dc1 node** after campaign 4. A `compact system paxos` on all three
nodes freed nothing: `paxos_state_purging = legacy` holds ballots and purges them
lazily. The residue was left to the engine's natural purge rather than forced on a
shared ring. Disk occupancy went from 507 GB at the initial survey to 525 GB
(+18 GB, entirely in `system.paxos`)
(`docs/campaigns/03-disk-regime.fr.md`, `docs/campaigns/04-tier-vs-storage.fr.md`).

This residue is also a measurement confound, not only an operational one — see
§6 and audit finding I6. And because the ring's state changed between campaigns
in ways that cannot be reversed, **these numbers are not reproducible even on
this host**: the conditions no longer exist, and they were not clean to begin
with (audit finding I1).

---

## 8. Self-compliance: the six conditions

The article this campaign was written to verify demands six conditions of anyone
else's benchmark, and `probes/verify_storage_claims.py` opens by declaring that
"the harness applies to itself the six requirements the article imposes on anyone
else's benchmark". The adversarial audit then checked whether it did.

It did not. This table is reproduced from `docs/audit-adversarial.fr.md`, where it
is the opening finding, and it belongs in the methodology rather than in an
appendix:

| Requirement (article §10) | Met? |
|---|---|
| 1. Load driven at a **fixed offered rate**, not in a closed loop | **NO** — every mutation, read and comparison probe is a **sequential closed loop** (measure one operation, then the next). Only the freshness probe used an offered rate. |
| 2. Distributions, not means | yes (percentiles) — with the freshness-probe exception declared in §6 |
| 3. Equivalent durability, recorded | yes (`LOCAL_QUORUM` ↔ `w:majority`, declared — and see §4, the residual asymmetry favours HCD) |
| 4. Working set / RAM, **both cache and disk regimes** | **partial** — disk was reached only in campaign 3; everything else is cache-only |
| 5. Topology declared | yes |
| 6. Warm-up **and crossing compaction cycles** | **partial** — compaction crossed in campaign 3 only |

**The audit scores this at about 2.5 of six.** Its verdict, quoted rather than
paraphrased: *"A dossier that reproaches others for violating six rules and
violates three of them itself does not have the authority it claims. This is the
root fault: the measurement does not conform to its own standard."*

Nothing in this repository resolves that. It is the reason the audit's overall
finding is that the dossier is *"reliable as a qualitative account and as a
verification of mechanism; it is NOT reliable as a source of publishable
figures"*, and the reason the source article's own Disclosure carried no
benchmark number in its body.

---

## 9. How to quote a number from this repository

1. **Name the measurement identifier** (M1–M19) beside the figure. The evidence
   register in `docs/adr/ADR-001-modelling-policy.md` maps each identifier to its
   method, its verdict and its caveats.
2. **Name the regime** for any per-byte, per-KiB or growth figure (§5). A rate
   without its regime is a misquote.
3. **Carry the contest with the number.** Where the adversarial audit or the
   challenges dispute a figure, the dispute belongs in the same sentence, not in
   a footnote — the 44× beside the 40× engine figure; the ~1015 ms beside the
   p50 664.3 ms correction **and both beside `localDev`**, since neither is a
   MongoDB Atlas Search figure; the ×7.50 beside the ×1.52.
4. **Report the MongoDB pair, or neither.** `probe_comparative.py` states the
   rule: *"mongo-default is MongoDB as a team would deploy it … mongo-wildcard is
   MongoDB doing HCD's job … Report both or report neither."* Quoting only the
   default overstates MongoDB's advantage; quoting only the wildcard understates
   how MongoDB is actually used.
5. **Treat every figure as one build, on one shared host, on one day.** That is
   exactly what the [M] marker means, and it is the strongest thing any number
   here is entitled to claim.

Raw evidence is in `data/raw/` and is byte-identical to the run; it is never
edited. Probe source is in `probes/`. The companion `LIMITATIONS.md` collects the
scope limits in one place; this document covers how the measurements were taken.
