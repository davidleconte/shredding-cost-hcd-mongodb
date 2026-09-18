# Limitations, integrity findings and challenges

This file is the adversarial half of the dossier. It promotes to English the two French documents
written *against* the campaigns rather than for them: `docs/audit-adversarial.fr.md` (integrity
findings I1–I9) and `docs/challenges.fr.md` (challenges C1–C15, the meta-challenges D1–D5, and the
measured resolutions of C1, C2, C10 and D1).

---

## 1. Read this before quoting any number from this repository

**The experiment was built so that it could prove its own author wrong, and in several places it
did.** That is the only thing here worth more than the numbers. If you quote a figure from this
repository without the regime, the build and the caveat that the audit attached to it, you are
misquoting it — not paraphrasing it.

Four rules follow, and they are not decoration:

1. **No figure travels alone.** Every measured quantity in this dossier is a property of a regime
   (memtable or SSTable), of a stack (Data API or bare CQL), of a configuration (`atlas-local`
   defaults), or of a measurement floor (a ~45 ms HTTP round trip). Strip the regime and the number
   becomes false rather than approximate.
2. **The dossier fails the test it imposes on other people's benchmarks.** The article's section 10
   lists six conditions a defensible comparison must meet. This dossier satisfies about two and a
   half of them:

   | Section-10 requirement | Met? |
   |---|---|
   | 1. Load at a **fixed offered rate**, not closed-loop | **NO** — every mutation, read and comparison probe is **sequential and closed-loop** (one operation, then the next). Only the freshness probe used an offered rate. |
   | 2. Distributions, not means | yes (percentiles) |
   | 3. Equivalent durability, recorded | yes (`LOCAL_QUORUM` ↔ `w:majority`, declared) |
   | 4. Working set vs RAM, **cache AND disk regime** | **partial** — disk was reached only in campaign 3; everything else is cache-resident |
   | 5. Topology declared | yes |
   | 6. Warm-up **and compaction cycles crossed** | **partial** — compaction crossed in campaign 3 only |

   A dossier that faults others for breaking six rules and breaks three of them itself does not hold
   the authority it claims. The audit calls this the parent flaw: *the measurement does not conform
   to its own standard.*
3. **The epistemic markers are load-bearing**, and they are the article's, not an afterthought:
   - **[D] Documented.** Established by the vendor's own version-pinned documentation, by the
     project's source of record, or by peer-reviewed publication.
   - **[R] Reported.** Described publicly by the engineers who built the system, or by the upstream
     project, but not restated in the versioned documentation of the shipped product. Directionally
     reliable; not a contractual guarantee.
   - **[U] Unverified.** Asserted on structural grounds, or widely repeated in the practitioner
     literature, but not established by any source of acceptable rank.
   - **[M] Measured.** Observed on a named build under stated conditions. Stronger than [U], weaker
     than [D]: it establishes what one build did on one day, not what the vendor commits to.

   **No performance figure in this repository is [D].** Every measured quantity is [M], and [M] is
   the weak marker: what one build did on one day, on one machine, under one load.
4. **The audit's own verdict, unedited:** the dossier is reliable as a qualitative account and as a
   verification of mechanism; it is **not** reliable as a source of publishable figures. The
   *directions* survive. The *magnitudes* — 44×, 0.77 ms/KiB, ×7.50, ~1 s, 40×, 22× — are each
   tainted by a regime, a stack, a configuration, a product **edition**, or a measurement floor. The
   "~1 s" carries the heaviest tag of the six: it was measured against mongot `localDev`, a build its
   own vendor does not ship for production (I9, C10, D2).

Raw evidence is under `data/raw/` and is byte-identical to the run. Every number below names the
file it came from.

---

## 2. Integrity findings (I1–I9)

Severity is the audit's own: ⭑⭑ is the higher grade.

### I1 — Not reproducible, not isolated ⭑⭑

**The finding.** One host (`alphadebunker`, a shared QEMU VM), a **production-demo ring** also
carrying Presto, streaming and Jupyter, at a **load average of 14–16** throughout
(`docs/audit-adversarial.fr.md`). State **mutated between campaigns**: `system.paxos` grew from 0 to
**13 GiB per node** (campaign 4 report, `docs/campaigns/04-tier-vs-storage.fr.md`), and the twenty
`supply_chain_hcd` SAI indexes were dropped and recreated **six times**.

**What it undermines.** Reproducibility in the strict sense. Nobody can replay these figures: the
conditions no longer exist and were not clean to begin with. Every absolute latency is a
*noisy ceiling*, not a clean measurement.

**What it does not touch.** The structural observations, which do not depend on timing: the twelve
columns and nine SAI indexes (M1), the `SELECT`→`UPDATE … IF` trace (M2), the three-replica Paxos
message sequence (M5), the field-versus-byte *direction* (M11).

### I2 — The measurer wrote and modified the instruments ⭑⭑

**The finding.** The guarantee "an instrument I did not write, and therefore cannot rig" is largely
lost. **Five scripts written entirely by the measurer** — `probes/method2_trace.py`,
`probes/hcd_cql_arm.py`, `probes/rmw_postflush.py`, `probes/mongot_freshness.py`,
`probes/probe_read_search.py` — carry M12 (half), M14, M15, M16 and M17: **five of the decisive
measurements, including the two that make HCD the winner.** The supplied harness was also patched
(astrapy `Environment.HCD`; `indexing.deny`; the disk driver's `docker exec` and incompressible
payload; the tuple key bound through prepared statements). Every patch is declared and mechanically
justified, and none touched a threshold, a document size or a repetition count — but a hostile reader
counts them.

