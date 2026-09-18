# STATISTICS — what may and may not be inferred from this dossier

> **Scope.** This document performs the statistical re-analysis the seven campaigns never
> performed, over the evidence they left behind. It adds no measurement. Every figure below
> is read from a file under [`data/raw/`](../data/raw/), and every row names the file and the
> path inside it. Nothing under `data/raw/` was modified, moved or regenerated to
> produce this document; the machine-readable form of everything here is
> [`data/derived/inference.json`](../data/derived/inference.json).
>
> It is written in English, like [`METHODOLOGY.md`](../METHODOLOGY.md),
> [`RESULTS.md`](../RESULTS.md) and [`LIMITATIONS.md`](../LIMITATIONS.md), rather than in the
> French of the campaign reports.
>
> **It narrows what may be claimed. It does not strengthen anything.** Both of the axes on which
> HCD comes out ahead fail it; so does the dossier's own account of where the per-byte cost is
> charged; and the two measurements that reframed the flagship per-byte coefficient cannot be
> tested at all, because their records are too thin.
>
> **Headline of §3:** of 93 cross-engine or cross-arm comparisons enumerated from
> [`RESULTS.md`](../RESULTS.md), **56 are DISJOINT** (direction certain without any distributional
> assumption), **34 are OVERLAPPING** (nothing established), and **3 cannot be tested at all**.

---

## 1. The statistical policy of this dossier, and why percentiles only

The policy is stated in [`METHODOLOGY.md` §"Statistics"](../METHODOLOGY.md) and is short enough
to restate exactly: **this dossier publishes no means for latency.** Every probe emits the same
`distribution()` shape — `n`, `min_ms`, `p50_ms`, `p95_ms`, `p99_ms`, `max_ms` and a population
standard deviation — and all cross-arm comparison is done on `p50_ms`.

The reason is not stylistic. Service-time distributions on a loaded shared host are not
symmetric and are not light-tailed, and the records in this repository show it directly: at
16 × 1024 B, pass 1, the HCD Data API arm has p50 43.632 ms, p95 70.375 ms, p99 326.149 ms and
max 429.927 ms ([`cmp_hcd.json`](../data/raw/cmp_hcd.json)). A single mean over that sample
would be a number that describes no operation anybody performed, and its standard deviation of
69.344 ms would license an interval that the distribution's own shape contradicts. A median is
a statement about rank and survives the shape; a mean does not.

Two consequences follow, and they bind this document too.

1. **`stdev_ms` is present in almost every record and is used nowhere below.** A standard
   deviation over an unknown, visibly heavy-tailed distribution supports no confidence interval
   and no *t*-like test. Reaching for it because it is the only dispersion measure left would be
   exactly the move the percentiles-only policy exists to prevent.
2. **The policy was broken once, and the dossier says so.** The freshness records
   ([`findings_mongot_freshness.json`](../data/raw/findings_mongot_freshness.json),
   [`findings_hcd_vec_freshness.json`](../data/raw/findings_hcd_vec_freshness.json),
   [`findings_mongot_floor.json`](../data/raw/findings_mongot_floor.json)) each carry a
   `mean_ms`, and the campaign prose quotes the `mongot` mean of 646.3 ms in several places.
   This document uses the percentiles in the same records — for `mongot`, p50 **664.3 ms** — so
   that one axis is not quoted on a different statistic from every other axis.

A third point belongs here rather than in a footnote, because it is the premise of everything
that follows. **The campaigns computed no confidence interval and ran no significance test,
anywhere.** Verdicts came from pre-registered thresholds — a read-control growth rule, a
`tier_dominates` trigger, an S2-ratio band — which are decision procedures, not inference. They
were declared in advance, which is a real methodological virtue and is why several of them
returned INCONCLUSIVE against the author's interest. They are still not tests, and the dossier
has never claimed they were.

---

## 2. The artefact defect: the raw series were discarded

**Verify this first, because everything in §3 is a consequence of it.**

Of the 36 files under `data/raw/`, 25 carry at least one latency distribution. Of those 25,
**exactly two preserve the individual observations**:
[`vector_freshness_idle.json`](../data/raw/vector_freshness_idle.json) and
[`vector_freshness_loaded.json`](../data/raw/vector_freshness_loaded.json), each holding a
60-element `cycles[]` array with a per-cycle `insert_to_vec_visible_ms`. Every other
latency-bearing file stores the summary and nothing else. The observations that produced the
summary are gone: the probe processes exited, no vector was serialised, and no third party can
recover them.

Two records are thinner still, and both matter more than the rest:

| File | What it stores | Why it matters |
|---|---|---|
| [`rmw_postflush.json`](../data/raw/rmw_postflush.json) | `n`, `p50_ms`, `p95_ms`, `p99_ms`, `max_ms`, `stdev_ms` — **no `min_ms`** | This is M15, the measurement that overturned the dossier's flagship per-byte coefficient (×7.50 → ×1.52). It is the one measurement in the repository on which separation of support cannot be evaluated at all. |
| [`findings_disk_rf3.json`](../data/raw/findings_disk_rf3.json) | four `p50` values per variant — **no `n`, no `min`, no `max`, no percentiles** | This is M10, the ×5.94 disk-regime coefficient. Same consequence. |

So two of the three values of the dossier's most-quoted quantity — the ×7.50 / ×5.94 / ×1.52
interval that audit finding I4 identifies as the artefact's central instability — rest on
records too thin for any test whatsoever.

### What this forecloses, permanently, for a third party

- **Bootstrap confidence intervals** on any latency claim in this repository. Resampling needs
  the sample.
- **Rank tests** — Wilcoxon rank-sum / Mann–Whitney *U* — on any cross-engine latency claim
  except the vector-freshness pair of §3.16. Ranks need the observations.
- **Distribution fitting, tail-index estimation, modal analysis.** The p99/max pairs in
  [`cmp_hcd.json`](../data/raw/cmp_hcd.json) — 326.149 / 429.927 ms at 16 KiB, 360.077 /
  467.906 ms at 64 KiB pass 2 — are the visible edge of a bimodality (a garbage-collection
  pause, a flush, a Paxos retry) that cannot now be characterised, separated out, or shown to
  be independent of the treatment.
- **Re-aggregation across passes.** Each mutation point was measured twice, n = 30 each. Those
  are 60 observations of the same configuration and they cannot be pooled, because pooling
  percentiles is not an operation.
- **Any re-analysis at a percentile the probe did not emit.** There is no p75, no p90 outside
  the freshness records, no p999 outside campaign 1.
- **Any check of the probes' own percentile arithmetic.** The interpolation rule inside
  `distribution()` cannot be verified against data it no longer has.

This is a **first-class reproducibility defect**, and it is of a different kind from the
limitations the dossier already declares. A shared host, a single build, a memtable regime, a
closed loop — those are stated conditions that a future run can change. A discarded sample is
not a condition; it is a loss. The measurements can be *repeated*, but they can never be
*re-analysed*, and repetition on a different host in a different month answers a different
question. `probes/*.py` should have written the sample vector beside the summary, and did not.

### What survives the defect

Three classes of result are untouched by it, and they are, not coincidentally, the dossier's
strongest.

- **Structural results.** M1 (twelve physical columns, nine SAI indexes), M2 (the read-modify-write
  cycle in 10 of 10 traces), M20 (no `aggregate`, no `$group`, no `distinct` — `COMMAND_UNKNOWN`),
  M21 (`TooManyDocumentsToCountException` above 1 000 documents), M22
  (`estimatedDocumentCount()` returning 0 against a true count of 200 000). These are established
  by observation, not by *n*. Statistics neither strengthen nor weaken them.
- **Counts.** [`findings_turn_hcd.json`](../data/raw/findings_turn_hcd.json) and
  [`findings_turn_mongodb.json`](../data/raw/findings_turn_mongodb.json) store miss *counts*, not
  latencies, and counts admit an exact test with nothing discarded — §3.17.
- **Minima and maxima.** They are the whole of what §3 uses, and they are exactly enough to
  settle direction when the two arms do not overlap — and exactly not enough when they do.

---

## 3. Separation of support

### 3.1 The method, and the reason it is the only one available

For two arms with observed ranges `[min_A, max_A]` and `[min_B, max_B]`:

> If the ranges are **disjoint**, then every single observation of one arm beat every single
> observation of the other. The direction of the effect is then certain **with no distributional
> assumption at all** — no normality, no equal variance, no symmetry, no independence of the
> value from its size.

Under exchangeability of the pooled sample, the probability that one pre-specified arm of size
*n*<sub>A</sub> occupies all the extreme ranks against an arm of size *n*<sub>B</sub> is

```
p = 1 / C(n_A + n_B, n_A)
```

