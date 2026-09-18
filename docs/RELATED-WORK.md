# Related work, positioning, and what this work adds

*Until this file existed, this repository cited nothing. Not one author-year reference, not one DOI,
not one venue — outside `docs/article/`, which is the publication under verification and is out of
scope here. This document supplies the positioning that was missing. It adds no measurement, changes
no figure, and overturns no verdict. Its effect on the dossier's claims is to **narrow** them: most
of what was measured here was predictable from work published between 1983 and 2020, and saying so
is the precondition for stating clearly the few things that were not.*

**Nothing under `data/raw/`, `probes/` or `docs/article/` was read as anything but evidence, and
none of it was modified.** Every figure quoted below carries the raw file it comes from and the
regime it belongs to, per the rules in [RESULTS.md](../RESULTS.md#reading-rules-for-anyone-quoting-this-dossier)
and [METHODOLOGY.md §9](../METHODOLOGY.md).

---

## 0. Citation policy of this document

The dossier's evidence markers apply to sources as well as to claims. Three grades are used here,
and they are not interchangeable:

| Grade | Meaning | How it was checked |
|---|---|---|
| **Peer-reviewed / published** | A paper or book with a named author list, title and venue. | Author list, title, venue, year and — where given below — volume and pages were checked online during the writing of this document (18 September 2026). Where a full text was read, this document says so. |
| **Source of record** | Project or vendor documentation, a CEP, a release announcement, a repository. | URL loaded and the relied-upon passage quoted verbatim. These establish what a project or a vendor *says*, never what a system *does*. |
| **Unattributed** | A statement of common knowledge in the field, given without a source. | Written as common knowledge on purpose, because attaching it to a source that was not checked would be worse than leaving it unattributed. |

Anything that could not be verified is marked **[unverified reference]** in place, or is written
unattributed. There is no bibliography entry in §11 that was not checked. **Fewer and certain was
preferred to longer and plausible**, and the list is deliberately short: sixteen works, of which
thirteen are peer-reviewed or published books.

One consequence should be stated in advance, because it runs against the author. Adding a
bibliography does not make this dossier a piece of scholarship. It makes visible how much of the
dossier's mechanism was already published, which is the honest result and the reason this document
was written.

---

## 1. Log-structured merge storage, write amplification, and read-modify-write

**The published position.** The log-structured merge-tree was introduced by O'Neil, Cheng, Gawlick
and O'Neil (*Acta Informatica* 33(4), 1996, pp. 351–385) as a structure that converts random updates
into sequential writes by buffering in memory and merging to disk in the background. The design
trades read cost and background I/O for ingest cost. Luo and Carey's survey (*The VLDB Journal*
29(1), 2020, pp. 393–418) is the standard modern reference for the resulting taxonomy — write
amplification, read amplification, space amplification, and the fact that each is a function of the
merge policy and of where a given datum currently sits. Lu, Pillai, Arpaci-Dusseau and
Arpaci-Dusseau (*WiscKey*, USENIX FAST '16) is the standard reference for measuring write
amplification directly, in bytes written to the device per byte of logical update.

HCD 2.0.6 is a Cassandra-lineage engine — the vendor states that "HCD 2.x is based on Cassandra
5.0" (`docs/article/article-part1-what-a-mutation-costs.html`, appendix entry 5) — and Cassandra's storage engine is
LSM-structured (Lakshman and Malik, *ACM SIGOPS Operating Systems Review* 44(2), 2010, pp. 35–40).
MongoDB 8.x's default storage engine is not. **The mutation axis of this dossier is therefore, in
part, an LSM store measured against a B-tree-structured store, and no document in this repository
says so.** The words "LSM", "log-structured", "B-tree" and "WiredTiger" appear nowhere in the
repository's prose; "write amplification" appeared exactly once, as a keyword in `CITATION.cff`,
and has since been replaced there with "read-modify-write".

**What this positions.** The *direction* of M13 and M14 is what this literature predicts. A
read-modify-write over a wide, multiply-indexed row on an LSM store is expensive relative to a
targeted in-place field update on a B-tree store, and it is expensive in proportion to the volume
that has to be re-emitted, not in proportion to what changed. That is not a discovery. The
quantification on this stack is.

**And a correction that this literature forces on the dossier's own vocabulary.** The published
estimand for write amplification is **bytes**. This dossier measures **latency**:
`time.perf_counter()` around a client call in every latency probe, and coordinator-side durations
from `system_traces.sessions` for M5 and for method 2 of M12 (`data/README.md` records the
distinction). **No file under `data/raw/` contains a bytes-written, SSTable-bytes, write-amplification
or CPU-seconds figure.** `RESULTS.md §6` states it: "Write throughput | Never measured as such."
Therefore:

> **This dossier does not measure write amplification, and the `CITATION.cff` keyword
> "write amplification" overpromised.** It measures client-observed latency, from which write
> amplification cannot be recovered. The keyword now reads "read-modify-write"; the estimand the
> dossier cannot report is unchanged by the relabelling.

That distinction also explains the finding the dossier treats as its deepest — audit finding I4, the
×7.50 / ×5.94 / ×1.52 spread of the flagship coefficient across regimes (`data/raw/findings.json`,
`data/raw/findings_disk_rf3.json`, `data/raw/rmw_postflush.json`). In the LSM literature the cost of
touching a datum depends on whether it currently sits in the in-memory component or in a merged
on-disk component. A latency proxy therefore *must* move when the regime moves; a byte-level layout
cost would not move nearly as much. The ×5 interval is not only an empirical surprise: it is what a
latency operationalisation of a layout property produces. Stating it that way is stronger than
"unstable", because it says *why*.

## 2. Secondary-index maintenance on the write path

**The published position.** That secondary indexes are maintained synchronously on the write path,
and that their cost scales with the number of indexes and the volume of indexed content, is not a
research question; it is the documented design. For the specific mechanism measured here, the
sources of record are Apache Cassandra's own:

- **CEP-7: Storage Attached Index** (Apache Software Foundation wiki) states the motivation as
  indexing multiple columns on one table "without suffering scaling problems, especially at write
  time" — i.e. the write-path cost of multi-column indexing is the stated problem SAI exists to
  bound, not a side effect nobody anticipated.
- **Apache Cassandra documentation, "SAI write path and read path"**: *"After an SAI index is
  created, SAI is notified of all mutations against the current Memtable"*, and *"If an insert or
  update contains valid content for the indexed column, the content is added to a Memtable index,
  and the primary key of the updated row is associated with the indexed value."*

On the research side, Luo and Carey (*PVLDB* 12(5), 2019, pp. 531–543) treat LSM secondary-index
maintenance and its ingestion cost directly.

**What this positions.** M1 establishes that a collection declaring nothing gets **nine SAI indexes
created automatically** on **twelve physical columns** (`data/raw/findings.json`). M2 establishes
that a single-field `$set` compiles to a `SELECT` followed by one `UPDATE` carrying **eleven
assignments**, in 10 of 10 traces (same file). Put beside the sources above, the cost is exactly
what the write path is documented to do — the indexes are notified of the mutation and re-emit.

The part that is *not* inherited from the documentation, and that is this dossier's own, is
narrower and should be claimed at that width:

1. The user never declared the indexes. The Data API creates them, so the write-path cost is
   charged **by default rather than by choice** (M1; and the upstream `[D]` limit of "ten indexes
   per collection" is the creation budget, not the count created).
2. The `UPDATE` rewrites **derived columns the mutation never touched** — nine of them plus the
   whole `doc_json` — which is why M3's growth tracks the document's indexed content rather than the
   changed field (`data/raw/findings.json`, p50 12.104 → 90.783 ms = ×7.50 at 1 KB → 128 KB, **a
   memtable-resident RF = 1 figure**, against a same-size read control of ×1.56).

   **Reserve, and it is a serious one:** the raw file carrying that ×1.56 read control,
   `control_read_B.json`, **is not in this repository.** `probes/README.md` gap 8 records it as
   living in an off-repository archive. A published number rests on an unpublished file, and that
   sentence belongs beside the number wherever it is quoted.

## 3. Shredding: the XML- and JSON-into-relational lineage

**The published position.** Decomposing a hierarchical document into typed relational columns —
"shredding" — is a pattern with a twenty-five-year literature, and the title of this repository uses
its name without ever connecting it to that lineage.

- **Schema-driven shredding**: Shanmugasundaram, Tufte *et al.*, *Relational Databases for Querying
  XML Documents: Limitations and Opportunities*, VLDB 1999. Maps a document's declared structure
  onto relational tables, and analyses what the mapping costs and what it forecloses.
- **Schema-oblivious shredding**: Florescu and Kossmann, *Storing and Querying XML Data using an
  RDBMS*, IEEE Data Engineering Bulletin 22(3), 1999. Generic, structure-independent mappings —
  the ancestor of the pattern measured here, in which the storage layer knows nothing about the
  document's shape and must therefore carry a generic column set.
- **The JSON descendant**: Chasseur, Li and Patel, *Enabling JSON Document Stores in Relational
  Systems*, WebDB 2013 — the **Argo** mapping layer and the **NoBench** micro-benchmark. This is the
  published work closest to this dossier's subject, and the repository neither cites it nor uses its
  benchmark.

**What this positions, and the claim it licenses.** The Data API's layout observed in M1 — one row,
a `doc_json` blob holding the document verbatim, plus typed value maps (`query_text_values`,
`query_dbl_values`, `query_bool_values`, `query_null_values`, `query_timestamp_values`), presence and
shape metadata (`exist_keys`, `array_contains`, `array_size`) — is a schema-oblivious shredding in
the Florescu–Kossmann sense, expressed in a wide-column store rather than in a relational one. M8's
dotted-path flattening (`payer.account.id`, `lines.0.qty`) is the same idea applied to nesting.

From M1 and M2 together, one claim generalises beyond this build, and it is the only one that does:

> **For any schema-oblivious mapping of documents onto typed columns, a single-field mutation is a
> read-modify-write over the whole row, and its cost tracks indexed content rather than changed
> content — because the mapping cannot know which derived values changed without recomputing them.**

That is a statement about a design point, it is consistent with the lineage above, and it is the
level at which this work is of interest to a reader who will never deploy HCD. It is **argued**, not
established: this dossier measured **one** implementation of the pattern. A third arm holding the
document model fixed while varying the physical layout — a relational store with a general-purpose
index over the same documents is the natural choice — would be required to establish it. No such arm
was run, and `RESULTS.md §6`'s sixteen unmeasured axes do not currently list "only two systems"
among them. It should.

## 4. Near-real-time indexing and refresh intervals

**The published position.** mongot, the process that answers `$search`, is Lucene-based and separate
from `mongod`. MongoDB's own announcement of 15 January 2026 states both: *"Apache Lucene provides
mongot with the specialized data structures required for performant, feature-rich search and vector
search capabilities"*, and mongot *"can be run as a sidecar process on the same machine as
mongod … or … deployed as a service behind a load balancer"*.

That a Lucene-derived indexer makes new content visible only when a reader is reopened, and that
this reopening is periodic rather than per-write, is **stated here as common knowledge about
near-real-time indexers, without attribution** — there is no canonical paper for it, and attaching
it to one that was not read would be exactly the failure this document exists to avoid.

On the HCD side the corresponding vendor statement already sits in the article's appendix (entry 4):
DataStax states that *"When you insert data, JVector adds those new documents to the graph
immediately"*.

**What this positions.** M18 measured, with the probe de-synchronised, `$search` lag of min **89.1
ms**, p50 **664.3 ms**, max **1170.2 ms**, broad and phase-uniform
(`data/raw/findings_mongot_floor.json`). That profile is the signature of a periodic refresh, not of
a fixed per-write delay — which is to say M18 **confirms a documented design parameter of a class of
indexer**, and its value on one build. It is not a discovery about MongoDB, and three reserves
already recorded in the dossier must travel with it:

- the build is **mongot 1.75.1 `localDev`** on a single-node `atlas-local` container
  (`data/raw/findings_mongot_provenance.json`, image digest
  `sha256:e118f5c1…986d8f1`, edition read from the on-image file
  `/etc/mongodb-atlas-local/mongot-edition`). It may not be quoted as Atlas Search behaviour
  (challenge D2);
- the commit interval is internal to the jar and **was never read** (same file), so the ~1.1 s
  characterisation in `LIMITATIONS.md` is measured here, not sourced;
- M17's p50 **1015.201 ms** (`data/raw/findings_mongot_freshness.json`) was the worst phase of the
  cycle and was superseded by M18 by the author's own later measurement. The superseded file is
  still published, unedited, which is to the dossier's credit and does not make the superseded
  number quotable.

Symmetrically, HCD's side confirms a vendor claim rather than discovering a property: M17's HCD arm
gives p50 **44.972 ms** with poll attempts min = median = max = 1
(`data/raw/findings_hcd_vec_freshness.json`), which **bounds** the lag below the probe's HTTP
round-trip floor and does not show it to be zero (challenge C11). And the comparison is lexical
`$search` against vector JVector — not the same path (challenges C14, D4).

## 5. Conditional writes and consensus

**The published position.** Paxos is Lamport, *The Part-Time Parliament*, ACM Transactions on
Computer Systems 16(2), 1998, pp. 133–169. Cassandra's lightweight transactions are a Paxos-based
conditional-write facility; the vendor documentation for the phases is already cited in the
article's appendix (entry 14).

**What this positions.** M5 traced a full three-replica round for every conditional write on an
RF = 3 keyspace, message by message, with coordinator-side p50 for `UPDATE … IF` of **13.738 ms**
(`data/raw/findings_rf3.json`). Nothing about the protocol is new. Two things about its
*application* are worth stating, one of which runs against HCD and one of which runs against the
measurement:

- The Data API charges a Paxos-guarded conditional on **every single-field update** (M2, guarded by
  `IF tx_id = ?`). That is an API design decision with a per-mutation consensus cost, and it is
  observed here rather than documented anywhere the author could find.
- **13.738 ms is not the cost of Paxos.** All three replicas shared one host with sub-millisecond
  inter-replica latency. The protocol shape is established; the magnitude is measured where it hurts
  least, and on a real topology it is worse for HCD, not better (challenge C3; reading rule 8).

## 6. Benchmarking methodology

This is the section where the repository's own self-audit was, until now, **entirely
self-referential**: `METHODOLOGY.md §8` and `LIMITATIONS.md §1` score the dossier against "the six
conditions the article imposes on other people's benchmarks" — the author's own standard. A reader
could not tell whether the pitfall list was complete or merely the pitfalls the author thought of.

### 6.1 An external checklist

Raasveldt, Holanda, Gubner and Mühleisen, *Fair Benchmarking Considered Difficult: Common Pitfalls
In Database Performance Testing*, DBTest '18 (Houston, TX, 15 June 2018), catalogues eight pitfalls
in §3. The full text was read for this document. The mapping below is this document's own; the
pitfall names are the paper's section headings, verbatim.

| Pitfall (Raasveldt *et al.* §3) | Where this dossier stands |
|---|---|
| **3.1 Non-Reproducibility** | **Split.** Probe source and unedited raw JSON are published — better than most. But `env/` ships the MongoDB compose only; `REPRODUCING.md §4` declares the Data API container environment `[U] not recorded` and the HCD image's registry prefix unrecorded; images are referenced by mutable tag; and thirteen evidence files plus two producing scripts are in an off-repository archive (`probes/README.md` gap 8). **The HCD half of the system under test cannot be stood up from this repository.** |
| **3.2 Failure To Optimize** | **Acknowledged, and inverted in one place.** M16-A's 21.7× is a win over a MongoDB that was never given the index (challenge C12) — the paper's pitfall exactly, and the dossier says so in the headline cell. In the other direction, M13's durability matching was a declared judgement that **favoured HCD** (`j:true` waits for the fsync; `commitlog_sync periodic 10 s` does not), which is the opposite of the incentive the paper describes, and should be claimed as such. |
| **3.3 Apples vs Oranges** | **The dossier's densest cluster of known threats**: challenge C1 (M13 compares stacks, not engines), C15 (the read axis never corrected for the tier), C14/D4 (lexical `$search` against vector JVector), I8 (two different MongoDB deployments in one dossier), and M23's CQL arm, which reaches ~2 s only by abandoning the document model. All are declared; none is resolved. |
| **3.4 Overly-specific Tuning** | **The mirror image applies.** No system was tuned to a benchmark, but the *workload was designed to the mechanism*: 16 string fields of 512–8000 B chosen to make the indexed-byte term visible, with the chunking forced by the Data API's refusal of indexed strings above 8000 bytes (`METHODOLOGY.md` fix 2; M11 records that "the intended three-arm design was not executable" for the same reason). The ballast is not a corpus and is nowhere defended as representative of one. |
| **3.5 Cold vs Hot Runs** | **Direct hit, already conceded.** Challenge C2: no genuinely disk-bound RMW read exists anywhere in the dossier. The OS page cache was never dropped — no root on the host — and every raw record claiming a disk regime carries its own `page_cache_note` saying so. Every per-KiB rate in this repository is a hot coefficient. |
| **3.6 Cold vs Warm Runs** | **Met and declared**: 5 warm-ups before 30 timed repetitions in the supplied harness family, unchanged by the declared patches (`probes/README.md`). |
| **3.7 Ignoring Preprocessing Time** | **Reported, not hidden**: load times appear (MongoDB 4.0 s, native CQL 68.9 s, Data API 185.3 s for 200 000 rows; 1 057.2 s for HCD's 1 M-document load) and `RESULTS.md §6` states they are single readings with no percentiles and different durability paths. |
| **3.8 Incorrect Code** | **The open one.** Audit finding I2 records that the measurer wrote and modified the instruments. What no integrity finding caught, because none of them re-derived a published number from the published data, is that `probes/probe_comparative.py` fits **pass 1 only** — the merge hard-codes `k = f"{sz.label}\|pass1"` — so every cross-engine slope, r² and headline ratio is a single-pass figure, while pass 2 sits unused in `cmp_mongo.json` and `cmp_hcd.json`. This was verified again while writing this document. **Nothing in the dossier's prose declares it**, and audit finding I7 characterises inter-pass variance as "roughly 10–15 %" without covering the comparative slopes that carry the headline. |

One further recommendation from the same paper bears directly on this dossier's statistical policy:
the authors report *"the median value together with non-parametric, quantile-based 95% confidence
intervals"*. This dossier reports the median and no interval — and, as
[`docs/STATISTICS.md`](STATISTICS.md) establishes, cannot now compute one for 23 of its 25
latency-bearing files, because the per-observation series were summarised at write time and
discarded. The recommended apparatus is not merely absent; for most of the corpus it is permanently
unavailable.

### 6.2 Open versus closed loop, and coordinated omission

The dossier discusses closed-loop versus fixed-offered-rate load in at least four places
(`REPRODUCING.md §7`, `RESULTS.md §6`, `METHODOLOGY.md §6`, `LIMITATIONS.md §5`) and never names the
phenomenon. It has two names, one academic and one from practice:

- **Open versus closed system models**: Schroeder, Wierman and Harchol-Balter, *Open Versus Closed:
  A Cautionary Tale*, USENIX NSDI '06. Establishes that a closed model — in which a new request is
  triggered only by the completion of the previous one — and an open model, in which arrivals are
  independent of completions, produce substantially different behaviour, and that the choice is not
  a detail of the harness.
- **Coordinated omission**: named and popularised by **Gil Tene** (Azul Systems) in talks on latency
  measurement from around 2013, and corrected in the tools he publishes — HdrHistogram and the
  constant-throughput load generator `wrk2` (<https://github.com/giltene/wrk2>). **There is no
  canonical paper**; the attribution is to the talks and the tooling and is given that way here
  rather than dressed as a citation. The author's own article already cites `wrk2` for exactly this
  (appendix entry 30), so the vocabulary was available and was not used in the repository.

The mechanism, stated once, because the dossier never states it: in a closed loop the sampling rate
is itself a decreasing function of latency, so slow periods contribute proportionally fewer
observations. The published distribution is biased toward the fast regime **by construction**, which
is why its upper percentiles are not tails of anything. `docs/STATISTICS.md §4` now works this out
for this corpus.

Credit where the dossier has it and does not claim it: campaign 1's freshness probe paces on an
absolute schedule (`next_due += interval` — it waits for the clock, never for the server) and records
the residual slip. That is the correct construction, and it is the only probe in the repository that
has it.

### 6.3 Rigour in repetition and summarisation

Kalibera and Jones, *Rigorous Benchmarking in Reasonable Time*, ACM SIGPLAN ISMM 2013, is the
standard reference for deciding how many repetitions a systems experiment needs and for reporting
results with an effect-size confidence interval rather than a point.

Position, without softening: **no sample size in this dossier is justified.** n = 30 is inherited
from the supplied harness constant and carried forward; there is no power analysis, no minimum
detectable effect, and no stopping rule. The consequence is on record in the dossier's own data —
M11's pre-registered rule returned "BYTES DOMINATE" on pass 1 (endpoint ratio 1.128) and
"INCONCLUSIVE" on pass 2 (1.187), straddling its own 1.15 threshold
(`data/raw/findings_fieldbyte.json`). That is not an inconclusive *outcome*; it is a threshold finer
than the apparatus can resolve.

### 6.4 Reference workloads, and why none was used

- Gray (ed.), *The Benchmark Handbook for Database and Transaction Processing Systems*, Morgan
  Kaufmann, 1993 — the standard early collection on benchmark design.
- Bitton, DeWitt and Turbyfill, *Benchmarking Database Systems: A Systematic Approach*, VLDB 1983,
  pp. 8–19 — the Wisconsin Benchmark.
- Cooper, Silberstein, Tam, Ramakrishnan and Sears, *Benchmarking Cloud Serving Systems with YCSB*,
  ACM SoCC 2010, pp. 143–154 — the reference workload for this class of store.
- Chasseur, Li and Patel, WebDB 2013 — **NoBench**, the micro-benchmark for JSON document workloads,
  which is the closest published harness to this dossier's subject.

**No reference workload was run in any campaign.** The choice is defensible — YCSB does not exercise
a single-field `$set` against a wide, automatically indexed document, which is the entire axis of
interest, and NoBench targets query shapes rather than mutation cost — but the dossier never argues
it, and an unargued methodological choice reads as an oversight. The consequence is concrete and
should be stated where readers will meet it: **no number in this repository is commensurable with
any number published anywhere else.** "No reference workload was run" belongs in `RESULTS.md §6`'s
"Axes never measured" table, where it is currently absent.

### 6.5 Publishing benchmark results at all: the DeWitt-clause problem

The practice of prohibiting publication of benchmark results by licence is known as the **DeWitt
clause**, after the Wisconsin Benchmark (Bitton, DeWitt and Turbyfill, VLDB 1983) and the vendor
reaction to it. The clause is named in the peer-reviewed literature: Raasveldt *et al.* (DBTest '18,
§3.1) write that *"Calling systems 'DBMS-X' to avoid incurring the wrath of their legal departments
('DeWitt clause') is also counter-productive for reproducibility. Even if someone had access to a
particular system, how would one know which one was used?"* — i.e. the clause is treated there as a
**reproducibility** problem, not only a legal one. The detailed history of the clause's origin and
spread is documented in secondary, non-peer-reviewed sources, and no primary legal citation is given
here rather than a guessed one. **[unverified reference: no primary source for the clause's naming
history was checked.]**

This bears on the repository in two ways, and both are uncomfortable:

1. **The dossier names its systems and versions in full** — HCD 2.0.6 release
   `5.0.7.0-ea50e91ba01f`, Data API v1.0.33, MongoDB 8.0.32, mongot 1.75.1 `localDev` — which is the
   condition Raasveldt *et al.* say reproducibility requires, and is the opposite of "DBMS-X". That
   is a real methodological credit and should be claimed.
2. **`DISCLAIMER.md` then declines to state the author's own licence position**, saying that the
   check "is theirs to make, not the author's". A one-sentence answer either way would be more
   credible than the deferral, particularly given the employment conflict the same document
   declares. The reader is being handed the one question the author is best placed to answer.

## 7. The one directly comparable prior study

**Haughian, Osman and Knottenbelt, *Benchmarking Replication in Cassandra and MongoDB NoSQL
Datastores*, DEXA 2016, LNCS vol. 9828, pp. 152–166, Springer.**

This is the only published peer-reviewed comparison of the two engine *families* the author could
identify, and the diptych cites it (Part II, reference 32) with the annotation
"full text not consulted". **The full text was read while writing this document.** What it did, in
its own terms:

- **Harness**: YCSB, extended by the authors to support MongoDB write concerns and read
  preferences, plus a warm-up stage. One read-heavy workload (YCSB workload B, 95/5 read/write) and
  one custom write-heavy workload (95/5 write/read), at 1 KB records.
- **Systems**: **Cassandra 1.2.16** and **MongoDB 2.6.1**, the latter *"with all standard factory
  settings, with the exception that journaling (i.e., logging) was disabled"*.
- **Topology**: 14 VMs on a private cloud, 12 of them cluster nodes, 6 GB RAM and 8 cores each;
  64 client threads.
- **Axes**: replication factor against non-replicated clusters of equal size; consistency levels
  ONE, QUORUM and ALL; uniform, Zipfian and latest access distributions.
- **Finding**: master-slave replication (MongoDB, at that version) *"tend[s] to reduce the impact of
  replication compared to multi-master replication models exhibited by Cassandra"*, and replication
  must be modelled explicitly to evaluate either store accurately.

**How this dossier stands relative to it: it does not.** The two are not comparable, and the reasons
are worth naming precisely, because "not comparable" is itself a positioning result:

| | Haughian *et al.* 2016 | This dossier |
|---|---|---|
| Axis of interest | Replication factor and consistency level | Physical storage layout and its mutation cost |
| Load model | 64 concurrent YCSB threads across a 12-node cluster | **A single sequential closed-loop client**, every probe, every campaign (`RESULTS.md §6`) |
| Durability | MongoDB journaling **disabled** | `w:majority` + `j:true`, a declared choice that **favoured HCD** (M13) |
| Versions | Cassandra 1.2.16, MongoDB 2.6.1 | HCD 2.0.6 (Cassandra 5.0 lineage) with Data API v1.0.33; MongoDB 8.0.32 / 8.3.11 |
| What the versions foreclose | Predates SAI, predates the Data API and its shredding layer, predates mongot | — |
| Topology | 12 nodes, separate VMs | All HCD nodes and all MongoDB members on **one** host |

The one place the two touch is replication: their axis is replicated throughput and latency under
tunable consistency; this dossier's replication content is M5's Paxos-guarded conditional write at
RF = 3, M10's disk-regime re-run, and M7's `LOCAL_ONE` vector-freshness verdict of **NOT
DETECTABLE** (`data/raw/findings_vector_rf3.json`, 120/120 first-`LOCAL_ONE` hits). Lightweight
transactions are not a YCSB operation, so their study says nothing about M5, and M5 says nothing
about their finding.

**Conclusion, stated at full strength: not one claim in this dossier is confirmed or contradicted by
the only published comparison of these two engine families.** The dossier is unpositioned against
prior art not because prior art disagrees with it, but because prior art measured something else,
a decade earlier, on systems that no longer exist in the forms measured. That is the honest
relationship, and it is better than an invented agreement.

*Flagged, not edited (`docs/article/` is out of scope): article reference 32's annotation "full text
not consulted" remains a defect in the article. The paragraph above is this repository's answer, not
the article's.*

---

## 8. What this work adds

The identifiers **N1–N5** are introduced by this document and do not collide with the audit findings
(I1–I9), the challenges (C1–C15), the meta-challenges (D1–D5) or the measurements (M1–M23).

Each contribution is stated at the strength the evidence supports and no higher, with the raw file,
the regime, and the reserve that voids or bounds it.

### N1 — A documentation contribution: the physical schema of an undocumented shredding layer

On HCD 2.0.6 (release `5.0.7.0-ea50e91ba01f`) with Data API v1.0.33, a collection declaring no
options is stored as **one row of twelve physical columns with nine storage-attached indexes created
automatically**, read directly from `system_schema` (`data/raw/findings.json`, M1). Nine columns
appear under the names the pattern's public descriptions lead one to expect; **three do not** —
`key frozen<tuple<tinyint,text>>`, `tx_id timeuuid`, `query_lexical_value text`. Nested documents are
flattened to dotted paths, with positional paths inside arrays of objects and no `$elemMatch`-by-path
(M8).

- **Epistemic status**: `[U] → [M]`. The vendor documents none of these names.
- **Scope**: one build, one collection, one day. This is an observation of a build, **not an
  interface**, and any of it may change without notice.
- **Why it is a contribution at all**: the layer is undocumented, so a direct schema read is the only
  way to know. The audit rates M1 as one of two unattackable results precisely because it depends on
  no code the measurer wrote.
- **Reserve**: M8's evidence is **not** a raw JSON file — it is a CQL row read transcribed into the
  ADR evidence register (`RESULTS.md §3`). M1's is.

### N2 — Direct CQL-trace evidence of the read-modify-write cycle and its eleven assignments

Every `updateOne` carrying a single `$set` was observed, in **10 of 10 traces**, to compile to
`SELECT key, tx_id, doc_json … LIMIT 1` followed by one `UPDATE` carrying **eleven assignments**
(`tx_id = now()`, nine derived columns, and the whole `doc_json`), guarded by `IF tx_id = ?` under
Paxos (`data/raw/findings.json`, M2). Statement counts: `insertOne` = 1, `updateOne` = 2,
`deleteOne` = 2. The shape is identical at RF = 3, and the `updateOne` HTTP payload is constant at
122–124 B request / 47 B response across 1, 8, 32 and 128 KB documents, so the growth cannot be HTTP
transfer.

- **Why it is a contribution**: this is the mechanism, shown rather than inferred. It is what makes
  the design-point claim in §3 arguable at all, and it is independent of every latency figure in the
  dossier.
- **Reserve**: the companion consistency-level result M4 is stated as "70/70 statements at
  `LOCAL_QUORUM`", but the trace file that qualifies it — `probe4_traced.json`, which records
  `LOCAL_QUORUM` 70 **alongside `ONE` 42 and `LOCAL_ONE` 2** over 200 traces — is in the
  off-repository archive (`probes/README.md` gap 8), not in `data/raw/`.

### N3 — A methodological contribution: the per-byte cost coefficient is a regime artefact, not a property

The same quantity, on the same system, measured three ways:

| Regime | Growth, 1 KB → 128 KB | Raw file |
|---|---|---|
| Memtable-resident, RF = 1 | **×7.50** (p50 12.104 → 90.783 ms) | `data/raw/findings.json` (M3) |
| Disk-resident *dataset*, RF = 3, but the probe re-reads a memtable-resident row | **×5.94** (20.389 → 121.189 ms) | `data/raw/findings_disk_rf3.json` (M10) |
| `nodetool flush` before each update, forcing the cycle's `SELECT` onto the SSTable path | **×1.52** (107.765 → 163.402 ms) | `data/raw/rmw_postflush.json` (M15) |

An interval of roughly ×5 on one quantity. **A single "cost per KiB" for an LSM-backed document
store is therefore not a well-formed number**, and this is the most transferable thing in the
dossier: it is a statement about how such a cost can be measured at all, not about HCD.

Four reserves, all of which cut against the strength of the result:

1. **M15's ~100 ms absolute is inflated by its own protocol.** Flushing before every update
   fragments the table into ~35 small SSTables; a single `SELECT` may merge all of them. The true
   disk-bound value lies between the memtable figures and this fragmented worst case.
2. **No genuinely disk-bound RMW read exists anywhere in the dossier** (challenge C2). The page
   cache could never be dropped.
3. **The regimes differ in hardware as well as in regime** — campaign 1 on `rh-hcd`, campaigns 3–6
   on the `p16` ring — and the raw record says so.
4. **Two of the three legs cannot be examined statistically at all.** `findings_disk_rf3.json` stores
   p50 only, with no n, min or max; `rmw_postflush.json` stores no `min_ms`
   ([`docs/STATISTICS.md §3.14`](STATISTICS.md)). The triangle rests on point estimates, and only the
   ×7.50 leg — the one already relabelled a memtable artefact — separates.

This contribution also cost the dossier its own headline: every per-KiB rate in it (M3, M10, M11,
M12, M13) was relabelled a memtable/cache figure, and ADR-001's action item 1 was reopened from
`[x]` to `[~]`.

### N4 — Correctness and capability gaps in the Data API surface

The only family of findings in this dossier that is independent of host, load, cache regime and
percentile.

- **Exact counting is capped.** `countDocuments({})` and `countDocuments({cat:"c3"})` both fail with
  `TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the server`
  on a stock container, despite a client `upper_bound` of 400 000. **Captured**: the exception string
  is in `data/raw/findings_agg_hcd.json` (`result.counts.count_all_error`,
  `result.counts.filtered_error`), M21.
- **`estimatedDocumentCount()` returns a wrong answer, silently.** It answered p50 **6.875 ms** with
  the value **0** against a collection holding **200 000** documents. **Captured**:
  `result.counts.estimated = 0`, `result.counts.count_all_correct = false`,
  `result.ground_truth.n = 200000`, M22. Not approximate — **wrong**, with nothing in the API
  signalling the condition. An application testing `if count == 0` on a freshly loaded collection
  concludes it is empty.

**This is the single most novel item in the dossier**: a silent wrong answer, not a slow one.
Everything else measured here is a cost; this is a correctness failure. It is currently registered
as one row of the campaign the repository itself marks as carrying **no adversarial verdict**.

Three reserves, and the first is severe:

1. **The companion claim M20 is not captured evidence, in whole.** `RESULTS.md` M20 states that the
   `COMMAND_UNKNOWN` result "is a captured artefact — `findings_agg_hcd.json` (`structural` field)".
   Verified while writing this document: that field holds a **fixed string literal**, written
   unconditionally at `probes/probe_aggregation.py:190` regardless of server behaviour, and **no
   probe under `probes/` ever issues `aggregate`, `$group` or `distinct` against HCD** — the only
   `aggregate` calls in the tree are pymongo `$search`/`$group` calls against MongoDB. The probe's
   own docstring calls the finding "recon, not a measurement". M20 should therefore be read as
   **report-transcribed in whole** — the nineteen-command allow-list *and* the `COMMAND_UNKNOWN`
   result — and marked as such alongside M6 and M8. M21 and M22 are unaffected: their evidence is in
   the file.
2. **M22 is proven in the unflushed regime the campaign ran in**, which the zero itself proves. Its
   behaviour after a flush was never tested.
3. **The count cap is the server's own default on a stock container**; whether it is
   server-configurable was never established (M21 says so). The campaign showed only that the
   client's `upper_bound` does not move it.

### N5 — The adversarial self-verification apparatus, offered as a template

`RESULTS.md §4` reproduces **fifty-two numbered points** at which the measurements contradicted the
article they were written to support, "because a summary would be a softening". Two published
headlines were overturned by the author's own later measurements and both records were kept:
`findings_mongot_freshness.json` still carries `p50_ms: 1015.201` after `findings_mongot_floor.json`
refuted it, and the ×7.50 coefficient still stands in the register beside the ×1.52 that reduced it
to a memtable artefact. The instrument-provenance register in `probes/README.md` was written as a
direct answer to the audit's own finding I2, and it names the weaknesses of the instruments that
produced the author's favourite results.

**The honest reserve, which is the reason this is listed fifth and not first:** the self-criticism
was, until `docs/STATISTICS.md` was written, **conceptual and never computational**. Nine integrity
findings, fifteen challenges, five meta-challenges and two adversarial-verifier passes did not
re-derive a single published number from the published data. That is how the pass-1-only fit in
`probe_comparative.py` and the M20 evidence claim survived intact. A template whose weakness is that
it never checks the arithmetic should be offered with that weakness attached.

### Which measurements are confirmations, and which are not

| Class | Measurements | Reading |
|---|---|---|
| **Predictable in kind; the quantification on this stack is what is new** | M1, M2, M3, M5, M10, M11, M12, M13, M14, M16, M17, M18 | The mechanisms are documented or published (§§1–5). Valuable, specific, on an undocumented implementation — but not results a reader of the LSM, shredding and near-real-time-indexing literature would have been surprised by. |
| **Not predicted** | **M15** (the coefficient is a regime artefact — N3) and **M22** (a silent wrong count — N4) | These two are the dossier's genuine contributions in kind, and both are currently buried: M15 as a correction to the author's own headline, M22 as one row of an unchallenged campaign. |
| **Capability facts, not performance results** | M20, M21 | No server-side aggregation pipeline; exact count capped at 1 000. Independent of every regime caveat in the dossier — but see N4's reserve 1 on M20's evidence. |
| **Negative results, correctly kept** | M7 (NOT DETECTABLE), M11's straddle, variant A INCONCLUSIVE in every regime | Published adverse verdicts are stronger protection against selective reporting than most submitted work carries. |

---

## 9. What is **not** a contribution

Stated plainly, because a reviewer who is not told will assume the widest claim.

1. **Not a measurement of write amplification.** No byte-level figure exists anywhere in
   `data/raw/`. The `CITATION.cff` keyword has been replaced with "read-modify-write".
2. **Not a concurrency result.** `README.md`'s title and `CITATION.cff` both said "concurrency";
   every probe in every campaign is a single sequential closed-loop client, and `RESULTS.md §6`'s
   first row says so. The title overpromised, and both have been corrected to drop the word. The
   article under verification still carries it, and citations of the earlier repository title
   remain in circulation.
3. **Not a discovery that document shredding costs writes.** Shanmugasundaram *et al.* 1999,
   Florescu and Kossmann 1999, Chasseur *et al.* 2013.
4. **Not a discovery that secondary-index maintenance costs writes.** CEP-7 states it as the problem
   SAI exists to bound; the Cassandra documentation describes the write path.
5. **Not a discovery that a Lucene-derived indexer has a refresh interval.**
6. **Not a result about Paxos.** Lamport 1998. And 13.738 ms is not the cost of Paxos.
7. **Not a result about MongoDB Atlas Search.** mongot 1.75.1 `localDev` on `atlas-local`.
8. **Not a result about "document databases" as a class.** Two products, one host, one day per
   campaign, no third physical layout. The design-point claim in §3 is **argued** from M1 and M2, not
   established.
9. **Not a source of publishable magnitudes.** The dossier's own verdict, and it is correct. In
   addition: the headline 44×/79× are **pass-1-only fits**, undeclared anywhere in the prose, and
   `docs/STATISTICS.md` shows that 34 of 93 enumerated comparisons have ratio intervals containing
   1.0 — including **both** of HCD's wins.
10. **Not the first comparison of Cassandra-family and MongoDB storage.** Haughian, Osman and
    Knottenbelt 2016 exists, on other axes, other versions, other topology (§7).
11. **Not an independent verification.** The author is employed by one of the two vendors
    (`DISCLAIMER.md`), five decisive instruments are his own code (audit finding I2), and the axis
    selection is his own and accreted campaign by campaign (challenge C9).

---

## 10. Claims in this repository that this document could not source

Written down rather than quietly left, because an appeal to a body of work that is never named is
the one claim a reader cannot check — and this dossier's whole authority is traceability.

| Claim | Where | Status after this pass |
|---|---|---|
| "the practitioner literature" — the nine generic column names it "names", and the three it "omits" | `RESULTS.md:86`, `LIMITATIONS.md:539`, `METHODOLOGY.md:114` ([U] marker definition), `probes/README.md:27` ([R] marker definition), `docs/campaigns/01-verification.fr.md:68` | **Unsourced.** Two public sources describing the *pattern* were located: the Stargate project's post introducing the JSON API and Mongoose (13 March 2023, <https://stargate.io/2023/03/13/introduce-stargate-mongoose.html>, already appendix entry 13 of the article), which is the origin of the "super shredding" characterisation and **does not enumerate column names**; and a contemporaneous trade article on the same API whose body could not be retrieved during this pass. **Neither was confirmed to enumerate the nine names.** Recommended wording, which costs nothing and is true: *"nine columns whose names the author had previously seen asserted; the source was not recoverable at the time of writing."* The same applies to the `[U]` and `[R]` marker definitions, which rest on "practitioner literature" as a category with no exemplar. |
| "a Lucene-style refresh interval of roughly 1.1 s" | `LIMITATIONS.md:394` | **Half-sourced.** That mongot is Lucene-based **is** vendor-documented (§4, quoted). The ~1.1 s figure is **measured here** (`data/raw/findings_mongot_floor.json`), not sourced, and the commit interval internal to the jar was never read (`data/raw/findings_mongot_provenance.json` says so). The sentence should separate the two. |
| The nineteen-command Data API allow-list, and "the `data-api` container carries no count-limit environment variable" | `RESULTS.md` M20, M21 | **Report-transcribed, no captured artefact.** M21's own row already hedges the second as *d'après le rapport de campagne*. Per N4 reserve 1, the first should be extended to the whole of M20. |
| The supplier of the "vendor-supplied" harness, the class on which the dossier's entire trust ordering rests | `probes/README.md:20`, and ~20 uses of "vendor-supplied" across the Markdown | **Named nowhere.** If the supplier cannot be named and dated, the ordering measures **pre-registration**, not independence, and should say so. |

---

## 11. Bibliography

Sixteen entries. Each was checked online while this document was written (18 September 2026):
author list, title, venue and year in every case; volume and pages where stated below. Two full
texts were read for this document and are marked. Nothing is cited that was not checked, and no DOI,
page range or issue number is given that was not confirmed.

### Peer-reviewed papers and books

1. **O'Neil, P. E., Cheng, E., Gawlick, D., & O'Neil, E. J.** (1996). *The Log-Structured Merge-Tree
   (LSM-Tree).* **Acta Informatica**, 33(4), 351–385.
   — Establishes the storage structure underlying the HCD side of every mutation measurement (§1).
2. **Luo, C., & Carey, M. J.** (2020). *LSM-based storage techniques: a survey.* **The VLDB
   Journal**, 29(1), 393–418.
   — The modern taxonomy of write, read and space amplification; the reason a per-KiB coefficient is
   regime-dependent by construction (§1, N3).
3. **Luo, C., & Carey, M. J.** (2019). *Efficient Data Ingestion and Query Processing for LSM-Based
   Storage Systems.* **PVLDB**, 12(5), 531–543.
   — LSM secondary-index maintenance and its ingestion cost (§2).
4. **Lu, L., Pillai, T. S., Arpaci-Dusseau, A. C., & Arpaci-Dusseau, R. H.** (2016). *WiscKey:
   Separating Keys from Values in SSD-Conscious Storage.* **USENIX FAST '16**.
   — The reference for measuring amplification in bytes, which is the estimand this dossier does
   **not** use (§1).
5. **Shanmugasundaram, J., Tufte, K., et al.** (1999). *Relational Databases for Querying XML
   Documents: Limitations and Opportunities.* **VLDB 1999**, Edinburgh.
   — Schema-driven shredding of hierarchical documents into relational storage (§3). *The full
   author list is six names; it is given here as "et al." rather than risk stating the order
   wrongly.*
6. **Florescu, D., & Kossmann, D.** (1999). *Storing and Querying XML Data using an RDBMS.* **IEEE
   Data Engineering Bulletin**, 22(3).
   — Generic, structure-independent (schema-oblivious) mappings: the direct ancestor of the layout
   observed in M1 (§3).
7. **Chasseur, C., Li, Y., & Patel, J. M.** (2013). *Enabling JSON Document Stores in Relational
   Systems.* **WebDB 2013**.
   — The Argo mapping layer and the **NoBench** micro-benchmark; the closest published work to this
   dossier's subject, and the reference workload that was not used (§3, §6.4).
8. **Cooper, B. F., Silberstein, A., Tam, E., Ramakrishnan, R., & Sears, R.** (2010). *Benchmarking
   Cloud Serving Systems with YCSB.* **ACM SoCC 2010**, 143–154.
   — The reference workload for this class of store (§6.4), and the harness used by entry 13.
9. **Raasveldt, M., Holanda, P., Gubner, T., & Mühleisen, H.** (2018). *Fair Benchmarking Considered
   Difficult: Common Pitfalls In Database Performance Testing.* **DBTest '18**, Houston, TX.
   — **Full text read for this document.** The external checklist of §6.1, and the peer-reviewed
   naming of the DeWitt clause as a reproducibility problem (§6.5).
10. **Schroeder, B., Wierman, A., & Harchol-Balter, M.** (2006). *Open Versus Closed: A Cautionary
    Tale.* **USENIX NSDI '06**.
    — The academic statement of the closed-loop problem that this dossier describes four times and
    never names (§6.2).
11. **Kalibera, T., & Jones, R. E.** (2013). *Rigorous Benchmarking in Reasonable Time.* **ACM
    SIGPLAN ISMM 2013**.
    — Repetition counts and effect-size intervals; the apparatus this dossier has neither justified
    nor retained the data for (§6.3).
12. **Bitton, D., DeWitt, D. J., & Turbyfill, C.** (1983). *Benchmarking Database Systems: A
    Systematic Approach.* **VLDB 1983**, 8–19.
    — The Wisconsin Benchmark (§6.4, §6.5).
13. **Haughian, G., Osman, R., & Knottenbelt, W. J.** (2016). *Benchmarking Replication in Cassandra
    and MongoDB NoSQL Datastores.* **DEXA 2016**, LNCS vol. 9828, 152–166, Springer.
    — **Full text read for this document.** The only published comparison of the two engine
    families; §7 states why it is not comparable to this work.
14. **Lamport, L.** (1998). *The Part-Time Parliament.* **ACM Transactions on Computer Systems**,
    16(2), 133–169.
    — Paxos, which M2's conditional write and M5's traced round rest on (§5).
15. **Lakshman, A., & Malik, P.** (2010). *Cassandra: A Decentralized Structured Storage System.*
    **ACM SIGOPS Operating Systems Review**, 44(2), 35–40.
    — The lineage of the engine under HCD 2.0.6 (§1).
16. **Gray, J. (ed.)** (1993). *The Benchmark Handbook for Database and Transaction Processing
    Systems.* Morgan Kaufmann.
    — Benchmark design as a discipline (§6.4).

### Sources of record (project and vendor documentation)

All loaded on 18 September 2026. These establish what a project or a vendor **says**, not what a
system does.

- **Apache Software Foundation, CEP-7: Storage Attached Index** —
  <https://cwiki.apache.org/confluence/display/CASSANDRA/CEP-7%3A+Storage+Attached+Index>.
  Establishes that write-time scaling of multi-column indexing is the stated design problem (§2).
- **Apache Cassandra documentation, "SAI write path and read path"** —
  <https://cassandra.apache.org/doc/stable/cassandra/developing/cql/indexing/sai/sai-read-write-paths.html>.
  Establishes the notification-on-mutation write path, quoted verbatim in §2.
- **Apache Cassandra project blog, "Apache Cassandra 5.0 Features: Storage Attached Indexes"** —
  <https://cassandra.apache.org/_/blog/Apache-Cassandra-5.0-Features-Storage-Attached-Indexes.html>.
  SAI as a 5.0 feature; HCD 2.x is based on Cassandra 5.0 per the vendor (§1, §2).
- **MongoDB, "Now Source Available: The Engine Powering MongoDB Search"**, 15 January 2026 —
  <https://www.mongodb.com/company/blog/product-release-announcements/now-source-available-the-engine-powering-mongodb-search>.
  Establishes that Apache Lucene provides mongot's data structures and that mongot runs as a
  separate process; both quoted verbatim in §4.
- **Stargate project, "Introducing Stargate Mongoose and JSON API"**, 13 March 2023 —
  <https://stargate.io/2023/03/13/introduce-stargate-mongoose.html>. The origin of the "super
  shredding" characterisation; **does not enumerate column names** (§10).
- **Gil Tene, `wrk2` and HdrHistogram** — <https://github.com/giltene/wrk2>. Coordinated omission and
  constant-throughput load generation. **There is no canonical paper**; the attribution is to the
  talks and the tooling (§6.2).

### Stated without attribution, on purpose

- That a Lucene-derived indexer makes new content visible on a periodic reader reopening rather than
  per write (§4).
- That closed-loop harnesses under-report tails; that percentiles are not additive; that pooling
  percentiles across passes is not an operation (these three are already stated unattributed in
  `docs/STATISTICS.md §7`, and are repeated here under the same policy).

### Deliberately not cited

No source is cited here for: the naming history of the DeWitt clause beyond the peer-reviewed
mention in entry 9 (**[unverified reference]**); the internal commit interval of mongot 1.75.1
(never read — `data/raw/findings_mongot_provenance.json`); the "practitioner literature" appealed to
five times in this repository (§10); and any statement about MongoDB's WiredTiger internals beyond
the fact, asserted here as common knowledge, that it is not log-structured in the LSM sense. Where a
reader expects a citation and finds none, the absence is the claim.

---

*This document positions; it measures nothing. Every figure in it is quoted from a file under
`data/raw/` or from the campaign reports, with the file named. Where this document disagrees with
the repository's prose — on M20's evidence, on the pass-1-only fits, on "write amplification", on
"concurrency" in the title — the disagreement is stated here and the prose has not been edited to
match. Correcting it is a separate act, and it should be made deliberately.*
