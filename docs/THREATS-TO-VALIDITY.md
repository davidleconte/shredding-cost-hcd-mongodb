# Threats to validity

A classification of every adversarial finding this repository already holds, under the four-way
taxonomy used in empirical research: **construct**, **internal**, **external** and **statistical
conclusion** validity.

This document contains **no new measurement and no new finding**. It is an index and a
re-classification. Every entry below is already written down somewhere in this repository, in
French or in English, and every entry names where. Where this document says something the source
documents do not, it says so explicitly and marks it — see §9, which is the list of threats that
no existing identifier carries.

**Reading order.** If you have arrived from `docs/audit-adversarial.fr.md` or
`docs/challenges.fr.md` and want to find one finding, go to the concordance in §7. If you are
assessing coverage, go to §9. If you want the short answer to "what most constrains what this
dossier may claim", go to §10.

**Sources indexed here**

| Register | Identifiers | Source |
|---|---|---|
| Integrity audit | I1–I9, and one unnumbered parent finding | [`docs/audit-adversarial.fr.md`](audit-adversarial.fr.md) (French) |
| Challenge rounds 1–3 | C1–C15, D1–D5 | [`docs/challenges.fr.md`](challenges.fr.md) (French) |
| Challenge round 4 (campaign 7) | D6–D14 | [`docs/challenges-campagne7.fr.md`](challenges-campagne7.fr.md) (French) |
| "What this repository cannot tell you" | relabelled **L1–L11** here | [`LIMITATIONS.md`](../LIMITATIONS.md) §5 |
| Provenance gaps in the instrument register | relabelled **G1–G8** here | [`probes/README.md`](../probes/README.md) "Gaps in this register" |
| Axes never measured | 16 rows, referenced as a block | [`RESULTS.md`](../RESULTS.md) §6 |
| Statistical re-analysis | §2, §3, §4 | [`docs/STATISTICS.md`](STATISTICS.md) |
| Research questions and construct table | RQ1–RQ8 | [`docs/RESEARCH-DESIGN.md`](RESEARCH-DESIGN.md) |

`L1–L11` and `G1–G8` are **this document's labels** for entries that the source documents publish
as unnumbered bullets. They are introduced so that the coverage argument in §9 can be checked; they
are not audit identifiers and must not be quoted as though they were.

---

## 1. The taxonomy, and the rule used to assign a finding to a class

The four classes are the standard ones, stated here in the terms this dossier needs.

**Construct validity** — does the quantity that was measured stand for the thing that was claimed?
A construct threat is present whenever the operational definition and the published label denote
different things: client HTTP latency published as "write cost"; `attempts = 1` published as
"synchronous"; a dataset resident on disk published as "a disk regime"; a 1 000-document refusal
published as "cannot count"; one `GROUP BY` shape published as "aggregation".

**Internal validity** — could something other than the stated cause have produced the observed
effect? Shared-host load from other tenants, a 13 GiB `system.paxos` residue, an instrument written
by the person whose claim it adjudicates, a flush protocol that fragments the table it then reads,
a probe that phase-locks onto the commit cycle it is measuring.

**External validity** — to what does the result generalise? One host, one build of each engine, no
multi-host topology, no WAN, no concurrency, no sharding, a search tier its own vendor labels
`localDev`, a corpus of 200 000 rows on ten partitions.

**Statistical conclusion validity** — is the inference from the data to the claim sound? No
intervals, no tests, *n* = 3 on a headline arm, closed-loop probes whose upper percentiles are not
tails of anything, ratios of medians published as effect sizes, and — the defect that dominates all
the others — per-observation series that were never persisted, so that no interval can ever be
computed by anyone. This class is developed quantitatively in
[`docs/STATISTICS.md`](STATISTICS.md); this document classifies and cross-references, it does not
duplicate.

**Assignment rule.** Each identifier is assigned exactly one **primary** class — the validity it
threatens *first*, in the sense that the other threats it raises are consequences of that one — and
any number of **secondary** classes. Where the primary assignment is arguable, the table carries
the reason, so that a reader who disagrees can re-file it and see what changes. Nothing is assigned
to two primaries: a register in which every finding threatens everything is not a taxonomy.

**A note on the boundary between construct and internal validity**, because this dossier sits on it
repeatedly. When a regime changes the *value* of a quantity, that is an internal threat (a
confound). When a regime change shows that there is no single value to speak of, that is a
construct threat (the quantity was never well-formed). Finding I4 is the second kind, and §10
argues that this is the most constraining thing in the dossier.

---

## 2. Two severity axes, and why one of them is new

### 2.1 The inherited grade: ⭑ and ⭑⭑

The audit and the challenge documents grade some findings ⭑ or ⭑⭑. `LIMITATIONS.md` line 57 states
the whole of what is known about that rubric: *"Severity is the audit's own: ⭑⭑ is the higher
grade."* **No criteria are given at the source, and none are invented here.** The grades are
reproduced in §7 exactly as the source documents carry them, and where a finding carries no star,
the cell is empty rather than filled by inference.

### 2.2 The consequence grade, defined here

A uniform caveat is functionally a blanket disclaimer: a reader who cannot tell a reserve that
destroys a claim from one that merely narrows it learns to skip both. This document therefore adds
one axis, and defines it:

| Grade | Meaning | Test |
|---|---|---|
| **VOIDS** | The claim as published cannot be stated. Not "approximately right": wrong as worded. | Would a correction of this threat change the sentence's truth value, not only its error bars? |
| **BOUNDS** | The direction survives; the magnitude as published does not. | Does the threat move the number without moving the sign? |
| **SCOPES** | Both direction and magnitude survive **inside a narrower population** than the claim addresses. | Does the threat leave the result intact and shrink the set of situations it covers? |

The grade is this document's, not the audit's, and it is derived from what each source document
itself concludes — never from a fresh judgement about the measurement. Where a source records a
resolution that removed the threat, the grade describes the **residue after the resolution**, and
the resolution is named.

---

## 3. Construct validity

The emptiest cell in the source registers when they were written, and the fullest here — because
most of the findings the dossier records as *contradictions* or as *instabilities* are, on
inspection, disagreements between a label and an operational definition.

