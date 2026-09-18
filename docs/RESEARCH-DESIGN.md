# RESEARCH DESIGN — the question, the hypotheses, and what would have refuted them

**Status of this document.** It was written on 18 September 2026, *after* every campaign in this
repository had run. It is a **reconstruction of the design**, recovered from the campaign reports'
own abstracts, from the decision rules carried in the probe sources, and from
`docs/adr/ADR-001-modelling-policy.md`. It is **not a pre-registration**, and it must not be read as
one. Section 5 states exactly which parts of the design were fixed before the data and which were
not, and it is the most important section here for anyone judging the evidential weight of what
follows.

Nothing in this document is a new measurement. Every figure traces to a named file under
`data/raw/` or to a named campaign report; where a claim in the repository could not be traced to a
published artefact, this document says so rather than repeating it.

**Companion documents.** `METHODOLOGY.md` states how the measurements were taken;
`docs/STATISTICS.md` states what may and may not be inferred from them; `LIMITATIONS.md` states what
they cannot be used for; `RESULTS.md` §3 is the measurement register M1–M23. This document states
what was being asked, and what answer would have counted as "no".

---

## 0. The motivating question

**Does the physical storage layout a document database chooses — a schema-oblivious shred of each
JSON document into generic typed columns with automatic indexes, against a native document store —
determine what it costs to mutate one field of a document, how quickly that document becomes
searchable, and which queries the database can answer at all?**

That sentence is a reconstruction, not a quotation: no document in this repository states a question
in this form. The nearest thing written before a run is the `question` field emitted by one probe,
`probes/probe_tier_vs_storage.py:323`, and it asks a narrower question about one campaign.

---

## 1. Constructs, and what stands for them

A research question is only as good as the substitution it makes between the thing it is about and
the thing it measures. This dossier makes three such substitutions, and only the first is ever
actually measured.

| Construct | What stands for it here | Instrument | Measurements | What the substitution costs |
|---|---|---|---|---|
| **Write cost** (the construct in the title) | **Client-observed wall-clock latency** around a single driver or HTTP call | `time.perf_counter()` around the call, in every latency probe (`probes/hcd_cql_arm.py`, `probes/rmw_postflush.py`, `probes/probe_comparative.py`, `probes/probe_field_vs_byte.py`, `probes/probe_read_search.py`, `probes/probe_aggregation.py`) | M3, M10, M11, M12 (arm A), M13, M14, M15, M16, M23 | Bundles HTTP transport, the Data API tier (parse, shred, serialise), the CQL driver, coordinator work, replication and the local storage engine into one number that is then attributed to "storage layout". It is also **regime-dependent by construction**: a latency proxy for a layout property inherits the cache state of the run. That dependence is exactly audit finding I4 — see RQ4 |
| **Server-side work** | **Coordinator duration** from `system_traces.sessions` | `probes/verify_storage_claims_rf3.py`, `probes/method2_trace.py` | M5, M12 (method 2) | Excludes the HTTP and tier hops entirely, so it is not comparable with the row above; `data/README.md` warns of this directly. It is also a *coordinator's* view, not a replica's |
| **Engine work** — bytes written, write amplification, compaction load, CPU-seconds | **Nothing. Never measured.** | — | — | `RESULTS.md` §6 records "write throughput — never measured as such". No file under `data/raw/` carries a bytes-written, write-amplification or SSTable-bytes figure. The only CPU datum in the corpus is `docker stats` on the Data API container (M12). `CITATION.cff` nonetheless listed "write amplification" as a keyword, which the evidence does not support; it has since been replaced with "read-modify-write" |

**The consequence, stated once and not softened.** Because "write cost" is operationalised as
latency and never as bytes, the flagship per-byte coefficient is a property of a measurement regime
rather than of a layout. A byte-level operationalisation — derivable in principle from M1's twelve
columns and M2's eleven assignments — would not have moved across the three regimes of RQ4. The ×5
spread the dossier reports as its deepest empirical surprise is, in part, a consequence of the
estimand it chose.

Two further constructs are used without a single name:

- **"Freshness"** is operationalised as *poll-until-found*: insert, then query in a loop until the
  document appears, and record the elapsed time and the attempt count. This cannot measure a lag
  shorter than one round trip on the client's own transport — which is why M7 and M17 report floors
  (~74 ms and ~45 ms) rather than zeros, and why M7's verdict is **NOT DETECTABLE** rather than
  "no window".
- **"The tier's share"** is operationalised three different ways (RQ5), which is why it has three
  values.

---

## 2. Research questions

Eight questions are stated below. They are recovered from the seven campaign abstracts and from the
challenge rounds; none was numbered before the fact. Each carries a **falsification criterion**,
marked:

- **[PRE]** — the rule existed in the instrument's own published source *before* that run, and is
  echoed back by that instrument into the raw record. Cited by file and line.
- **[PRE — record-only]** — the rule is stated only in the raw record, with no publishing probe
  and no protocol document in this repository to cite. It may have governed the run; nothing here
  shows that it did, so it is discounted as **[POST]** is.
- **[POST]** — reconstructed here, after the fact. It states what *would* have refuted the
  hypothesis, but it did not govern the run and no reader should count it as pre-registration.

---

### RQ1 — What physical row does the HCD Data API store a JSON document as?

**Hypothesis H1.** A collection declaring no schema is stored as a single table of generic typed
columns — one column holding the document verbatim, the rest holding derived projections of it —
with indexes created automatically rather than declared.

**Operationalisation.** Direct read of `system_schema.columns` and `system_schema.indexes` after a
Data API `insertOne`. This is a structural read, not a proxy: the construct and the measurement are
the same object. It is the only place in the dossier where that is true.

**Procedure.** `probes/verify_storage_claims.py` probe 1, two passes, RF = 1 (campaign 1); re-run
unchanged at RF = 3 (campaign 2). Nested documents examined separately by a raw CQL row read
(M8).

**Falsification criterion [PRE].** `probes/verify_storage_claims.py:231` — fewer than six of the nine
predicted column names present returns INCONCLUSIVE; **none of them present returns CONTRADICTED**,
with the in-code instruction that "the article's section 2.1 should be rewritten against what this
probe actually found". A per-field or per-document-type schema, or a declared-index-only collection,
would have refuted H1 outright.

**Outcome.** SUPPORTED, and *over*-fulfilled: 12 physical columns, all 9 predicted names present,
plus three the author did not predict (`key frozen<tuple<tinyint,text>>`, `tx_id timeuuid`,
`query_lexical_value text`); 9 SAI indexes created automatically. Identical on the second pass and
at RF = 3. Source: `data/raw/findings.json`, `data/raw/findings_rf3.json`. **Not refuted.** The
adversarial audit rates M1 and M2 as the two results it cannot attack.

**Reserve that travels with it.** One build, one collection, one day. The vendor documents none of
these names, so this is an observation of an implementation, not of an interface. M8's evidence is a
transcription into ADR-001 with **no raw JSON file** — the weakest traceability in the register.

---

### RQ2 — What sequence of engine operations does a single-field `updateOne` compile to, and at which consistency levels?

