# Wording to insert — "One field, five operations" — after the 17 September 2026 measurement

All measurements: IBM DataStax HCD 2.0.6 (release string `5.0.7.0-ea50e91ba01f`, read from the node), Data API v1.0.33, one node, RF 1, working set memtable-resident, `commitlog_sync periodic 10 s`, client on the same host over loopback, harness `verify_storage_claims.py` 1.0 with two mechanical fixes recorded in `findings.json`.

---

## I. New marker — legend block (add after the [U] paragraph)

Visible text:

> **[M] Measured.** Observed on a named build under stated conditions, by a harness reproduced in the appendix. Stronger than [U], weaker than [D]: it establishes what one build did on one day, not what the vendor commits to. Every [M] claim names its measurement (M1–M4) and every measurement names its conditions.

HTML (matches the existing markup):

```html
<p><span class="ep ep-m">M</span> <strong>Measured.</strong> Observed on a named build under stated conditions, by a harness reproduced in the appendix. Stronger than <span class="ep ep-u">U</span>, weaker than <span class="ep ep-d">D</span>: it establishes what one build did on one day, not what the vendor commits to. Every <span class="ep ep-m">M</span> claim names its measurement (M1–M4) and every measurement names its conditions.</p>
```

CSS (add next to `.ep-u`):

```css
.ep-m{background:#E6F4EA;color:#1E5631;border:1px solid #BFE3C8}
```

---

## II. Replacements in the body (visible text; marker changes noted)

### II.1 — §2.1, column-names paragraph — marker [U] → [M]

REPLACE
> They should not be treated as an interface. Schedule them for verification against the build you deploy, not against this article.

WITH
> They should not be treated as an interface. On HCD 2.0.6 with Data API v1.0.33 (appendix, measurement M1) all nine appear under exactly these names, alongside three that the practitioner literature omits: `key`, the typed partition key; `tx_id`, a timeuuid that guards every conditional write; and `query_lexical_value`, the lexical column. Nine storage-attached indexes were created on that collection, which declared no vector option. That is one build's answer, not an interface; verify against the build you deploy.

### II.14 — §2.1, new paragraph on nested JSON (add after the [M] column-names paragraph, before Figure 1)

The shredding paragraph describes the decomposition for a flat document; nested JSON is where the model's reach and its limits both become concrete. Insert a new paragraph immediately after the column-names paragraph (the one II.1 re-marks to [M]) and before the Figure 1 `<figure>`:

Visible text:

> [M] Nesting is where this decomposition earns its keep and shows its edges. A nested document is flattened to dotted paths: every scalar, at any depth, lands in the typed value map for its type keyed by its full path — `payer.account.id`, `meta.flags.risk`, `lines.0.qty` — so any nested field becomes filterable with no index declaration, exactly as a top-level one does (measured on HCD 2.0.6, appendix M8). `exist_keys` enumerates every path including array indices; scalar arrays carry membership tokens, so `{tags: "instant"}` matches. Two edges are worth knowing before you model against them. First, inside an **array of objects** only positional paths exist: `{"lines.0.sku": "A"}` filters, but `{"lines.sku": "A"}` — "any line with that sku" — does not, because no path aggregates the field across elements. Second, the shredder enforces hard shape limits: nesting depth at most sixteen, at most one thousand properties per indexable object, and — as already noted — no indexed string beyond eight thousand bytes. All three surface as `SHRED_DOC_LIMIT_VIOLATION` at write time, not at query time. And because a mutation rewrites `doc_json` in full together with every derived map, the write cost of section 3 grows with the breadth and depth of the nesting, not only with the count of top-level fields.

HTML:

```html
<p><span class="ep ep-m">M</span> Nesting is where this decomposition earns its keep and shows its edges. A nested document is flattened to dotted paths: every scalar, at any depth, lands in the typed value map for its type keyed by its full path — <code>payer.account.id</code>, <code>meta.flags.risk</code>, <code>lines.0.qty</code> — so any nested field becomes filterable with no index declaration, exactly as a top-level one does (measured on HCD 2.0.6, appendix M8). <code>exist_keys</code> enumerates every path including array indices; scalar arrays carry membership tokens, so <code>{tags: "instant"}</code> matches. Two edges are worth knowing before you model against them. First, inside an <em>array of objects</em> only positional paths exist: <code>{"lines.0.sku": "A"}</code> filters, but <code>{"lines.sku": "A"}</code> — "any line with that sku" — does not, because no path aggregates the field across elements. Second, the shredder enforces hard shape limits: nesting depth at most sixteen, at most one thousand properties per indexable object, and — as already noted — no indexed string beyond eight thousand bytes. All three surface as <code>SHRED_DOC_LIMIT_VIOLATION</code> at write time, not at query time. And because a mutation rewrites <code>doc_json</code> in full together with every derived map, the write cost of section 3 grows with the breadth and depth of the nesting, not only with the count of top-level fields.</p>
```