| ID | The threat, in one sentence | Grade | Secondary | Source |
|---|---|---|---|---|
| **I4** ⭑⭑ | "Cost per indexed KiB" names no stable quantity: the same measurement is ×7.50 (memtable, RF 1), ×5.94 (disk-regime dataset, RF 3) and ×1.52 (SSTable read path). | **VOIDS** any single rate | internal | audit I4; `LIMITATIONS.md` §2; `METHODOLOGY.md` §5 |
| **C2** | "Disk regime" denoted a *dataset* on disk, never a *read* from disk; the probed row was memtable-resident throughout campaign 3. | **VOIDS** M10's label | internal | challenges C2, **CONFIRMED** by M15 |
| **I3** ⭑ | "The tier's share" is one name over three estimators of three different quantities — bypass difference (29 %), coordinator-trace residual (19 %), slope difference in another regime (9 %). | **VOIDS** any single percentage | conclusion | audit I3; `METHODOLOGY.md` §5 |
| **C7** | M12's arm B rewrites already-shredded values and so never exercises the shredding code; the "tier" term aggregates parsing, shredding and serialisation without separating them. | **BOUNDS** — direction only | internal | challenges C7 |
| **C1** ⭑ | The 44×/79× compare *stacks* (Data API + Paxos against a native driver), not storage engines. | **BOUNDS**; residue after M14 | — | challenges C1, **partly REFUTED** by M14 (40×/72× engine-to-engine) |
| **C15** | Two different MongoDB deployments in one campaign, and the read axis was never corrected for the tier the way the mutation axis was. | **BOUNDS** the ~19.6× read gap | external | challenges C15; `LIMITATIONS.md` I8 |
| **C11** | `attempts = 1` was published as "synchronous, zero lag"; it means "found on the first query", and that query arrives ~45 ms after the write. | **VOIDS** "zero" | conclusion | challenges C11 |
| **C12** | The 21.7 × undeclared-field result was read as engine speed; the construct it actually measures is dispensation from index design. | **VOIDS** the engine-speed reading | — | challenges C12 |
| **C13** | "Freshness" was claimed where **search-path** freshness was measured; on an ordinary secondary index the two engines tie. | **SCOPES** to `$search`/`$vectorSearch` | — | challenges C13 |
| **C14** / **D4** | HCD **vector** (JVector) against MongoDB **text** (`$search`): the two halves do not exercise the same path. | **SCOPES** — architectural, not like-for-like | external | challenges C14; D4 records it unresolved |
| **D3** | The mongot distribution has a **fixed ~89.1 ms floor**, so "refresh interval, floor ~0" mis-models it; the honest model is fixed ingestion plus a refresh phase. | **BOUNDS** (and *strengthens* the direction) | conclusion | challenges D3 |
| **D13** ⭑ | The 46× ingest asymmetry confounds a **documented 100-document `insertMany` ceiling** (2 000 round trips against MongoDB's 20) with per-document shredding cost; one batch size per engine was tried, so nothing separates them. | **VOIDS** "HCD ingests 46× slower" | internal | campaign-7 challenges D13 |
| **D14** | "Aggregation" was operationalised as exactly one query shape: `GROUP BY` on a ten-group key, `SUM` of a double, no filter, no sort, no join, uniform corpus. | **SCOPES** M23; does **not** touch M20 | external | campaign-7 challenges D14 |
| **D8** ⭑ | The 1 000-document count ceiling is a **documented** mechanism, not a discovery — and the measurement bounds the documentation, since the probe requested `upper_bound = 400 000` and the server ignored it. Marker moves [M] → [D] for the mechanism, [M] stays for the value. | reclassification; **BOUNDS** the novelty claim | external (the page consulted is HCD 1.2, not 2.0.6) | campaign-7 challenges D8 |
| **I9** ⭑ | Both headline magnitudes on the HCD-favourable axis are artefacts of configuration or of a measurement floor (the cluster C10 + C11). | **VOIDS** both magnitudes as stated | external | audit I9 |
| **I8** ⭑ | The comparison is never truly matched: a ring plus a stateless tier plus a Paxos round against a driver and a mongod, and two different MongoDB deployments across campaigns 5–6. | **BOUNDS** every cross-engine multiplier | internal | audit I8 |

**Three consequences of this table that the source registers do not draw.**

1. **I3 has two halves, and the analysis below absorbs only the first.**

   *The first half is an identification problem.* Three estimators are reported as three estimates
   of one estimand. Method 1 is a difference of two client-observed latencies; method 2 subtracts a
   coordinator-internal duration from a client latency, which — as the campaign-4 report itself
   explains — subtracts a strictly larger "storage"; M14 is a difference of two regression slopes
   taken in another regime with separated rather than interleaved arms. The absolute tier slopes
   are 0.219, 0.145 and 0.0738 ms/KiB, so the disagreement is in the numerator as well as in the
   ratio, and normalisation is not the whole story. With regime, arm scheduling and estimator all
   moving together, the quantity is **not identifiable from this design** — for that half, a
   stronger and more defensible statement than "never reconciled". What survives is the direction,
   which all three agree on: the majority of the rate lives in the stateful engine.
   ([`findings_tier.json`](../data/raw/findings_tier.json),
   [`findings_tier_method2.json`](../data/raw/findings_tier_method2.json),
   [`comparison_v2.json`](../data/raw/comparison_v2.json).)

   *The second half is a use-of-evidence charge, which this document neither weakens nor absorbs.*
   The source states it and it stands as stated: the narrative used **29 %** to deflate the engine
   ratio to ~31×, then **9 %** to correct that deflation to 40× — each use declared, the value
   changing with the need (audit I3; [`LIMITATIONS.md`](../LIMITATIONS.md) §I3). Non-identifiability
   is a fact about the **design**; value-switching is a fact about the **argument built on it**, and
   only the second is unfavourable to the author. The first does not excuse the second, and the
   source's own heading for I3 — *contradiction interne non résolue* — is not retracted here.

2. **C7's caveat belongs to M14 and is not attached to it anywhere.** C7 charges that
   `probe_tier_vs_storage.py`'s arm B reuses already-shredded values and therefore never exercises
   the shredding code, making its storage figure an optimistic floor. `probes/hcd_cql_arm.py` does
   the same thing — the derived values and `doc_json` are read once and hoisted out of the timed
   loop, and every warm-up and repetition rewrites those same constants — and it carries M14, the
   40×/72× engine-to-engine ratio and the 9 % tier share that refuted C1. The direction of the
   resulting bias runs **against HCD**: if the CQL arm's storage term is an optimistic floor, the
   subtraction 0.7775 − 0.7037 is an *upper* bound on the tier term, so 9 % is a ceiling rather
   than a point, and 40×/72× are lower bounds. Stating this costs the dossier nothing and is
   required by its own symmetry rule.

3. **The construct named in the repository's title is carried by three non-equivalent quantities**
   — client wall-clock around a driver call, coordinator duration from `system_traces.sessions`,
   and engine work (bytes written, write amplification, CPU), the last of which is measured
   nowhere. **No adversarial identifier carries this**, and I4 is its consequence rather than its
   statement. [`docs/RESEARCH-DESIGN.md`](RESEARCH-DESIGN.md) §1, written in the same documentation
   pass as this file, now states the operational definitions in a construct table; §9, X1 records
   what remains open after it.

---

## 4. Internal validity

| ID | The threat, in one sentence | Grade | Secondary | Source |
|---|---|---|---|---|
| **I1** ⭑⭑ | One shared QEMU VM at load average 14–16 throughout, carrying Presto, streaming and Jupyter; ring state mutated between campaigns (`system.paxos` 0 → 13 GiB per node; twenty SAI indexes dropped and recreated six times). | **BOUNDS** every absolute latency (noisy ceiling) | external | audit I1 |
| **I2** ⭑⭑ / **C5** | The measurer wrote five of the instruments — `method2_trace.py`, `hcd_cql_arm.py`, `rmw_postflush.py`, `mongot_freshness.py`, `probe_read_search.py` — which carry M12 (half), M14, M15, M16 and M17, **including both measurements in which HCD wins**; supplied harnesses were additionally patched. | **BOUNDS**; see §10.3 | conclusion | audit I2; challenges C5; `probes/README.md` gap 6 raises the true count to **seven** (`mongot_floor.py`, `turn_latency.py`) |
| **I6** ⭑ / **C8** | Campaigns 4–6 ran on a ring carrying 6–13 GiB per node of unpurged `system.paxos` (`paxos_state_purging = legacy` does not reclaim on compaction); the pressure was never quantified or subtracted. | **BOUNDS** HCD's absolutes | — | audit I6; challenges C8 |
| **C6** | Durability was matched by a judgement that favours HCD: MongoDB `j:true` waits for the journal fsync, HCD's `commitlog_sync periodic 10 s` acknowledges before it. | **BOUNDS** — and *reverses*: HCD was given the advantage and lost by 44× | — | challenges C6; audit I8 |
| **C10** ⭑ (mechanism) | The M17 probe **phase-locked onto the commit cycle it was measuring**: each cycle began just after a commit, so every write waited close to a full interval. | **VOIDS** M17's 1015.201 ms as a typical lag | conclusion | challenges C10, **CONFIRMED**; corrected by M18 (p50 664.3 ms) |
| **M15's own method** (unnumbered) | Flushing before every update creates one SSTable per flush — up to ~35 small SSTables merged per `SELECT` — a fragmentation normal compaction would not leave, so the ~100 ms absolute is inflated by the instrument. | **BOUNDS** the ×1.52 absolute | construct | declared in `probes/rmw_postflush.py`, in challenges C2's resolution, and in `LIMITATIONS.md` I4 |
| **L6** | The physical storage class was never established: a QEMU virtual SCSI device on ext4, `rotational=1` being the QEMU default rather than evidence of media, no `smartctl`, no root. | **BOUNDS** every I/O-sensitive figure | external | `LIMITATIONS.md` §5 |
| **L7** | The OS page cache was never dropped (no root). "SSTable-resident" never means "cold". | **BOUNDS** every regime claim | construct | `LIMITATIONS.md` §5; every raw record's `page_cache_note` |

### 4.1 Evidence-chain threats (G1–G8)

`probes/README.md` publishes the holes in its own instrument register. They are internal-validity
threats of a particular kind: they do not concern whether the effect had another cause, but whether
the published number can be attributed to any published instrument at all.

| Label | Gap | Consequence |
|---|---|---|
| **G1** | `probe3_variant_b.py` is named by ADR-001 as an instrument of M10 and is not in the repository; it survives in the withheld archive of G8. | M10's variant-B provenance class cannot be established from this repository. |
| **G2** | The HCD half of M17 has no producing script here; `findings_hcd_vec_freshness.json` records its producer only as prose. | HCD's 44.972 ms freshness figure has no published instrument. |
| **G3** | `control_read_A_run1.json` / `_run2.json` have no producing script here; campaign 1's pass-1 read control was **overwritten by pass 2** because the filename was fixed, and its values were transcribed from the run log. | A control that arbitrates the A3 verdict is partly transcription. |
| **G4** | `tier_comparison.json` is a derived merge with no producing script; it carries M12's cardinal caveat (34.0 % divergence at 64 KiB, 27.7 % at 125 KiB). | The file that quantifies the two methods' disagreement is itself unreproducible. |
| **G5** | M20–M23 are in this repository and in no ADR register; the adversarial audit (M1–M17) never saw them. | Campaign 7 was outside every register until D6–D14 (see §9, X8). |
| **G6** | The audit counts five measurer-written scripts; `mongot_floor.py` and `turn_latency.py` post-date it by the same pattern, making the true count **seven**. | I2 understates itself. |
| **G7** | `vector_freshness_rf3.py` is classified vendor-supplied **by inference, not by diff** — no `.orig`, no declared patch. | A reader who rejects the inference must read M7 as measurer-written. M7's verdict is NOT DETECTABLE either way. |
| **G8** | Thirteen evidence files and two producing scripts exist in an off-repository archive, none byte-identical to anything published. **The ×1.56 variant-B read control quoted in `RESULTS.md` M3 is in `control_read_B.json`, which is in that archive**; and `probe4_traced.json` records `LOCAL_QUORUM` 70 *alongside `ONE` 42 and `LOCAL_ONE` 2* over 200 traces, where M4 is published as "70/70 at `LOCAL_QUORUM`". The register records no decision to withhold and no reason. | **One published figure rests on an unpublished file, and one withheld file qualifies a published verdict.** |

G8 is the gravest of the eight and is graded **VOIDS** for M3's ×1.56 as a checkable figure: a
reader cannot verify it, and a withheld file settles nothing.

---

## 5. External validity

The class the dossier covers best, because it declines to generalise almost everywhere. The entries
below are therefore mostly **SCOPES**: they do not damage results, they delimit them.

| ID | The threat | Grade | Source |
|---|---|---|---|
| **C4** | One host, one build, one shared VM: `alphadebunker`, HCD 2.0.6 (`5.0.7.0-ea50e91ba01f`), Data API v1.0.33, MongoDB 8.0.32 / 8.3.11. Nothing transposes. | **SCOPES** everything | challenges C4; `LIMITATIONS.md` L1–L2 |
| **C3** | The three dc1 replicas share one host, so Paxos is measured at sub-millisecond inter-replica latency — where consensus hurts least. | **SCOPES**; direction runs **against** HCD elsewhere | challenges C3 |
| **D2** ⭑⭑ in effect | The search-freshness axis was measured against **mongot 1.75.1, edition `localDev`** — read verbatim from `/etc/mongodb-atlas-local/mongot-edition` and from the image label ([`findings_mongot_provenance.json`](../data/raw/findings_mongot_provenance.json)). That is the edition MongoDB ships for local development, not the tier that serves Atlas. | **VOIDS** any quotation of these figures as MongoDB's, Atlas's, or the product's | challenges D2, **CONFIRMED by direct evidence** |
| **D1** ⭑⭑ | The axis itself may not matter where the article says it matters: a conversational RAG turn lasts 1–10 s, longer than the whole window. | **SCOPES** — resolved by M19 to a τ bracket | challenges D1, **CONFIRMED and quantified** |
| **C9** | Axis selection: the first five campaigns measured only the axis where HCD is expected to lose. Campaign 6 was written to close it; the selection remained the author's throughout. | **SCOPES**; also a conclusion threat to the scoreboard (§9, X5) | challenges C9 |
| **D11** | HCD's other surfaces — Data API tables, an external analytic engine on the same ring — were never tried. M20 is a finding about the Data API **as exposed by default**. | **SCOPES** M20/M23 | campaign-7 challenges D11 |
| **D9** | `estimatedDocumentCount() = 0` was read minutes after a 185.3 s load with no flush. What the estimator returns in steady state was never measured. | **SCOPES** M22 to the pre-flush window — the application hazard is unchanged | campaign-7 challenges D9 |
| **L3** | No multi-host and no WAN topology. | **SCOPES** | `LIMITATIONS.md` §5 |
| **L4** | **No concurrency.** Every probe is a single sequential client. | **SCOPES** — and see X1, since the repository title names concurrency | `LIMITATIONS.md` §5; `RESULTS.md` §6 |
| **L5** | Closed-loop probes, not a fixed offered rate, except the freshness probe (50 writes/s, slip 0.055–0.078 s). | **BOUNDS** every tail figure | `LIMITATIONS.md` §5; `STATISTICS.md` §4 |
| **L9** | Two axes never measured at all: vector ANN search quality, and the freshness of HCD's lexical path against mongot's `$vectorSearch`. | **SCOPES** | `LIMITATIONS.md` §5 |
| **L11** | Reproduction is impossible in the strict sense: the ring's state mutated across campaigns and the machine was never idle. What can be reproduced is the method. | **SCOPES** | `LIMITATIONS.md` §5 |
| **D12** (scale half) ⭑⭑ | 200 000 rows on ten partitions is a tiny coordinator-side scan. Nothing here says what happens at 10⁸ rows or 10⁵ partitions, where the cross-partition anti-pattern is real. | **SCOPES** the CQL reference arm | campaign-7 challenges D12 |

`RESULTS.md` §6 tabulates sixteen unmeasured axes and is the fuller version of this section. Three
of its rows are **not** external-validity items and are filed elsewhere here: *a genuinely
disk-bound read* (construct, C2), *environmental isolation* (internal, I1/I6) and *reproducibility
across days or hosts* (conclusion, I7).

---

## 6. Statistical conclusion validity

This class is quantified in [`docs/STATISTICS.md`](STATISTICS.md). What follows classifies; the
figures and the method are there.

| ID | The threat | Grade | Source |
|---|---|---|---|
| **I7** ⭑ | *n* = 30–50 per point, two passes at most, medians only, **no confidence intervals, no significance tests**; between-pass variance of roughly 10–15 % (×1.92 against ×2.21 on the same variant-A probe) is larger than some claimed effects; the MongoDB fits carry r² 0.7809 and 0.8794. | **BOUNDS** every effect below ~20 % | audit I7 |
| **D5** | M18 is *n* = 60, one pass, and its "refresh interval versus fixed delay" verdict is a threshold in the author's own code (`near_zero and spread > 0.5 * max`), not a test. | **BOUNDS** | challenges D5 |
| **D6** | The HCD aggregation arm is *n* = 3, so the exact permutation *p* floor is 1 / C(18,3) = 1.23 × 10⁻³ — **set by *n*, not by the effect**, which is astronomical. Four more executions would have taken it below 10⁻⁵ (1 / C(22,7) = 5.9 × 10⁻⁶); three more reach only 1.8 × 10⁻⁵ (1 / C(21,6)), at 134 s each. | **BOUNDS** the strength of proof, not the direction | campaign-7 challenges D6; `STATISTICS.md` §3.4 |
| **D7** ⭑ | The first draft of that challenge decomposed the 134 s using M16's point-read p50 — a different operation, a different collection, a different campaign — and produced a 30 s residue that was an artefact of the wrong constant. The correct decomposition needs no import: 133 984.229 ms ÷ 10 000 pages = **13.398 ms per page**, no residue. | self-correcting; **upgrades** M23's decomposition [U] → [M] | campaign-7 challenges D7 |
| **D12** ⭑⭑ (statistical half) | The campaign charged the CQL path with a partition-design cost on the strength of a ×1.28 median ratio whose supports **overlap** — honest ratio interval **[0.966×, 1.421×]**, containing 1.0, so the data cannot even exclude that the unaligned scan is faster. | **VOIDS** the design-cost clause; the "abandon the document model" half is structural and survives | campaign-7 challenges D12 |
| **I5** ⭑ | ADR action 1 was ticked `[x]` on the strength of M10 while M15 showed no disk-bound read had been measured — an inference from data to claim that the later data did not support. | **VOIDS** the closure; **status: corrected**, reopened to `[~]` at ADR revision 11 | audit I5 |
| **L5** | Closed loop: the sampling rate is a decreasing function of latency, so slow periods contribute proportionally fewer observations. The published p95/p99 are tails of a **service-time** distribution sampled at negligible utilisation, not of a response-time distribution under load. | **VOIDS** every tail figure *as a load tail* | `STATISTICS.md` §4.1 |
| **L8** | Percentiles only, no means for latency. **This is a strength, listed here so that the class is complete** — it is the policy that protects the conclusions, enforced in probe source. | — | `METHODOLOGY.md` §6 |

### 6.1 What `docs/STATISTICS.md` adds that no I/C/D identifier carries

These are not new findings of this document; they are findings of the statistical re-analysis,
recorded here so that the conclusion-validity class is not read as I7 alone.

- **The per-observation series were never persisted.** Of the 25 latency-bearing files under
  `data/raw/`, exactly two retain the observations
  ([`vector_freshness_idle.json`](../data/raw/vector_freshness_idle.json),
  [`vector_freshness_loaded.json`](../data/raw/vector_freshness_loaded.json), 60 values each).
  For the other 23, no bootstrap, no rank test, no re-percentiling, no distributional check and no
  pooling across passes is possible — **by anyone, including the author, permanently**. This is not
  a condition a future run can change; it is a loss. (`STATISTICS.md` §2.)
- **Two of the three legs of the ×7.50 / ×5.94 / ×1.52 triangle cannot be tested at all.**
  [`rmw_postflush.json`](../data/raw/rmw_postflush.json) (M15) stores no `min_ms`;
  [`findings_disk_rf3.json`](../data/raw/findings_disk_rf3.json) (M10) stores four p50 values and
  nothing else. The only leg that separates is M3's ×7.50 — the one already relabelled a memtable
  artefact. (`STATISTICS.md` §2, §3.3(d).)
- **34 of 93 enumerated comparisons overlap**, and the overlapping set is identical to the set whose
  ratio interval contains 1.0. **Both axes on which HCD wins are in it**: M16-A's 21.7 ×
  (interval [0.465, 65.842]) and M18's corrected freshness margin (interval [0.155, 36.683]). The
  only version of the freshness comparison that separates is the uncorrected M17, which the author
  has already withdrawn. (`STATISTICS.md` §3.3(a).)
- **The tier question rests on no separated comparison.** All 10 of 10 cells of M12's method 1
  overlap, and 9 of 10 of M14's. I3's "9–29 %, unpinned" is unpinned at both ends.
  (`STATISTICS.md` §3.3(c).)
- **MongoDB's mutation win is the most robust quantitative result in the dossier**: 19 of 20 cells
  disjoint against the Data API arm, 18 of 20 against the CQL-direct arm, the three exceptions all
  at 8 KiB on pass 2 and all caused by a MongoDB tail. The regime caveat travels unchanged and is
  not softened by this. (`STATISTICS.md` §3.3(b).)
- **M19 survives intact because it stores counts, not latencies** — exact tests are available, and
  from τ ≥ 1000 ms the comparison is 0/30 against 0/30, where no test can distinguish anything.
  (`STATISTICS.md` §3.17.)

---

## 7. Concordance

### 7.1 Forward — every identifier, in source order

⭑ grades are the source documents'; the class and consequence grade are this document's.

| ID | ⭑ | Primary class | Secondary | Consequence | Argued here | Source |
|---|---|---|---|---|---|---|
| I1 | ⭑⭑ | Internal | External | BOUNDS | §4 | audit-adversarial.fr.md |
| I2 | ⭑⭑ | Internal | Conclusion | BOUNDS | §4, §10.3 | audit-adversarial.fr.md |
| I3 | ⭑ | Construct | Conclusion | VOIDS | §3, §3 note 1 | audit-adversarial.fr.md |
| I4 | ⭑⭑ | Construct | Internal | VOIDS | §3, §10.1 | audit-adversarial.fr.md |
| I5 | ⭑ | Conclusion | — | VOIDS (corrected) | §6 | audit-adversarial.fr.md |
| I6 | ⭑ | Internal | — | BOUNDS | §4 | audit-adversarial.fr.md |
| I7 | ⭑ | Conclusion | — | BOUNDS | §6, §10.2 | audit-adversarial.fr.md |
| I8 | ⭑ | Construct | Internal | BOUNDS | §3 | audit-adversarial.fr.md |
| I9 | ⭑ | Construct | External | VOIDS | §3 | audit-adversarial.fr.md |
| C1 | ⭑ | Construct | — | BOUNDS (refuted in part) | §3 | challenges.fr.md |
| C2 | | Construct | Internal | VOIDS | §3, §10.1 | challenges.fr.md |
| C3 | | External | — | SCOPES | §5 | challenges.fr.md |
| C4 | | External | Internal | SCOPES | §5 | challenges.fr.md |
| C5 | | Internal | Conclusion | BOUNDS | §4 (≡ I2) | challenges.fr.md |
| C6 | | Internal | — | BOUNDS (reverses) | §4 | challenges.fr.md |
| C7 | | Construct | Internal | BOUNDS | §3, §3 note 2 | challenges.fr.md |
| C8 | | Internal | — | BOUNDS | §4 (≡ I6) | challenges.fr.md |
| C9 | | External | Conclusion | SCOPES | §5 | challenges.fr.md |
| C10 | ⭑ | Internal (mechanism) | Construct, External | VOIDS M17's magnitude | §4 | challenges.fr.md |
| C11 | | Construct | Conclusion | VOIDS "zero" | §3 | challenges.fr.md |
| C12 | | Construct | — | VOIDS the speed reading | §3 | challenges.fr.md |
| C13 | | Construct | — | SCOPES | §3 | challenges.fr.md |
| C14 | | Construct | External | SCOPES | §3 | challenges.fr.md |
| C15 | | Construct | External | BOUNDS | §3 | challenges.fr.md |
| D1 | ⭑⭑ | External | Construct | SCOPES | §5 | challenges.fr.md |
| D2 | | External | — | VOIDS the attribution | §5 | challenges.fr.md |
| D3 | | Construct | Conclusion | BOUNDS | §3 | challenges.fr.md |
| D4 | | Construct | External | SCOPES | §3 (≡ C14) | challenges.fr.md |
| D5 | | Conclusion | Internal | BOUNDS | §6 | challenges.fr.md |
| D6 | | Conclusion | — | BOUNDS | §6 | challenges-campagne7.fr.md |
| D7 | ⭑ | Conclusion | Construct | self-correcting; upgrades | §6 | challenges-campagne7.fr.md |
| D8 | ⭑ | Construct | External | reclassification [M]→[D] | §3 | challenges-campagne7.fr.md |
| D9 | | External | Construct | SCOPES | §5 | challenges-campagne7.fr.md |
| D10 | | Internal | — | **resolved against the challenger** | §8 | challenges-campagne7.fr.md |
| D11 | | External | — | SCOPES | §5 | challenges-campagne7.fr.md |
| D12 | ⭑⭑ | Conclusion | Construct, External | VOIDS the design-cost clause | §6, §5 | challenges-campagne7.fr.md |
| D13 | ⭑ | Construct | Internal | VOIDS the 46× reading | §3 | challenges-campagne7.fr.md |
| D14 | | Construct | External | SCOPES | §3 | challenges-campagne7.fr.md |
| L1 | | External | Internal | SCOPES | §5 | LIMITATIONS.md §5 |
| L2 | | External | — | SCOPES | §5 | LIMITATIONS.md §5 |
| L3 | | External | — | SCOPES | §5 | LIMITATIONS.md §5 |
| L4 | | External | — | SCOPES | §5 | LIMITATIONS.md §5 |
| L5 | | Conclusion | External | VOIDS tails as load tails | §6 | LIMITATIONS.md §5 |
| L6 | | Internal | External | BOUNDS | §4 | LIMITATIONS.md §5 |
| L7 | | Internal | Construct | BOUNDS | §4 | LIMITATIONS.md §5 |
| L8 | | Conclusion | — | (policy, a strength) | §6 | LIMITATIONS.md §5 |
| L9 | | External | — | SCOPES | §5 | LIMITATIONS.md §5 |
| L10 | | — | — | superseded, see §9 X8 | §9 | LIMITATIONS.md §5 |
| L11 | | External | Conclusion | SCOPES | §5 | LIMITATIONS.md §5 |
| G1–G8 | | Internal (evidence chain) | Conclusion | G8 VOIDS M3's ×1.56 as checkable | §4.1 | probes/README.md |

### 7.2 Reverse — arriving from a source document

| If you are reading… | …find it here |
|---|---|
| `audit-adversarial.fr.md`, the unnumbered parent finding (the dossier meets ~2.5 of its own §10's six conditions) | §9, X10 — it is a **compliance** finding that decomposes into L5 (conclusion), C2/I4 (construct) and I1 (internal); no single class holds it |
| `audit-adversarial.fr.md` §I1–I9 | §4 (I1, I2, I6), §3 (I3, I4, I8, I9), §6 (I5, I7) |
| `challenges.fr.md`, "les trois blessures réelles" (C1, C2, C3) | §3 (C1, C2), §5 (C3) |
| `challenges.fr.md`, "les objections de méthode" (C4–C9) | §5 (C4, C9), §4 (C5, C6, C8), §3 (C7) |
| `challenges.fr.md`, campaign-6 pass (C10–C15) | §4 (C10), §3 (C11, C12, C13, C14, C15) |
| `challenges.fr.md`, meta-challenges (D1–D5) | §5 (D1, D2), §3 (D3, D4), §6 (D5) |
| `challenges.fr.md`, the measured resolutions (C1, C2, C10, D1) | named in the row of the challenge they resolve; the consequence grade describes the **residue after** the resolution |
| `challenges-campagne7.fr.md` (D6–D14) | §6 (D6, D7, D12), §3 (D8, D13, D14), §5 (D9, D11), §8 (D10) |
| `LIMITATIONS.md` §5 bullets | §5 (L1–L4, L9, L11), §4 (L6, L7), §6 (L5, L8), §9 (L10) |
| `probes/README.md` gaps | §4.1 |
| `RESULTS.md` §6 "axes never measured" | §5, with three rows re-filed as noted there |
| `docs/STATISTICS.md` | §6 and §6.1 throughout |
| `docs/RESEARCH-DESIGN.md` (RQ1–RQ8, construct table) | §3 note 3 and §9, X1 for the constructs; the RQ→measurement mapping there is the complement of the concordance above — that document maps questions to evidence, this one maps threats to claims |

---

## 8. Duplicates, clusters and one finding resolved against its challenger

Recording these makes the count honest: **there are fewer distinct threats than there are
identifiers**, and a reader who counts identifiers overstates the coverage.

- **I2 ≡ C5.** The same ground, stated once as integrity and once as scope. The source documents say
  so. One threat.
- **I6 ≡ C8.** Same. `LIMITATIONS.md` C8 ends "(Same substance as I6)". One threat.
- **C14 ≡ D4.** D4 exists to record that C14 was never resolved. One threat, two dates.
- **I9 = C10 + C11.** I9 is the audit's name for the cluster the challenges raise separately.
- **I3 depends on C7.** If arm B's storage term is an optimistic floor, the tier term is
  over-estimated by method 1 — which is one of the three reasons the three estimates disagree.
- **I4 and C2 are one mechanism seen twice.** C2 is the objection; I4 is what measuring it produced.
- **D1 and D2 both bear on the same axis** and cut in opposite directions: D1 narrows HCD's win to
  sub-second write-then-search, D2 removes MongoDB's number from MongoDB.

**D10 is the one challenge resolved against the challenger.** It asked under which index state
MongoDB's 222.711 ms `$group` ran; the probe source answers it (`cat_idx` was created before the C1
measurement) and the data show the index was irrelevant, since `$sum: "$amt"` cannot be served by an
index on `cat` alone — the same filtered count served by `cat_idx` runs at p50 12.659 ms against the
`$group`'s 222.711 ms. The recommendation it leaves standing is a real one and belongs in this
document's terms: **each arm's index state should be recorded in the result JSON, not only in the
probe source.**

---

## 9. Coverage: what this taxonomy does *not* cover

A validity taxonomy whose only function is to re-file what is already written would be decoration.
This section is the reason to build one: the classes make visible what no identifier occupies.

### 9.1 Per class, what is not covered

- **Construct.** No adversarial identifier occupies the central term (X1 below), which is registered
  in the design documents and in no register written *against* the dossier. Also empty on the
  ballast: no identifier asks
  whether 16 string fields of 512–8000 B, chunked because the Data API refuses indexed strings above
  8000 B, stands for any real corpus. The shape was forced by an engine constraint, and no document
  characterises it against a production document, a field-type mix, a nesting depth or an
  update-shape distribution.
- **Internal.** No identifier carries the **hardware and topology confound** folded into the regime
  comparison (X6). No identifier carries **serial dependence** within a run — GC pauses, compaction,
  page-cache warming — which cannot now be tested because the series are gone.
- **External.** No identifier states a **target population** or a scope of inference. The title
  generalises to "document databases"; the evidence covers one build of one Data API on one host.
  And no identifier registers **"only two systems"** as a limitation, although a design-point claim
  about shredding needs a third layout to be a claim about anything but two products.
- **Conclusion.** Covered by I7 alone in the source registers, and by `docs/STATISTICS.md` since it
  was written. No identifier carries **X2**, **X5** or the absence of any stated
  minimum detectable effect: *n* = 30 is inherited from the supplied harness and justified nowhere,
  with the visible consequence that M11's pre-registered 1.15 threshold is finer than the design's
  own between-pass spread, so its straddle (1.128 / 1.187) is undecidable by construction rather
  than inconclusive by outcome.

### 9.2 Threats carried by no identifier

These are labelled **X1–X10** for reference. They are this document's labels. Each one is stated
with the check that establishes it, so that a reader can verify rather than believe.

**X1 — "Write cost", the construct in the title, is carried by three non-equivalent quantities, and
no adversarial identifier registers that as a threat.** *Construct.* The three are: client
wall-clock around a driver call (`time.perf_counter()` in every latency probe), coordinator-side
duration from `system_traces.sessions` (M5 and M12's method 2, which `data/README.md` correctly
distinguishes), and **engine work** — bytes written, write amplification, compaction load, CPU
seconds — which is measured **nowhere**: no file under `data/raw/` carries a bytes-written or
write-amplification figure, and `RESULTS.md` §6 records write throughput as never measured as such.
`CITATION.cff` nonetheless listed "write amplification" as a keyword, and both it and
`README.md` named concurrency in the title, which L4 says was never measured; the keyword and both
titles have since been corrected, while the article under verification still carries "concurrency"
in its own title and earlier citations of it stand uncorrected.
**Consequence, and it is the point of §10.1:**
because cost is operationalised as latency, its value is a property of a cache regime — which is
exactly the instability the dossier publishes as its deepest finding (I4). A bytes-written
operationalisation, derivable in principle from M1's twelve columns and M2's eleven assignments,
would be regime-stable and was never attempted. **Status at the time of writing:**
[`docs/RESEARCH-DESIGN.md`](RESEARCH-DESIGN.md) §1 now publishes the construct table and states the
regime-dependence explicitly, which closes the *declaration* half of this gap. What it does not
close, and what no document can close without a new campaign, is the **measurement** half: the
engine-work row stays empty, so the dossier's title quantity has no regime-stable estimate anywhere.

**X2 — Every cross-engine slope, r² and headline ratio is fitted on pass 1 only, undeclared.**
*Conclusion.* `probes/probe_comparative.py`, inside `compare()`, selects points with
`k = f"{sz.label}|pass1"`; pass-2 points sit unused in
[`cmp_mongo.json`](../data/raw/cmp_mongo.json), [`cmp_hcd.json`](../data/raw/cmp_hcd.json) and
[`cmp_hcdcql.json`](../data/raw/cmp_hcdcql.json). The published `y_range_ms` values are the pass-1
endpoints, which confirms the selection. No document declares it — `METHODOLOGY.md` §6 and
`RESULTS.md` §3 speak of two passes, and I7 characterises between-pass variance as roughly 10–15 %
without applying that to the comparative slopes. **This is the strongest-provenance instrument in
the dossier** (supplied, unmodified, the basis of M13), which is precisely why the omission
matters: nine integrity findings, twenty challenges and two adversarial rounds passed over it,
because not one of them re-derived a published number from the published data.

**X3 — M20's "captured artefact" is a constant.** *Internal, evidence chain.* `RESULTS.md` M20
states that "the `COMMAND_UNKNOWN` result is a captured artefact" and cites the `structural` field
of [`findings_agg_hcd.json`](../data/raw/findings_agg_hcd.json). That field is a fixed string
written unconditionally by `probes/probe_aggregation.py`, and the decisive check is that the
**identical string also appears in
[`findings_agg_mongodb.json`](../data/raw/findings_agg_mongodb.json)** — a record produced by the
MongoDB arm, which never addresses HCD at all. No probe in `probes/` ever issues `aggregate`,
`$group` or `distinct` against HCD; the only `aggregate` calls in the tree are pymongo `$search` and
`$group` against MongoDB, and the probe's own docstring calls the finding structural recon rather
than a measurement. **The finding may well be true** — the campaign-7 report records the refusals,
and D6–D14 leave M20 unscratched — but its status in this repository is **transcribed, not
captured**, exactly like the nineteen-command allow-list that the same row already labels as
transcribed. The row should say so for both halves.

**X4 — Two front-matter documents assert a universal timestamp the data contradict.** *Internal,
evidence chain.* `README.md` "At a glance" states `run_at_utc` is "stamped in every raw file", and
`DISCLAIMER.md` repeats it. In fact **12 of the 36 files carry no `run_at_utc` at all** —
`cmp_hcdcql.json`, `control_read_A_run1.json`, `control_read_A_run2.json`,
`findings_hcd_vec_freshness.json`, `findings_tier_method2.json`, `findings_turn_hcd.json`,
`findings_turn_mongodb.json`, `probe4_rf3_supplementary.json`, `rmw_postflush.json`,
`tier_comparison.json`, `vector_freshness_idle.json`, `vector_freshness_loaded.json` — and a
thirteenth, `findings_vector_rf3.json`, carries the hand-typed string `"2026-09-17T16:5x (p16
ring)"`. `data/README.md` states this correctly; the two documents a reader opens first do not.
Note which files are in that list: `rmw_postflush.json` is M15, and the two turn-latency files are
M19 — headline evidence.

**X5 — The scoreboard aggregates non-independent, author-selected axes, and double-counts one
measurement.** *Conclusion.* "MongoDB won five of the ten measured axes, HCD two; three named no
winner" is the first sentence of both `README.md` and `RESULTS.md` §1. The unit of analysis, "axis",
is defined nowhere; the axes were accreted campaign by campaign in response to challenge C9, so
they are neither pre-registered nor independent; mutation cost, the per-byte rate and the tier share
are three views of one phenomenon; two of the ten axes (M20–M23) had no adversarial verdict at all
until D6–D14; and rows four and five of the headline table are **the same HCD measurement**, p50
17.376 ms, scored once for HCD and once against it — the table says so in its own cell. A derived
statistic over such a set is a reading aid, not a result.

**X6 — The regime comparison mixes regime with hardware and topology.** *Internal.* Campaign 1 ran
on `rh-hcd` at RF 1 in a 3 GiB container with a 2 G heap; campaigns 3–6 on the `p16` ring at RF 3
with 8 GiB nodes and a 4 G heap. The ×7.50 / ×5.94 / ×1.52 interval therefore spans three regimes
**and** two machines **and** two replication factors. `METHODOLOGY.md` §5 states this in its third
caveat and the raw record carries it as
`findings_fieldbyte.json → conditions.hardware_confound_vs_campaign1`. No I, C or D identifier
carries it, so it never reaches the tables where the interval is quoted.

**X7 — Pre-registration is asserted and is not evidenced by this repository's own standard.**
*Conclusion.* `METHODOLOGY.md` §1 states that the protocol was fixed before the numbers and that
each probe carried its decision rule in its own source before it ran. The first half is testimonial:
the git history is six commits, all on 2026-09-18 between 10:03:02 and 11:00:25, later than every
run stamp in `data/raw/` except the mongot provenance check at 10:05:00; and every probe file
carries the identical mtime 2026-09-18 09:35, a single import. Nothing orders protocol before data.
The repository **accepts mtime as evidence when it argues against itself** — `probes/README.md`
rejects `probe_tier_vs_storage.py.orig` as independent evidence because its mtime post-dates the
patched probe it should predate — so this is the author's own instrument, unapplied to his own
strongest claim. The second half is checkable and false as a generalisation: most probes carry no
verdict rule, and the ones that do not include `hcd_cql_arm.py` (M14), `rmw_postflush.py` (M15),
`probe_read_search.py` (M16) and `mongot_freshness.py` (M17) — that is, every instrument that
produced a post-campaign-4 headline, **including both measurements in which HCD wins**. The pattern
is worth stating plainly because it is the compound threat of §10.3: the probes with the weakest
provenance under I2 are, with few exceptions, the probes with no pre-declared rule, so two
independent safeguards fail on the same rows. What *is* evidenced, and should be claimed instead:
the two rules a published probe both declares and echoes back into the output record —
`findings_fieldbyte.json`'s `verdict_per_pass`, emitted at `probes/probe_field_vs_byte.py:323`, and
`probe_comparative.py`'s `cross_engine_comparison_permitted` gate, emitted at line 264 — plus
`probe_aggregation.py`'s pre-declared exactness check against precomputed ground truth, which is a
genuine pre-registered **correctness** criterion and is nowhere named as one.

**A third rule was listed here and does not survive this document's own test.**
`findings.json → findings[2].read_control_pre_registered_rule` is the rule credited with the
dossier's most-cited adverse verdict — variant A INCONCLUSIVE at RF = 1, RF = 3 and on disk. **That
verdict stands.** It is published as INCONCLUSIVE in all three regimes — `RESULTS.md` M3 at RF = 1,
M10 in the disk regime, and `docs/RESEARCH-DESIGN.md` RQ3 for all three — and nothing in this
paragraph restores the harness's raw SUPPORTED. What does not stand is the rule's status as *pre-registration*:
`grep -rn "pre_registered" probes/` returns nothing, the block is hand-assembled, and its own
`read_source` field records that run 1's distribution JSON was overwritten by run 2. That is the
same class of defect X3 applies to M20's "captured artefact" and `docs/RESEARCH-DESIGN.md` §5.2
item 4 applies to the two `VERDICT` blocks — applied there to records that embarrass the dossier,
and withheld until now from the one that flatters its method, which is the asymmetry X7 exists to
name. The same sentence is owed here: the rule appears only in the output record, is attributed to
a "User protocol step 3" the repository does not contain, and is emitted by no published probe; it
should be read as **declared by the author and not independently evidenced**.

**X8 — Four English documents still say campaign 7 has never been challenged.** *Record accuracy.*
`docs/challenges-campagne7.fr.md` (D6–D14) exists and is committed. `LIMITATIONS.md` §5 (L10),
`RESULTS.md` §2 and §3 (the M20, M21 and M23 rows), `README.md`'s headline table and
`docs/STATISTICS.md` §3.4 all still carry the sentence "no figure in it has been challenged" or its
equivalent. That sentence was true when written and is now false. This document classifies D6–D14
on the assumption that the campaign-7 register is live.

**X9 — There is no claim A1.** *Record accuracy.* The English documents adjudicate the article's
claims by label — `RESULTS.md` says "SUPPORTED — claim A2, [U] → [M]" and "claim A3" — and the
labels are defined only in French, in `docs/campaigns/01-verification.fr.md` (A2, A3, A4, A5a, A5b,
plus F, L and P) and `docs/campaigns/02-replication-rf3.fr.md`. **No document in this repository
defines an A1**; a search of every Markdown file outside `docs/article/` returns no occurrence of
the label. Any summary that speaks of "claims A1–A5" is naming a claim that does not exist. An
English claims table belongs in `METHODOLOGY.md` before the first English use of an A-label.

**X10 — The parent finding of the audit is a compliance finding and fits no single class.** The
audit's dominant result is that the dossier meets about 2.5 of the six conditions the article
imposes on other people's benchmarks. It decomposes here into L5 (conclusion — closed loop rather
than fixed offered rate), C2 and I4 (construct — one campaign reached a disk regime and none reached
a disk-bound read), and I1 (internal — compaction crossed in campaign 3 only). It is recorded as a
cluster rather than re-filed, because its force comes from being counted as a whole: a dossier that
faults others on six rules and breaks three of them does not hold the authority it claims, and that
statement is not a threat to any one measurement.