which is reported below as a one-sided exact permutation *p*-value. (The two-sided value is
twice it.) It is also the **smallest** *p*-value the Wilcoxon rank-sum / Mann–Whitney *U*
statistic can attain at those sample sizes: complete separation is the most extreme rank
configuration that exists.

If the ranges **overlap**, then with summary statistics alone **nothing follows about
significance**. Not "the effect is small", not "the difference is probably real anyway" — just
nothing. The observations that would settle it were discarded. This document says "not
established by these data" in every such row and does not reach for `stdev_ms`.

Alongside each comparison, two effect-size statements:

- **the ratio of medians**, `p50_slow / p50_fast`, as a point estimate; and
- **the ratio interval**, `[min_slow / max_fast, max_slow / min_fast]` — the widest honest
  statement of effect size obtainable from summary statistics. Where it **spans 1.0** (marked
  ⚠︎), the direction is not established.

Note the identity, which is worth stating so that no reader treats the two as independent
confirmations: **the ratio interval contains 1.0 if and only if the supports overlap.** They are
the same test written twice. Both are given because readers reach for different ones.

### 3.2 Four warnings about how to read the matrix

1. ***p* here measures *n*, not effect size.** Every 30-versus-30 disjoint comparison in the
   matrix returns the identical value 8.46 × 10⁻¹⁸, whether the ratio of medians is 1.96× or
   18.89×. The *p*-value is a function of the sample sizes and the fact of separation, and of
   nothing else. It is reported because the task of a significance statement is to rule out
   chance ordering, and it does that. **It must never be quoted as a measure of how large or how
   important an effect is.** The ratio interval is the quantity that carries magnitude.
2. **Exchangeability is doubtful here, and that weakens the *p*-values, not the separations.**
   The permutation argument assumes the pooled observations are exchangeable under the null.
   Every probe in this repository except the freshness probes is a **closed-loop sequential
   client** on a shared host at load average 14–16, so successive observations within an arm are
   serially correlated; and the arms were run in **blocks separated in time**, not interleaved —
   M14's own caveat says so explicitly for the CQL arm. Under serial correlation the effective
   sample size is below *n* and the true *p* is larger than the tabulated one. Read the
   *p*-values as *the best a rank test could possibly do at this n*, not as an achieved
   significance level. The **separation itself** — the statement that every observation of one
   arm beat every observation of the other — is a fact about the data and is not affected.
3. **OVERLAPPING does not mean "no effect".** It means the evidence needed to decide was thrown
   away. `RS-A-HCD-vs-MDBdefault` below has a median ratio of 21.7× and overlapping support,
   because one MongoDB collection scan out of fifty completed in 13.335 ms while HCD's slowest
   of fifty took 28.697 ms. With the raw series a rank test on those two samples would almost
   certainly have been decisive. It is not available. The honest sentence is "very likely real,
   not demonstrable from what was kept" — and that sentence is a **criticism of the artefact,
   not a defence of the claim**.
4. **The comparisons are not independent, so do not count significant rows.** Each mutation
   point appears in several pairings and each pass re-uses the same arms. No multiplicity
   correction is applied and none would be meaningful; the matrix is a per-claim audit, not a
   family of hypotheses tested together.

### 3.3 The count, and the four findings that come out of it

Ninety-three cross-engine or cross-arm comparisons were enumerated from the headline table of
[`RESULTS.md`](../RESULTS.md) §2 and the M1–M23 register of §3, and each arm's `n`, `min_ms`,
`p50_ms` and `max_ms` were pulled from `data/raw/`.

| | Count |
|---|---|
| **DISJOINT** — direction certain, exact permutation *p* computable | **56** |
| **OVERLAPPING** — ratio interval spans 1.0, nothing established | **34** |
| **Not testable** — record too thin, or not a latency comparison at all | **3** |
| Total | 93 |

Four findings follow, and three of them cut against the dossier.

**(a) Both of the axes on which HCD wins fail separation of support.** The dossier names two
HCD wins: filtered search on an undeclared field, and search-index freshness.

- *Filtered search, undeclared field (M16-A, 21.7×).* HCD p50 17.376 ms against mongo-default
  p50 376.698 ms — and the supports **overlap**, ratio interval **[0.465, 65.842]**. One
  MongoDB collection scan of fifty finished in 13.335 ms; HCD's slowest of fifty took
  28.697 ms. The 21.7× is a ratio of medians whose direction these data do not establish.
- *Search-index freshness, at the magnitude the dossier's own correction leaves standing
  (M18).* HCD JVector p50 44.972 ms against de-synchronised `mongot` p50 664.3 ms — and the
  supports **overlap**, ratio interval **[0.155, 36.683]**, because `mongot`'s 89.1 ms floor
  sits below HCD's 573.598 ms max. Only the **uncorrected** M17 comparison separates (`mongot`
  min 978.641 ms above HCD max 573.598 ms, *p* = 9.30 × 10⁻²⁴), and M18 exists precisely
  because the author judged that comparison to be a probe artefact. **The separated version is
  the one the dossier has already withdrawn.**

  What does survive on this axis is not a latency comparison at all but the **miss-rate** result
  of §3.17, which uses counts rather than latencies and is therefore exactly testable.

**(b) MongoDB's mutation win is the most robust quantitative result in the dossier.** Of the
20 size × pass cells comparing HCD's Data API against a MongoDB arm, **19 are disjoint**; of the
20 cells comparing HCD over native CQL against a MongoDB arm, **18 are disjoint**. All three
exceptions are the smallest document size (8 KiB) on the second pass, and all three are caused
by a **MongoDB tail**, not by HCD getting close: `mongo-default` 8 KiB pass 2 has min 3.652 ms
and max 31.529 ms against an HCD Data API arm whose minimum is 27.961 ms. At 125 KiB, where the
effect is largest, the ratio intervals against `mongo-wildcard` are [8.848, 64.912] on pass 1
and [8.559, 34.950] on pass 2; against `mongo-default`, [2.030, 80.090] and [8.572, 36.095].
Even the lower bounds are large effects.

The regime caveat travels unchanged and is not softened by any of this: these are
**memtable-resident, cache-resident, closed-loop, single-client** rates on one shared host, and
the per-byte coefficient they rest on collapses from ×5.94 to ×1.52 once the read half of the
read-modify-write cycle is forced onto SSTables (M15). Separation of support establishes the
**direction** of this comparison very strongly and says nothing whatever about whether the
magnitude transfers.

**(c) The dossier's account of where the per-byte cost is charged rests on no separated
comparison at all.** All **10 of 10** cells of M12's method 1 (Data API arm against direct-CQL
arm, [`findings_tier.json`](../data/raw/findings_tier.json)) **overlap**, every ratio interval
spanning 1.0. And **9 of 10** cells of M14's Data-API-versus-CQL-direct comparison overlap as
well. Audit finding I3 records that the tier share is 29 % by one method and 9 % by another and
that the two were never reconciled. This analysis adds a harder statement: **neither number
rests on a comparison whose direction these data establish.** The published range "9–29 %,
unpinned" is, by this criterion, unpinned at both ends. The only separated cell in either family
is `MUT-HCDAPI-vs-HCDCQL-8K-p2` (ratio interval [1.101, 3.205]) — one cell out of twenty.

**(d) The two measurements that reframed the flagship coefficient cannot be tested at all.**
M10 (×5.94, disk regime) and M15 (×1.52, post-flush) are both UNDETERMINABLE, for the record
reasons in §2. The ×7.50 of M3, the value the later two were meant to correct, **is** separated
(ratio interval [3.661, 27.123], *p* = 8.46 × 10⁻¹⁸) — so the only leg of the ×7.50 / ×5.94 /
×1.52 triangle that can be examined is the one the dossier has already relabelled as a memtable
artefact that must never be quoted as an engine property.

A fifth observation, neutral rather than adverse: **the internal controls behave as internal
controls should.** M11's 16 × 4096 B point, measured in both series, overlaps in both passes
(ratio of medians 1.02 and 1.01) — which is the desired outcome, not a failure. And M3's
variant A overlaps, agreeing with the author's own pre-registered read-control rule, which had
already called it INCONCLUSIVE.

### 3.4 Claims resting on n < 10

One arm in the repository has *n* < 10: **the HCD Data API aggregation arm, n = 3**
([`findings_agg_hcd.json`](../data/raw/findings_agg_hcd.json), `result.C2_client_scan_aggregate_ms`).

- **Its p95 and p99 carry no information.** With three observations, the 95th percentile is an
  interpolation between the 2nd and the 3rd — that is, between the two largest values of a
  three-element sample. The fields `p95_ms = 134990.509` and `p99_ms = 135079.956` are
  arithmetic on `max_ms = 135102.317` and the value below it; they are not estimates of a tail.
  `RESULTS.md` already says "HCD arm is n = 3; its p95/p99 carry no information", and this
  analysis confirms it rather than discovering it.