### II.15 — §3.1, opening-phenomenon resolution — sharpen "fields" to "indexed bytes" (measurement M11)

The resolution paragraph attributes the crept-up latency to the *count* of added fields. The field-vs-byte measurement (appendix M11) shows the driver is the indexed *volume*, not the count: at constant indexed bytes, a 14× rise in field count moved update latency ×1.13–1.19, while at constant field count a ~16× rise in bytes-per-field moved it ×4.6 (r² 0.9999). Adding fields normally adds cost because the fields carry bytes, not because they are counted — so the sentence should name the real lever.

REPLACE
> The opening phenomenon now resolves itself. Write latency crept upward because the team <em>added fields</em>, and each added field was silently enrolled in the maintained index set. Nothing about their write pattern changed. The cost of their write pattern did.

WITH
> The opening phenomenon now resolves itself. Write latency crept upward because the team <em>added indexed content</em> — each new field was silently enrolled in the maintained index set, and it is the <em>volume</em> of that indexed content, not the number of fields, that the write pays for (appendix, measurement M11): at a fixed indexed volume, multiplying the field count fourteenfold barely moved the cost, while at a fixed field count the cost rose almost linearly with the bytes indexed. Nothing about their write pattern changed. The cost of their write pattern did.

HTML (the `<em>` tags are already in the source; only the middle changes):

```html
<p>The opening phenomenon now resolves itself. Write latency crept upward because the team <em>added indexed content</em> — each new field was silently enrolled in the maintained index set, and it is the <em>volume</em> of that indexed content, not the number of fields, that the write pays for (appendix, measurement M11): at a fixed indexed volume, multiplying the field count fourteenfold barely moved the cost, while at a fixed field count the cost rose almost linearly with the bytes indexed. Nothing about their write pattern changed. The cost of their write pattern did.</p>
```

### II.16 — §3.1, after the resolution paragraph — where the cost sits (additive [M] note, measurement M12)

The tier does not dominate the rate, so no existing sentence claiming the cost is in storage needs replacing — storage is where most of it is. But the article never says *which component* carries the cost, and that is a design fact worth stating: part of the rate is elastic, part is not. Insert a new paragraph immediately after the §3.1 resolution paragraph (the one ending "The cost of their write pattern did.") and before the "4. What decomposition purchases" heading is reached:

Visible text:

> [M] Where that cost sits is itself a design fact the paragraph above leaves implicit. Measured on this build (appendix, measurement M12), the per-byte rate splits roughly seventy–thirty between the two components that both grow with indexed bytes: about seventy per cent is the read, the conditional rewrite and the index maintenance, in the stateful storage engine that scales only by adding data-bearing nodes; the remaining quarter to a third is the JSON parse, the shred and the response serialisation, in the stateless Data API tier that scales by adding instances behind a load balancer. On a latency chart they are the same milliseconds, but they are not the same object of design — the minority is elastic, the majority is not. Two independent methods placed the split in that neighbourhood yet disagreed by more than a quarter at the largest sizes, so read it as a direction, not a precise ratio.

HTML:

```html
<p><span class="ep ep-m">M</span> Where that cost sits is itself a design fact the paragraph above leaves implicit. Measured on this build (appendix, measurement M12), the per-byte rate splits roughly seventy–thirty between the two components that both grow with indexed bytes: about seventy per cent is the read, the conditional rewrite and the index maintenance, in the stateful storage engine that scales only by adding data-bearing nodes; the remaining quarter to a third is the JSON parse, the shred and the response serialisation, in the stateless Data API tier that scales by adding instances behind a load balancer. On a latency chart they are the same milliseconds, but they are not the same object of design — the minority is elastic, the majority is not. Two independent methods placed the split in that neighbourhood yet disagreed by more than a quarter at the largest sizes, so read it as a direction, not a precise ratio.</p>
```

### II.17 / II.18 / II.19 — the "no MongoDB measurement" limitation falls (measurement M13)

Campaign 5 measured MongoDB's single-field mutation against HCD's on the same host, matched regime, matched durability and resources. Three passages that asserted or implied no MongoDB measurement are corrected.