---

## 10. The three threats that most constrain what may be claimed

Not the three most severe in the abstract, and not the three the dossier apologises for most. The
three that most narrow the set of sentences this repository is entitled to publish. Two of them are
already in the registers; the third is a compound that no identifier states, because each of its
halves is registered separately and their conjunction is where the damage is.

The selection criterion, stated so it can be disputed: a threat ranks here if correcting it would
change **what may be said**, not merely **how precisely**. On that criterion the external-validity
findings — I1, C4, C3, L1–L4, and the whole of `RESULTS.md` §6 — do not rank, despite being the most
numerous and the most conspicuously declared, and it is worth saying why. The dossier does not
generalise. Every figure is marked [M], every document repeats that [M] means one build on one day
on one machine, and `RESULTS.md`'s eight reading rules bind each headline to its regime. A threat
to generalisation cannot constrain claims that were never made. I6 is the clearest case: the
`system.paxos` residue may have slowed HCD, but contamination that slows HCD makes MongoDB's result
*more* favourable to MongoDB, so it cannot be the explanation of a two-order-of-magnitude gap. It
bounds an absolute nobody is entitled to quote anyway.

### 10.1 Construct — "cost" was operationalised as latency, so the flagship quantity is not well-formed

*(I4 ⭑⭑, C2, X1, with M15's own fragmentation caveat and X6's confound attached.)*