**Hypothesis H2.** A one-field `$set` is not an in-place field write but a read-modify-write of the
whole row: a `SELECT` of the stored document, then one `UPDATE` rewriting the document and every
derived column, guarded by a conditional.

**Operationalisation.** CQL query tracing at `settraceprobability 1.0`, read back from
`system_traces`. The construct (what the engine does) and the measurement (what the trace records)
are separated only by the tracing subsystem's own fidelity. A reader who rejects trace evidence must
hold H2 unproven, because the latency evidence for it is inconclusive — see RQ3.

**Procedure.** `probes/verify_storage_claims.py` probe 4 (M2, M4), 10 traced `updateOne` operations
at RF = 1; re-run by `probes/verify_storage_claims_rf3.py` at RF = 3 with tracing raised on the three
dc1 replicas and restored afterwards (M5); Data API consistency configuration read from the
container's startup log (M6).

**Falsification criteria.**
- **[PRE]** `probes/verify_storage_claims.py:427` — if `LOCAL_QUORUM` does not appear among the
  observed consistency levels, the consistency claim returns INCONCLUSIVE rather than SUPPORTED.
- **[POST]** H2 itself would have been refuted by a trace showing **one** statement per `updateOne`,
  or an `UPDATE` touching only the mutated column, or an unguarded write. The trace is unambiguous
  on all three points and none occurred.

**Outcome.** SUPPORTED by trace: `SELECT key, tx_id, doc_json … LIMIT 1` then one `UPDATE` with
**eleven assignments** (`tx_id = now()`, nine derived columns, the whole `doc_json`) under
`IF tx_id = ?`, in **10 of 10** traced operations; statement counts `insertOne` = 1,
`updateOne` = 2, `deleteOne` = 2. At RF = 3 each conditional runs a full three-replica Paxos round,
traced message by message, coordinator p50 13.738 ms for `UPDATE … IF` against 6.582 ms for a
non-conditional `SELECT`. Sources: `data/raw/findings.json`, `data/raw/findings_rf3.json`,
`data/raw/probe4_rf3_supplementary.json`. **Not refuted.**

**Reserves.** (a) The **unmodified harness returned INCONCLUSIVE** on the consistency claim at
RF = 3, with `consistency_levels_observed = {}` over 200 traces, in both passes; the SUPPORTED verdict
rests on a supplementary per-statement query written by the measurer — audit finding I2 applies
directly. (b) `probes/README.md` gap 8 records that an unpublished archive file,
`probe4_traced.json`, carries `LOCAL_QUORUM` 70 **alongside `ONE` 42 and `LOCAL_ONE` 2** over 200
traces examined, where M4 is published as "70 of 70 statements at `LOCAL_QUORUM`" (70 of 70 on the
*target table*). (c) The three dc1 replicas share one host, so the Paxos magnitude is measured where
consensus hurts least (challenge C3). (d) M6's evidence is a transcribed log, with no raw file.

---

### RQ3 — Does the cost of a constant single-field mutation grow with indexed content the mutation never touches, and is the driver the *number* of indexed fields or the *volume* of indexed bytes?

**Hypothesis H3.** If H2 holds, the cost of a `$set` is charged against the whole row, so it grows
with the document's indexed content and not with what changed. The article under verification claims
the opposite in its step 4 ("maintain the indexes covering the fields that changed"), which makes
this the one place where the dossier and its own source article make incompatible predictions.

**Operationalisation.** Client-observed latency of `updateOne` at fixed mutation and growing ballast,
minus the growth of a **same-size read** of the same document. The read control is what converts a
latency curve into an argument: without it, a growing curve is equally consistent with the wire cost
of transferring a larger document. The substitution still bundles the tier and the network — see
RQ5 and RQ6.

**Procedure.**
- Campaign 1 (M3): variant A (ballast *not* indexed) and variant B (indexed chunks ≤ 8000 B, 2/5/17
  fields at 8/32/128 KB), one scalar `$set` held constant, n = 30 per size after 5 warm-ups, two
  passes, RF = 1, memtable-resident.
- Campaign 3 (M10): the same variant B against a **proven** disk-regime dataset — 6 491 369 675 B
  (6.05 GiB) on disk against a 2 048 MiB memtable budget, 40 SSTables after a major compaction, 78
  compactions crossed, caches invalidated.
- Campaign 3 (M11): the two terms separated. Series S1 holds field count at 16 and varies bytes per
  field 512 → 8000; series S2 holds indexed volume at 64 KiB and varies field count 9 → 128; an
  internal control (16 × 4096 B) sits in both series.

**Falsification criteria.**
- **[PRE]** `probes/verify_storage_claims.py:380,385` — p50 growth ≥ 1.6 returns SUPPORTED; **growth
  ≤ 1.2 returns CONTRADICTED**, with the in-code text that the read-modify-write account "is not
  supported on this build and should be withdrawn".
- **[PRE — record-only]** The **read-control rule**, recorded in
  `data/raw/findings.json → findings[2].read_control_pre_registered_rule` and attributed there to
  "User protocol step 3": *if the read curve has the same slope as the update curve, the growth is
  wire cost and the probe is INCONCLUSIVE.* This rule is **not** cited by file and line, because no
  published probe emits it and the protocol it names is not in this repository (§5.1). Under §6 it
  should be discounted the way a `[POST]` criterion is — the verdict it returned stands, but it is
  not evidence that the result could have come out the other way.
- **[PRE]** `probes/probe_field_vs_byte.py:320` (`verdict_rule`, echoed into
  `data/raw/findings_fieldbyte.json`): S2 endpoint ratio ≤ 1.15 → bytes dominate; ≥ 1.5 → field
  count is an independent driver; between → INCONCLUSIVE.

**Outcome — and this is the rule that bit hardest.** The harness's raw verdict on variant A was
SUPPORTED (growth ×1.92). The read-control rule **overrode it to INCONCLUSIVE**, because update
growth ×1.92 / ×2.21 is not separable from same-size read growth ×1.86 / ×1.94
(`data/raw/findings.json`). The same rule returned INCONCLUSIVE again at RF = 3 (×1.72 / ×1.91
against ×1.86 / ×1.85) and again in the disk regime (×1.78 against ×1.89). **Variant A is
INCONCLUSIVE in every regime in which it was run, and the dossier publishes it that way.**

Variant B, where the ballast is indexed, separates: p50 12.104 → 90.783 ms = **×7.50** across a ×128
document, against a same-size read control of ×1.56 and an `updateOne` HTTP request constant at
122–124 bytes. The article's step 4 is **CONTRADICTED**. On the byte-versus-field question, S1 fits
at r² **0.9999** with an endpoint ratio of 4.556, while S2 moves only 1.128 and 1.187 — so the byte
term dominates in direction, but **the pre-registered rule returns no clean verdict**, because the
two passes straddle its 1.15 line. Sources: `data/raw/findings.json`,
`data/raw/findings_disk_rf3.json`, `data/raw/findings_fieldbyte.json`, `data/raw/disk_state.json`.

**Was it refuted?** H3 was **not** refuted; the article's step 4 was. Two sub-claims failed their own
tests and are published as failures: variant A's latency argument, and M11's strict verdict.