**II.17 — appendix M-block, "what the measurements do not establish".** REPLACE the tail:
> Anything about another version of HCD or the Data API, about Apache Cassandra 5.0 or 6.0, or about MongoDB.

WITH:
> On the MongoDB side, only the single-field-mutation axis is measured (appendix, measurement M13, same host, matched durability and resources); read, search, aggregation and index freshness on MongoDB remain unmeasured. Anything about another version of HCD or the Data API, or about Apache Cassandra 5.0 or 6.0.

**II.18 — "Limitations", the documented-vs-measured asymmetry paragraph.** APPEND after "…and may reasonably weight the comparison accordingly.":
> One asymmetry that earlier editions carried has since been closed on the axis this article is about: MongoDB's single-field mutation was measured against HCD's on the same host, in a matched regime, with durability and resources matched (appendix, measurement M13). It confirmed the structural prediction of section 3 rather than overturning it — MongoDB's in-place update is far cheaper on this axis, by a wide margin, even when a wildcard index is added to match HCD's automatic indexing. The eleven-to-zero measurement asymmetry this section once conceded no longer holds for the mutation axis; it still holds for read, search and index freshness, where nothing on the MongoDB side was measured.

**II.19 — Disclosure.** REPLACE:
> the appendix reports one build's measurements, each with its conditions, and none of them licenses a comparison with anything.

WITH:
> the appendix reports one build's measurements, each with its conditions; one of them (M13) is a deliberate exception — a same-host, matched comparison against MongoDB on the single-field-mutation axis, the one place the methodology section's six requirements can be met on my own hardware because both engines run on it at once.

### II.2 — §2.1, index-budget paragraph — [D] unchanged, add one sentence

AFTER
> — five collections before exhaustion, on the upstream defaults.

INSERT
> (That figure is the budget the API checks at creation; the collection measured in the appendix, created without a vector option, received nine — measurement M1.)

### II.3 — §3, numbered list, step 4

REPLACE
> Maintain the indexes covering the fields that changed.

WITH
> Maintain the indexes — on the build measured here, over every indexed field of the document, not only the fields that changed (appendix, measurement M3).

### II.4 — §3, read-modify-write paragraph — marker [U] → [M]

REPLACE
> Pace that 2020 statement, which concerns a different API generation and cannot settle the question either way: whether the current shredding implementation reintroduces the cycle, or avoids it by some mechanism not publicly described, is precisely the kind of question the measurement in section 6 answers empirically for your build in a quarter of an hour.

WITH
> Pace that 2020 statement, which concerns a different API generation and cannot settle the question either way. What settles it, for a build you control, is a query trace rather than a latency curve. On HCD 2.0.6 with Data API v1.0.33, with tracing enabled on the node, every `updateOne` carrying a single `$set` produced two CQL statements: a `SELECT` of `key`, `tx_id` and `doc_json` by key, then one `UPDATE` rewriting every derived column and the whole `doc_json`, guarded by `IF tx_id = ?` (appendix, measurement M2). The cycle is present on that build. A cost-versus-size probe on the same build grew in step with a same-size read and could not, on its own, separate a read from a read-plus-rewrite; it is the trace, not the curve, that carries the claim.

### II.5 — §3, step-five paragraph — inner marker [U] → [M]

REPLACE
> The serial consistency level at which this executes in the Data API is [U] not established by any source I consulted; earlier drafts of this article asserted LOCAL_SERIAL, and I have removed the claim rather than defend it from memory.

WITH
> The consistency levels at which this executes in the Data API are [M] not published by any source I consulted; measured on HCD 2.0.6 with Data API v1.0.33, every statement on the collection ran at `LOCAL_QUORUM` and every conditional statement carried `LOCAL_SERIAL` as its serial level (appendix, measurement M4). Earlier drafts asserted `LOCAL_SERIAL` from memory; it is restored here on the strength of a trace, on one node with RF = 1 — the name is established, the multi-replica cost is not.

### II.6 — §3, blockquote after step five — optional precision

REPLACE
> The net effect is a write materially heavier than a blind CQL insertion,

WITH
> The net effect — two CQL statements for an update and for a delete, one for an insert, on the build measured (M2) — is a write materially heavier than a blind CQL insertion,

### II.7 — Figure 1 caption (HTML `<figcaption>`, not the SVG)

REPLACE
> Column names are reported rather than documented; consistency levels are deliberately left unstated, since no source of acceptable rank established them.

WITH
> Column names and consistency levels are not documented by the vendor; both were measured on one build (appendix, measurements M1 and M4), and the boxes should be read as observations of that build, not as a contract.