**What it undermines.** The independence of exactly the verdicts that matter most.

**What it does not touch.** M1, M2, M3, M11 and M13 rest on a supplied script executed as given
(M13 through an unmodified `probes/probe_comparative.py`). Those are the solid ones, and the audit
says so.

### I3 — Unresolved internal contradiction: the tier term is 9 % or 29 % ⭑

**The finding.** M12 (campaign 4, disk regime, interleaved arms) puts the stateless Data API tier at
**29 %** of the per-kibibyte rate: tier 0.219 ms/KiB against storage 0.547 ms/KiB, summing to 0.766
and reproducing campaign 3's ~0.77 (`data/raw/findings_tier.json`; the coordinator-trace method in
the same file gives a tier slope of 0.145 ms/KiB, i.e. ~19 %). M14 (campaign 5 follow-up, cache
regime, separated arms) puts it at **9 %**: removing the tier moves the slope only from 0.7775 to
0.7037 ms/KiB (`data/raw/comparison_v2.json`). **A factor of three on the same quantity, both in the
ADR's evidence register, never reconciled.**

Worse for the narrative: the dossier used **29 %** to deflate the engine ratio to ~31×, then **9 %**
to correct that deflation to 40×. Each use was declared, but the value changed with the need.

**What it undermines.** Any sentence of the form "the Data API tier accounts for *X* % of the cost".
No such sentence is defensible. The honest statement is an unpinned **9–29 % range**, method- and
regime-dependent, with a per-size spread of 29.8–39.7 % inside method 1 alone
(`data/raw/tier_comparison.json`).

**What it does not touch.** The direction, which all three estimates agree on: the majority of the
rate lives in the **stateful** storage engine, which does not scale out by adding instances; a real
minority lives in the **stateless** tier, which does. That is the architecture-relevant claim, and it
survives.

### I4 — The flagship figure is not a stable property ⭑⭑

**The finding, and it is the most constraining in the dossier.** The growth factor of variant B —
the cost of a constant one-field `$set` as indexed ballast grows — takes three values:

| Regime | Growth of the variant-B update p50 | Source |
|---|---|---|
| Memtable, RF 1, campaign 1 | **×7.50** (12.104 ms at 1 KB → 90.783 ms at 128 KB) | `data/raw/findings.json` |
| Disk-regime dataset, RF 3, campaign 3 | **×5.94** (read control ×2.10) | `data/raw/findings_disk_rf3.json` |
| SSTable read path, post-flush (M15) | **×1.52** (107.765 ms at 1 KB → 163.402 ms at 128 KB) | `data/raw/rmw_postflush.json` |

That is a **five-fold interval on the headline coefficient**. The "0.77 ms per indexed KiB" and the
"×7.50" are **memtable-regime artefacts**; the post-flush pass proved it. Once the read half of the
read-modify-write cycle is forced onto SSTables, a large fixed read-path cost (~100 ms) dominates and
the per-byte growth flattens.

**What it undermines.** Quoting a single rate as *the* mutation cost of HCD is misleading. That rate
is the foundation of M3, M10, M11, M12 and M13, and of the first line of three reports.

**What it does not touch.** The **mechanism** of section 3 — read, modify, rewrite the whole document
plus every derived column, maintain the indexes over content that was never touched — which is
established by trace (M2), not by the curve. The mechanism transfers. The number does not.

**Caveat that travels with the ×1.52 itself:** flushing before *every* update creates one SSTable per
flush, up to ~35 small SSTables to merge per `SELECT` — a fragmentation normal compaction would not
produce. The ~100 ms absolute is therefore **inflated**. The true disk-bound cost lies **between**
the memtable figures (12–91 ms) and this fragmented worst case, and the OS page cache was never
dropped (no root), so "SSTable" does not mean "cold".

### I5 — The ADR marked action 1 "done" while a later measurement undermined it ⭑

**The finding.** Action item 1 was "reproduce the ×7.50 in a proven disk regime" and was ticked `[x]`
on the strength of M10. But M15 established that **no disk-bound read was ever measured**: M10 put a
*dataset* on disk, not the *probed read*, which stayed memtable-resident. Forcing the read onto disk
collapses the coefficient to ×1.52.

**What it undermines.** The ADR carried a closed action that a later measurement had partly
invalidated, without reopening it.

**Status:** corrected. The ADR's revision 11 reopened action 1 from `[x]` to `[~]`
(`docs/adr/ADR-001-modelling-policy.md`). What remains to close it truly: a disk-bound read *without*
the flush-per-update fragmentation M15 introduced, and with the OS page cache dropped (needs root,
unavailable). The RF and hardware confound between campaign 1 (RF 1, 3 GiB nodes) and campaign 3
(RF 3, 8 GiB nodes) also stands.

### I6 — Environmental contamination never quantified ⭑

**The finding.** Campaigns 4–6 ran on a ring carrying **6–13 GiB of `system.paxos` per node** and
third-party load (load average 14–16). The fills were LWT inserts (`INSERT … IF NOT EXISTS`) and
`paxos_state_purging = legacy` does not reclaim on compaction, so the residue accumulated from one
disk campaign to the next.