**Reserves.** (a) The ×1.56 read control quoted for variant B is recorded in `control_read_B.json`,
which is in an **unpublished off-repository archive** (`probes/README.md` gap 8) — a published
number resting on a file this repository does not contain. (b) `control_read_A_run1.json`'s p50
values were transcribed from the run log because a fixed output filename let pass 2 overwrite pass 1.
(c) The 8000-byte indexed-string cap forced the chunked ballast shape, so the workload is driven by
an engine constraint rather than by any corpus. (d) M11's strict straddle sits inside the
apparatus's own resolution: `docs/STATISTICS.md` and audit finding I7 put inter-pass spread at
roughly 10–15 %, and the 1.15 threshold is a 15 % line, so that rule was **undecidable by
construction** at this n.

---

### RQ4 — Is the per-byte mutation coefficient a property of the engine, or of the cache regime it was measured in?

**Hypothesis H4.** *(This question did not exist until challenge C2 was raised against the dossier's
own campaign 3.)* If every read-modify-write probe re-reads the row it has just written, then that
read never leaves the memtable, whatever the size of the dataset around it — and the coefficient
measured is a memtable coefficient, not an engine one.

**Operationalisation.** The same variant-B latency series, with `nodetool flush` on the three dc1
nodes **before each timed update**, so the cycle's internal `SELECT` must take the SSTable read path.
The flush itself is not timed. The substitution is the same latency proxy as RQ3; what changes is the
state the proxy is taken in.

**Procedure.** `probes/rmw_postflush.py` (M15), variant B at 1/8/32/128 KB, n = 30, one pass.

**Falsification criterion [POST].** H4 would have been refuted if the post-flush growth factor had
come back at or above M10's ×5.94 — that is, if forcing the read onto SSTables had left the shape of
the cost unchanged. The probe's own `reading` string
(`probes/rmw_postflush.py:84`) offers exactly those two branches: "materially above M10's 5.94" or
"similar". **Neither branch covers what happened.** The observed ×1.52 falls *below* both, and the
published interpretation — a fixed read-path cost of roughly 90–100 ms taking over — was constructed
**after** the observation. This is the clearest case in the dossier of a rule written before a run
that did not anticipate the run's outcome, and it should not be counted as pre-registration.

**Outcome.** H4 **CONFIRMED**, at the cost of the dossier's flagship number. Post-flush: p50 107.765
→ 163.402 ms, growth **×1.52**, against ×5.94 (M10, disk dataset) and ×7.50 (M3, memtable RF = 1) —
a ×5 interval on one quantity. Source: `data/raw/rmw_postflush.json`. Every per-KiB rate in the
dossier (M3, M10, M11, M12, M13) was relabelled a memtable/cache figure, and ADR-001's action item 1
was reopened from `[x]` to `[~]`.

**Reserves.** (a) M15 inflates its own absolute: flushing before every update fragments the table
into roughly 35 small SSTables, so its ~100 ms is a fragmented worst case and the true disk-bound
value lies between the memtable figures and it. (b) The OS page cache was never dropped — no root on
the host — so "SSTable-resident" never means "platter-cold". (c) `data/raw/rmw_postflush.json`
carries **no `run_at_utc`, no host block and no `conditions` object**: the file that overturned the
headline has the thinnest fingerprint in the corpus. (d) `docs/STATISTICS.md` records that M10 and
M15 **cannot be tested at all** — `findings_disk_rf3.json` stores p50 only, `rmw_postflush.json`
stores no `min_ms` — so two of the three legs of the ×7.50 / ×5.94 / ×1.52 triangle are not open to
re-analysis by anyone.

---

### RQ5 — Where is that per-byte rate charged: in the stateless Data API tier, or in the stateful storage engine?

**Hypothesis H5.** If a substantial majority of the rate sits in the stateless tier, the cost scales
out by adding instances and the architectural criticism in the source article is largely defused; if
the majority sits in the stateful engine, it is not.

**Operationalisation — and this is where the dossier's worst construct problem lives.** "The tier's
share" is estimated three ways, and they are **three different estimands**, not three estimates of
one:

| Estimator | What it subtracts | Regime / arm layout | Tier slope | Share |
|---|---|---|---|---|
| Tier-by-arm-difference (method 1) | Client latency of a CQL arm from client latency of the Data API arm | disk regime, arms interleaved | 0.219 ms/KiB (r² 0.983) | ~29 % |
| Tier-by-trace-residual (method 2) | Coordinator-side trace duration from client latency | same run | 0.145 ms/KiB (r² 0.992) | ~19 % |
| Tier-by-slope-difference (M14) | One fitted slope from another, arms run separately | cache regime, arms separated in time | 0.0738 ms/KiB (0.7775 − 0.7037) | ~9 % |

Method 2 subtracts a strictly larger "storage" than method 1 — the campaign report says so
(`docs/campaigns/04-tier-vs-storage.fr.md`) — and M14 changes the regime *and* the arm scheduling at
the same time. The absolute numerators span 3×, so normalisation is not the whole story. With three
confounds moving together across three estimates, **the quantity is not identified by this design**,
which is a stronger and more defensible statement than the dossier's "never reconciled".

**Procedure.** `probes/probe_tier_vs_storage.py` (method 1, M12) runs the identical mutation as arm A
through `updateOne` and arm B as the same CQL statement pair against the same row, with the shredded
values read back rather than recomputed; `probes/method2_trace.py` (method 2, M12) subtracts the
coordinator duration; `probes/hcd_cql_arm.py` (M14) fits a separate CQL-direct slope in the
comparative campaign's cache regime.

**Falsification criteria.**
- **[PRE]** `probes/probe_tier_vs_storage.py:81` — `AGREEMENT_TOLERANCE = 0.25`, carrying the in-code
  comment *"methods disagreeing by more than this invalidate both"*.
- **[PRE, provenance-defective]** `RESULTS.md` M12 describes a pre-declared trigger
  `tier_dominates`, which would have replaced an article claim had it returned true. The field
  exists in `data/raw/findings_tier.json` (`VERDICT.tier_dominates: false`), **but no probe published
  in `probes/` emits it**: `probes/probe_tier_vs_storage.py:320–362` builds its record with no
  `VERDICT` key at all. The same defect affects `data/raw/comparison.json`. The trigger may well have
  been declared; this repository does not evidence it, and a reader should treat it as undeclared.

**Outcome.** The direction holds: **majority in the stateful engine, minority in the stateless tier.**
The tier does real work, not merely a network hop — the Data API container's CPU alternated between
0.52 % (arm B) and 230.33 % (arm A), median 29.73 %. But the pre-registered agreement rule
**failed**: the two methods diverge by 34.0 % at 64 KiB and 27.7 % at 125 KiB, both above the 0.25
line, and the per-size shares in `data/raw/tier_comparison.json` run as high as 39.7 %. By the
probe's own in-source rule, both methods are invalidated at the two largest sizes. The dossier's
response — publish no point value, publish a 9–29 % range and the divergence — is the right one, and
it is weaker than the rule required. Sources: `data/raw/findings_tier.json`,
`data/raw/findings_tier_method2.json`, `data/raw/tier_comparison.json`, `data/raw/comparison_v2.json`.