- **The separation still holds, and with a usable *p*.** Three observations against MongoDB's
  fifteen give 1 / C(18, 3) = **1.23 × 10⁻³** — small, and the separation is extreme (133 827 ms
  against 293.734 ms). Direction is certain. The point estimate 602× and the interval
  [455.607, 625.601] are quotable as *this run's* magnitude.
- **And the caveat that must travel with it is a capability caveat, not a statistical one.**
  The 602× must never be quoted as "HCD is 602× slower". The same storage engine on the same
  host aggregates the same corpus in ~2 s through native CQL
  ([`findings_agg_cqlref.json`](../data/raw/findings_agg_cqlref.json)); the 134 s belongs to a
  tier that exposes no aggregation surface and therefore forces all 200 000 documents through
  the client at the Data API's default ~20 documents per page. And the CQL reference arm
  carries its own disqualifying label in its own result file: reaching it means abandoning the
  document model and pre-designing a table partitioned by the group key. Both halves are
  required. Campaign 7 sat outside the adversarial audit (M1–M17) and the first three challenge
  rounds; it was challenged in
  [`docs/challenges-campagne7.fr.md`](challenges-campagne7.fr.md) (D6–D14), and D6 addresses
  this arm's *n* = 3 directly.

### 3.5 Mutation, HCD Data API against MongoDB (M13)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `MUT-HCDAPI-vs-MDB-wildcard-8K-p1` | M13 | HCD Data API 8 KiB pass1<br>n=30; 32.113 / 40.9 / 55.818 | mongo-wildcard 8 KiB pass1<br>n=30; 4.237 / 5.544 / 10.53 | **DISJOINT** | 8.46e-18 | 7.38× | [3.050, 13.174] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-8K-p2` | M13 | HCD Data API 8 KiB pass2<br>n=30; 27.961 / 35.734 / 48.591 | mongo-wildcard 8 KiB pass2<br>n=30; 4.033 / 5.541 / 15.353 | **DISJOINT** | 8.46e-18 | 6.45× | [1.821, 12.048] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-16K-p1` | M13 | HCD Data API 16 KiB pass1<br>n=30; 35.437 / 43.632 / 429.927 | mongo-wildcard 16 KiB pass1<br>n=30; 3.672 / 5.405 / 11.112 | **DISJOINT** | 8.46e-18 | 8.07× | [3.189, 117.082] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-16K-p2` | M13 | HCD Data API 16 KiB pass2<br>n=30; 35.18 / 42.145 / 75.258 | mongo-wildcard 16 KiB pass2<br>n=30; 4.025 / 5.824 / 9.25 | **DISJOINT** | 8.46e-18 | 7.24× | [3.803, 18.698] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-32K-p1` | M13 | HCD Data API 32 KiB pass1<br>n=30; 47.733 / 56.867 / 78.308 | mongo-wildcard 32 KiB pass1<br>n=30; 3.616 / 6.006 / 9.284 | **DISJOINT** | 8.46e-18 | 9.47× | [5.141, 21.656] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-32K-p2` | M13 | HCD Data API 32 KiB pass2<br>n=30; 45.868 / 53.727 / 68.441 | mongo-wildcard 32 KiB pass2<br>n=30; 3.846 / 6.274 / 21.12 | **DISJOINT** | 8.46e-18 | 8.56× | [2.172, 17.795] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-64K-p1` | M13 | HCD Data API 64 KiB pass1<br>n=30; 67.321 / 79.214 / 116.039 | mongo-wildcard 64 KiB pass1<br>n=30; 4.115 / 5.846 / 14.679 | **DISJOINT** | 8.46e-18 | 13.55× | [4.586, 28.199] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-64K-p2` | M13 | HCD Data API 64 KiB pass2<br>n=30; 63.479 / 74.677 / 467.906 | mongo-wildcard 64 KiB pass2<br>n=30; 4.384 / 6.111 / 12.715 | **DISJOINT** | 8.46e-18 | 12.22× | [4.992, 106.730] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-125K-p1` | M13 | HCD Data API 125 KiB pass1<br>n=30; 103.095 / 130.787 / 335.336 | mongo-wildcard 125 KiB pass1<br>n=30; 5.166 / 7.621 / 11.652 | **DISJOINT** | 8.46e-18 | 17.16× | [8.848, 64.912] | certain in direction |
| `MUT-HCDAPI-vs-MDB-wildcard-125K-p2` | M13 | HCD Data API 125 KiB pass2<br>n=30; 91.27 / 122.138 / 165.281 | mongo-wildcard 125 KiB pass2<br>n=30; 4.729 / 6.465 / 10.663 | **DISJOINT** | 8.46e-18 | 18.89× | [8.559, 34.950] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-8K-p1` | M13 | HCD Data API 8 KiB pass1<br>n=30; 32.113 / 40.9 / 55.818 | mongo-default 8 KiB pass1<br>n=30; 4.368 / 5.67 / 11.326 | **DISJOINT** | 8.46e-18 | 7.21× | [2.835, 12.779] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-8K-p2` | M13 | HCD Data API 8 KiB pass2<br>n=30; 27.961 / 35.734 / 48.591 | mongo-default 8 KiB pass2<br>n=30; 3.652 / 5.16 / 31.529 | **OVERLAPPING** | not computable | 6.93× | [0.887, 13.305] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-MDB-default-16K-p1` | M13 | HCD Data API 16 KiB pass1<br>n=30; 35.437 / 43.632 / 429.927 | mongo-default 16 KiB pass1<br>n=30; 4.178 / 5.217 / 9.138 | **DISJOINT** | 8.46e-18 | 8.36× | [3.878, 102.903] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-16K-p2` | M13 | HCD Data API 16 KiB pass2<br>n=30; 35.18 / 42.145 / 75.258 | mongo-default 16 KiB pass2<br>n=30; 4.263 / 5.68 / 8.409 | **DISJOINT** | 8.46e-18 | 7.42× | [4.184, 17.654] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-32K-p1` | M13 | HCD Data API 32 KiB pass1<br>n=30; 47.733 / 56.867 / 78.308 | mongo-default 32 KiB pass1<br>n=30; 3.613 / 5.31 / 13.519 | **DISJOINT** | 8.46e-18 | 10.71× | [3.531, 21.674] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-32K-p2` | M13 | HCD Data API 32 KiB pass2<br>n=30; 45.868 / 53.727 / 68.441 | mongo-default 32 KiB pass2<br>n=30; 4.318 / 6.605 / 12.684 | **DISJOINT** | 8.46e-18 | 8.13× | [3.616, 15.850] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-64K-p1` | M13 | HCD Data API 64 KiB pass1<br>n=30; 67.321 / 79.214 / 116.039 | mongo-default 64 KiB pass1<br>n=30; 4.134 / 6.039 / 10.772 | **DISJOINT** | 8.46e-18 | 13.12× | [6.250, 28.069] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-64K-p2` | M13 | HCD Data API 64 KiB pass2<br>n=30; 63.479 / 74.677 / 467.906 | mongo-default 64 KiB pass2<br>n=30; 3.859 / 6.437 / 11.983 | **DISJOINT** | 8.46e-18 | 11.60× | [5.297, 121.251] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-125K-p1` | M13 | HCD Data API 125 KiB pass1<br>n=30; 103.095 / 130.787 / 335.336 | mongo-default 125 KiB pass1<br>n=30; 4.187 / 6.484 / 50.781 | **DISJOINT** | 8.46e-18 | 20.17× | [2.030, 80.090] | certain in direction |
| `MUT-HCDAPI-vs-MDB-default-125K-p2` | M13 | HCD Data API 125 KiB pass2<br>n=30; 91.27 / 122.138 / 165.281 | mongo-default 125 KiB pass2<br>n=30; 4.579 / 6.468 / 10.647 | **DISJOINT** | 8.46e-18 | 18.88× | [8.572, 36.095] | certain in direction |

### 3.6 Mutation, HCD over native CQL against MongoDB (M14)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `MUT-HCDCQL-vs-MDB-wildcard-8K-p1` | M14 | HCD CQL-direct 8 KiB pass1<br>n=30; 15.847 / 18.407 / 63.786 | mongo-wildcard 8 KiB pass1<br>n=30; 4.237 / 5.544 / 10.53 | **DISJOINT** | 8.46e-18 | 3.32× | [1.505, 15.055] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-8K-p2` | M14 | HCD CQL-direct 8 KiB pass2<br>n=30; 15.161 / 18.269 / 25.387 | mongo-wildcard 8 KiB pass2<br>n=30; 4.033 / 5.541 / 15.353 | **OVERLAPPING** | not computable | 3.30× | [0.988, 6.295] ⚠︎ | not established by these data |
| `MUT-HCDCQL-vs-MDB-wildcard-16K-p1` | M14 | HCD CQL-direct 16 KiB pass1<br>n=30; 18.77 / 25.233 / 73.06 | mongo-wildcard 16 KiB pass1<br>n=30; 3.672 / 5.405 / 11.112 | **DISJOINT** | 8.46e-18 | 4.67× | [1.689, 19.896] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-16K-p2` | M14 | HCD CQL-direct 16 KiB pass2<br>n=30; 22.912 / 29.599 / 76.393 | mongo-wildcard 16 KiB pass2<br>n=30; 4.025 / 5.824 / 9.25 | **DISJOINT** | 8.46e-18 | 5.08× | [2.477, 18.980] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-32K-p1` | M14 | HCD CQL-direct 32 KiB pass1<br>n=30; 31.203 / 40.393 / 95.033 | mongo-wildcard 32 KiB pass1<br>n=30; 3.616 / 6.006 / 9.284 | **DISJOINT** | 8.46e-18 | 6.73× | [3.361, 26.281] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-32K-p2` | M14 | HCD CQL-direct 32 KiB pass2<br>n=30; 30.787 / 41.274 / 90.098 | mongo-wildcard 32 KiB pass2<br>n=30; 3.846 / 6.274 / 21.12 | **DISJOINT** | 8.46e-18 | 6.58× | [1.458, 23.426] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-64K-p1` | M14 | HCD CQL-direct 64 KiB pass1<br>n=30; 49.891 / 61.653 / 110.686 | mongo-wildcard 64 KiB pass1<br>n=30; 4.115 / 5.846 / 14.679 | **DISJOINT** | 8.46e-18 | 10.55× | [3.399, 26.898] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-64K-p2` | M14 | HCD CQL-direct 64 KiB pass2<br>n=30; 44.873 / 59.034 / 188.228 | mongo-wildcard 64 KiB pass2<br>n=30; 4.384 / 6.111 / 12.715 | **DISJOINT** | 8.46e-18 | 9.66× | [3.529, 42.935] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-125K-p1` | M14 | HCD CQL-direct 125 KiB pass1<br>n=30; 73.131 / 101.645 / 173.264 | mongo-wildcard 125 KiB pass1<br>n=30; 5.166 / 7.621 / 11.652 | **DISJOINT** | 8.46e-18 | 13.34× | [6.276, 33.539] | certain in direction |
| `MUT-HCDCQL-vs-MDB-wildcard-125K-p2` | M14 | HCD CQL-direct 125 KiB pass2<br>n=30; 82.088 / 100.633 / 119.768 | mongo-wildcard 125 KiB pass2<br>n=30; 4.729 / 6.465 / 10.663 | **DISJOINT** | 8.46e-18 | 15.57× | [7.698, 25.326] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-8K-p1` | M14 | HCD CQL-direct 8 KiB pass1<br>n=30; 15.847 / 18.407 / 63.786 | mongo-default 8 KiB pass1<br>n=30; 4.368 / 5.67 / 11.326 | **DISJOINT** | 8.46e-18 | 3.25× | [1.399, 14.603] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-8K-p2` | M14 | HCD CQL-direct 8 KiB pass2<br>n=30; 15.161 / 18.269 / 25.387 | mongo-default 8 KiB pass2<br>n=30; 3.652 / 5.16 / 31.529 | **OVERLAPPING** | not computable | 3.54× | [0.481, 6.952] ⚠︎ | not established by these data |
| `MUT-HCDCQL-vs-MDB-default-16K-p1` | M14 | HCD CQL-direct 16 KiB pass1<br>n=30; 18.77 / 25.233 / 73.06 | mongo-default 16 KiB pass1<br>n=30; 4.178 / 5.217 / 9.138 | **DISJOINT** | 8.46e-18 | 4.84× | [2.054, 17.487] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-16K-p2` | M14 | HCD CQL-direct 16 KiB pass2<br>n=30; 22.912 / 29.599 / 76.393 | mongo-default 16 KiB pass2<br>n=30; 4.263 / 5.68 / 8.409 | **DISJOINT** | 8.46e-18 | 5.21× | [2.725, 17.920] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-32K-p1` | M14 | HCD CQL-direct 32 KiB pass1<br>n=30; 31.203 / 40.393 / 95.033 | mongo-default 32 KiB pass1<br>n=30; 3.613 / 5.31 / 13.519 | **DISJOINT** | 8.46e-18 | 7.61× | [2.308, 26.303] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-32K-p2` | M14 | HCD CQL-direct 32 KiB pass2<br>n=30; 30.787 / 41.274 / 90.098 | mongo-default 32 KiB pass2<br>n=30; 4.318 / 6.605 / 12.684 | **DISJOINT** | 8.46e-18 | 6.25× | [2.427, 20.866] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-64K-p1` | M14 | HCD CQL-direct 64 KiB pass1<br>n=30; 49.891 / 61.653 / 110.686 | mongo-default 64 KiB pass1<br>n=30; 4.134 / 6.039 / 10.772 | **DISJOINT** | 8.46e-18 | 10.21× | [4.631, 26.775] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-64K-p2` | M14 | HCD CQL-direct 64 KiB pass2<br>n=30; 44.873 / 59.034 / 188.228 | mongo-default 64 KiB pass2<br>n=30; 3.859 / 6.437 / 11.983 | **DISJOINT** | 8.46e-18 | 9.17× | [3.745, 48.776] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-125K-p1` | M14 | HCD CQL-direct 125 KiB pass1<br>n=30; 73.131 / 101.645 / 173.264 | mongo-default 125 KiB pass1<br>n=30; 4.187 / 6.484 / 50.781 | **DISJOINT** | 8.46e-18 | 15.68× | [1.440, 41.381] | certain in direction |
| `MUT-HCDCQL-vs-MDB-default-125K-p2` | M14 | HCD CQL-direct 125 KiB pass2<br>n=30; 82.088 / 100.633 / 119.768 | mongo-default 125 KiB pass2<br>n=30; 4.579 / 6.468 / 10.647 | **DISJOINT** | 8.46e-18 | 15.56× | [7.710, 26.156] | certain in direction |