**What it undermines.** This memory and CPU pressure may have **slowed HCD** in M12, M13 and M16. It
was never measured and never subtracted. HCD's absolute figures are a noisy ceiling.

**What it does not touch.** The direction of M13 — the gap to MongoDB is two orders of magnitude, far
larger than any plausible contamination. Contamination that slows HCD makes the MongoDB result
*more* favourable to MongoDB, not less, so it cannot be the explanation of the gap.

### I7 — Statistical weakness ⭑

**The finding.** n = 30–50 per point, two passes, **medians only, no confidence intervals, no
significance test**. Between-pass variance of roughly 10–15 % (×1.92 against ×2.21 on the same
variant-A probe, `data/raw/findings.json`) is **larger than some of the claimed effects**. The
MongoDB fits are weak by construction: r² 0.7809 (default arm) and 0.8794 (wildcard arm)
(`data/raw/comparison_v2.json`) — near-zero slopes drowned in noise. A single sequential client:
**nothing about concurrency**, which is the production regime.

**What it undermines.** Any effect smaller than about 20 %. That includes the field-count term of
M11 (×1.13 / ×1.19 across two passes, `data/raw/findings_fieldbyte.json`), whose two passes straddle
the pre-registered 1.15 line at 1.128 and 1.187 and return no clean verdict.

**What it does not touch.** Effects of 40× and above, and the r² 0.9999 byte-series fits in the same
file, where the signal is not marginal.

**Note on the weak r² values:** they are not a defect of the MongoDB measurement — they *are* the
MongoDB result. A slope that close to zero is flat, and flatness is what was being tested.

### I8 — The comparison is never truly matched ⭑

**The finding.** HCD (a three-node ring, plus a Data API tier, plus a Paxos round) against MongoDB
(sometimes a 3-member replica set, sometimes single-member `atlas-local` for the freshness half).
**Two different MongoDB deployments** across campaigns 5 and 6. The tier and Paxos are inherent to
HCD, but they make this **stack against stack, not engine against engine**.

**What it undermines.** The precise multiplier of any cross-engine comparison.

**What it does not touch.** The mutation axis, where M14 measured the correction directly rather than
assuming it: removing the tier leaves the bare engine at 40× the wildcard arm. The **read** axis was
never corrected the same way (see C15), so the ~20× point-read gap still contains an unsubtracted
tier hop.

**And one asymmetry runs the other way:** MongoDB `j:true` waits for the journal fsync before
acknowledging; HCD's `commitlog_sync periodic 10 s` acknowledges **before** the fsync (up to 10 s of
acknowledged writes are loseable). In the matched pairing, **HCD acknowledged without waiting for the
disk and MongoDB waited** — a latency advantage handed to HCD. It still loses by 44×. This objection
strengthens the conclusion instead of weakening it (see C6).

### I9 — Magnitudes that are configuration or floor artefacts ⭑

**The finding.** The two headline magnitudes on the HCD-favourable axis are artefacts:

- The "~1 s of mongot lag" (M17, p50 1015.201 ms, `data/raw/findings_mongot_freshness.json`) is the
  **at-rest default of `atlas-local`** — a commit interval — not a property of MongoDB Search (C10).
  **Upgraded from inference to pinned fact on 18 September 2026.** The image was interrogated directly:
  `mongot` is version **1.75.1**, edition **`localDev`** — the string is read verbatim from
  `/etc/mongodb-atlas-local/mongot-edition` inside the image and repeated in the image label
  `mongot-edition=localDev` (`data/raw/findings_mongot_provenance.json`). `localDev` is the edition
  MongoDB ships for local development; it is **not** the search tier that serves Atlas. So M17, M18 and
  M19 may not be quoted as "MongoDB Atlas Search lag", as "MongoDB's search freshness", or as any
  property of MongoDB the product. They characterise `mongot` 1.75.1 `localDev` beside a single-node
  replica set on a loaded shared host. Note also what the interrogation did **not** find: the commit
  interval is not exposed in the launch script, the README or any image environment variable, so the
  ~1015 ms and the ~1.1 s interval remain **empirical observations of this build**, not a documented
  default that was read off.
- "HCD synchronous, zero lag" is **"under 45 ms, below the HTTP floor"** (p50 44.972 ms, poll
  attempts median 1, `data/raw/findings_hcd_vec_freshness.json`), not a proven zero (C11).

**What it undermines.** Both numbers as stated.

**What it does not touch.** The architectural difference, which is the fact: HCD maintains its search
index on the write path, MongoDB's mongot ingests asynchronously through a change stream. M19 later
bounded the consequence exactly (see D1).

---

## 3. Challenges (C1–C15, D1–D5)

The challenge documents were written in three passes: **C1–C9** against campaigns 1–5, **C10–C15**
against campaign 6 (the axes favourable to HCD), and **D1–D5** against the author's own measured
closure of C10. Four challenges were then closed by new measurement — C1, C2, C10 and D1 — and one of
them refuted the challenger.

### C1 — M13 compares STACKS, not storage engines ⭑ (the strongest of the first pass)