### II.8 — Figure 5 caption

REPLACE
> Structural, not documented: the placement of steps 1–3 in the storage stratum, which inherits the [U] marking of section 3.

WITH
> Measured, not documented: the placement of steps 1–3 in the storage stratum, observed by query trace on one build (appendix, measurement M2) and inheriting the [M] marking of section 3.

### II.9 — §6.3, after the probe listing — one sentence so the probe is not mistaken for the answer to §3

AFTER
> Run it idle, then run it again under write load.

INSERT
> This probe measures index freshness, not the write path; it does not tell you whether an update reads before it writes. For that, enable query tracing on one node for a handful of updates and read `system_traces` — the method behind measurement M2.

### II.13 — §4, after the JVector blockquote (new [M] qualifier on the searchability claim)

The claim "a document becomes searchable as soon as it is written" is quoted from the HCD docs about JVector adding documents to the graph immediately. That is a single-node, storage-layer statement; at RF > 1 it meets a consistency-level qualifier the article does not currently mention. Insert a new paragraph immediately AFTER the `<cite>…Hyper-Converged Database 2.0.</cite></blockquote>` and before the "4.1 Index freshness as a correctness property" heading:

Visible text:

> [M] One qualifier the vendor sentence omits, and it only appears above a single replica. At RF > 1 the Data API reads a vector search at `LOCAL_ONE` — one replica — while it commits a write at `LOCAL_QUORUM` — two of three (appendix, measurement M6). "Searchable as soon as it is written" is therefore a single-replica read guarantee, not a quorum one: a vector query issued at acknowledgement can, in principle, read the one replica the write has not yet reached. Measured on the co-located test ring (appendix, measurement M7) the effect was **not detectable** — in 120 of 120 cycles the just-written vector was the top match on the first `LOCAL_ONE` query, because sub-millisecond inter-replica latency closes the gap far below the round-trip that carries the query. The window is bounded below the measurement floor here; a wide-area deployment, where inter-replica latency is tens of milliseconds, is exactly where it would surface — which is the same window this article attributes to the other engine in Figure 2. The searchability guarantee is real; its scope is one replica, and the reader deploying across datacentres should measure it there.

HTML:

```html
<p><span class="ep ep-m">M</span> One qualifier the vendor sentence omits, and it only holds above a single replica. At RF &gt; 1 the Data API reads a vector search at <code>LOCAL_ONE</code> — one replica — while it commits a write at <code>LOCAL_QUORUM</code> — two of three (appendix, measurement M6). "Searchable as soon as it is written" is therefore a single-replica read guarantee, not a quorum one: a vector query issued at acknowledgement can, in principle, read the one replica the write has not yet reached. Measured on the co-located test ring (appendix, measurement M7) the effect was <strong>not detectable</strong> — in 120 of 120 cycles the just-written vector was the top match on the first <code>LOCAL_ONE</code> query, because sub-millisecond inter-replica latency closes the gap far below the round trip that carries the query. The window is bounded below the measurement floor here; a wide-area deployment, where inter-replica latency is tens of milliseconds, is exactly where it would surface — the same window this article attributes to the other engine in Figure 2. The searchability guarantee is real; its scope is one replica, and the reader deploying across datacentres should measure it there.</p>
```

### II.10 — Disclosure block

REPLACE
> **First**, no benchmark figures appear anywhere above, because a number produced on my hardware with my workload would tell you nothing about yours and would carry an authority it has not earned.

WITH
> **First**, no benchmark figures appear in the body of this article, because a number produced on my hardware with my workload would tell you nothing about yours and would carry an authority it has not earned; the appendix reports one build's measurements, each with its conditions, and none of them licenses a comparison with anything.

### II.11 — "Limitations of this article", first bold paragraph

REPLACE
> Several of these are almost certainly true. None is asserted here as documented.

WITH
> The first three were subsequently measured on one build — HCD 2.0.6 with Data API v1.0.33, one node, RF = 1 — and hold there (appendix, measurements M1–M4); they carry the [M] marker, which is weaker than [D]: an observation of a build is not a vendor's commitment. The fourth remains unverified. None is asserted here as documented.

### II.12 — "Limitations of this article", second paragraph — optional

REPLACE
> The equivalent statements about the Data API's physical representation are not published anywhere I could reach: they circulate as engineering description and practitioner lore.

WITH
> The equivalent statements about the Data API's physical representation are not published anywhere I could reach: they circulate as engineering description and practitioner lore — and, since this revision, as a measurement on one build, which is a different thing from documentation.

