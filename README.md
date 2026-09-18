# Shredding cost: what physical storage layout does to write cost and index freshness in document databases

*An adversarial self-verification. IBM DataStax HCD 2.0.6 (release `5.0.7.0-ea50e91ba01f`, Data API
v1.0.33) measured against MongoDB 8.0.32, and — for search freshness only — `mongodb-atlas-local`
8.3.11 with mongot 1.75.1 `localDev`.*

> **Note on the title.** Earlier versions of this title, and `CITATION.cff`, say *concurrency*.
> Concurrency was never measured: every probe in every campaign is a single sequential client
> ([RESULTS.md §6](RESULTS.md), [docs/RELATED-WORK.md §9](docs/RELATED-WORK.md)).

---

## Abstract

**Question.** Does the physical storage layout a document database chooses — a schema-oblivious
shred of each JSON document into generic typed columns with automatic indexes, against a native
document store — determine what it costs to mutate one field, how quickly that document becomes
searchable, and which queries the database can answer at all? **Method.** Seven measurement
campaigns over two days produced 23 numbered measurements (M1–M23) against the two stacks above, on
one shared host, with every probe a single sequential closed-loop client; the probe source, the
unedited raw JSON, an ADR evidence register and an adversarial audit written *against* the campaigns
are all published. **Principal findings.** On this build a single-field `updateOne` compiles to a
`SELECT` followed by one Paxos-guarded `UPDATE` carrying **11 assignments** over a **12-column** row
with **9 automatically created** storage-attached indexes, so mutation cost is charged against the
indexed content the mutation never touches (M1, M2); MongoDB's per-KiB mutation rate is more than an
order of magnitude below HCD's in a memtable-resident regime, and that direction is certain by
separation of support in 19 of 20 size × pass cells (M13, M14); and HCD's Data API exposes no
server-side aggregation, caps exact counting at 1 000 documents, and answers
`estimatedDocumentCount()` with **0** against a true 200 000 with nothing in the API signalling the
condition (M20–M22). Both axes on which HCD leads — filtered search on an undeclared field, and
search-index freshness — **fail separation of support as latency comparisons**; what survives on the
freshness axis is a miss-rate result, exactly tested, and bounded to write-to-search gaps below
about one second ([docs/STATISTICS.md §3.3](docs/STATISTICS.md), §3.17). **Principal limitation.**
"Write cost" is operationalised as client-observed latency and never as bytes, so the flagship
per-byte coefficient is not a property of the system: it takes the values **×7.50**, **×5.94** and
**×1.52** in three regimes on the same machine. And no probe persisted its per-observation series, so
no confidence interval can ever be computed from this artefact by anyone, including the author. What
this dossier establishes is **mechanism and direction**. It does not establish production magnitudes.

## Contribution

What is claimed to be new, at the strength the evidence supports and no higher. The long form, with
the prior work each item sits against, is [docs/RELATED-WORK.md §8](docs/RELATED-WORK.md).

- **A documentation contribution.** The physical row of an undocumented shredding layer, read
  directly from `system_schema`: twelve columns and nine automatic SAI on a collection declaring
  nothing, of which three column names are not in any public description of the pattern
  ([`findings.json`](data/raw/findings.json), M1); and the compiled form of a single-field `$set`,
  observed in 10 of 10 CQL traces (M2). `[U] → [M]`. One build, one day; an observation of an
  implementation, not an interface.
- **A methodological contribution, and the dossier's own correction of itself.** The per-byte
  mutation coefficient is a **regime artefact**: ×7.50 memtable-resident at RF 1
  ([`findings.json`](data/raw/findings.json), M3), ×5.94 with the dataset on disk at RF 3
  ([`findings_disk_rf3.json`](data/raw/findings_disk_rf3.json), M10), ×1.52 once a flush before each
  update forces the cycle's `SELECT` onto the SSTable path
  ([`rmw_postflush.json`](data/raw/rmw_postflush.json), M15). A single "cost per KiB" for an
  LSM-backed document store is therefore **not a well-formed number**. Reserve, in both directions:
  the flush protocol fragments the table into ~35 SSTables, inflating M15's absolute, and two of the
  three legs cannot be tested at all for want of a complete summary record
  ([docs/STATISTICS.md §3.14](docs/STATISTICS.md)).