**The challenge.** The 44× and 79× set **HCD driven by the Data API** — HTTP, JSON parsing,
shredding, **plus a Paxos round** — against **MongoDB driven by its native driver**. Since M12 put
~29 % of HCD's cost in the stateless tier, an honest engine-to-engine comparison would drive HCD
through direct CQL. Subtracting the tier gives a storage term of ~0.55 ms/KiB and a ratio of ~31×.

**Resolution — the challenge was PARTLY REFUTED by measurement, against the challenger.** An
HCD-CQL-direct arm (`probes/hcd_cql_arm.py`, same host, same series, matched cache regime,
`--compare` gate permitted) measured:

| Arm | Slope (ms/KiB) | r² |
|---|---|---|
| mongo-default | 0.0098 | 0.7809 |
| mongo-wildcard | 0.0176 | 0.8794 |
| **hcd-cql-direct** (bare engine, tier removed) | **0.7037** | 0.9959 |
| hcd via Data API (full stack) | 0.7775 | 0.9970 |

Source: `data/raw/comparison_v2.json`. Removing the tier lowers the slope by only **9 %**, not the
29 % extrapolated from M12. **Engine against engine: 40× the wildcard arm, 72× the default arm** —
against 44× and 79× for the stack. **The challenger's ~31 % estimate was wrong: HCD's disadvantage is
almost entirely in the storage engine, not in the tier.** MongoDB's win is an engine result, not a
stack artefact.