**Was it refuted?** H5 as stated ("the tier dominates") was refuted; the trigger returned false and
no article claim was replaced. The *quantity* is unidentified.

**Reserve that must be carried onto M14 and currently is not.** Challenge C7 charges that arm B of
`probe_tier_vs_storage.py` reuses already-shredded values and therefore never exercises the shredding
code, so its storage term is an **optimistic floor**. `probes/hcd_cql_arm.py` does exactly the same
thing — the derived values and `doc_json` are read once and hoisted out of the timed loop, then
rewritten unchanged on every repetition — and it carries M14. No document transfers C7's caveat to
M14. The consequences run **against** HCD and so cost the dossier nothing to state: if the CQL arm's
storage term is a floor, the subtraction 0.7775 − 0.7037 is an **upper bound** on the tier term, so
9 % is a ceiling rather than a point, and M14's 40× / 72× engine ratios are **lower bounds**.

**What is contested in the other direction.** `docs/STATISTICS.md` reports that all ten
`TIER-API-vs-CQL` cells overlap in support, and nine of ten `MUT-HCDAPI-vs-HCDCQL` cells overlap:
the 29 %/9 % contradiction is a contradiction between two numbers neither of which rests on a
separated comparison.

---

### RQ6 — On the single axis the source article reasons about structurally — mutating one field of a document — how does HCD compare with MongoDB, and does the comparison survive removing the Data API tier?

**Hypothesis H6.** A shredding layout that rewrites every derived column on every mutation costs more
per indexed byte than a store that rewrites the document, and the gap survives when the stateless
tier is removed — i.e. it is an engine result, not a tier artefact.

**Operationalisation.** The per-KiB slope of client-observed update latency against indexed document
size, fitted over five sizes, one arm per engine configuration. Ratios of slopes stand for "how much
more expensive". The substitution's cost is severe on the MongoDB side and the dossier says so:
MongoDB's latency is nearly flat in document size, so its slope is near zero and the ratio's
denominator is the weakest quantity in the comparison (r² 0.7809 default, 0.8794 wildcard, against
0.997 for HCD).

**Procedure.** `probes/probe_comparative.py`, run **unmodified**, over sixteen indexed fields of
512 → 8000 bytes, n = 30, two passes, both engines on the same host in the same session, durability
matched by a declared judgement (`w:"majority"` + `j:true` against `LOCAL_QUORUM` + `LOCAL_SERIAL`),
resources matched at 8 GiB / 4 vCPU per node. MongoDB is run **twice**: with nothing indexed on the
ballast, and with a `$**` wildcard index matching HCD's automatic indexing.
`probes/hcd_cql_arm.py` then adds a fourth arm driving the same mutation straight over CQL (M14).

**Falsification criteria.**
- **[PRE]** `probes/probe_comparative.py:248` — a permission gate, not a verdict rule: the record
  emits `cross_engine_comparison_permitted: false` and the ratio is not to be read unless both
  engines ran on the same host with the same series shape and repetition counts.
- **[PRE, by design]** The probe's own reporting rule: *"Report both or report neither"* — quoting the
  default arm alone overstates MongoDB's advantage, quoting the wildcard arm alone understates how
  MongoDB is deployed.
- **[POST]** H6's second half would have been refuted by the CQL-direct arm's slope falling close to
  MongoDB's, or by a large fraction of the gap disappearing with the tier. The author predicted
  exactly that in his own challenge C1 (that the honest engine-to-engine figure was ~31×).
  **His own follow-up refuted him**: removing the tier moved the slope only 0.7775 → 0.7037.

**Outcome.** MongoDB, decisively, on this axis. HCD through the Data API 0.7775 ms/KiB (r² 0.997);
MongoDB wildcard 0.0176 (r² 0.8794); MongoDB default 0.0098 (r² 0.7809) — ratios 44× and 79×.
Engine-to-engine with the tier removed: 0.7037 ms/KiB, ratios 40× and 72×. Absolute update p50 over
8 → 125 KiB: HCD 40.9 → 130.787 ms; mongo-wildcard 5.544 → 7.621; mongo-default 5.67 → 6.484.
Sources: `data/raw/comparison.json`, `data/raw/comparison_v2.json`, `data/raw/cmp_hcd.json`,
`data/raw/cmp_mongo.json`, `data/raw/cmp_hcdcql.json`. **Not refuted; the author's own deflation
challenge was.**

**Reserves, all of which must travel with the ratio.** (a) A **cache-resident** rate whose coefficient
RQ4 showed to be a memtable phenomenon. (b) The durability mapping **favours HCD** — HCD acknowledges
up to ten seconds before fsync, MongoDB waits for it — and HCD lost anyway, so correcting the
asymmetry would widen MongoDB's margin (challenge C6). (c) Closed-loop sequential single client;
nothing here concerns concurrency. (d) The HCD ring carried ~13 GiB/node of unpurged `system.paxos`,
an unquantified drag, so HCD's absolutes are a noisy ceiling. (e) **The ratios are point estimates
with no interval.** `docs/STATISTICS.md` and the r² reserve above are part of the claim, not a
footnote: the denominator is a slope substantially indistinguishable from noise, and the published
44×/79× are fitted on **pass 1 only** (`probes/probe_comparative.py:255` selects `pass1`), a
selection the repository does not otherwise declare.

---

### RQ7 — Do the three axes the source article claims *for* HCD — index freshness, point read, filtered search — actually favour it?

**Hypothesis H7.** Automatic indexing on the write path should make a document searchable at
acknowledgement and make an undeclared field filterable without index design; those are the axes on
which a shredding layout should win.

**Operationalisation.** Poll-until-found for freshness (bounded below by the client's HTTP round
trip); client-observed p50 for reads and searches. The freshness instrument **cannot** return zero,
and the dossier's verdicts respect that: "bounded below the floor", not "synchronous".

**Procedure.** `probes/probe_read_search.py` (M16) at 1 000 000 documents on both engines, 50
repetitions, same host: (A) filtered read on an **undeclared** field, (B) point read by `_id`, (C)
freshness on an ordinary secondary index. `probes/vector_freshness_rf3.py` (M7) contrasts, per cycle
and on the same first attempt, a `LOCAL_ONE` vector search against a `LOCAL_QUORUM` key read at
RF = 3. `probes/mongot_freshness.py` (M17), `probes/mongot_floor.py` (M18) and
`probes/turn_latency.py` (M19) measure the search-freshness axis against `mongot`.

**Falsification criteria.**
- **[PRE]** `probes/vector_freshness_rf3.py:129–145` — the cleanest falsification rule in the
  repository. If any cycle shows the key read (`LOCAL_QUORUM`) hitting while the vector search
  (`LOCAL_ONE`) misses on the same first attempt, the record reports **WINDOW OBSERVED** and the
  article's §4 [D] claim fails at RF = 3. If every cycle hits, the record reports **NOT DETECTABLE** —
  explicitly *"not as a refutation of the claim"*. The docstring states the hypothesis under test in
  full, before the run.
- **[PRE]** `probes/verify_storage_claims.py:318` — the campaign-1 freshness probe returns SUPPORTED
  only if the under-load p99 is below 50 ms.