- **A correctness result, not a performance one.** `aggregate`, `$group` and `distinct` return
  `COMMAND_UNKNOWN` (M20); `countDocuments` is refused above 1 000 documents on a stock container
  (M21); `estimatedDocumentCount()` returns **0** on a collection holding 200 000 documents, because
  it reads SSTable metadata and the memtable had not been flushed — not approximate, **wrong**, and
  silent (M22, [`findings_agg_hcd.json`](data/raw/findings_agg_hcd.json)). Independent of host, load,
  cache regime and percentile. An allow-list is a product decision and can change; the mechanism —
  no pipeline means the corpus crosses the client — is what resists time.
- **The apparatus, offered as a template.** A dossier built so that it could refute its author, with
  the refutations published rather than summarised: 52 numbered points, four reversals of its own
  headlines, and the raw files of the refuted runs kept intact.

**What this is not.** Not a benchmark and not a product comparison. It measures **no bytes written**
and therefore no write amplification; **no concurrency**; **no second implementation of shredding**,
so it cannot establish a claim about shredding as a class, only about one implementation of it; and
it discovers neither that shredding costs writes nor that secondary-index maintenance costs writes —
both are long-established ([docs/RELATED-WORK.md §9](docs/RELATED-WORK.md)).

## Research questions

Eight, reconstructed after the fact from the campaign abstracts and the decision rules carried in the
probe sources. **They are not a pre-registration**, and
[docs/RESEARCH-DESIGN.md §5](docs/RESEARCH-DESIGN.md) states exactly which parts of the design were
fixed before the data and which were not.

| | Question | Verdict |
|---|---|---|
| **RQ1** | What physical row does the HCD Data API store a JSON document as? | Supported; over-fulfilled (M1, M8) |
| **RQ2** | What engine operations does a single-field `updateOne` compile to, at which consistency levels? | Supported by trace, 10/10 (M2, M4–M6) |
| **RQ3** | Does mutation cost grow with indexed content the mutation never touches — driven by field *count* or by *bytes*? | Bytes dominate; the article's own step 4 contradicted (M3, M10, M11) |
| **RQ4** | Is the per-byte coefficient a property of the engine, or of the cache regime it was measured in? | Regime. It refuted the dossier (M15) |
| **RQ5** | Where is that rate charged — stateless tier or stateful engine? | Majority in the engine; the *share* is unidentified (M12, M14) |
| **RQ6** | How does HCD compare with MongoDB on mutation, and does it survive removing the tier? | MongoDB decisively, tier removed or not (M13, M14) |
| **RQ7** | Do the three axes the article claims *for* HCD actually favour it? | Split; two of three go against it (M7, M16–M19) |
| **RQ8** | What can the Data API's document model answer at all, on aggregation and counting? | A capability gap, not a latency race (M20–M23) |

Full statements, falsification criteria, and which criteria are `[PRE]` rather than `[POST]`:
[docs/RESEARCH-DESIGN.md §2](docs/RESEARCH-DESIGN.md).

## Principal results

| | |
|---|---|
| **HCD** | HCD 2.0.6, `nodetool version` `5.0.7.0-ea50e91ba01f`, Data API v1.0.33; RF = 1 (campaign 1), `{dc1:3}` thereafter |
| **MongoDB** | 8.0.32, three-member replica set, `w:majority` + `j:true`. Search freshness only: 8.3.11 `atlas-local`, mongot 1.75.1 `localDev` — a different deployment (audit I8) |
| **Host** | One QEMU VM, 80 vCPU, 220 GiB RAM, **shared**, at load average 14–16 throughout. No root, so the page cache was never dropped |
| **Dates** | 17–18 September 2026. `run_at_utc` is recorded in **26 of the 38** raw files; the twelve exceptions and one hand-typed stamp are listed in [data/README.md](data/README.md) |
| **Statistics** | Percentiles only; **no means for latency**. n = 30 per point, two passes at most, **no confidence intervals — and none is recoverable**, see [docs/STATISTICS.md §2](docs/STATISTICS.md) |