**What survives of the challenge:** the tier/storage split remains unstable between regimes (9 % here
in cache with separated arms, 29 % in M12's disk regime with interleaved arms) — this is finding I3,
and it does not change the fact that ~90 % of the slope is storage.

### C2 — No genuinely disk-bound RMW measurement exists anywhere in the dossier

**The challenge.** Campaign 3 is titled "disk regime" and M10 is labelled "the coefficient holds
under disk". But the RMW probe **re-reads the row it has just written** — hot, memtable-resident,
whatever the dataset size. Filling 6.05 GiB creates *memory pressure*; it never puts the probed row
on disk. Action item 1 wanted reads forced from disk; it got a *dataset* on disk, not a *read* from
disk.

**Resolution — CONFIRMED, with a new caveat of its own.** A post-flush pass
(`probes/rmw_postflush.py`, `nodetool flush` before each update, so the internal `SELECT` touches an
SSTable):

| Size | Memtable (M10, disk-regime dataset) | **Post-flush (SSTable)** |
|---|---|---|
| 1 KB | 20.389 ms | **107.765 ms** |
| 128 KB | 121.189 ms | **163.402 ms** |
| **growth** | **×5.94** | **×1.52** |

Sources: `data/raw/findings_disk_rf3.json`, `data/raw/rmw_postflush.json`. Two lessons: (a) the
challenge held — the RMW read had never left the memtable, and forcing it out adds a massive fixed
cost; M10's label overreached; (b) **the per-byte coefficient collapses** once the read is
disk-bound, so the 0.77 ms/KiB at the heart of section 3 is a **memtable-regime phenomenon**.

**New declared caveat (already stated in I4):** flush-per-update fragments the SSTables and inflates
the ~100 ms absolute. The true disk-bound cost lies between the memtable figures and this worst case.

### C3 — The Paxos cost is measured without network latency

**The challenge.** M5 observes a full three-replica Paxos round — a real gain over campaign 1's
trivial RF 1 — with coordinator-side p50 of **13.738 ms for `UPDATE … IF` against 6.582 ms for a
non-conditional `SELECT`** (`data/raw/findings_rf3.json`). But the three dc1 replicas **share one
host**: inter-replica latency is sub-millisecond. Consensus is measured exactly where it hurts least.
On a real multi-host or wide-area deployment a Paxos round costs tens of milliseconds.

**What it undermines.** Every absolute figure, for any topology other than this one. Note the
direction: this objection works **against** HCD in production, so it does not flatter the dossier —
the M13 gap would widen, not narrow.

**What it does not touch.** The structure. The message sequence is traced
(`PAXOS2_PREPARE_REQ` 370 B → `PAXOS2_PREPARE_RSP` ≈263 KB → `PAXOS2_PROPOSE_REQ` ≈131 KB → commit;
232 `PAXOS_COMMIT` events over 30 sessions) and is independent of sizing.

### C4 — One host, one build, a shared VM

`alphadebunker`; HCD 2.0.6 (`nodetool version` 5.0.7.0-ea50e91ba01f); Data API v1.0.33; MongoDB
8.0.32 (replica set) and 8.3.11 (`atlas-local`). Nothing transposes. **The physical storage class was
never established** — the disk is a QEMU virtual SCSI device on ext4, `rotational=1` is the QEMU
default rather than evidence of media, and neither `smartctl` nor root was available; measured
effective throughput was 101 MB/s on a sequential `dd` with fsync
(`docs/campaigns/03-disk-regime.fr.md`). A bench on dedicated NVMe, or on slow network storage, would
give different absolutes. **Declared everywhere; still the parent limitation.**

### C5 — The measurer wrote and corrected instruments

The same ground as I2, stated as scope rather than integrity: verdicts resting on an **unmodified**
supplied script (M11 field/byte, M13 through an intact `probes/probe_comparative.py`) are firmer than
verdicts resting on the measurer's own code (M2's trace tooling, M12's method 2).

### C6 — M13's durability matching favours HCD, not MongoDB

MongoDB `j:true` waits for the journal fsync before acknowledging; HCD's `commitlog_sync periodic
10 s` acknowledges before the fsync. In the pairing, HCD acknowledged without waiting for disk and
MongoDB waited — and HCD still lost by 44×. **This objection reverses: it strengthens the "MongoDB
wins" conclusion.** It should be stated explicitly rather than buried, because it turns an apparent
weakness into robustness.

### C7 — M12 publishes no precise split, and its arm B is artificial

The two methods diverge by more than 25 % at the large sizes; 29 % / 19 % is a range, not a point.
Arm B **reuses already-shredded values** and therefore never exercises the shredding code — so its
"storage" figure is an optimistic floor and the "tier" term may be over- or under-estimated. The tier
term **aggregates** parsing, shredding and serialisation without separating them, and part of it is
client-library cost (`data/raw/findings_tier.json`, `known_confounds`). **The 70/30 is a direction,
not a figure.** C1 depended on it, which is exactly why C1's extrapolation failed.

### C8 — The Paxos residue may contaminate its own measurements

Campaigns 4 and 5 ran on a ring already carrying **6–13 GiB per node of unpurged `system.paxos`**.
That mass creates background memory and compaction pressure that may have slowed HCD in M12 and M13.
Probably a small effect, **uncontrolled, never quantified**. A clean bench would restart on a ring
with an empty paxos table. (Same substance as I6.)

### C9 — A single axis, and it is the axis where HCD is expected to lose

M13 measures the mutation of one field — precisely where decomposition is expensive **by design**.
At that point the dossier measured **nothing** of filtered reads, vector search, aggregation, or
index freshness at acknowledgement — the axis where HCD has its structural advantage. **A dossier
that measures only the unfavourable axis is as biased as a flattering one.** This was the largest
coverage gap in the first pass, and campaign 6 was written to close it.

---

### C10 — The "~1 s mongot lag" is almost certainly a configuration DEFAULT, not a floor ⭑ (strongest of the campaign-6 pass)

**The challenge.** mongot ingests through a change stream and commits its index on a configurable
interval. The measured ~1015 ms was remarkably **stable** (stdev 35.172 ms, median 34 poll attempts
≈ 34 × 20 ms of polling plus a fixed commit interval,
`data/raw/findings_mongot_freshness.json`) — the signature of a periodic interval, not of work. What
survives is the direction (async against sync); what falls is the figure.

**Resolution — CONFIRMED, and it corrects the author's own measurement.** De-synchronising the
insert from the commit cycle (random 0–1200 ms delay before each write, then 5 ms polling) shows the
lag is **broad, not tight** (n = 60, `data/raw/findings_mongot_floor.json`):

| | min | p10 | p50 | p90 | max | stdev |
|---|---|---|---|---|---|---|
| de-synchronised `$search` lag (ms) | **89.1** | 254.5 | **664.3** | 988.7 | **1170.2** | 290.8 |

**Verdict: a Lucene-style refresh interval of roughly 1.1 s, not a fixed delay.** M17's ~1015 ms was
the **worst phase** of the cycle, amplified by the probe's self-synchronisation — each cycle waited
for the next commit, so each insert landed just after one. On the medians the correction is
1015.201 ms → 664.3 ms. (The campaign text and the ADR quote an arithmetic mean from the same
record; this file quotes percentiles only, per the dossier's rule.) The interval is **not tunable**
in `atlas-local`: no configuration file, no exposed flag — it is an internal default of the mongot
binary.

**And the corrected figure is still not MongoDB's.** A provenance check on 18 September 2026 pinned the
build: mongot **1.75.1**, edition **`localDev`** (`data/raw/findings_mongot_provenance.json`, and see I9
and D2 above). So neither 1015.201 ms nor the corrected 664.3 ms is a property of MongoDB Atlas Search;
both characterise the local-development edition. The same check also confirmed that the interval is
exposed nowhere in the image — launch script, README, environment — so "roughly 1.1 s" remains an
**inferred** interval from an observed distribution, not a default that was read off. C10's resolution
therefore corrected the magnitude and **could not** establish the mechanism by direct reading.

**What it does not touch.** The direction. HCD remains synchronous, and mongot's **floor** (~89 ms)
already exceeds HCD's HTTP floor.

### C11 — "HCD synchronous, zero lag" is really "lag under 45 ms", below the HTTP floor

`attempts = 1` means "found on the first query" — but that query arrives ~45 ms after the write (the
HTTP round trip). **An HCD index lag anywhere between 0 and 45 ms would be undetectable.** The honest
statement is "HCD lag < 45 ms (below the measurement floor) against a mongot 1.75.1 `localDev`
refresh interval whose corrected p50 is 664.3 ms (M18, `data/raw/findings_mongot_floor.json`)" — not
"for MongoDB", which the provenance check forbids (I9, D2, C10) — a gap of about **14.8×** on the
medians (664.3 / 44.972), not the 22× that the superseded, self-synchronised p50 of 1015.201 ms gave
(C10 above); direction robust, **but zero is not proven**. This is the same limit M7 recorded on the
vector axis, where 120/120 cycles found the just-written vector top-1 on the first `LOCAL_ONE` search
and the verdict was recorded as NOT DETECTABLE rather than as a confirmation.

### C12 — The auto-index advantage (22×) is a win against a DEFAULT MongoDB, not a competent one

A team that queries a field regularly **declares an index on it**; it does not suffer the 376.698 ms
collection scan (`data/raw/findings_rs_mongo.json`). Against a MongoDB properly indexed on that
field, **MongoDB wins**: 0.732 ms against HCD's 17.376 ms (`data/raw/findings_rs_hcd.json`). HCD's
real advantage is therefore not speed but the **dispensation from index design** — you never pay for
the index you forgot. That is a genuine operational convenience, not engine superiority. The 22×
compares HCD to a badly configured MongoDB.

### C13 — The freshness win is bounded to the SEARCH path, not "freshness" in general

On an **ordinary secondary index**, freshness is a **tie**: all three arms found the just-written
document on the first query (attempts histogram `{"1": 40}` on both the HCD and the MongoDB wildcard
arms). MongoDB's asynchronous lag bites only `$search` and `$vectorSearch` — that is, workloads that
write and then immediately search full-text or vectors. An ordinary read-your-writes on MongoDB goes
through a synchronous b-tree index with no lag. **HCD's win is real and scoped to RAG-style search,
not global.**

### C14 — Text against vector: the two halves do not measure the same path

HCD was measured on **vectors** (JVector) against MongoDB on **text** (`$search`). The
synchronous-versus-asynchronous architecture is the same, but a purist demands like for like: HCD
lexical (BM25) against MongoDB `$search`, or HCD vector against MongoDB `$vectorSearch`. The
freshness of HCD's lexical path and of mongot's `$vectorSearch` **was not measured**. The
generalisation is architectural, not four-cornered. **D4 records that C14 was never resolved.**

### C15 — Two different MongoDB deployments in one campaign, and the tier tax not subtracted

The freshness half ran on `atlas-local` (mongot, **single member**); the read and search halves on
the **3-member** replica set. These are not the same MongoDB. And as in C1, HCD's point-read
disadvantage (~20×, p50 10.382 ms against 0.53–0.616 ms) is largely the **Data API tier hop** — an
HCD-CQL-direct arm would narrow it. **That arm was run for mutation (M14) and never for reads**, so
the ~20× read gap remains stack-against-engine.

---

### D1 — The sub-second search lag may be MOOT for the very RAG use case that motivates it ⭑⭑

**The challenge, against the author's own closure of C10.** Section 4.1 invokes RAG to justify why
freshness matters: write a fact, search for it on the next turn. But **a RAG turn takes seconds** —
LLM generation alone is 1 to 10 s — while MongoDB's search lag is under ~1.2 s at worst. By the time
the application reads back, the refresh interval has expired and the document **is** searchable. The
window bites only if write-then-search happens in under ~1.1 s. **HCD's synchronous-freshness
advantage is real and measured, but possibly of no operational consequence for the use case that
motivates it.**

**Resolution — CONFIRMED and quantified.** Miss rate of a search issued τ ms after the write, 30
cycles per point (`data/raw/findings_turn_mongodb.json`, `data/raw/findings_turn_hcd.json`):

| Write→search delay τ | **MongoDB `$search`** | **HCD** |
|---|---|---|
| 0 ms | **100 %** | 0 % |
| 100 ms | 93.3 % | 0 % |
| 250 ms | 83.3 % | 0 % |
| 500 ms | 50 % | 0 % |
| 750 ms | 33.3 % | 0 % |
| **1000 ms** | **0 %** | 0 % |
| 1500 / 2000 / 3000 ms | 0 % | 0 % |

What this establishes exactly:

- **For conversational RAG, HCD's advantage is moot.** An LLM-driven turn lasts 1–10 s; at τ ≥ 1000
  ms MongoDB **never** misses the document. Section 4.1's correctness argument, applied to
  conversational RAG, is **overstated**.
- **For sub-second write-then-search, HCD's advantage is real and decisive.** At τ = 0–500 ms
  MongoDB misses **50–100 %** of documents and HCD misses **0 %**. Agentic tool chains, tight
  ingestion loops and automated pipelines get from HCD a correctness property MongoDB `$search` does
  not give.
- **The scope is bounded at ~1 s**, and the dossier can now say so instead of assuming it.

### D2 — `atlas-local` is not production Atlas; the number does not transfer

The article cites "MongoDB 8.x", meaning production Atlas, not `atlas-local`. The ~1.1 s refresh
interval is the default of a **single-node development container**. Production Atlas (multi-node,
dedicated mongot, tuned) may be faster or slower — unknown. The measured figure characterises a
deployment **nobody runs in production**.

**Confirmed by direct evidence, 18 September 2026 — this challenge is no longer an inference.** The
image self-identifies: `mongot-edition=localDev`, `mongot-version=1.75.1`
(`data/raw/findings_mongot_provenance.json`). MongoDB itself labels this build as the local-development
edition. D2 therefore stands as **confirmed**, not merely plausible, and it is the single strongest
reservation on the whole HCD-favourable axis: the one axis the article claims most confidently for HCD
was measured against a MongoDB build its own vendor does not ship for production use.

### D3 — The ~90 ms floor is a FIXED component that the first verdict passed over

The distribution is not a pure refresh interval from 0 to T: the minimum is **89.1 ms, not ~0**. The
honest model is **~90 ms of fixed ingestion plus a refresh phase on top**. mongot is therefore
**never** instantaneous. This *strengthens* the direction for HCD, but the verdict "refresh interval,
floor ~0" recorded in `data/raw/findings_mongot_floor.json` is imprecise on its own terms.

### D4 — Still text against vector (C14 unresolved)

M18 measures MongoDB **text `$search`**; M17's HCD arm was **JVector vectors**. mongot's
`$vectorSearch` (same async pipeline, same interval) and HCD's lexical path were never measured. Two
different paths are still being compared, and the generalisation is architectural.

### D5 — n = 60, one pass, verdict by a heuristic the author wrote

No repetition; the distribution could move by tens of milliseconds on a replay. And the
classification "refresh interval versus fixed delay" is a threshold in the author's own code
(`near_zero and spread > 0.5 * max`, `probes/mongot_floor.py`), not a statistical test. The shape
(min 89.1, max 1170.2, stdev 290.8) supports it, but it is a judgement, not a proof.

---

## 4. What survives without a scratch

Three measurements and one class of result come through the audit and the challenges intact. They
are stronger than the rest **for a stated reason in each case**, not by assertion.

### M1 — The shredded layout: 12 columns, 9 SAI indexes

Twelve physical columns on a collection created with defaults — the nine generic columns the
practitioner literature names, plus `key` (the typed partition key), `tx_id` (a timeuuid guarding
every conditional write) and `query_lexical_value`. Nine storage-attached indexes were created
automatically on a collection that declared no vector option. Source: `data/raw/findings.json`.

**Why it is stronger.** It is a direct read of the engine's own schema tables
(`system_schema.columns`, `system_schema.indexes`), taken twice with identical results, through a
supplied script. It contains no timing, so **none of I1, I6 or I7 touches it**. A different build can
change the answer; the observation of *this* build cannot be argued with.

### M2 — The read-modify-write cycle: `SELECT` → `UPDATE … IF`, 11 assignments

Every `updateOne` carrying a single `$set` produced exactly two CQL statements: `SELECT key, tx_id,
doc_json WHERE key = ?`, then one `UPDATE` rewriting nine derived columns plus `tx_id` plus the whole
`doc_json`, guarded by `IF tx_id = ?`. Observed **10 of 10** traced operations. Statement counts:
`insertOne` = 1, `updateOne` = 2, `deleteOne` = 2. Source: `data/raw/findings.json`.

**Why it is stronger.** It is a query trace, not a latency curve. It is the *only* evidence that
carries the cycle claim at all — the latency probe was ruled INCONCLUSIVE by the author's own
pre-registered read-control rule (update growth ×1.92 / ×2.21 against a same-size read control of
×1.86 / ×1.94, `data/raw/findings.json`), which is itself a result that went against the author.
Because it is an observation of mechanism rather than of cost, **I4 does not touch it**: the
mechanism holds in every regime, even where the coefficient collapses.

### M11 — Indexed bytes dominate field count

At a fixed indexed volume of 64 KiB, raising field count from 9 to 128 (×14) moved the update p50
only **×1.13 and ×1.19** across two passes (series fits r² 0.5745 and 0.9154). At a fixed 16 fields,
raising bytes per field from 512 to 8000 moved it **×4.6**, with straight-line fits of **r² 0.9999 on
both passes**. The internal control (16 × 4096 B, measured in both series) spread 2.0 % and 0.7 %.
Source: `data/raw/findings_fieldbyte.json`; probe `probes/probe_field_vs_byte.py`, supplied and
unmodified.

**Why it is stronger.** The fit is r² 0.9999 on the decisive series, the two series cross-check each
other through a shared control point, and the probe is a supplied script the measurer did not write —
so **I2 does not touch it**.

**The caveat that must travel with it:** the pre-registered rule returns **no clean verdict**. The
two passes straddle the 1.15 "bytes dominate" line at 1.128 and 1.187. Neither approaches the 1.5
that would make field count an independent driver, so the *direction* is unambiguous, but the strict
rule says INCONCLUSIVE and this dossier does not quietly upgrade it.

### The directions, everywhere

The audit confirms that the **directions** survive every challenge, while the magnitudes do not:

| Direction | Survives because | Magnitude caveat |
|---|---|---|
| HCD is more expensive on single-field mutation | 40× after the tier is removed by measurement, not estimate (M14); the durability pairing favoured HCD (C6) and it still lost | The multiplier is a cache/memtable figure (I4, C2) |
| MongoDB has a search-freshness window HCD does not | Confirmed on both sides; MongoDB's own floor (~89.1 ms) exceeds HCD's HTTP floor | ~1 s is an `atlas-local` default (C10, D2); HCD's "zero" is "< 45 ms" (C11); decisive only under ~1 s (D1) |
| Indexed bytes, not field count, drive the mutation cost | r² 0.9999, unmodified supplied script (M11) | Strict verdict INCONCLUSIVE at the 1.15 boundary |
| MongoDB wins point reads on this deployment | 0.53–0.616 ms against 10.382 ms | Contains an unsubtracted Data API tier hop (C15) |
| HCD's automatic indexing avoids a collection scan on an undeclared field | 376.698 ms scan against 17.376 ms | Only against a *default* MongoDB; a wildcard index beats HCD at 0.732 ms (C12) |

### The ring restoration

At every campaign: 20 SAI indexes recreated == 20 captured definitions, experiment keyspaces dropped,
snapshots purged on all six nodes, tracing verified back at 0.0. Verified each time; the one declared
residue is `system.paxos`, which `paxos_state_purging = legacy` would not reclaim.

---

## 5. What this repository cannot tell you

- **One host.** Everything ran on `alphadebunker`, a shared QEMU VM (80 vCPU Xeon Gold 6148 @
  2.40 GHz, 220 GiB RAM), at a **load average of 14–16** throughout, alongside Presto, streaming and
  Jupyter workloads that were never quantified or subtracted. Absolute latencies are a noisy ceiling.
- **One build of each engine.** HCD 2.0.6 (`5.0.7.0-ea50e91ba01f`) with Data API v1.0.33; MongoDB
  8.0.32 as a 3-member replica set and 8.3.11 as single-node `atlas-local`. Nothing transposes to
  Apache Cassandra 5.0.x/6.0, to another HCD or Data API version, or to production Atlas.
- **No multi-host and no WAN topology.** The three dc1 replicas share one host, so inter-replica
  latency is sub-millisecond and the Paxos round is measured where it costs least (C3). On a real
  multi-host deployment the consensus cost rises into tens of milliseconds and the mutation gap
  widens. Equally, the `vector-search = LOCAL_ONE` staleness window recorded in M6 is a WAN concern
  that this co-located ring cannot reproduce — M7 returned NOT DETECTABLE, not "absent".
- **No concurrency.** Every probe is a **single sequential client**. There is nothing here about
  contention, queueing, thread pools, or behaviour under parallel load — which is the production
  regime.
- **Closed-loop probes, not a fixed offered rate.** One operation, then the next. Only the freshness
  probe used an offered rate (50 writes/s for 120 s, slippage 0.055–0.078 s). This breaks requirement
  1 of the article's own section 10, and it means nothing here characterises saturation or a
  latency-throughput curve.
- **The storage class was never established.** The data directory is `/dev/sda1` (ext4) on a **QEMU
  virtual SCSI disk**. `rotational=1` is the QEMU default, not evidence of physical media; neither
  `smartctl` nor root was available. Measured effective throughput was 101 MB/s on a sequential `dd`
  with fsync. Every I/O-sensitive figure is therefore a figure for an unidentified virtual disk.
- **The OS page cache was never dropped.** Dropping it needs root on the host, which was not
  available. "Disk-bound" in campaign 3 means the dataset exceeded the memtable budget and lived in
  SSTables — proven: 6.05 GiB on disk (6 491 369 675 bytes), 40 SSTables after a major compaction,
  the compaction counter crossing 651 → 729 (78 compactions), caches invalidated
  (`data/raw/disk_state.json`; campaign 4's equivalent state 875 → 951, `data/raw/disk_state_c4.json`).
  It does **not** mean any given read missed RAM. The 6.05 GiB dataset fits comfortably in 220 GiB of
  host memory.
- **No means for latency.** This dossier publishes percentiles only. Where a source file also records
  an arithmetic mean, this document quotes the percentiles from the same record.
- **Two axes were never measured at all.** Vector ANN search performance (as opposed to vector
  freshness, which M7 could only bound below the HTTP floor), and the freshness of HCD's lexical path
  against mongot's `$vectorSearch` (C14 / D4, explicitly unresolved).
- **Campaign 7 has a report, but no adversarial verdict.** `data/raw/findings_agg_hcd.json`,
  `data/raw/findings_agg_mongodb.json` and `data/raw/findings_agg_cqlref.json` were produced by
  `probes/probe_aggregation.py` and `probes/agg_cql_arm.py`, are covered in full by the campaign
  report `docs/campaigns/07-aggregation.fr.md`, and carry the identifiers M20–M23. What they do not
  carry is an adversarial verdict: `docs/audit-adversarial.fr.md` is written against M1–M17 over six
  campaigns, `docs/challenges.fr.md` against M1–M13, and neither document examines the aggregation
  axis. **No figure from M20–M23 has been challenged**, so each stands on the reserves its own report
  attaches to it — the HCD scan arm's n = 3, the cache regime that M22's zero proves, the
  apples-to-oranges label the CQL arm carries in its own result file — and on nothing beyond them.
- **Reproduction is not possible in the strict sense.** The ring's state mutated across campaigns
  (`system.paxos` from 0 to ~13 GiB per node; the 20 `supply_chain_hcd` indexes dropped and recreated
  six times), and the machine was never idle. What can be reproduced is the *method*: the probes are
  in `probes/`, the raw records in `data/raw/`.

---

## 6. The one-paragraph summary an honest reader should leave with

Decomposition makes single-field mutation expensive on HCD, measurably, and MongoDB is structurally
cheaper on that axis — that direction is solid and was measured with the durability pairing tilted in
HCD's favour. HCD does have a search-freshness property MongoDB's `$search` lacks, and it is total
where it applies (0 % misses against 100 % at τ = 0) and moot beyond about a second. Everything else
is a number attached to a regime: the flagship growth factor ranges over ×7.50, ×5.94 and ×1.52
depending on whether the read touches the memtable or an SSTable, and the Data API tier's share of
the cost is 9 % or 29 % depending on which campaign you read. **Neither engine leaves this dossier
with an advantage as clean as its first figure suggests — and that is the only result six campaigns
on one shared host permit anyone to publish.**