### 3.7 Mutation, HCD Data API against HCD over native CQL — the tier question (M14)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `MUT-HCDAPI-vs-HCDCQL-8K-p1` | M14 | HCD Data API 8 KiB pass1<br>n=30; 32.113 / 40.9 / 55.818 | HCD CQL-direct 8 KiB pass1<br>n=30; 15.847 / 18.407 / 63.786 | **OVERLAPPING** | not computable | 2.22× | [0.503, 3.522] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-8K-p2` | M14 | HCD Data API 8 KiB pass2<br>n=30; 27.961 / 35.734 / 48.591 | HCD CQL-direct 8 KiB pass2<br>n=30; 15.161 / 18.269 / 25.387 | **DISJOINT** | 8.46e-18 | 1.96× | [1.101, 3.205] | certain in direction |
| `MUT-HCDAPI-vs-HCDCQL-16K-p1` | M14 | HCD Data API 16 KiB pass1<br>n=30; 35.437 / 43.632 / 429.927 | HCD CQL-direct 16 KiB pass1<br>n=30; 18.77 / 25.233 / 73.06 | **OVERLAPPING** | not computable | 1.73× | [0.485, 22.905] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-16K-p2` | M14 | HCD Data API 16 KiB pass2<br>n=30; 35.18 / 42.145 / 75.258 | HCD CQL-direct 16 KiB pass2<br>n=30; 22.912 / 29.599 / 76.393 | **OVERLAPPING** | not computable | 1.42× | [0.461, 3.285] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-32K-p1` | M14 | HCD Data API 32 KiB pass1<br>n=30; 47.733 / 56.867 / 78.308 | HCD CQL-direct 32 KiB pass1<br>n=30; 31.203 / 40.393 / 95.033 | **OVERLAPPING** | not computable | 1.41× | [0.502, 2.510] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-32K-p2` | M14 | HCD Data API 32 KiB pass2<br>n=30; 45.868 / 53.727 / 68.441 | HCD CQL-direct 32 KiB pass2<br>n=30; 30.787 / 41.274 / 90.098 | **OVERLAPPING** | not computable | 1.30× | [0.509, 2.223] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-64K-p1` | M14 | HCD Data API 64 KiB pass1<br>n=30; 67.321 / 79.214 / 116.039 | HCD CQL-direct 64 KiB pass1<br>n=30; 49.891 / 61.653 / 110.686 | **OVERLAPPING** | not computable | 1.28× | [0.608, 2.326] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-64K-p2` | M14 | HCD Data API 64 KiB pass2<br>n=30; 63.479 / 74.677 / 467.906 | HCD CQL-direct 64 KiB pass2<br>n=30; 44.873 / 59.034 / 188.228 | **OVERLAPPING** | not computable | 1.26× | [0.337, 10.427] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-125K-p1` | M14 | HCD Data API 125 KiB pass1<br>n=30; 103.095 / 130.787 / 335.336 | HCD CQL-direct 125 KiB pass1<br>n=30; 73.131 / 101.645 / 173.264 | **OVERLAPPING** | not computable | 1.29× | [0.595, 4.585] ⚠︎ | not established by these data |
| `MUT-HCDAPI-vs-HCDCQL-125K-p2` | M14 | HCD Data API 125 KiB pass2<br>n=30; 91.27 / 122.138 / 165.281 | HCD CQL-direct 125 KiB pass2<br>n=30; 82.088 / 100.633 / 119.768 | **OVERLAPPING** | not computable | 1.21× | [0.762, 2.014] ⚠︎ | not established by these data |