The full table with every arm and every raw-file reference is
[RESULTS.md §2](RESULTS.md#2-the-headline-table); the register is
[RESULTS.md §3](RESULTS.md#3-measurements-m1m23). **Inference status** is from
[docs/STATISTICS.md §3](docs/STATISTICS.md): *direction certain* means the two samples' supports are
disjoint; *not established* means the ratio interval spans 1.0. Ratio intervals are min/max
envelopes, machine-readable in [`data/derived/inference.json`](data/derived/inference.json).

| Axis | Margin, with its regime | Inference status | The reserve that must travel with it |
|---|---|---|---|
| **Single-field mutation, per indexed KiB** — M13, M14 | HCD 0.7775 ms/KiB via the Data API, 0.7037 CQL-direct, against MongoDB 0.0176 (wildcard) / 0.0098 (default): **44× / 79×** stack-to-stack, **40× / 72×** engine-to-engine. **Memtable-resident rate only** | **Direction certain** — 19 of 20 Data-API cells and 18 of 20 CQL cells disjoint; the three exceptions are all 8 KiB pass 2, caused by a MongoDB tail | ⛔ **Voids the precision, not the direction:** the slopes are fitted on **pass 1 only**, undeclared until now ([ARTIFACT.md §8.5](ARTIFACT.md)), and MongoDB's denominator is near-flat (r² 0.78 / 0.88 against HCD's 0.997) — *"the weakest quantity in the comparison"* ([METHODOLOGY.md §6](METHODOLOGY.md)). ⚠︎ The coefficient behind it collapses ×5.94 → ×1.52 on SSTables (M15). Durability matching favoured HCD; HCD lost anyway |
| **Point read by `_id`** — M16 | MongoDB p50 0.530 ms against HCD 10.382 ms: **≈19.6×** | **Direction certain** — [7.0×, 35.7×] | ⛔ Stack versus stack: HCD's ~10 ms is the tier HTTP hop, charged on reads too, and **no CQL-direct read arm was run** (challenge C15) |
| **Filtered search, undeclared field** — M16-A | HCD p50 17.376 ms against MongoDB-default 376.698 ms: **21.7× at the median** | **NOT ESTABLISHED** — interval **[0.465, 65.842]**, spanning 1.0 | ⛔ **The margin is not a result.** MongoDB-default's fastest of fifty (13.335 ms) beats HCD's median; HCD's slowest is 28.697 ms. What these data show is **predictability** — ~17 ms whatever the document, against 13–863 ms — over a MongoDB *never given the index* (C12) |
| **Filtered search, declared wildcard index** — M16-A | MongoDB p50 0.732 ms against the same HCD 17.376 ms: **23.7×** | **Direction certain** — [12.6×, 49.3×] | ⚠︎ The same HCD measurement as the row above: HCD has one path. A wildcard index is MongoDB doing HCD's job, and is not free at write time — which is row 1 |
| **Search-index freshness** — M17, M18, M19 | Miss rate of one search τ ms after the write: **HCD 0/30 at every τ; MongoDB 30/30 at τ = 0, 15/30 at 500 ms, 0/30 from τ = 1 000 ms**. Latency form: HCD p50 44.972 ms against mongot 664.3 ms corrected (1015.201 ms uncorrected) | **Counts: exactly tested**, Fisher *p* = 8.46e-18 at τ = 0, **no difference from τ ≥ 1 000 ms**. **Latency: NOT ESTABLISHED** — [0.155, 36.683]. The only separated version is the one the author withdrew | ⛔ The mongot measured is **1.75.1 `localDev`** on a single-node container: it may not be quoted as MongoDB Atlas Search. ⛔ Not like-for-like — `$search` is lexical, HCD JVector is vector (C14). ⚠︎ HCD's "synchronous" is only bounded below a ~45 ms HTTP floor; its max was 573.598 ms |
| **Aggregation** — M23, revised by campaign 7bis | MongoDB `$group` p50 222.711 ms against the Data API's client scan-and-aggregate 133 984.229 ms: **602× at ten groups**. Re-measured at three query shapes: **584×** at 10 groups, **151×** at 100 000 groups, **609×** filtered. HCD's own native CQL sweep: 2 011.399 ms — **66.6× between HCD's two paths**, 9.0× against MongoDB | **Direction certain**, bootstrap intervals over retained raw series: [577, 592], [148, 153], [599, 617], supports disjoint. The **n = 3** reserve is discharged — at n = 15 the HCD median is 132 985.311 ms, −0.7 % | ⛔ **A capability gap, not a latency race**: never quote "HCD is 602× slower", and never without the query shape — MongoDB's cost scales with group cardinality, HCD's does not. The same engine, host and corpus aggregate in ~2 s through CQL. ⚠︎ The CQL arm means abandoning the document model; the *pre-designing the partition key* half was withdrawn by D12, then **reinstated** when D12 was found to rest on a false premise — its "misaligned arm" runs against the same pre-partitioned table. Most of D12 survives: the ×1.28 between its two query shapes is still not established, and its scale reserve is untouched |
| **Exact count** — M21, M22, revised by campaign 7bis | MongoDB answers (115.009 ms exact, 12.659 ms indexed, estimate 200 000 **exact**); HCD **cannot** count above 1 000 documents at any phase, and its estimate returned **0** pre-flush, **171 267** after flush and **172 132** after major compaction, against a true 200 000 | **Structural, not statistical** — HCD produced no observations because the operation is refused | ⛔ The estimator is wrong in **steady state**, not only at cold start: ~14 % off after flush *and* after compaction. An earlier revision of this repository narrowed it to a cold-start artefact (D9); campaign 7bis **withdrew that narrowing**. ⚠︎ MongoDB wins by *answering*, not cheaply: its exact count is a scan |

Three further axes name no winner and are in the full table: **where the per-byte cost is charged**
(9 % by one method, 29 % by another, never reconciled — and **all ten cells of that comparison
overlap**, so neither figure rests on an established direction); **secondary-index freshness** (a
tie on first-query hits, attempts `{1: 40}` on every arm); and **vector freshness at RF = 3 under
`LOCAL_ONE`** (120/120 first-attempt hits; verdict **NOT DETECTABLE**, because any window is bounded
below a ~74 ms measurement floor).

**Why this count is ten and the article's is eight.** The diptych's tables report *eight* axes —
[Part I §4.4](docs/article/article-part1-what-a-mutation-costs.html) and
[Part II §6.1](docs/article/article-part2-when-the-index-is-current.html) — because two of the
measurements counted here have no comparator: **where the per-byte cost is charged** compares one
engine's own tier against its own storage, and **vector freshness under `LOCAL_ONE`** measures one
engine against its own acknowledgement. Both are properties of a single engine rather than axes on
which two engines are set against each other, and the article says so beneath its own tables. This
register counts them because it registers *measurements*; the article counts *comparisons*. Ten
minus those two is eight, and neither figure is wrong inside its own scope.

⛔ marks a reserve that **voids the claim as stated**; ⚠︎ one that **bounds its magnitude**. The
grading is developed in [docs/THREATS-TO-VALIDITY.md §2.2](docs/THREATS-TO-VALIDITY.md).

## The dossier against itself

This is the artefact's distinguishing feature, and it is meant to be read before the table above, not
after.

- **The flagship coefficient did not survive its own author.** ×7.50 was published, then shown to be
  a memtable artefact that flattens to **×1.52** once the read half of the read-modify-write cycle is
  forced onto SSTables (M15). Every per-KiB rate in the dossier was relabelled a memtable figure as a
  result, and ADR-001's action item 1 was reopened from `[x]` to `[~]`. **No genuinely disk-bound RMW
  read exists anywhere in this dossier.**
- **HCD's clearest win was narrowed three times, each time by the author.** The ~1 s mongot lag
  became 664.3 ms when the probe stopped phase-locking onto the refresh cycle (M18); then moot for
  conversational RAG, because MongoDB's miss rate is 0/30 once the write-to-search gap reaches
  1 000 ms (M19); then attributable to a **`localDev` build**, which is not MongoDB the product at
  all. [`findings_mongot_freshness.json`](data/raw/findings_mongot_freshness.json) still reads
  `p50_ms: 1015.201`, unedited, beside the file that refuted it.
- **Fifty-two numbered points** at which the measurements contradicted the article they were written
  to support — kept as a list rather than a summary, *because a summary would be a softening*:
  [RESULTS.md §4](RESULTS.md#4-where-the-dossier-proved-its-own-author-wrong).
- **And this revision adds two more against itself**: both axes on which HCD wins fail separation of
  support ([docs/STATISTICS.md §3.3](docs/STATISTICS.md)), and the headline ratios were fitted on one
  of the two passes collected, undeclared ([ARTIFACT.md §8.5](ARTIFACT.md)).

## Limitations in one screen

The full taxonomy — construct, internal, external and statistical conclusion validity, with every
I1–I9, C1–C15 and D1–D14 identifier filed against exactly one class — is
[docs/THREATS-TO-VALIDITY.md](docs/THREATS-TO-VALIDITY.md). Its §10 argues that these three, and not
the more conspicuous external ones, are what most narrow what may be said:

1. **Construct.** "Cost" is latency, never bytes. A layout property estimated through a latency proxy
   inherits the cache state of the run, which is why the flagship rate spans ×5 across three regimes,
   two container sizes and two replication factors. The rate is not merely imprecise; it is ill-formed.
   The **mechanism** (M1, M2) is untouched by this, because neither is a latency measurement.
2. **Statistical conclusion.** The per-observation series were discarded at write time by the probes'
   shared summarising helper: of 25 latency-bearing files, **two** retain their observations. No
   interval, no test, no re-percentiling, for any reader including the author, **permanently**. What
   the surviving minima and maxima do decide is overlap — and 34 of 93 comparisons overlap.
3. **Internal.** The instruments written by the measurer, the measurements carrying no pre-declared
   decision rule, and the comparisons that fail separation of support are **largely the same rows** —
   and they are disproportionately the rows favourable to the author's employer's product. The threat
   is not dishonesty; the dossier's conduct argues against that. It is that on exactly those rows a
   reader has no mechanism of verification and must take the author's word.

Everything else — one host, one build, no concurrency, no multi-host topology, a ~13 GiB/node
`system.paxos` residue, an unpurgeable page cache — is in [LIMITATIONS.md](LIMITATIONS.md) and
constrains *precision*, not *permission*.

## Repository map

| Path | What it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | Master register: headline table, M1–M23 by campaign, the 52 self-refutations, the measurements a later campaign overturned, the 16 axes never measured |
| [`docs/RESEARCH-DESIGN.md`](docs/RESEARCH-DESIGN.md) | The reconstructed design: constructs, RQ1–RQ8, falsification criteria, and what pre-registration is and is not evidenced |
| [`docs/STATISTICS.md`](docs/STATISTICS.md) | What may and may not be inferred: 93 comparisons classified by separation of support, ratio intervals, exact tests where counts survive, coordinated omission |
| [`docs/THREATS-TO-VALIDITY.md`](docs/THREATS-TO-VALIDITY.md) | The four-class taxonomy, the concordance from every I/C/D identifier, coverage gaps, and the three threats that most constrain |
| [`docs/RELATED-WORK.md`](docs/RELATED-WORK.md) | Positioning against prior work, what is confirmation and what is not, contributions N1–N5, and what is explicitly **not** a contribution |
| [`ARTIFACT.md`](ARTIFACT.md) | Artefact-evaluation record: ACM badge assessment (none claimable today), evidence manifest, what counts as a reproduction, defects found by re-running the published code |
| [`LIMITATIONS.md`](LIMITATIONS.md) | The adversarial half in English: integrity findings I1–I9, challenges C1–C15, meta-challenges D1–D5. The campaign-7 round D6–D14 exists only in French, and in the taxonomy |
| [`METHODOLOGY.md`](METHODOLOGY.md) | Verdict rules, evidence markers, instrument provenance, durability matching, regime taxonomy, self-compliance (about 2.5 of the 6 conditions the article imposes on others) |
| [`REPRODUCING.md`](REPRODUCING.md) | How to stand both stacks up and contradict us. States up front that you will not reproduce these numbers and are not supposed to |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | What to send: a refutation. Issue forms for a differing reproduction, a challenged claim, an evidence or citation defect |
| [`DISCLAIMER.md`](DISCLAIMER.md) | Personal research, not an employer position; what was measured; why this is not a benchmark or advice |
| [`data/raw/`](data/raw/) | The 36 JSON files the probes wrote, unedited, including the files a later run refuted |
| [`data/derived/inference.json`](data/derived/inference.json) | The re-analysis behind `docs/STATISTICS.md`, machine-readable and re-derived in CI |
| [`data/README.md`](data/README.md) | Data dictionary: one entry per raw file, its host fingerprint, and how to quote a number out of it |
| [`probes/`](probes/) · [`probes/README.md`](probes/README.md) | Every script that produced a number, and the provenance register: supplied-unmodified, supplied-patched (each patch listed), or measurer-written — written because audit finding I2 says the decisive verdicts rest most on the measurer's own code |
| [`docs/campaigns/`](docs/campaigns/) | The seven campaign reports, in French, as written at the time — except [06](docs/campaigns/06-freshness-read-search.fr.md), amended additively on 18 September 2026 to retract its own mongot claim. Nothing deleted, nothing reworded |
| [`docs/audit-adversarial.fr.md`](docs/audit-adversarial.fr.md) · [`docs/challenges.fr.md`](docs/challenges.fr.md) · [`docs/challenges-campagne7.fr.md`](docs/challenges-campagne7.fr.md) | The hostile record, in French; promoted to English in `LIMITATIONS.md`. **French is authoritative where the two diverge** |
| [`docs/adr/ADR-001-modelling-policy.md`](docs/adr/ADR-001-modelling-policy.md) | The modelling policy and the evidence register for M1–M8, M10–M19. **M20–M23 were never entered in it**; they live in `RESULTS.md` §3 |
| [`docs/synthesis/huit-axes.fr.html`](docs/synthesis/huit-axes.fr.html) | One-screen colour-coded synthesis of the eight axes for a reader who will not open the article: winner, margin, whether the direction is established, and whether the result holds beyond the measured envelope. `check_article_refs.py` compares its verdicts against the article's table and fails if they diverge |
| [`docs/article/`](docs/article/) | The article under verification, in its current two-volet form: [Part I](docs/article/article-part1-what-a-mutation-costs.html) (what a mutation costs) and [Part II](docs/article/article-part2-when-the-index-is-current.html) (when the index is current). Both carry the corrections this repository forced, including the separation-of-support verdicts and the pass-one disclosure. The single-file `article-corrected.html` they replace is removed |
| [`.github/workflows/`](.github/workflows/) | CI. A green check asserts internal consistency only — hashes, links, JSON validity, probe syntax, and the derived inference numbers. It re-measures nothing |

## How to quote a number from this repository

The full rule set is [docs/STATISTICS.md §6](docs/STATISTICS.md); these are the ones most often broken.

1. **Quote the measurement identifier** (Mxx) with the number, so its regime travels with it.
2. **Quote the regime word** — *memtable-resident*, *cache-resident*, *post-flush*. A per-KiB rate
   quoted without saying which of ×7.50 / ×5.94 / ×1.52 it is, is a misquote.
3. **Quote the interval, not the point.** "23.7× [12.6, 49.3]" is a claim; "23.7×" is a number
   without a width, and the width is often larger than the point.
4. **If the status is NOT ESTABLISHED, the permitted sentence is "not established by these data"** —
   not "no difference". The evidence was discarded, not collected and found null.
5. **Never quote a p95, p99 or max from an arm with n < 10**, and never quote any p99 here as a load
   tail: a closed loop samples slow periods less often than fast ones by construction.
6. **Never quote a mongot figure as MongoDB Atlas Search.** The build is `localDev`.
7. **Never quote any latency here as a production magnitude.** One host, one build, one client.
8. **Prefer the structural results** when the point is architectural: M1, M2, M20, M21 and M22 need
   no statistics and survive every method challenge. The latency ratios are the decorative ones.
9. **Cite the raw filename.** A magnitude without its file cannot be checked — and since the
   observations are gone, it cannot be re-derived either.

## Reproduction, licence, citation, conflict of interest

**Reproduction.** [REPRODUCING.md](REPRODUCING.md) states how to stand both stacks up, and states up
front that you will not reproduce these numbers. What *would* count as a reproduction is defined
qualitatively, with **no magnitude in any criterion**, in [ARTIFACT.md §5.1](ARTIFACT.md). Half the
system under test cannot be stood up from this repository as it stands — `env/` ships the MongoDB
compose only, and the Data API container's environment is `[U] not recorded`.

**Licence.** Apache-2.0 for everything under `probes/` ([LICENSE](LICENSE)); CC BY 4.0 for `docs/`,
`data/` and the root Markdown ([LICENSE-docs](LICENSE-docs)). If you redistribute the JSON under
`data/raw/` in modified form, say so: the value of that dataset is that it has not been edited after
the fact.

**Citation.**

> Leconte, David (2026). *Shredding cost: what physical storage layout does to write cost and index
> freshness in document databases.* Dataset. https://github.com/davidleconte/shredding-cost-hcd-mongodb

Machine-readable metadata: [`CITATION.cff`](CITATION.cff). **There is no DOI and no archival
deposit**, so this citation cannot be pinned to a state of the repository, and no ACM artefact badge
is claimable today — [ARTIFACT.md §2](ARTIFACT.md) says so at length rather than claiming otherwise.

**Conflict of interest.** The author is an IBM employee measuring an IBM product, and the result is
unfavourable to that product on most of the axes measured. The axes themselves were chosen by the
author and accreted campaign by campaign; where that selection is skewed toward HCD's expected
weakness, [DISCLAIMER.md](DISCLAIMER.md) and challenge C9 say so rather than leaving a reader to
notice. Most of the instruments carrying the decisive verdicts — including both verdicts favourable
to HCD — were written or patched by the measurer (audit finding I2), and the register that tabulates
that is [`probes/README.md`](probes/README.md). No figure under [`data/raw/`](data/raw/) has been
edited after the fact, including the figures a later run refuted. Corrections, contradictions and
reproductions that disagree with these results are the point of publishing, and are welcome as
issues.