---

## III. New appendix subsection — insert after the sources `<dl>` and before "Limitations of this article"

Visible text, then HTML.

### Appendix B — measurements

Each entry records what was observed, on which build, under which conditions, and where the raw record lives. A measurement establishes what one build did on one day; it is not a vendor's documentation and does not license comparison with any other product.

**Common conditions.** IBM DataStax HCD 2.0.6, release string `5.0.7.0-ea50e91ba01f` read from the running node (`nodetool version`, `system.local`); Data API `stargateio/data-api` v1.0.33; astrapy 2.3.1. One node, one datacentre, RF 1 (`NetworkTopologyStrategy {dc1: 1}`), 16 vnodes. Virtual machine, 80 vCPU Intel Xeon Gold 6148 @ 2.40 GHz, 220 GiB RAM; the database container limited to 3 GiB with a 2 GiB heap; storage class of the backing media not determinable from the guest. `commitlog_sync periodic`, 10 000 ms. Working set memtable-resident throughout: no SSTable was flushed and no compaction crossed. Load driven at a fixed offered rate of 50 writes/s for 120 s, open loop, schedule slip under 0.06 s. Client on the same host over loopback. Harness `verify_storage_claims.py` 1.0 with two mechanical fixes (client environment set to HCD; probe-3 ballast excluded from indexing because the Data API refuses any indexed string above 8 000 bytes). 17 September 2026. Full record: `findings.json`.

**M1 — Physical column layout.** Establishes: a collection created with default options and no vector dimension is one table of twelve columns — `key frozen<tuple<tinyint,text>>`, `tx_id timeuuid`, `doc_json text`, `exist_keys set<text>`, `array_size map<text,int>`, `array_contains set<text>`, `query_bool_values map<text,tinyint>`, `query_dbl_values map<text,decimal>`, `query_text_values map<text,text>`, `query_null_values set<text>`, `query_timestamp_values map<text,timestamp>`, `query_lexical_value text` — with nine storage-attached indexes created automatically over all but `key`, `tx_id` and `doc_json`. Read from `system_schema.columns` and `system_schema.indexes`; identical in two runs.

**M2 — The write path of a single-field update.** Establishes: with query tracing at probability 1.0 on the node, each of ten `updateOne` operations carrying one `$set` produced, in order, `SELECT key, tx_id, doc_json FROM … WHERE key = ? LIMIT 1` and then `UPDATE … SET tx_id = now(), exist_keys = ?, array_size = ?, array_contains = ?, query_bool_values = ?, query_dbl_values = ?, query_text_values = ?, query_null_values = ?, query_timestamp_values = ?, query_lexical_value = ?, doc_json = ? WHERE key = ? IF tx_id = ?`. Each `deleteOne` produced `SELECT key, tx_id … WHERE key = ?` then `DELETE … WHERE key = ? IF tx_id = ?`. Each `insertOne` produced one `INSERT … IF NOT EXISTS`. Tracing was reset to 0.0 afterwards. Ten of ten updates showed the pair.

**M3 — Cost of a constant mutation against unchanged content.** Establishes: with one scalar field mutated by `$set`, thirty timed repetitions after five warm-ups per size, and the `updateOne` HTTP payload constant at every size (122–124 bytes request, 47 bytes response), median latency grew 7.50× (12.1 ms → 90.8 ms) between a 1 KB document and a 128 KB document whose additional content was seventeen indexed string fields that the mutation never touched; a same-size read by key grew 1.56×. With the same total sizes but the additional content excluded from indexing, the update grew 1.92× and 2.21× in two runs against reads of 1.86× and 1.94× — indistinguishable from a read under the pre-registered control rule, and therefore not, on its own, evidence of the cycle that M2 observes directly.

**M4 — Consistency levels.** Establishes: every one of seventy traced statements against the collection ran at `LOCAL_QUORUM`; every one of thirty conditional statements (`INSERT … IF NOT EXISTS`, `UPDATE … IF tx_id = ?`, `DELETE … IF tx_id = ?`) carried `LOCAL_SERIAL` as its serial consistency level. The client set no level; these are the Data API tier's defaults. On one node with RF 1 a single replica satisfies both, so the level's name is established and its multi-replica cost is not.