### 3.8 Read and search (M16)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `RS-A-HCD-vs-MDBdefault` | M16-A | mongo-default filtered read, collection scan<br>n=50; 13.335 / 376.698 / 863.381 | HCD filtered read, automatic SAI<br>n=50; 13.113 / 17.376 / 28.697 | **OVERLAPPING** | not computable | 21.68× | [0.465, 65.842] ⚠︎ | not established by these data |
| `RS-A-MDBwildcard-vs-HCD` | M16-A | HCD filtered read, automatic SAI<br>n=50; 13.113 / 17.376 / 28.697 | mongo-wildcard filtered read, declared index<br>n=50; 0.582 / 0.732 / 1.039 | **DISJOINT** | 9.91e-30 | 23.74× | [12.621, 49.308] | certain in direction |
| `RS-A-MDBwildcard-vs-MDBdefault` | M16-A | mongo-default filtered read, collection scan<br>n=50; 13.335 / 376.698 / 863.381 | mongo-wildcard filtered read, declared index<br>n=50; 0.582 / 0.732 / 1.039 | **DISJOINT** | 9.91e-30 | 514.61× | [12.835, 1,483.473] | certain in direction |
| `RS-B-MDBwildcard-vs-HCD` | M16-B | HCD point read by _id<br>n=50; 8.04 / 10.382 / 14.88 | mongo-wildcard point read by _id<br>n=50; 0.417 / 0.53 / 1.146 | **DISJOINT** | 9.91e-30 | 19.59× | [7.016, 35.684] | certain in direction |
| `RS-B-MDBdefault-vs-HCD` | M16-B | HCD point read by _id<br>n=50; 8.04 / 10.382 / 14.88 | mongo-default point read by _id<br>n=50; 0.456 / 0.616 / 1.309 | **DISJOINT** | 9.91e-30 | 16.85× | [6.142, 32.632] | certain in direction |
| `RS-C-MDBwildcard-vs-HCD` | M16-C | HCD insert->found, secondary index<br>n=40; 24.439 / 33.24 / 97.558 | mongo-wildcard insert->found, secondary index<br>n=40; 4.31 / 7.072 / 11.435 | **DISJOINT** | 9.30e-24 | 4.70× | [2.137, 22.635] | certain in direction |
| `RS-C-HCD-vs-MDBdefault` | M16-C | mongo-default insert->found, secondary index<br>n=40; 868.97 / 894.213 / 964.006 | HCD insert->found, secondary index<br>n=40; 24.439 / 33.24 / 97.558 | **DISJOINT** | 9.30e-24 | 26.90× | [8.907, 39.445] | certain in direction |

### 3.9 Search-index freshness (M17, M18)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `FRESH-HCD-vs-MONGOT-selfsync` | M17 | mongot $search write->visible, self-synchronised probe<br>n=40; 978.641 / 1,015.201 / 1,224.72 | HCD JVector write->searchable<br>n=40; 31.9 / 44.972 / 573.598 | **DISJOINT** | 9.30e-24 | 22.57× | [1.706, 38.392] | certain in direction |
| `FRESH-HCD-vs-MONGOT-desync` | M18 | mongot $search lag, de-synchronised probe<br>n=60; 89.1 / 664.3 / 1,170.2 | HCD JVector write->searchable<br>n=40; 31.9 / 44.972 / 573.598 | **OVERLAPPING** | not computable | 14.77× | [0.155, 36.683] ⚠︎ | not established by these data |
| `FRESH-MONGOT-selfsync-vs-desync` | M17 vs M18 | mongot $search write->visible, self-synchronised probe<br>n=40; 978.641 / 1,015.201 / 1,224.72 | mongot $search lag, de-synchronised probe<br>n=60; 89.1 / 664.3 / 1,170.2 | **OVERLAPPING** | not computable | 1.53× | [0.836, 13.745] ⚠︎ | not established by these data |
| `FRESH-MONGOT-search-vs-findbyid` | M17 | mongot $search write->visible, self-synchronised probe<br>n=40; 978.641 / 1,015.201 / 1,224.72 | mongot deployment, find({_id})<br>n=40; 1.035 / 1.306 / 2.768 | **DISJOINT** | 9.30e-24 | 777.34× | [353.555, 1,183.304] | certain in direction |

### 3.10 Aggregation (M23)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `AGG-MDB-vs-HCDAPI` | M23 | HCD Data API client scan-and-aggregate<br>n=3; 133,827 / 133,984 / 135,102 | MongoDB server-side $group<br>n=15; 215.956 / 222.711 / 293.734 | **DISJOINT** | 1.23e-03 | 601.61× | [455.607, 625.601] | certain in direction |
| `AGG-MDB-vs-CQLbest` | M23 | native CQL per-partition sweep (10 queries)<br>n=15; 1,924.195 / 2,011.399 / 2,471.012 | MongoDB server-side $group<br>n=15; 215.956 / 222.711 / 293.734 | **DISJOINT** | 6.45e-09 | 9.03× | [6.551, 11.442] | certain in direction |
| `AGG-CQLbest-vs-HCDAPI` | M23 | HCD Data API client scan-and-aggregate<br>n=3; 133,827 / 133,984 / 135,102 | native CQL per-partition sweep (10 queries)<br>n=15; 1,924.195 / 2,011.399 / 2,471.012 | **DISJOINT** | 1.23e-03 | 66.61× | [54.159, 70.212] | certain in direction |
| `AGG-CQLsweep-vs-CQLgroupby` | M23 | native CQL cross-partition GROUP BY<br>n=15; 2,387.172 / 2,568.372 / 2,734.854 | native CQL per-partition sweep (10 queries)<br>n=15; 1,924.195 / 2,011.399 / 2,471.012 | **OVERLAPPING** | not computable | 1.28× | [0.966, 1.421] ⚠︎ | not established by these data |
| `AGG-MDB-vs-CQLgroupby` | M23 | native CQL cross-partition GROUP BY<br>n=15; 2,387.172 / 2,568.372 / 2,734.854 | MongoDB server-side $group<br>n=15; 215.956 / 222.711 / 293.734 | **DISJOINT** | 6.45e-09 | 11.53× | [8.127, 12.664] | certain in direction |

### 3.11 Counting (M21, M22)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `CNT-MDBexact-vs-MDBest` | M21 | MongoDB count_documents({}) exact<br>n=30; 108.007 / 115.009 / 128.577 | MongoDB estimated_document_count()<br>n=30; 0.336 / 0.408 / 0.768 | **DISJOINT** | 8.46e-18 | 281.88× | [140.634, 382.670] | certain in direction |
| `CNT-MDBscan-vs-MDBidx` | M21 | MongoDB filtered count, collection scan<br>n=30; 149.065 / 157.177 / 210.183 | MongoDB filtered count, declared cat index<br>n=30; 11.261 / 12.659 / 15.643 | **DISJOINT** | 8.46e-18 | 12.42× | [9.529, 18.665] | certain in direction |
| `CNT-HCDest-vs-MDBest` | M22 | HCD estimatedDocumentCount() [RETURNED 0, TRUE COUNT 200 000]<br>n=30; 5.551 / 6.875 / 10.652 | MongoDB estimated_document_count()<br>n=30; 0.336 / 0.408 / 0.768 | **DISJOINT** | 8.46e-18 | 16.85× | [7.228, 31.702] | certain in direction |
| `CNT-HCDexact-vs-MDBexact` | M21 | HCD countDocuments({})<br>n=0; — / — / — | MongoDB count_documents({}) exact<br>n=30; 108.007 / 115.009 / 128.577 | **NOT A LATENCY COMPARISON** | — | — | — | structural, not statistical — HCD produced no observations because the operation is refused; nothing here is a distribution and no test applies |