The dossier's central quantity is a rate: milliseconds per indexed kibibyte, equivalently a growth
factor from 1 KB to 128 KB of indexed ballast. It takes three values on the same system — **×7.50**
in the memtable regime at RF 1, **×5.94** with the dataset on disk at RF 3, **×1.52** once a flush
before each update forces the cycle's `SELECT` onto the SSTable path — and the audit publishes that
five-fold interval as its most constraining finding. It is right to. But the registers file the
instability as an empirical surprise about regimes, and it is not one. It is what must happen when a
property of physical layout is estimated through a latency proxy: a layout cost measured in bytes
would not move across those three conditions, and a layout cost measured in milliseconds must,
because a millisecond is a property of where the bytes were when they were read.

Three things follow, and each of them narrows what may be written.

First, **"HCD's mutation cost per indexed KiB" is not a quantity this design can estimate**, in any
regime, because the estimator and the regime are not separable. The dossier already forbids quoting
a rate without its regime (reading rule 1). The stronger and more defensible statement is that the
rate is not a property of the engine at all under this operationalisation, and that a single figure
is not merely imprecise but ill-formed.

Second, **the arbitration is unavailable**. Of the three legs, the two that would settle where the
truth lies — M10's ×5.94 and M15's ×1.52 — are exactly the two records too thin for any test:
`rmw_postflush.json` stores no `min_ms`, `findings_disk_rf3.json` stores four p50 values and nothing
else. The only leg that separates is M3's ×7.50, the one the dossier has already relabelled a
memtable artefact that must never be quoted as an engine property
([`docs/STATISTICS.md`](STATISTICS.md) §2, §3.3(d)). And the ×1.52 leg carries an instrument
artefact of its own: flush-per-update leaves up to ~35 small SSTables to merge per `SELECT`, so its
~100 ms absolute is inflated by the protocol that produced it, and the true disk-bound cost lies
somewhere between the memtable figures and that fragmented worst case — a gap nothing in the
repository closes, because the page cache was never droppable (L7) and no genuinely disk-bound read
exists anywhere in the dossier (C2, confirmed).