**M7 — Vector-search freshness at RF 3 (added measurement, three-replica ring).** Establishes: on a six-node, two-datacentre ring with the collection at `{dc1: 3}`, a vector collection of dimension 16 (cosine), the Data API reading vector search at `LOCAL_ONE` while writing at `LOCAL_QUORUM`, a just-written vector was the top match on the first `LOCAL_ONE` query in 120 of 120 cycles (60 idle, 60 under 40 vector-writes per second); in no cycle did the `LOCAL_QUORUM` key read find the document while the `LOCAL_ONE` vector search missed it. The insert-to-visible interval was HTTP-bound (median 74 ms in both regimes). Validity: the marker vector returned at cosine similarity 1.0 in rank 1, background vectors at 0.83 or below, and an unrelated query returned a different top match. Verdict: **not detectable** — the window `LOCAL_ONE` permits in principle is, on a ring whose replicas share one host and answer in under a millisecond, shorter than the round trip that carries the query. This neither confirms nor refutes the searchability claim; it bounds the window below the measurement floor, and names the wide-area topology this bench cannot reproduce as the place to measure it.

**M8 — Nested-JSON shredding (added measurement, raw CQL row).** Establishes, by reading the shredded row a nested document produced: nesting is flattened to dotted paths, and every scalar at any depth is placed in the typed value map for its type keyed by its full path (`payer.account.id`, `meta.flags.risk`, `lines.0.qty`), while `exist_keys` enumerates every path including array indices, `array_contains` carries scalar-array membership tokens and whole encoded array-objects, `array_size` holds per-path array lengths, and `doc_json` retains the original verbatim. Any nested scalar is therefore filterable with no index declaration. Two limits, both surfacing as `SHRED_DOC_LIMIT_VIOLATION` at write time: inside an array of objects only positional paths exist (`lines.0.sku` filters, `lines.sku` across elements does not), and shape is capped at nesting depth sixteen, one thousand properties per indexable object, and eight thousand bytes per indexed string. Because a mutation rewrites `doc_json` and every derived map, the section-3 write cost grows with nesting breadth and depth, not only with top-level field count.

**M10 — Disk-regime read-modify-write at RF 3 (added measurement).** Establishes, against a disk-bound state proven rather than assumed — 6.05 GiB on disk (three times the 2 GiB memtable budget), forty SSTables after a major compaction, seventy-eight compactions crossed on the counter, key and row caches invalidated — that the indexed-content coefficient does not collapse when the engine is made to touch its disk. A single-field update against seventeen indexed chunks grew ×5.94, against ×7.50 for the same probe in the memtable regime of an earlier campaign; index maintenance stays a first-order cost beside the input-output. Two confounds are left standing and must travel with the number: the earlier campaign ran on a smaller single-replica node, so the ×7.50→×5.94 change mixes regime with topology and hardware; and the operating-system page cache could not be dropped without root, so "disk-bound" means the dataset genuinely exceeds the memtable and lives in SSTables, not that every read missed memory. The probe also re-reads the row it just wrote, which is memtable-resident regardless of dataset size, so the regime acts through memory pressure rather than by serving the probed row from disk.

**M11 — Field count versus byte volume (added measurement, the decisive one).** Establishes which term of the indexed-content cost is the real driver, by two series each holding one term fixed. At a fixed indexed volume of 64 KiB, raising the field count from nine to one hundred and twenty-eight moved the update median only ×1.13 to ×1.19. At a fixed field count of sixteen, raising the bytes per field from 512 to 8000 moved it ×4.6, with a straight-line fit of r² 0.9999. The indexed **byte volume** is therefore the driver; field count is a weak secondary factor. An internal control — the sixteen-field, 4096-byte configuration, which appears in both series and is thus measured twice — agreed to within 2.0% and 0.7%, so the slopes are trustworthy. The pre-registered two-pass rule returns no clean verdict, because the two passes straddle the 1.15 line that separates "bytes dominate" from "inconclusive" (at 1.128 and 1.187); but neither approaches the 1.5 that would make field count an independent driver. The article's earlier "how many indexed fields" is consequently imprecise: the lever is indexed bytes.

**M12 — Where the per-byte rate lives: tier versus storage (added measurement).** Establishes, in the same proven disk regime as M10 and M11, that the ~0.77 ms per indexed kilobyte splits between two components that both scale with indexed bytes. By the bypass method — the same mutation measured through the Data API and again as the identical CQL statement pair run directly against the same row, its shredded values read back rather than recomputed — the storage term is 0.547 ms per kilobyte (r² 0.997) and the tier term 0.219 (r² 0.98), so the tier is about twenty-nine per cent of the rate; a second, independent method that subtracts the coordinator-side trace duration from the client latency put it lower, near nineteen per cent. The rate therefore lives majority in the stateful storage engine and a substantial minority in the stateless tier that scales out by adding instances. The Data API container carried a 2 GiB memory limit and no CPU cap, co-located with the nodes; its CPU alternated between about half a per cent while the direct-CQL arm ran and forty to two hundred per cent while the API arm ran, a third and independent sign that the tier does real work. The two methods agreed within a quarter at 8, 16 and 32 KiB but diverged by more than a quarter at 64 and 125 KiB, so the split is reported as a direction and a range, never a single ratio.