### 3.12 Document size and indexed content, HCD-internal (M3, M11)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `SIZE-M3-variantB-1kb-vs-128kb` | M3 | variant B, 128 kb document<br>n=30; 71.783 / 90.783 / 258.239 | variant B, 1 kb document<br>n=30; 9.521 / 12.104 / 19.608 | **DISJOINT** | 8.46e-18 | 7.50× | [3.661, 27.123] | certain in direction |
| `SIZE-M3-variantB-readcontrol-1kb-vs-128kb` | M3 | variant B read control, 128 kb<br>n=30; 9.424 / 11.523 / 28.532 | variant B read control, 1 kb<br>n=30; 6.166 / 7.39 / 12.656 | **OVERLAPPING** | not computable | 1.56× | [0.745, 4.627] ⚠︎ | not established by these data |
| `SIZE-M3-variantA-1kb-vs-128kb` | M3 | variant A, 128 kb document<br>n=30; 17.299 / 22.066 / 43.152 | variant A, 1 kb document<br>n=30; 8.535 / 11.468 / 30.435 | **OVERLAPPING** | not computable | 1.92× | [0.568, 5.056] ⚠︎ | not established by these data |
| `FB-S1-512B-vs-8000B-p1` | M11 | S1 16x8000B pass1<br>n=30; 97.957 / 114.649 / 410.991 | S1 16x512B pass1<br>n=30; 21.878 / 25.163 / 31.986 | **DISJOINT** | 8.46e-18 | 4.56× | [3.062, 18.786] | certain in direction |
| `FB-S2-9x7281B-vs-128x512B-p1` | M11 | S2 128x512B pass1<br>n=30; 62.223 / 75.291 / 98.91 | S2 9x7281B pass1<br>n=30; 57.862 / 66.74 / 77.329 | **OVERLAPPING** | not computable | 1.13× | [0.805, 1.709] ⚠︎ | not established by these data |
| `FB-internal-control-16x4096B-p1` | M11 | S1 16x4096B pass1<br>n=30; 54.974 / 68.384 / 77.996 | S2 16x4096B pass1<br>n=30; 56.977 / 67.044 / 142.729 | **OVERLAPPING** | not computable | 1.02× | [0.385, 1.369] ⚠︎ | not established by these data |
| `FB-S1-512B-vs-8000B-p2` | M11 | S1 16x8000B pass2<br>n=30; 97.984 / 117.269 / 275.371 | S1 16x512B pass2<br>n=30; 20.579 / 24.753 / 31.804 | **DISJOINT** | 8.46e-18 | 4.74× | [3.081, 13.381] | certain in direction |
| `FB-S2-9x7281B-vs-128x512B-p2` | M11 | S2 128x512B pass2<br>n=30; 61.767 / 80.281 / 606.43 | S2 9x7281B pass2<br>n=30; 55.583 / 67.629 / 113.034 | **OVERLAPPING** | not computable | 1.19× | [0.546, 10.910] ⚠︎ | not established by these data |
| `FB-internal-control-16x4096B-p2` | M11 | S1 16x4096B pass2<br>n=30; 52.581 / 69.054 / 118.05 | S2 16x4096B pass2<br>n=30; 54.415 / 68.609 / 93.298 | **OVERLAPPING** | not computable | 1.01× | [0.564, 2.169] ⚠︎ | not established by these data |

### 3.13 Where the per-byte cost is charged, method 1 (M12)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `TIER-API-vs-CQL-8K-p1` | M12 | Data API arm 8 KiB pass1<br>n=30; 24.047 / 28.827 / 48.348 | direct-CQL arm 8 KiB pass1<br>n=30; 14.476 / 17.871 / 64.712 | **OVERLAPPING** | not computable | 1.61× | [0.372, 3.340] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-8K-p2` | M12 | Data API arm 8 KiB pass2<br>n=30; 20.352 / 26.464 / 34.571 | direct-CQL arm 8 KiB pass2<br>n=30; 12.419 / 15.468 / 65.781 | **OVERLAPPING** | not computable | 1.71× | [0.309, 2.784] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-16K-p1` | M12 | Data API arm 16 KiB pass1<br>n=30; 28.63 / 33.9 / 59.404 | direct-CQL arm 16 KiB pass1<br>n=30; 14.936 / 22.761 / 73.266 | **OVERLAPPING** | not computable | 1.49× | [0.391, 3.977] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-16K-p2` | M12 | Data API arm 16 KiB pass2<br>n=30; 26.972 / 33.48 / 61.514 | direct-CQL arm 16 KiB pass2<br>n=30; 10.069 / 24.504 / 77.54 | **OVERLAPPING** | not computable | 1.37× | [0.348, 6.109] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-32K-p1` | M12 | Data API arm 32 KiB pass1<br>n=30; 38.914 / 47.838 / 138.868 | direct-CQL arm 32 KiB pass1<br>n=30; 24.544 / 32.715 / 101.059 | **OVERLAPPING** | not computable | 1.46× | [0.385, 5.658] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-32K-p2` | M12 | Data API arm 32 KiB pass2<br>n=30; 37.632 / 46.108 / 62.808 | direct-CQL arm 32 KiB pass2<br>n=30; 26.088 / 32.059 / 84.032 | **OVERLAPPING** | not computable | 1.44× | [0.448, 2.408] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-64K-p1` | M12 | Data API arm 64 KiB pass1<br>n=30; 57.611 / 70.639 / 81.817 | direct-CQL arm 64 KiB pass1<br>n=30; 14.294 / 49.307 / 100.861 | **OVERLAPPING** | not computable | 1.43× | [0.571, 5.724] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-64K-p2` | M12 | Data API arm 64 KiB pass2<br>n=30; 60.819 / 71.087 / 331.451 | direct-CQL arm 64 KiB pass2<br>n=30; 14.43 / 44.568 / 94.13 | **OVERLAPPING** | not computable | 1.59× | [0.646, 22.970] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-125K-p1` | M12 | Data API arm 125 KiB pass1<br>n=30; 99.396 / 119.023 / 160.253 | direct-CQL arm 125 KiB pass1<br>n=30; 31.158 / 86.431 / 216.007 | **OVERLAPPING** | not computable | 1.38× | [0.460, 5.143] ⚠︎ | not established by these data |
| `TIER-API-vs-CQL-125K-p2` | M12 | Data API arm 125 KiB pass2<br>n=30; 93.465 / 115.719 / 145.094 | direct-CQL arm 125 KiB pass2<br>n=30; 18.479 / 78.409 / 195.138 | **OVERLAPPING** | not computable | 1.48× | [0.479, 7.852] ⚠︎ | not established by these data |

### 3.14 Regime comparisons that cannot be tested at all (M10, M15)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `REGIME-M15-postflush-1kb-vs-128kb` | M15 | post-flush 128 kb<br>n=30; — / 163.402 / 229.834 | post-flush 1 kb<br>n=30; — / 107.765 / 171.608 | **UNDETERMINABLE** | — | 1.52× | — | not established by these data (summary record incomplete) |
| `REGIME-M10-disk-1kb-vs-128kb` | M10 | disk RF=3 variant B, 128 kb<br>n=—; — / 121.189 / — | disk RF=3 variant B, 1 kb<br>n=—; — / 20.389 / — | **UNDETERMINABLE** | — | 5.94× | — | not established by these data (summary record incomplete) |

### 3.15 The one probe driven at a fixed offered rate (campaign 1 freshness)

| ID | M‑ref | Slower arm — n; min / p50 / max (ms) | Faster arm — n; min / p50 / max (ms) | Support | Exact perm. *p* (1‑sided) | Ratio of medians | Ratio interval | Verdict |
|---|---|---|---|---|---|---|---|---|
| `FRESH-M1-idle-vs-underload-rf1` | M1/campaign 1 | under load, 50 writes/s<br>n=120; 32.471 / 42.534 / 60.932 | idle<br>n=40; 19.479 / 25.462 / 100.919 | **OVERLAPPING** | not computable | 1.67× | [0.322, 3.128] ⚠︎ | not established by these data |
| `FRESH-M1-idle-vs-underload-rf1-pass2` | M1/campaign 1 | under load, 50 writes/s (pass 2)<br>n=120; 32.821 / 42.285 / 55.644 | idle (pass 2)<br>n=40; 13.857 / 18.71 / 68.62 | **OVERLAPPING** | not computable | 2.26× | [0.478, 4.016] ⚠︎ | not established by these data |


### 3.16 The one latency comparison on which real inference was possible

[`vector_freshness_idle.json`](../data/raw/vector_freshness_idle.json) and
[`vector_freshness_loaded.json`](../data/raw/vector_freshness_loaded.json) preserve their
per-cycle observations. This is the only place in the repository where a bootstrap, a rank test
and a permutation test could be run at all, so they were run — as a demonstration of what the
other 91 comparisons could have had.

M7's claim is that vector-search freshness at RF = 3 under `vector-search = LOCAL_ONE` is
unaffected by a 40 vector-writes/s background load: insert → visible p50 **74.735 ms** idle
against **74.406 ms** loaded.