Third, **X6 adds two more moving parts to the interval**: campaign 1 was RF 1 on a 3 GiB container,
campaigns 3–6 RF 3 on 8 GiB nodes. So the flagship interval spans three regimes, two machines and
two replication factors, and no identifier carries that confound into the tables where the interval
is quoted.

What survives untouched, and should be stated in the same breath, is the **mechanism**: read,
modify, rewrite the whole document plus every derived column under a Paxos-guarded conditional,
observed in 10 of 10 CQL traces (M2), over a row whose twelve columns and nine automatic SAI indexes
were read directly from `system_schema` (M1). Neither is a latency measurement, so neither is
touched by any of this. The mechanism transfers and the rate does not — and the reason it does not
is the estimand, not the laboratory.

### 10.2 Conclusion — the observations were discarded, and what the summaries retain already refuses two headlines

*(I7 ⭑, L5, D5, D6, D12, plus `docs/STATISTICS.md` §2 and §3.3.)*

The registers record "no confidence intervals, anywhere" as a **decision**. It is not a decision. Of
the 25 latency-bearing files under `data/raw/`, exactly two retain their observations; the other 23
hold only `n`, `min`, `p50`, `p95`, `p99`, `max` and `stdev`, and the samples that produced them no
longer exist. No bootstrap, no rank test, no distributional check, no pooling of the two passes, no
re-derivation under a different percentile estimator, and no verification of the probes' own
percentile arithmetic is possible — **for any reader, including the author, permanently**. Every
other limitation in this document is a condition a future run can change. This one is a loss, and it
converts the repository's central promise, that a hostile reader can check it, into a promise that
holds for its prose and fails for its statistics.