**M13 — HCD versus MongoDB on the single-field-mutation axis (added measurement, cross-engine).** Establishes, on one host with both engines running at once and the harness refusing to emit a ratio otherwise, that MongoDB's update is far cheaper than HCD's on this axis and, unlike HCD's, barely grows with document size. The same series (sixteen indexed fields, 512 to 8000 bytes each), thirty repetitions, two passes, cache-resident on both sides, gave a per-kilobyte slope of 0.7775 ms on HCD (r² 0.997) against 0.0098 ms for MongoDB with nothing indexed on the ballast (r² 0.78) and 0.0176 ms for MongoDB carrying a wildcard index that matches HCD's automatic indexing (r² 0.88) — HCD costing about seventy-nine and forty-four times the rate respectively. In absolute terms the update median rose from 41 to 131 milliseconds on HCD across the range and stayed near 5.5 to 7.6 milliseconds on MongoDB. Durability was matched by a declared judgement: MongoDB at a majority write concern with journalling, against HCD at LOCAL_QUORUM with LOCAL_SERIAL, each satisfied by two of three real replicas. MongoDB ran as a three-member replica set so the majority was genuine; each member and each HCD node was held to eight gibibytes and four virtual CPUs, though HCD additionally carries a Data API tier the other does not. One asymmetry is named rather than aligned: every HCD mutation pays a Paxos round that MongoDB, atomic at the document, does not. The pair of MongoDB arms is the finding — the default arm is MongoDB as deployed, the wildcard arm is MongoDB doing HCD's job — and both must be quoted or neither. This is the result the article's own reasoning predicts.