| Quantity | Value |
|---|---|
| idle: n, min / p50 / max | 60; 54.886 / 74.735 / 393.759 ms |
| loaded (40 writes/s): n, min / p50 / max | 60; 63.365 / 74.406 / 122.534 ms |
| Support | OVERLAPPING |
| Median difference (idle − loaded) | **+0.329 ms** |
| Bootstrap 95 % CI on the median difference (20 000 resamples) | **[−4.522, +1.632] ms** |
| Mann–Whitney *U* (idle), *z*, two-sided *p* (normal approximation, tie-corrected) | 1 685.0; *z* = −0.604; *p* = 0.546 |
| Permutation test on the median difference (200 000 shuffles, two-sided) | *p* = 0.860 |

**Verdict: no difference established between the idle and loaded arms.** The bootstrap interval
on the median difference contains zero and is narrow — ±a few milliseconds on a quantity of
~74 ms.

And it changes nothing, which is the point worth making. **A null result here is not evidence
that the `LOCAL_ONE` / `LOCAL_QUORUM` asymmetry is safe.** Both arms sit on a co-located ring
whose inter-replica latency is sub-millisecond, and the entire measurement is bounded below the
~74 ms HTTP round-trip floor. The dossier's own verdict on this axis — **NOT DETECTABLE**,
neither confirming nor refuting the article's §4 claim — is the correct one, and this analysis
does not improve on it. Note also the asymmetry the summary statistics were already showing: the
idle arm's max is 393.759 ms against the loaded arm's 122.534 ms, so if anything the *idle* run
carried the worse tail. With n = 60 that is one observation and it is not a finding.

The lesson is about the artefact, not about HCD. **The only *latency* comparison in this dossier
on which a third party can perform real statistical inference is an HCD-internal one with no
cross-engine counterpart, whose published verdict is that nothing was detectable.** Every
cross-engine *latency* claim in the headline table had its evidence discarded. One cross-engine
claim in that table does survive exact testing — the M19 miss rate — and it survives for a
reason that proves the rule: its probe stored **counts**, not latencies, so there was no sample
to summarise away (§3.17).

### 3.17 Miss rate at τ (M19) — an exact test that survives intact