That would be a grave but survivable defect if the surviving summaries were mute. They are not. The
minima and maxima that did survive are enough to decide, for any pair of arms, whether their
supports overlap — and the re-analysis finds **34 of 93 comparisons overlapping**, with the
overlapping set identical to the set whose ratio interval contains 1.0. Two results in that set
matter more than the other thirty-two:

- **M16-A, the 21.7× undeclared-field search** — ratio interval **[0.465, 65.842]**. One MongoDB
  collection scan of fifty finished in 13.335 ms, faster than HCD's median; HCD's slowest of fifty
  took 28.697 ms. What these data establish is **predictability** — HCD answers in about 17 ms
  whatever the document, MongoDB-default anywhere from 13 ms to 863 ms — and that is a different and
  weaker claim than "22× faster". `README.md` has been corrected to say so; the correction is the
  model for what this class of threat requires everywhere.
- **M18, the corrected search-freshness margin** — ratio interval **[0.155, 36.683]**, because
  mongot's 89.1 ms floor sits below HCD's 573.598 ms maximum. The only version of this comparison
  whose supports separate is the **uncorrected** M17, and M17 is the measurement the author has
  already withdrawn as a probe artefact (C10).

**Both of the axes on which HCD wins are therefore in the overlapping set**, and on the freshness
axis the separated version is the withdrawn one. What is left standing on that axis is not a latency
comparison at all but M19's **miss counts**, which are exact and which survive intact: HCD 0/30 at
every τ; MongoDB 30/30 at τ = 0, 15/30 at 500 ms, 0/30 from τ = 1000 ms. That is the form in which
HCD's freshness advantage may be stated — a correctness property inside a bracket, not a multiplier
— and D1's resolution already says exactly that.