**What the measurements do not establish.** Any multi-replica cost was measured at RF 3 (M5) but only for the conditional-write path; end-to-end latencies there mix replication with a hardware difference (the three-replica ring's nodes are larger than the single node). Any disk-bound behaviour (every regime memtable-resident, no compaction crossed). The vector-search window under a real wide-area latency (M7 was measured on co-located replicas and could not reproduce it). The separation of replication lag from JVector index-build lag (M7 saw zero misses, so the two could not be told apart). Page-cache-cold reads (M10 could not drop the OS page cache; no root). The RF-and-hardware confound between the single-replica and three-replica campaigns. A memtable repeat of the field-versus-byte split (M11 ran only in the disk regime, though its per-byte linearity at r² 0.9999 is expected to be regime-robust). Anything about another version of HCD or the Data API, about Apache Cassandra 5.0 or 6.0, or about MongoDB.

HTML:

```html
<h2>Appendix B — measurements</h2>

<p>Each entry records what was observed, on which build, under which conditions, and where the raw record lives. A measurement establishes what one build did on one day; it is not a vendor's documentation and does not license comparison with any other product.</p>

<dl class="appendix">

<dt>Common conditions</dt>
<dd>IBM DataStax HCD 2.0.6, release string <code>5.0.7.0-ea50e91ba01f</code> read from the running node (<code>nodetool version</code>, <code>system.local</code>); Data API <code>stargateio/data-api</code> v1.0.33; astrapy 2.3.1. One node, one datacentre, RF 1 (<code>NetworkTopologyStrategy {dc1: 1}</code>), 16 vnodes. Virtual machine, 80 vCPU Intel Xeon Gold 6148 @ 2.40 GHz, 220 GiB RAM; the database container limited to 3 GiB with a 2 GiB heap; storage class of the backing media not determinable from the guest. <code>commitlog_sync periodic</code>, 10 000 ms. Working set memtable-resident throughout: no SSTable was flushed and no compaction crossed. Load driven at a fixed offered rate of 50 writes/s for 120 s, open loop, schedule slip under 0.06 s. Client on the same host over loopback. Harness <code>verify_storage_claims.py</code> 1.0 with two mechanical fixes (client environment set to HCD; probe-3 ballast excluded from indexing because the Data API refuses any indexed string above 8 000 bytes). 17 September 2026.</dd>
<dd class="m">Full record: <code>findings.json</code>.</dd>

<dt>M1 — Physical column layout</dt>
<dd>Establishes: a collection created with default options and no vector dimension is one table of twelve columns, with nine storage-attached indexes created automatically over all but <code>key</code>, <code>tx_id</code> and <code>doc_json</code>. Read from <code>system_schema.columns</code> and <code>system_schema.indexes</code>; identical in two runs.</dd>
<dd class="q">key frozen&lt;tuple&lt;tinyint,text&gt;&gt; · tx_id timeuuid · doc_json text · exist_keys set&lt;text&gt; · array_size map&lt;text,int&gt; · array_contains set&lt;text&gt; · query_bool_values map&lt;text,tinyint&gt; · query_dbl_values map&lt;text,decimal&gt; · query_text_values map&lt;text,text&gt; · query_null_values set&lt;text&gt; · query_timestamp_values map&lt;text,timestamp&gt; · query_lexical_value text</dd>

<dt>M2 — The write path of a single-field update</dt>
<dd>Establishes: with query tracing at probability 1.0 on the node, each of ten <code>updateOne</code> operations carrying one <code>$set</code> produced, in order, a <code>SELECT</code> of the whole document by key and then one <code>UPDATE</code> rewriting every derived column and <code>doc_json</code>, conditioned on <code>tx_id</code>. Each <code>deleteOne</code> produced a <code>SELECT</code> of <code>key, tx_id</code> then <code>DELETE … IF tx_id = ?</code>. Each <code>insertOne</code> produced one <code>INSERT … IF NOT EXISTS</code>. Tracing was reset to 0.0 afterwards. Ten of ten updates showed the pair.</dd>
<dd class="q">SELECT key, tx_id, doc_json FROM … WHERE key = ? LIMIT 1 — then — UPDATE … SET tx_id = now(), exist_keys = ?, array_size = ?, array_contains = ?, query_bool_values = ?, query_dbl_values = ?, query_text_values = ?, query_null_values = ?, query_timestamp_values = ?, query_lexical_value = ?, doc_json = ? WHERE key = ? IF tx_id = ?</dd>

<dt>M3 — Cost of a constant mutation against unchanged content</dt>
<dd>Establishes: with one scalar field mutated by <code>$set</code>, thirty timed repetitions after five warm-ups per size, and the <code>updateOne</code> HTTP payload constant at every size (122–124 bytes request, 47 bytes response), median latency grew 7.50× (12.1 ms → 90.8 ms) between a 1 KB document and a 128 KB document whose additional content was seventeen indexed string fields that the mutation never touched; a same-size read by key grew 1.56×. With the same total sizes but the additional content excluded from indexing, the update grew 1.92× and 2.21× in two runs against reads of 1.86× and 1.94× — indistinguishable from a read under the pre-registered control rule, and therefore not, on its own, evidence of the cycle that M2 observes directly.</dd>

<dt>M4 — Consistency levels</dt>
<dd>Establishes: every one of seventy traced statements against the collection ran at <code>LOCAL_QUORUM</code>; every one of thirty conditional statements carried <code>LOCAL_SERIAL</code> as its serial consistency level. The client set no level; these are the Data API tier's defaults. On one node with RF 1 a single replica satisfies both, so the level's name is established and its multi-replica cost is not.</dd>

<dt>What the measurements do not establish</dt>
<dd>Any multi-replica cost (RF 1). Any disk-bound behaviour (memtable-resident, no compaction crossed). The write-to-searchable interval of the vector index: the freshness probe exercised a storage-attached index on a scalar field, found the document on the first query in forty of forty idle cycles, and measured an end-to-end interval dominated by two HTTP round trips (idle median 19–25 ms, p99 54–78 ms; under 50 writes/s median 42 ms, p99 54–59 ms). Anything about another version of HCD or the Data API, about Apache Cassandra 5.0 or 6.0, or about MongoDB.</dd>

</dl>
```

---

## IV. SVG values — flagged, not patched (Figure 1 unless stated)

| Node text (verbatim) | Reason |
|---|---|
| `consistency levels: not established` / `by any source consulted here` / `verify against your own build` | superseded by M4 |
| `column names: reported, not documented` | superseded by M1; the box also omits `key`, `tx_id`, `query_lexical_value` |
| `maintain the indexes covering mutated paths` | contradicted by M3 |
| `shred → N CQL statements` | measured N: 1 insert, 2 update, 2 delete — information, not contradiction |
| Figure 5 `document fetched, changed in memory` / `whole document + derived columns` | confirmed by M2 — no change |