- **[POST]** M16 and M17 carry **no decision rule of any kind**. Both are measurer-written, and both
  produce HCD's only two wins in the entire dossier. The criterion stated after the fact would be:
  HCD's automatic-index advantage fails if a MongoDB configured as a competent team would configure
  it answers the same query faster. **That is what happened** — and the dossier publishes it.

**Outcome — two of the three axes did not favour HCD.** Point read by `_id` went to MongoDB
(p50 0.53 ms wildcard / 0.616 ms default against HCD 10.382 ms, the Data API tier hop, ≈19.6×).
Freshness on an ordinary secondary index was a **tie**: all three arms returned the just-written
document on the first query, attempts `{1: 40}` each. Filtered search on an undeclared field split
in two: HCD's automatic SAI answered at p50 17.376 ms against a 376.698 ms collection scan on
default MongoDB (21.7×), but MongoDB **with a wildcard index** answered at p50 0.732 ms — 23.7×
faster than HCD. What HCD buys is the dispensation from index design, not speed.
Sources: `data/raw/findings_rs_hcd.json`, `data/raw/findings_rs_mongo.json`.

M7 returned **NOT DETECTABLE**: 120 of 120 cycles had the just-written vector top-1 on the first
`LOCAL_ONE` search, 0 cycles with the key-hit/vector-miss contrast, insert-to-visible p50 74.735 ms
idle / 74.406 ms loaded (`data/raw/vector_freshness_idle.json`,
`data/raw/vector_freshness_loaded.json`, `data/raw/findings_vector_rf3.json`). The window is bounded
below the ~74 ms HTTP floor, not shown to be absent — and the marker on the underlying claim was
left unchanged, because a measurement that cannot see an effect is not evidence of absence.

On search freshness HCD won in direction and then had its own margin cut down three times by its own
author: M17's `mongot` p50 1015.201 ms was the **worst phase of a periodic refresh cycle**, inflated
by a self-synchronised probe, and M18's de-synchronised measurement put it at p50 664.3 ms with a
floor of 89.1 ms and a max of 1170.2 ms; M19 then showed MongoDB's miss rate falling from 30/30 at
τ = 0 ms to **0/30 at τ ≥ 1000 ms**, which makes the advantage total below one second and moot for
the conversational-RAG turn the article invokes to justify caring about it; and a provenance check
established that the `mongot` measured is **1.75.1, edition `localDev`**, so none of those figures
is a MongoDB Atlas Search number at all. Sources: `data/raw/findings_mongot_freshness.json`,
`data/raw/findings_mongot_floor.json`, `data/raw/findings_hcd_vec_freshness.json`,
`data/raw/findings_turn_hcd.json`, `data/raw/findings_turn_mongodb.json`,
`data/raw/findings_mongot_provenance.json`.

**Was it refuted?** **Yes, on two of the three axes**, and the third was narrowed three times. This
is the question on which the dossier's own hypothesis fared worst.

**Reserves.** (a) The 21.7× is a win over a MongoDB that was **never given the index** (challenge
C12), and it is the one comparison in the dossier whose two samples **overlap**: HCD spans
[13.113, 28.697] ms over n = 50 while mongo-default spans [13.335, 863.381] ms, so the defensible
claim is *predictability*, not speed, and `docs/STATISTICS.md` puts the honest ratio interval at
[0.46×, 65.8×], containing 1.0. (b) `mongot` ran on a single-node `atlas-local`, a different
deployment from M16's three-member replica set (challenge C15). (c) MongoDB `$search` is lexical and
HCD JVector is vector — the two halves do not exercise the same path (challenge C14, D4). (d) HCD's
freshness is bounded below the ~45 ms HTTP floor, never shown to be zero (challenge C11). (e) The
premise that makes the τ ≥ 1000 ms column decisive — that an LLM turn takes 1–10 s — is an
assumption stated by the challenge author, not measured. (f) 0/30 bounds MongoDB's true miss rate
below roughly 10 %, not at zero. (g) `findings_turn_hcd.json` and `findings_turn_mongodb.json` carry
no timestamp, no host and no deployment block, and both carry the same copy-pasted `reading` string
asserting MongoDB's refresh interval **inside the HCD record**.

---

### RQ8 — What can the Data API's document model answer at all, on the aggregation and counting axis?

**Hypothesis H8.** A document API built over a shredded columnar layout may expose a narrower query
surface than a native document store, and where the surface is missing the cost is not a slower
answer but a client-side workaround.

**Operationalisation.** Two different things, and they must not be confused. The **capability**
questions are answered by the server's own response strings (`COMMAND_UNKNOWN`,
`TooManyDocumentsToCountException`, the returned count) — these are correctness observations,
independent of host, load, regime and percentile. The **cost** question is answered by
client-observed latency, with all the reserves of RQ3 and RQ6.

**Procedure.** `probes/probe_aggregation.py` and `probes/agg_cql_arm.py` over 200 000 documents
(10 categories × 20 000, fields `cat` string and `amt` double), MongoDB 8.0.32 replica set at
`w:majority` + `j:true` against HCD keyspace `cmp` at `{dc1:3}`. Four arms on the group-by axis:
MongoDB server-side `$group`; native CQL per-partition sweep; native CQL cross-partition `GROUP BY`;
HCD Data API client scan-and-aggregate.

**Falsification criteria.**
- **[PRE]** `probes/probe_aggregation.py:69` — `sums_match()`, an exactness check of every arm's
  result against a deterministic pre-computed ground truth, per category sum and per category count.
  A fast arm returning a wrong answer fails. This is a genuine pre-registered **correctness**
  criterion and it is the only one in campaign 7.
- **[POST]** H8 would have been refuted by `aggregate` or `distinct` being served, or by
  `countDocuments` returning the true cardinality. Neither happened.

**Outcome.** The Data API command allow-list contains **nineteen** commands; `aggregate`, `$group`
and `distinct` all return `COMMAND_UNKNOWN` — no server-side aggregation pipeline (M20). Exact
counting is capped: `countDocuments({})` and `countDocuments({cat:"c3"})` both failed with
`TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the server`
(M21). `estimatedDocumentCount()` answered in p50 6.875 ms and returned **0** while the collection
held 200 000 documents — not approximate, **wrong**, with nothing in the API signalling the
condition (M22). Every group-by arm was verified exact against ground truth; medians were MongoDB
`$group` 222.711 ms, native CQL sweep 2 011.399 ms, native CQL cross-partition 2 568.372 ms, HCD Data
API client scan 133 984.229 ms at n = 3 (M23). Sources: `data/raw/findings_agg_hcd.json`,
`data/raw/findings_agg_mongodb.json`, `data/raw/findings_agg_cqlref.json`. **Not refuted.**