The same class of threat, applied to the CQL reference arm, produced D12: the campaign charged the
CQL path with a partition-design cost on a ×1.28 median ratio whose supports overlap, honest interval
[0.966×, 1.421×], which does not even exclude the unaligned scan being faster. A design penalty
asserted without separating it from noise is the fault the dossier reproaches in other people's
benchmarks, and it committed it once.

Nothing here reverses a direction. MongoDB's mutation win is the most robust quantitative result in
the repository — 19 of 20 cells disjoint against the Data API arm, 18 of 20 against the CQL-direct
arm — and the capability results (M20, M21, M22) are not statistical claims at all and are untouched.
What must narrow is the **magnitude language**: ratios of medians are this design's effect sizes, six
significant figures are not supportable by a two-pass design, and no p95 or p99 in this dossier is a
tail of anything, because a closed loop samples slow periods less often than fast ones by
construction (L5).

### 10.3 Internal — the decisive verdicts, the measurer-written instruments and the missing decision rules are the same rows

*(I2 ⭑⭑ / C5, G6, X7, with `docs/STATISTICS.md` §3.3(a) and `DISCLAIMER.md`.)*

The audit's I2 states that five instruments were written by the measurer and that they carry M12
(half), M14, M15, M16 and M17 — five of the decisive measurements, **including both in which HCD
wins**. `probes/README.md` gap 6 raises the count to seven. That is registered, and stated at full
strength. What is not registered is the conjunction of three facts about exactly those rows.