M19 measures a **proportion**, not a latency: the fraction of just-written documents *not*
returned by a single search issued τ ms after the write, 30 cycles per point per engine. Counts
are not summarised away, so the exact conditional test for a 2 × 2 table (Fisher's) applies with
nothing lost.

| τ (ms) | MongoDB `$search` misses | HCD JVector misses | Fisher exact *p* (1‑sided) | Verdict |
|---|---|---|---|---|
| 0 | 30/30 | 0/30 | 8.46e-18 | certain in direction |
| 100 | 28/30 | 0/30 | 4.19e-15 | certain in direction |
| 250 | 25/30 | 0/30 | 2.74e-12 | certain in direction |
| 500 | 15/30 | 0/30 | 2.92e-06 | certain in direction |
| 750 | 10/30 | 0/30 | 3.99e-04 | certain in direction |
| 1000 | 0/30 | 0/30 | — | no difference observed |
| 1500 | 0/30 | 0/30 | — | no difference observed |
| 2000 | 0/30 | 0/30 | — | no difference observed |
| 3000 | 0/30 | 0/30 | — | no difference observed |
At τ = 0 the test reduces to the separation formula of §3.1: 30/30 against 0/30 is complete
separation of a binary outcome, *p* = 1 / C(60, 30) = 8.46 × 10⁻¹⁸.

**Read the last four rows as carefully as the first five.** From τ ≥ 1000 ms the two engines are
indistinguishable — both 0/30 — and no test can distinguish 0/30 from 0/30. The result is
therefore *bounded in workload class*: HCD's freshness edge is total below ~1 s and absent
above it. Three reserves travel with the table and none is droppable:

- The premise that makes the τ ≥ 1000 ms column decisive — that an LLM-driven conversational
  turn takes 1–10 s — is an **assumption stated by the challenge author** (D1), never measured
  against a real workload. The dossier says so.
- The crossover at ~1 s is **this deployment's own refresh interval**. The `mongot` measured is
  version 1.75.1, `localDev` edition, on a single-node `atlas-local` container; the commit
  interval is internal to the jar and was never read. It may **not** be quoted as "MongoDB Atlas
  Search lag" or as a property of MongoDB the product. A differently configured `mongot` moves
  the crossover.
- It is not like-for-like: MongoDB `$search` is lexical, HCD JVector is vector (C14, D4).


---

## 4. Coordinated omission: what a closed-loop probe actually measured

### 4.1 The mechanism

Every probe in this repository except the freshness probes is a **closed-loop sequential
client**: issue one operation, wait for it to complete, record the elapsed time, issue the next.
No operation is ever attempted while another is outstanding.

A closed loop cannot measure latency under load, because the load it applies is a function of
the latency it is measuring. When an operation is slow, the loop does not issue the requests
that would have arrived during it — it waits. The requests that would have queued behind the
slow operation are never sent, so the queueing delay they would have suffered is never sampled.
The probe records **service time at an offered rate the system under test is itself
setting** — which is the definition of the measurement artefact commonly called *coordinated
omission* (§7).

The consequences here are specific and they are not symmetric.

**(a) The two arms of every cross-engine comparison were driven at different offered rates,
and the slower engine got the gentler rate.** The offered rate a closed loop achieves is
1 / *service time*. The implied rates, computed from the published p50s in
[`cmp_hcd.json`](../data/raw/cmp_hcd.json) and [`cmp_mongo.json`](../data/raw/cmp_mongo.json)
(this is arithmetic on figures already published, not a new measurement):

| Arm, 16 × 8000 B (125 KiB), pass 1 | p50 (ms) | Implied offered rate (ops/s) |
|---|---|---|
| HCD Data API | 130.787 | ≈ 7.6 |
| HCD CQL-direct | 101.645 | ≈ 9.8 |
| mongo-wildcard | 7.621 | ≈ 131.2 |
| mongo-default | 6.484 | ≈ 154.2 |

The MongoDB arms were therefore asked to do roughly **17 to 20 times more work per second** than
the HCD arms, purely as a consequence of being faster. Neither arm approached saturation, so
this does not invalidate the comparison — but it does mean the comparison is between two systems
at two different, self-selected and unequal utilisations, and it is not the comparison the
article's own §10 requirement 1 asks for. The aggregation arm is the extreme case: at a p50 of
133 984 ms the HCD Data API scan offered ≈ 0.0075 operations per second.

**(b) The tails are systematically under-reported, on both sides.** The p95, p99 and max in
every record are tails of a service-time distribution sampled at negligible utilisation. They
are not tails of a response-time distribution under load, and there is no way to recover the
latter from the former. `RESULTS.md` already frames every latency figure here as a best case;
this is the mechanism by which that is true.

**(c) The one exception is declared, and it is the freshness probe.** Campaign 1's freshness
probe and its RF = 3 repeat were driven **open loop at a fixed offered rate** — 50 writes/s for
120 s, with the measured schedule slip recorded (0.056 s and 0.055 s at RF = 1; 0.066 s and
0.078 s at RF = 3) — as was the vector-freshness loaded arm at 40 vector-writes/s. Those are the
only measurements in the dossier that are not exposed to this artefact, and the article's §10
demands that shape of *every* comparison. The dossier's self-assessment scores itself at about
2.5 of §10's six requirements and fails requirement 1 outright. That self-assessment is correct
and this section does not soften it.

### 4.2 M17 → M18 is a coordinated-omission correction in miniature, and the only one in the dossier

This deserves to be named, because it is the same class of error caught and fixed inside the
artefact itself.

M17's `mongot` freshness probe wrote a document and then polled until the document became
searchable, then immediately began the next cycle. Because `mongot`'s commit is *periodic*, the
probe's cycle **phase-locked onto the commit cycle**: each cycle started just after a commit, so
each write waited close to a full interval. The result, p50 1015.201 ms with a tight spread
(min 978.641, max 1224.720), is not the lag of a typical write — it is the lag of a write issued
at the worst phase, measured repeatedly because the measuring loop had synchronised itself with
the system it was measuring.

M18 fixed it the way such artefacts are always fixed: by **breaking the coordination**. A random
0–1200 ms delay before each insert desamples the phase, and the lag becomes broad — min 89.1,
p10 254.5, p50 664.3, p90 988.7, max 1170.2 ms over n = 60 — a refresh interval of ~1.1 s rather
than a fixed per-write delay.

Two things follow, and the second is uncomfortable.

1. **The author found and corrected a measurement artefact that cut in his own favour**, at the
   cost of halving the headline margin on the one axis where HCD wins. That is the behaviour the
   rest of this repository is built to enable, and it worked.
2. **The same reasoning was never applied to any other probe.** Every mutation, read, search,
   aggregation and counting probe remains closed-loop, and the coordination there is not with a
   commit cycle but with the system's own service time — a subtler version of the same fault,
   and the one §10 requirement 1 exists to prevent. The dossier fixed the instance it noticed
   and left the class.

---

## 5. What a future run must record to permit real inference

None of this requires a better lab. It requires a different `distribution()`. The list below is
ordered by what it unlocks, and each item states what is currently impossible without it.

**1. The raw sample vector, always, beside the summary.** Every observation, in issue order,
with no filtering. This single change restores bootstrap intervals, rank tests, distribution
fitting, cross-pass pooling and every percentile a future reader might want. It costs a few
hundred kilobytes per campaign. Write both: the summary for reading, the vector for checking.

**2. Three timestamps per observation, not one duration.** The time the operation was *scheduled*
to be issued, the time it was *actually* issued, and the time it *completed*. The gap between
the first two is the schedule slip, and it is the only way to detect coordinated omission after
the fact rather than reasoning about it from the harness shape. Campaign 1's freshness probe
already records an aggregate slip; the pattern should be per-observation and universal.

**3. A declared offered-rate schedule, fixed and identical across arms.** Not "as fast as the
client can go", which is what a closed loop means. A rate, declared before the run, applied to
both arms, with the achieved rate and slip recorded. Where an arm cannot sustain the declared
rate, that is itself the finding — it is the saturation point, which this dossier never measured
on either engine. Requirement 1 of the article's §10 asks for exactly this.

**4. An *n* justified by a power calculation against a pre-declared minimum effect of
interest.** The dossier's n = 30 / 40 / 50 / 60 are conventions, not decisions; nowhere is there
a statement of the smallest difference that would have mattered. The declaration has two halves
and both must be written down before the run:

- *The minimum effect of interest.* For a latency comparison the natural form is a ratio of
  medians — "a difference below 1.2× would not change any conclusion in this dossier" — and it
  should be argued from the decision the measurement is supposed to inform, not chosen to be
  reachable.
- *The n that detects it.* For a distribution-free two-sample comparison the relevant effect
  size is the probabilistic index *p* = P(*X*<sub>A</sub> > *X*<sub>B</sub>), and Noether's
  formula for the Wilcoxon–Mann–Whitney test gives, for two equal-sized arms and total sample
  size *N*,

  ```
  N  =  (z_{1-alpha/2} + z_{1-beta})^2  /  ( 3 * (p - 0.5)^2 )        n per arm = N / 2
  ```

  (Noether 1987; see §7). Declaring α, 1 − β and the *p* corresponding to the minimum effect of
  interest fixes *n* by arithmetic instead of by habit.

  Worked, so that the numbers are concrete. At α = 0.05 two-sided and 80 % power: *p* = 0.70
  needs ≈ **33** observations per arm, *p* = 0.65 needs ≈ **58**, and *p* = 0.60 needs
  ≈ **131**. Run the same arithmetic backwards on the dossier's own sample sizes and it says
  something uncomfortable: **n = 30 per arm has 80 % power only against *p* ≈ 0.71** — an effect
  so large that seven of every ten paired draws must run in the claimed direction. Anything
  subtler than that was undetectable at the chosen *n* no matter what analysis anyone ran
  afterwards, which is exactly the pattern §3 shows: 56 separations at enormous ratios, and
  nothing usable in between.

**5. Interleaved arms, not blocks.** M14's own caveat records that its arms were "separated in
time rather than interleaved". Interleaving (A, B, A, B, …, with the order randomised) converts
a confound into noise and is what makes the exchangeability assumption behind §3's permutation
*p*-values defensible rather than merely conventional.

**6. Environment counters sampled alongside the observations.** On a shared host at load average
14–16, with a `system.paxos` residue that grew from 0 to ~13 GiB per node across the campaigns,
the state of the machine is a covariate. Record the host load average, the compaction counter,
the SSTable count and the `system.paxos` size at the start and end of every arm. Audit findings
I1 and I6 exist because none of this was captured and the contamination can therefore never be
quantified.

**7. A seed, and the harness version, per run.** The probes randomise (document contents,
ballast, the M18 pre-insert delay). Without the seed, "re-running the probe" is not repetition.

**8. Pre-registration of the analysis, not only of the thresholds.** The dossier already
pre-registers its decision rules, which is more than most engineering write-ups do. The missing
half is the analysis: which test, on which statistic, at which α, decided before the data are
seen. Where a threshold rule and a test would disagree — as M11's S2 ratio straddling its own
1.15 boundary across two passes nearly did — that must be resolved in advance.

---

## 6. How to quote a number from this repository

Derived from everything above. These rules are stricter than `RESULTS.md`'s caveat column, and
they are meant to be.

1. **Quote a ratio only with its support verdict.** If the row in §3 says OVERLAPPING, the
   permitted sentence is *"not established by these data"*. It is not *"no difference"* — the
   evidence was discarded, not collected and found null.
2. **Quote the ratio interval, not only the ratio of medians.** "23.7× [12.6, 49.3]" is a claim.
   "23.7×" alone is a number without a width, and the width here is often larger than the point
   estimate.
3. **Never quote a *p*-value from this document as a measure of size or importance.** It is a
   function of *n* and of separation, nothing else; every 30-versus-30 separation returns the
   same 8.46 × 10⁻¹⁸. And read it as an upper bound on evidential strength, because
   exchangeability is doubtful under closed-loop serial correlation (§3.2, warning 2).
4. **Never quote p95, p99 or max from an arm with n < 10.** That means the HCD aggregation arm's
   `p95_ms` and `p99_ms` are not quotable at all. Its p50 and its separation are.
5. **Every magnitude carries its regime word.** *Memtable-resident*, *cache-resident*,
   *disk-proven dataset but memtable-resident probed row*, or *post-flush*. A per-KiB rate quoted
   without saying which of ×7.50 / ×5.94 / ×1.52 it belongs to is a misquote, and two of those
   three cannot be tested at all (§2).
6. **Never quote any latency figure here as a production magnitude.** Closed loop, single
   sequential client, no concurrency, one shared and already-loaded host, one build of each
   engine, no multi-host topology. What the dossier establishes is mechanism and direction.
7. **Never quote the `mongot` figures as MongoDB Atlas Search.** The build measured is `mongot`
   1.75.1 `localDev` on a single-node `atlas-local` container, and the campaign record says so.
8. **Prefer the structural results when the point is architectural.** M1, M2, M20, M21 and M22
   need no statistics, gain nothing from them, and survive every method challenge in the dossier.
   They are the load-bearing results. The latency ratios are the decorative ones.
9. **Cite the raw filename.** Every row of the matrix names one, and every claim in
   `RESULTS.md` names one. A magnitude quoted without its file cannot be checked, and after §2
   it cannot be re-derived either.
10. **When quoting an HCD win, quote it from §3.** Both of them overlap. The one that survives
    on this axis is the **miss-rate** result of §3.17 — counts, exactly tested, direction certain
    below τ ≈ 1 s and absent above it — not either of the two latency margins.

---

## 7. References

Deliberately few. Each was checked against its publication record while writing this document.

- Wilcoxon, F. (1945). *Individual Comparisons by Ranking Methods.* **Biometrics Bulletin**,
  vol. 1, pp. 80–83. — the rank-sum test whose minimum attainable *p*-value is the exact
  permutation probability used throughout §3.
- Mann, H. B., & Whitney, D. R. (1947). *On a Test of Whether one of Two Random Variables is
  Stochastically Larger than the Other.* **The Annals of Mathematical Statistics**, 18(1),
  50–60. — the *U* statistic, used in §3.16 on the only arms whose observations survive.
- Noether, G. E. (1987). *Sample Size Determination for Some Common Nonparametric Tests.*
  **Journal of the American Statistical Association**, 82(398), 645–647. — the power formula
  quoted in §5, item 4.
- The exact conditional test for a 2 × 2 contingency table, due to R. A. Fisher, used in §3.17.
  Standard, and cited here without a venue string rather than with a guessed one.
- *Coordinated omission* (§4) is a measurement artefact named and popularised by **Gil Tene**
  (Azul Systems) in talks on latency measurement from around 2013, and corrected in the tools he
  publishes — HdrHistogram and the constant-throughput load generator `wrk2`
  (<https://github.com/giltene/wrk2>). There is no canonical paper; the attribution is to the
  talks and the tooling, and is given that way rather than dressed as a citation.

No other reference is claimed. Where this document states something as generally known —
that closed-loop harnesses under-report tails, that percentiles are not additive, that pooling
percentiles across passes is not an operation — it is stated unattributed rather than attached
to a source that was not checked.

---

*Generated from `data/raw/` on 18 September 2026. Machine-readable form:*
[`data/derived/inference.json`](../data/derived/inference.json). *Nothing under `data/raw/` was
modified.*