**Reserves.** (a) The 602× must never be quoted as "HCD is 602× slower": the same engine, same host,
same corpus aggregates in ~2 s through native CQL, so the gap is an API surface — **and** reaching
the CQL path means abandoning the document model and pre-designing a table partitioned by the group
key, which is the index-design work the Data API's pitch is to avoid. Both halves are required. The
second half was withdrawn by challenge D12 and **reinstated** when D12 was found to rest on a false
premise: on a table not partitioned by the group key, its `GROUP BY` arm is refused by the engine.
(b) The HCD arm is **n = 3** (MongoDB's `$group` arm is n = 15): the repetition asymmetry is by
construction and the p95/p99 of the n = 3 arm carry no information. (c) M22's zero is itself proof
that this campaign ran in a **cache regime**, not a proven disk regime. Challenge D9 further held it
to be a cold-start property presented in the register as a property tout court; **campaign 7bis
refuted D9 on 18 September 2026** — the estimator returns 171 267 after flush and 172 132 after major
compaction against a true 200 000, so the defect is steady-state and the narrowing is withdrawn. The
cache-regime reserve itself is **discharged** by the same campaign, which re-measured axis C after
flush and major compaction at 130 127.0 ms, 2.1 % *faster* than in cache. (d) The nineteen-command
allow-list and the "no count-limit environment variable" statement are **report-transcribed**, in no
raw file. (e) `RESULTS.md` M20 describes the `COMMAND_UNKNOWN` result as a captured artefact in
`findings_agg_hcd.json`'s `structural` field; that field is a **fixed string literal** written at
`probes/probe_aggregation.py:196` and emitted unconditionally, and no probe in this repository ever
issues `aggregate`, `$group` or `distinct` against HCD. The finding is credible and the artefact
does not evidence it. (f) Campaign 7 stood outside the adversarial audit and the challenge rounds
until `docs/challenges-campagne7.fr.md` (D6–D14) was written. That pass reversed no conclusion **at
the time**; campaign 7bis then reversed three (D9's narrowing, the 46.3× ingest ratio, and the 602×'s
generality beyond ten groups), and **D12 was annulled** when its "misaligned arm" was found to be a
second query shape against the same pre-partitioned table — so the clause in reserve (a) stands.

---

## 3. What no research question here asks

Stated so that a reader does not supply the missing questions himself.

- **Nothing asks about concurrency.** Every probe is a single sequential closed-loop client. The
  title of this repository, and `CITATION.cff`, named concurrency; no measurement bears on it, and
  both have been corrected to drop the word. The article under verification still names it.
- **Nothing asks about engine work in bytes.** See §1: the construct is empty.
- **Nothing asks about a third storage layout.** Two products cannot establish a claim about a class
  of design. As it stands the dossier can say that *this* shredding implementation is expensive on
  this axis and MongoDB is not; the stronger claim its title suggests — that schema-oblivious
  shredding as a design point is expensive on this axis — is argued from M1 and M2 as a mechanism,
  not established by a comparison.
- **Nothing asks against a reference workload.** No published benchmark was run, so no number here is
  commensurable with any number outside this repository.
- **Nothing asks about a multi-host or WAN topology, a production-sized Data API tier, a
  production-edition `mongot`, a sharded MongoDB, or a genuinely page-cache-cold read.**
  `RESULTS.md` §6 lists sixteen such axes.

---

## 4. RQ → campaign → measurement → verdict → was it refuted?

"Refuted" below means *the hypothesis as stated was contradicted by the evidence*, not *the
measurement failed*. Where a pre-registered rule returned INCONCLUSIVE, that is recorded as a failed
test, not as a refutation.

| RQ | Campaign(s) | Measurements | Instrument provenance | Verdict | Was it refuted? |
|---|---|---|---|---|---|
| **RQ1** — physical layout | 1, 2, follow-up | M1, M1 (re-run), M8 | supplied, patched (M1); **no raw file** (M8) | SUPPORTED, [U] → [M]; 12 columns, 9 automatic SAI | **No.** Over-fulfilled: three columns the author did not predict |
| **RQ2** — the write path and its consistency levels | 1, 2 | M2, M4, M5, M6 | supplied, patched (M2, M4, M5); **no raw file** (M6); supplementary analysis measurer-written (M4 at RF = 3) | SUPPORTED by trace, 10/10; Paxos round observed at RF = 3 | **No.** But the unmodified harness returned INCONCLUSIVE on A5 at RF = 3, and the SUPPORTED rests on measurer-written analysis (audit I2) |
| **RQ3** — cost driver: unchanged indexed content, bytes or fields | 1, 3 | M3, M10, M11 | supplied, patched (M3, M10); supplied, **unmodified** (M11) | Article's step 4 **CONTRADICTED**; bytes dominate in direction | **H3 no; the source article yes.** Two sub-tests failed their own rules: variant A INCONCLUSIVE in every regime; M11's strict verdict straddles its own 1.15 line |
| **RQ4** — is the coefficient a regime artefact? | challenge C2 → M15 | M15 (against M3, M10) | **measurer-written** | C2 **CONFIRMED**: ×7.50 → ×5.94 → ×1.52 | **Not refuted — and it refuted the dossier.** The flagship coefficient became a memtable figure; ADR-001 action 1 reopened |
| **RQ5** — where the rate is charged | 4, challenge C1 → M14 | M12 (methods 1 and 2), M14 | supplied, patched (M12 method 1); **measurer-written** (M12 method 2, M14) | Majority in the stateful engine; `tier_dominates` = false | **H5 refuted** (the tier does not dominate). The *share* is unidentified: 29 % / 19 % / 9 %, and the in-source 0.25 agreement rule failed at 64 and 125 KiB |
| **RQ6** — mutation against MongoDB, stack and engine | 5, challenge C1 → M14 | M13, M14 | supplied, **unmodified** (M13); **measurer-written** (M14) | MongoDB decisively: 44× / 79× stack, 40× / 72× engine | **No — and the author's own deflation challenge C1 was refuted.** Removing the tier moved the slope 0.7775 → 0.7037 |
| **RQ7** — the axes claimed for HCD | 6, 2 (M7), challenges C10 → M18, D1 → M19 | M7, M16, M17, M18, M19 | supplied, unmodified by inference (M7); **measurer-written** (M16, M17, M18, M19) | Split: MongoDB on point read (19.6×) and on declared-index search (23.7×); tie on secondary-index freshness; HCD on undeclared-field search (21.7×, supports overlap) and on search freshness (direction) | **Yes, on two of three axes.** And the one clear HCD win was narrowed three times by its own author: 1015 → 664 ms, then moot at τ ≥ 1000 ms, then `localDev` |
| **RQ8** — aggregation and counting capability | 7 | M20, M21, M22, M23 | **measurer-written**; allow-list and count-limit claims **report-transcribed** | Capability gap, not a latency race: no pipeline, count capped at 1 000, `estimatedDocumentCount()` returns 0 against a true 200 000 | **No.** M22 is a silent wrong answer — a correctness result, independent of host, load, regime and percentile |

**Two pieces of book-keeping the table makes visible.** First, **no research question in this dossier
was refuted by evidence favourable to HCD.** Every reversal in the corpus either cut against HCD
(RQ7) or cut against the dossier's own published magnitude (RQ4, RQ5, and M17 → M18). Second, the
questions with the weakest instrument provenance — RQ4, RQ5's second half, RQ7, RQ8 — are, with the
exception of `probe_field_vs_byte.py` and `probe_aggregation.py`'s exactness check, the same
questions with no pre-declared decision rule. Two independent safeguards fail on the same
measurements, and §5 quantifies that.

---

## 5. Pre-registration: what is evidenced, and what is not

`METHODOLOGY.md` §1 states the cardinal rule as a fact: *"The protocol was fixed before the numbers,
and was never retuned to make the numbers converge on the article's claims"*, and adds that *"Each
probe carried its decision rule in its own source before it ran"*. The first clause is partly
evidenced and partly testimonial. The second is **false as a generalisation**, and this section says
so with the same directness the dossier applies to everything else.

### 5.1 What the repository does evidence

**Eight published probe sources carry a decision procedure — eleven rules in all, since
`verify_storage_claims.py` carries four of them — and a twelfth rule in the table below lives only in
an output record (`data/raw/findings.json`), in no source at all. Several of these rules returned
answers the author did not want.**

*Reconciliation with §5.2, which counts more strictly.* Five of these eight sources are among the six
probes §5.2 credits with a verdict or threshold construct (the sixth, `verify_storage_claims_rf3.py`,
re-runs the same four rules at RF = 3 and is represented in the table by its campaign-1 twin). The
other three — `probe_comparative.py`, `probe_aggregation.py` and `mongot_floor.py` — carry a
permission gate, an exactness check and a classification heuristic respectively, and §5.2 counts all
three among the **ten** probes that carry no pre-declared verdict rule. Eight is therefore a count of
sources carrying *some* published decision procedure; the stricter number, and the one that governs
the pre-registration claim, is **six of sixteen**.

| Instrument | Rule, where it lives | Did it bind? |
|---|---|---|
| `verify_storage_claims.py:231` | ≥ 6 of 9 predicted column names → SUPPORTED; none → CONTRADICTED | Yes — returned SUPPORTED on 9/9 |
| `verify_storage_claims.py:318` | under-load p99 < 50 ms → SUPPORTED, else INCONCLUSIVE | **Yes, adversely** — 59.178 / 53.849 ms → INCONCLUSIVE, published |
| `verify_storage_claims.py:380,385` | p50 growth ≥ 1.6 → SUPPORTED; ≤ 1.2 → CONTRADICTED | Yes — raw SUPPORTED at ×1.92, then overridden by the read control |
| `verify_storage_claims.py:427` | `LOCAL_QUORUM` observed → SUPPORTED, else INCONCLUSIVE | **Yes, adversely at RF = 3** — `consistency_levels_observed = {}` → INCONCLUSIVE in both passes |
| Read-control rule, `data/raw/findings.json → findings[2].read_control_pre_registered_rule` **[record-only, not instrument source — see the note below]** | Update growth must be separable from same-size read growth, else INCONCLUSIVE | **Yes, adversely, in all three regimes** — variant A INCONCLUSIVE at RF = 1, RF = 3 and on disk |
| `probe_field_vs_byte.py:320` (`verdict_rule`, echoed into the raw record with `verdict_per_pass`) | S2 endpoint ratio ≤ 1.15 / ≥ 1.5 / between | **Yes, adversely** — 1.128 and 1.187 straddle the line; strict verdict INCONCLUSIVE, published |
| `probe_tier_vs_storage.py:81` | `AGREEMENT_TOLERANCE = 0.25`, "methods disagreeing by more than this invalidate both" | **Yes, adversely** — 34.0 % and 27.7 % divergence at 64 and 125 KiB |
| `vector_freshness_rf3.py:10–22, 129–145` | Hypothesis stated in the docstring; WINDOW OBSERVED / NOT DETECTABLE / MIXED branches | Yes — returned NOT DETECTABLE, explicitly *"not a refutation"* |
| `probe_comparative.py:41, 248` | `cross_engine_comparison_permitted` gate on same host, same series shape, same repetitions | Yes — returned true; a permission gate, not a verdict rule |
| `probe_aggregation.py:69` | `sums_match()` exactness against pre-computed ground truth | Yes — every arm verified exact |
| `disk_regime_driver.py:25–33, 223` | Four proof obligations; `disk_bound = all(checks)`; the driver refuses to report success otherwise | Yes — and it **refused a run**: a constant-byte ballast compressed ~120:1 and failed the on-disk-size proof, which is why the incompressible-payload fix exists |
| `mongot_floor.py:69–74` | `near_zero and spread > 0.5·max` → REFRESH INTERVAL, else FIXED PIPELINE DELAY | Yes — but the dossier's own D5 records that this is the author's judgement, not a test, and D3 records that the emitted verdict's prose ("floor near 0") contradicts the same record's `min_ms` of 89.1 |

**What follows from that twelfth row being a record and not an instrument.** The read-control
rule is marked `[record-only, not instrument source]` because it lives only in the output record:
`grep -rn "pre_registered" probes/` returns nothing, no published probe emits
`read_control_pre_registered_rule`, the block is hand-assembled, it attributes the rule to a "User
protocol step 3" this repository does not contain, and its own `read_source` field records that run
1's distribution JSON was overwritten by run 2. That is the test §5.2 item 4 applies to the two
`VERDICT` blocks, and it does not become inapplicable because this record's verdict is adverse to
the author. **The verdict is unaffected and is not softened here**: variant A is published
INCONCLUSIVE at RF = 1, RF = 3 and on disk, in `RESULTS.md` M3 and M10 and in RQ3 above, and the
harness's raw SUPPORTED is not restored. What is withdrawn is the claim that the rule governing it
is *evidenced* as pre-registered; it should be read as **declared by the author and not
independently evidenced by this repository**. The row is kept in view rather than deleted, because
deleting it would remove an adverse verdict from the table; it is not counted among the eight
sources, and no criterion resting on it may be marked `[PRE]` (see the marker list in §2 and RQ3).

**The instrument patches are declared and partly diffable.** Five mechanical fixes are listed in
`METHODOLOGY.md` §1 and `probes/README.md`, nine in-code `Mechanical fix` comments sit in four
files, and `probes/verify_storage_claims.py.orig` is a genuinely retained original whose diff can be
machine-checked. None of the patches touches a size, a threshold, a repetition count, a warm-up
count or a verdict rule — which is the property to check, and it checks out for the one diff that is
independent evidence.

**Adverse verdicts were kept and published.** That is the strongest protection against selective
reporting in this repository, and it is stronger than most submitted work carries.

### 5.2 What the repository does **not** evidence

**1. No timestamped protocol document exists prior to any run.** The git history begins at
2026-09-18 10:03:02 UTC and runs to 11:00:25 — six commits, all **after** the last measurement run
stamped in `data/raw/` (`findings_agg_cqlref.json`, 2026-09-18T09:33:35). There is no tag, no hash
manifest, no external deposit, and no artefact anywhere that orders a protocol before a datum.

**2. File times carry no ordering information either.** Every `.py` file in `probes/` carries the
identical mtime **2026-09-18 09:35:57** — a single import 2.5 minutes after the last run. The
repository applies precisely this test against itself elsewhere: `probes/README.md` rejects
`probe_tier_vs_storage.py.orig` as independent evidence *because its mtime (10:03) is later than the
patched probe it is supposed to predate (09:35)*. The same instrument, turned on the pre-registration
claim, returns nothing. The claim should be stated as **declared by the author and not independently
evidenced by this repository**.

**3. The blanket sentence is false.** Of the sixteen probes in `probes/`, **six** carry a verdict or
threshold construct. The ten that carry none include every instrument that produced a
post-campaign-4 headline:

| Probe | Carries | Backs |
|---|---|---|
| `hcd_cql_arm.py` | no decision rule | M14 — the 40× / 72× engine figure that refuted challenge C1 |
| `rmw_postflush.py` | a two-branch `reading` string that does not cover the outcome | M15 — the ×1.52 that demoted the flagship coefficient |
| `probe_read_search.py` | no decision rule | M16 — HCD's 21.7 × win |
| `mongot_freshness.py` | no decision rule | M17 — HCD's freshness win |
| `turn_latency.py` | no decision rule | M19 |
| `method2_trace.py` | no decision rule | M12, half |
| `probe_aggregation.py` | an exactness check only | M20–M23 |
| `agg_cql_arm.py` | no decision rule | M23's CQL arms |
| `probe_comparative.py` | a permission gate, not a verdict rule | M13 |
| `mongot_floor.py` | a classification heuristic the dossier itself flags (D5) | M18 |

**The pattern matters and is not flattering.** The probes with no pre-declared rule are, with the two
noted exceptions, the same probes audit finding I2 classifies as measurer-written — including
**both** measurements in which HCD comes out ahead. Two independent safeguards, pre-registration and
instrument independence, fail on the same set of measurements. Neither the provenance register nor
the methodology says this, and it is the sharpest thing that can be said against the dossier's
epistemic ordering.

**4. Two decisive verdict objects are not instrument output.** `data/raw/comparison.json` and
`data/raw/findings_tier.json` each carry a top-level `VERDICT` block that **no probe published in
`probes/` emits** — verified by reading the record construction at
`probes/probe_tier_vs_storage.py:320–362` and `probes/probe_comparative.py:264`, and by the fact
that `comparison_v2.json`, written by the same code path, has no such block. No figure inside either
block is unsupported by the file's own arms, so this is a **provenance and labelling defect, not
fabricated data** — but `RESULTS.md` M12 calls `tier_dominates` a "pre-declared trigger", and this
repository does not evidence that it was declared anywhere. `data/raw/findings_vector_rf3.json` is
likewise a hand-assembled summary rather than probe output, though in its case the rule that produced
its verdict **is** in the published source.

**5. One published interpretation is post hoc and is presented as pre-registered.**
`probes/rmw_postflush.py:84` offers two readings — growth "materially above M10's 5.94", or
"similar". The observed ×1.52 is below both. The account the dossier publishes (a fixed ~90–100 ms
read-path cost taking over) was constructed after the observation, and `METHODOLOGY.md` §1 lists
M15's campaign under the pre-registered-rule heading without saying so.

### 5.3 The distinction that matters most: confirmatory versus exploratory

**Campaign 1 and its RF = 3 repeat (campaign 2) are confirmatory.** They tested claims stated in
advance (A2, A3, A4, A5a, A5b, F, L, P), with a harness the measurer did not write, carrying rules in
its own source, and they returned verdicts against the author that were published unchanged.

**Campaigns 3 through 7 are exploratory, and reactive.** Each exists *because of* what the previous
one found:

| Campaign | Exists because | Chronology (`run_at_utc`) |
|---|---|---|
| 3 — disk regime, field vs byte | Campaign 1 grew field count and byte volume **together** and could not separate them; and its ×7.50 was memtable-only | 2026-09-17T21:29 → 21:36 |
| 4 — tier vs storage | Campaign 3 produced a rate, and where that rate is charged changes the architectural reading | 2026-09-17T22:31 → 22:34 |
| 5 — HCD vs MongoDB | Campaign 4 located the rate; the comparison is the natural next question | 2026-09-18T06:12 → 06:14 |
| M14 — CQL-direct arm | Answers the author's own challenge **C1**, raised against campaign 5's own headline | 2026-09-18T06:31 — **17 minutes after** `comparison.json` |
| M15 — post-flush RMW | Answers challenge **C2** | not stamped |
| 6 — freshness, read, search | Answers challenge **C9**: campaign 5 measured only the axis where HCD was expected to lose | 2026-09-18T07:17 → 07:45 |
| M18 — `mongot` floor | Answers challenge **C10** against campaign 6's own headline | 2026-09-18T08:05 |
| M19 — turn-latency sweep | Answers meta-challenge **D1** against M18 | not stamped |
| 7 — aggregation | The remaining untouched axis | 2026-09-18T09:09 → 09:33 |

**Reactive is not confirmatory.** Each of those campaigns chose its hypothesis after seeing the
previous result, and several chose the arm that would test the author's own most recent claim. That
is good exploratory practice and it is the reason the dossier caught its own errors; it also means
that for campaigns 3–7 there is no protection against the degrees of freedom that matter — which
arms to run, at which sizes, in which regime, and when to stop. The axis set itself accreted this
way, which is why the ten-axis scoreboard in `README.md` and `RESULTS.md` §1 aggregates
author-chosen, sequentially added, non-independent axes (and, in one case, the same HCD measurement
of p50 17.376 ms counted once for HCD and once against it).

**What this costs, precisely.** Not the direction of any result: a ×40 gap does not arise from
analytic flexibility, and a `COMMAND_UNKNOWN` does not arise from it at all. What it costs is the
right to treat the *magnitudes* as tested rather than estimated, and the right to treat the axis
scoreboard as a summary statistic. Both are things this dossier already declines to claim elsewhere;
this section only makes the reason explicit.

### 5.4 What a future campaign would have to do

1. Commit and tag the protocol — questions, hypotheses, arms, sizes, n, stopping rule and verdict
   thresholds — **before the first run**, and publish the tag's hash.
2. Emit the decision rule from the instrument into the record, as `probe_field_vs_byte.py` already
   does, so that the rule and the data it adjudicated travel together in one file.
3. Persist the per-observation series alongside the summary (see `docs/STATISTICS.md` §5), so that
   the rule can be re-applied by someone else.
4. State, per measurement, whether it is confirmatory or exploratory, and never let an exploratory
   arm inherit the epistemic status of the confirmatory campaign it grew out of.
5. Ship a checksum manifest for `data/raw/`, so that "byte-identical to the run" becomes a claim a
   reader can check rather than one he must accept.

---

## 6. How to use this document

- A claim in `RESULTS.md` should be read against the RQ it answers, not on its own. The RQ carries
  the operationalisation, and the operationalisation carries the substitution cost.
- A **falsification criterion marked [PRE]** is evidence that the result could have come out the
  other way. A criterion marked **[POST]** is not; it is an after-the-fact statement of what would
  have counted as "no", and it should be discounted accordingly.
- Where an RQ's answer rests on an instrument with no pre-declared rule **and** measurer-written
  provenance, both discounts apply at once. §4's provenance column and §5.2's table identify every
  such case.
- No magnitude in this document may be quoted without the regime and scope reserves attached to it
  in its RQ. `RESULTS.md`'s eight reading rules and `docs/STATISTICS.md` §6 state the specific
  misquotations this dossier is most likely to suffer.

---

*Related work and positioning are deliberately absent from this document: it states the design, not
the field it sits in. This repository currently contains no scholarly references at all, which is a
separate and open defect.*