**First**, the measurer-written instruments are also, with few exceptions, the instruments that
carry **no pre-declared decision rule** (X7). The supplied harnesses of campaigns 1–4 carry verdict
rules in their source and echo them back into the output record; `hcd_cql_arm.py` (M14),
`rmw_postflush.py` (M15), `probe_read_search.py` (M16) and `mongot_freshness.py` (M17) do not. So
the two safeguards the dossier relies on — instrument independence and pre-registration — fail on
the same measurements rather than covering for each other.

**Second**, those same measurements are the ones that fail separation of support. The two HCD wins
(M16-A, M18) are both in the overlapping set; M15 cannot be tested at all for want of a `min_ms`;
M14's Data-API-versus-CQL comparison overlaps in 9 of its 10 cells. A reader looking for the
statistical safeguard where the other two failed does not find it either.

**Third**, the direction of the residual risk is not neutral. `DISCLAIMER.md` declares the author's
employment and states the axis-selection bias, which is the hard part and is done. But the rows
where all three safeguards are absent are, disproportionately, the rows favourable to the author's
employer's product. Nothing in this repository suggests that any verdict was constructed — the
opposite is conspicuous: the dossier withdrew its own 1015.201 ms figure, reopened a closed ADR
action, published `findings_mongot_freshness.json` intact after `findings_mongot_floor.json` refuted
it, and kept fifty-two points at which the evidence contradicted its author. The threat is not
dishonesty. It is that **on the rows where the dossier's conclusions are most favourable to HCD, a
reader has no mechanism of verification at all** — not an independent instrument, not a rule fixed
before the run, not a separated support — and must take those rows on the author's word, which is
precisely the thing the rest of the artefact is built to make unnecessary.

The remedy is not more measurement. It is to carry the grade into the tables: mark each headline row
with its instrument provenance, whether a decision rule predated it, and whether its supports
separate. Where all three are absent, say so in the row. Two of the dossier's ten axes would then
carry that mark, and both are HCD's.

---

## 11. Provenance of the taxonomy

The four-way classification — statistical conclusion, internal, construct and external validity — is
standard in the design of field experiments and in empirical software engineering. Two works are
named here because they are the ones this structure comes from, and only what is certain about them
is stated: no page numbers, no DOIs, no volume strings.

- Thomas D. Cook and Donald T. Campbell, *Quasi-Experimentation: Design and Analysis Issues for
  Field Settings*, 1979 — the source of the four-way scheme in the form used above. (Verified to
  exist with these authors, this title and this year. The publisher is recorded inconsistently
  across catalogues and is therefore omitted rather than guessed.)
- Claes Wohlin, Per Runeson, Martin Höst, Magnus C. Ohlsson, Björn Regnell and Anders Wesslén,
  *Experimentation in Software Engineering*, Springer — the software-engineering adaptation, which
  is where the convention of publishing a threats-to-validity section organised by these four
  classes comes from. (Verified to exist with these authors, this title and this publisher; it has
  appeared in more than one edition, so no year is given.)

**Coordinated omission**, named in §6 and developed in `docs/STATISTICS.md` §4, is attributed there
as that document attributes it: to Gil Tene's talks and to the `wrk2` and `HdrHistogram` tools, with
the explicit statement that there is no canonical paper to cite. That attribution is repeated here
unchanged rather than upgraded.

Everything else in this document is either an observation of this repository, with the file and
field named, or a statement of common knowledge carrying no attribution. No reference is cited that
was not checked, and nothing marked here as verified rests on recollection alone.

---

*Written 18 September 2026 against the repository as it then stood — `docs/challenges-campagne7.fr.md`
(D6–D14) included, `docs/STATISTICS.md` included. No measurement was taken, no file under
`data/raw/`, `probes/` or `docs/article/` was read as anything but evidence, and none was modified.*
