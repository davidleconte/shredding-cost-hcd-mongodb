> **English abstract.** This campaign asked whether the claims the author had marked [U] in his own article hold on a real build: that a JSON document is shredded into one row of generic columns, that a single-field update performs a read-modify-write cycle, that step 4 of that cycle maintains only "the indexes covering the fields that changed", and at which consistency levels the Data API writes. Method: the pre-registered harness `verify_storage_claims.py` 1.0 — with two mechanical fixes that touched no threshold, no document size and no repetition count — ran four probes twice against HCD 2.0.6 with Data API v1.0.33 on one node, percentiles only, n = 30 per document size after five warm-ups, alongside a CQL query trace taken at `settraceprobability 1.0` and a same-size read control pre-declared to invalidate any verdict drawn from latency alone. Headline result: the cycle is observed directly rather than inferred — each `updateOne` carrying one `$set` produced `SELECT key, tx_id, doc_json` followed by a single `UPDATE` rewriting nine derived columns, `tx_id` and the whole `doc_json` under `IF tx_id = ?`, in 10 of 10 traced operations — and step 4 is contradicted: with the ballast indexed but never modified, a constant one-field `$set` grew from p50 12.104 ms at 1 KB to 90.783 ms at 128 KB (×7.50), against a read control of ×1.56 and an `updateOne` HTTP request that stayed at 122–124 bytes at every size. Two results went against the author: by his own control rule the latency probe is INCONCLUSIVE, because update growth (×1.92 and ×2.21 over two passes) is not separable from same-size read growth (×1.86 and ×1.94), so the trace and not the curve carries the claim; and the article's sentence promising that "the measurement in section 6 answers empirically … in a quarter of an hour" points at the wrong measurement, section 6.3 measuring freshness rather than the cycle. The freshness probe is itself INCONCLUSIVE against the harness's own 50 ms rule (p99 under load 59.178 ms and 53.849 ms), although at idle the marker was found on the first `find_one` in 40 of 40 cycles. Scope limit that must travel with every number above: one node, RF = 1, the whole working set memtable-resident (zero SSTables flushed, no compaction crossed, so requirement 6 of the harness is not met), client on the same host over loopback, `commitlog_sync periodic 10 s` — `LOCAL_QUORUM` and `LOCAL_SERIAL` are therefore names satisfied by a single replica rather than measured multi-replica costs, and the ×7.50 is a memtable-regime coefficient which a later post-flush pass (M15, `data/raw/rmw_postflush.json`), forcing the cycle's `SELECT` onto the SSTable path, collapsed to ×1.52.
>
> *Report body below is in French. Raw evidence: `data/raw/findings.json`.*

---

# Vérification des affirmations [U] — HCD 2.0.6 + Data API v1.0.33 sur `rh-hcd` (alphadebunker), 17 septembre 2026

**Le résultat ne vous donne pas tort sur la thèse, et vous donne tort sur deux formulations.** Le cycle lecture-modification-réécriture (A3) existe sur ce build : il est **observé directement** dans les traces CQL (`SELECT … doc_json` puis `UPDATE` de toutes les colonnes `IF tx_id = ?`). En revanche : (1) la **sonde de latence seule ne tranche pas** — par votre propre règle de contrôle en lecture, la sonde 3 est INCONCLUSIVE (facteurs de croissance update ×1,92 / ×2,21 contre lecture ×1,86 / ×1,94), et la phrase de §3 qui promet qu'une mesure « answers empirically … in a quarter of an hour » désigne de surcroît la mauvaise mesure (§6.3 mesure la fraîcheur, pas le cycle) ; (2) l'étape 4 « *Maintain the indexes covering the fields that changed* » est **contredite** sur ce build : toutes les colonnes dérivées sont réécrites à chaque update, et le coût d'une mutation constante d'un champ croît ×7,5 avec du contenu indexé **non modifié**. A2 (colonnes) et A5 (niveaux de cohérence) sont SUPPORTED. La fraîcheur (sonde 2) est INCONCLUSIVE par le seuil du harness (p99 chargé 59,2 / 53,8 ms ≥ 50), sans latence d'index détectable à vide (40/40 trouvés au premier essai).

Tous les chiffres ci-dessous valent pour : **1 nœud, RF = 1, jeu de données entièrement en memtable (0 SSTable flushée), client sur la même machine via loopback, `commitlog_sync periodic 10 s`**. Conditions complètes dans `findings.json → conditions.TO_BE_COMPLETED_BY_HAND`.

---

## 0. Ce qui a été changé dans le harness, et pourquoi (avant tout chiffre)

| Où | Changement | Raison mécanique | Effet sur le protocole |
|---|---|---|---|
| `connect_data_api()` | `DataAPIClient(token)` → `DataAPIClient(token, environment=Environment.HCD)` | HCD auto-hébergé sert `/v1` ; sans `environment`, astrapy 2.3.1 cible `/api/json/v1` d'Astra → **HTTP 404 sur toute commande** (reproduit en lecture seule avant le changement) | aucun |
| `main()`, `create_collection` | ajout de `definition={"indexing": {"deny": ["ballast"]}}` | La Data API **refuse toute chaîne indexée > 8 000 octets** (`SHRED_DOC_LIMIT_VIOLATION` à 8 192 o) : le ballast mono-chaîne de 8/32/128 Ko de la sonde 3 ne peut pas être indexé | Tailles, mutation, 5 échauffements, 30 répétitions, seuils 1,2/1,6 **inchangés**. Le ballast reste dans `doc_json`. Variante A = verdict A3, pré-déclarée ; variante B (chunks indexés ≤ 8 000 o, collection à indexation par défaut) rapportée en complément — option C validée par vous |

Aucun seuil, aucune taille, aucune répétition n'a été modifié. Le script original est conservé (`verify_storage_claims.py.orig`), le diff est intégral dans la conversation.

## 1. Conditions d'exécution

- **Produit** : HCD 2.0.6 (`hcd:2.0.6-ubi`), `nodetool version` = `5.0.7.0-ea50e91ba01f`, idem `system.local` ; Data API `stargateio/data-api:v1.0.33` ; astrapy 2.3.1 ; cassandra-driver 3.30.1 ; Python 3.12.3.
- **Topologie** : 1 nœud `rh-hcd` (172.27.0.2), cluster `recherche-hybride`, dc1/rack1, 16 vnodes. Keyspace `verif_stockage_20260917` = `NetworkTopologyStrategy {dc1: 1}`. Un seul niveau Data API (`rh-data-api`, 2 Gio), même pont Docker ; client sur l'hôte via `127.0.0.1:8181`.
- **Matériel** : VM QEMU, 80 vCPU Xeon Gold 6148 @ 2,40 GHz, 220 Gio RAM ; disque virtuel 1,4 Tio (`ROTA=1`, média physique indéterminable). Conteneur : `mem_limit` 3 Gio (max observé 2,944 Gio, **aucun OOM-kill, 0 redémarrage**), pas de plafond CPU, heap 2 Gio, memtable 512 + 512 Mio, `file_cache` 512 Mio. Pause GC max sur l'uptime : 2 165 ms ; pendant l'expérience : 26 ms.
- **Working set / RAM** : régime **en mémoire** uniquement — 12 000 documents de charge (~0,6 Ko) dans la collection A, **0 SSTable flushée, aucune compaction traversée** (l'exigence 6 du harness n'est pas remplie). `nodetool tablestats` lève une NPE sur ce build ; tailles lues via `du` et `count(*)`.
- **Durabilité** : `commitlog_sync = periodic`, période **10 000 ms** (ack avant fsync), `trickle_fsync = true`. Niveaux de cohérence : non fixés côté client ; ceux observés sont les défauts du niveau Data API.
- **Charge** : 50 écritures/s offertes pendant 120 s, boucle ouverte ; **glissement 0,056 s (passe 1) et 0,055 s (passe 2)** → débit tenu, aucun relancement à débit réduit n'a été nécessaire. Tracing remis à 0,0 et vérifié.

## 2. Tableau de synthèse

| # | Affirmation | Marqueur actuel | Verdict mesuré (ce build) | Marqueur proposé |
|---|---|---|---|---|
| A2 | Colonnes génériques `doc_json`, `exist_keys`, `array_contains`, `array_size`, `query_*_values` (§2.1, Fig. 1) | [U] | **SUPPORTED** — 9/9 noms exacts ; en plus : `key frozen<tuple<tinyint,text>>` (clé), `tx_id timeuuid` (garde LWT), `query_lexical_value text` ; **9 index SAI** créés (pas de vecteur) — identique en passe 2 | **[M]** (voir §5) |
| A3 | Cycle lecture-modification-réécriture, étapes 1–3 (§3, Fig. 1, Fig. 5) | [U] | Sonde de latence : harness ×1,92 / ×2,21 (SUPPORTED brut) **→ INCONCLUSIVE par votre règle de contrôle** (lecture ×1,86 / ×1,94). **Trace CQL : SUPPORTED** — par `updateOne` : `SELECT key, tx_id, doc_json WHERE key = ?` puis `UPDATE SET` 11 colonnes `+ doc_json … IF tx_id = ?` | **[M]** ; réécrire la phrase qui renvoie à §6 |
| A4 | Étape 4 « Maintain the indexes covering the fields that changed » (§3, Fig. 1 SVG) | non marqué | **CONTRADICTED** — l'UPDATE réécrit toutes les colonnes dérivées ; variante B : p50 12,1 → 90,8 ms (**×7,50**) pour 1 → 17 champs indexés **non touchés**, lecture ×1,56, charge HTTP constante | reformuler + **[M]** |
| A5a | Écritures Data API à `LOCAL_QUORUM` (Fig. 1 : « not established ») | [U] | **SUPPORTED** — 70/70 instructions sur la table à `LOCAL_QUORUM` | **[M]** |
| A5b | Niveau sériel (§3 : `LOCAL_SERIAL` retiré des brouillons) | [U] | **SUPPORTED** — `LOCAL_SERIAL` sur les 30 instructions conditionnelles (`INSERT … IF NOT EXISTS`, `UPDATE … IF tx_id = ?`, `DELETE … IF tx_id = ?`) | **[M]** ; RF = 1 : le **nom** est établi, pas le coût multi-réplicas |
| F | « searchable as soon as it is written » (§4, citation JVector) | [D] | Harness : **INCONCLUSIVE** (p99 chargé 59,2 / 53,8 ms ≥ seuil 50 ms). À vide : **40/40 trouvés au 1er `find_one`** ; intervalle = insert p50 9,8 + find p50 11,2 ms. Mesure SAI scalaire, **pas JVector** | [D] inchangé ; l'expérience ne le touche pas |
| L | « ten indexes are required per collection » (§2.1, [D] amont) | [D] | Nuance : 10 = budget vérifié à la création ; **9 créés** sur cette collection sans option vecteur | [D] + nuance |
| P | « the measurement in section 6 answers empirically … in a quarter of an hour » (§3) | — | **Contredit comme renvoi** : §6.3 mesure la fraîcheur, pas le cycle ; ici c'est la trace, non la courbe, qui a tranché | corriger |

Chiffres de latence (p50, ms, n = 30 par taille, après 5 échauffements) — variante A, `update_one` `$set` d'un champ / `find_one` par `_id` :

| Taille | update p1 | update p2 | lecture p1 | lecture p2 | fil `updateOne` req/rép | fil `findOne` rép |
|---|---|---|---|---|---|---|
| 1 Ko | 11,47 | 10,58 | 7,30 | 6,25 | 122 / 47 o | 1 135 o |
| 8 Ko | 13,41 | 12,62 | 9,91 | 7,07 | 122 / 47 o | 8 303 o |
| 32 Ko | 14,85 | 12,63 | 10,70 | 7,05 | 123 / 47 o | 32 880 o |
| 128 Ko | 22,07 | 23,41 | 13,58 | 12,15 | 124 / 47 o | 131 185 o |
| **croissance** | **×1,92** | **×2,21** | **×1,86** | **×1,94** | constante | ×115 |

Ce que la règle de contrôle ne capture pas, et que je signale sans en tirer de verdict : la charge HTTP d'`updateOne` est constante (122–124 / 47 octets) à toutes les tailles, donc la croissance de l'update **ne peut pas être** du transfert HTTP ; celle de la lecture inclut une réponse de 1,1 → 131 Ko. En pente absolue, update = 0,083 / 0,101 ms·Ko⁻¹ contre lecture 0,049 / 0,046. La courbe seule ne sépare pas « une lecture complète » de « lecture + réécriture » ; la trace le fait.

Fraîcheur (harness, ms) : passe 1 — à vide n = 40 : p50 25,5 · p99 78,4 · max 100,9 ; sous charge n = 120 : p50 42,5 · p99 59,2 · max 60,9. Passe 2 — à vide p50 18,7 · p99 54,5 ; sous charge p50 42,3 · p99 53,8 · max 55,6. Le p50 sous charge vaut 1,7–2,3× le p50 à vide ; le p99 ne se dégrade pas.

## 3. Correctifs — texte visible, cité verbatim depuis le HTML

Les mesures sont désignées M1 (colonnes), M2 (trace du cycle), M3 (variante B), M4 (niveaux de cohérence) ; les entrées d'annexe correspondantes sont proposées en §3.9.

**3.1 — §2.1, paragraphe [U] des noms de colonnes.** Remplacer :
> They should not be treated as an interface. Schedule them for verification against the build you deploy, not against this article.

par :
> They should not be treated as an interface. On HCD 2.0.6 with Data API v1.0.33 (appendix, measurement M1) all nine appear under exactly these names, alongside three that the practitioner literature omits: `key`, the typed partition key; `tx_id`, a timeuuid that guards every conditional write; and `query_lexical_value`, the lexical column. Nine storage-attached indexes were created on that collection, which declared no vector option. That is one build's answer, not an interface; verify against the build you deploy.

Marqueur du paragraphe : [U] → [M].

**3.2 — §3, paragraphe [U] du cycle.** Remplacer la dernière phrase :
> Pace that 2020 statement, which concerns a different API generation and cannot settle the question either way: whether the current shredding implementation reintroduces the cycle, or avoids it by some mechanism not publicly described, is precisely the kind of question the measurement in section 6 answers empirically for your build in a quarter of an hour.

par :
> Pace that 2020 statement, which concerns a different API generation and cannot settle the question either way. What settles it, for a build you control, is a query trace rather than a latency curve. On HCD 2.0.6 with Data API v1.0.33, with tracing enabled on the node, every `updateOne` carrying a single `$set` produced two CQL statements: a `SELECT` of `key`, `tx_id` and `doc_json` by key, then one `UPDATE` rewriting every derived column and the whole `doc_json`, guarded by `IF tx_id = ?` (appendix, measurement M2). The cycle is present on that build. A cost-versus-size probe on the same build grew in step with a same-size read and could not, on its own, separate a read from a read-plus-rewrite; it is the trace, not the curve, that carries the claim.

Marqueur du paragraphe : [U] → [M].

**3.3 — §3, liste numérotée, étape 4.** Remplacer :
> Maintain the indexes covering the fields that changed.

par :
> Maintain the indexes — on the build measured here, over every indexed field of the document, not only the fields that changed (appendix, measurement M3).

**3.4 — §3, paragraphe [D] de l'étape 5.** Remplacer :
> The serial consistency level at which this executes in the Data API is [U] not established by any source I consulted; earlier drafts of this article asserted LOCAL_SERIAL, and I have removed the claim rather than defend it from memory.

par :
> The consistency levels at which this executes in the Data API are [M] not published by any source I consulted; measured on HCD 2.0.6 with Data API v1.0.33, every statement on the collection ran at `LOCAL_QUORUM` and every conditional statement carried `LOCAL_SERIAL` as its serial level (appendix, measurement M4). Earlier drafts asserted `LOCAL_SERIAL` from memory; it is restored here on the strength of a trace, on one node with RF = 1 — the name is established, the multi-replica cost is not.

**3.5 — Légende de la figure 1 (HTML, hors SVG).** Remplacer :
> Column names are reported rather than documented; consistency levels are deliberately left unstated, since no source of acceptable rank established them.

par :
> Column names and consistency levels are not documented by the vendor; both were measured on one build (appendix, measurements M1 and M4), and the boxes should be read as observations of that build, not as a contract.

**3.6 — Légende de la figure 5.** Remplacer :
> Structural, not documented: the placement of steps 1–3 in the storage stratum, which inherits the [U] marking of section 3.

par :
> Measured, not documented: the placement of steps 1–3 in the storage stratum, observed by query trace on one build (appendix, measurement M2) and inheriting the [M] marking of section 3.

**3.7 — « Limitations of this article », premier paragraphe en gras.** Remplacer :
> Several of these are almost certainly true. None is asserted here as documented.

par :
> The first three were subsequently measured on one build — HCD 2.0.6 with Data API v1.0.33, one node, RF = 1 — and hold there (appendix, measurements M1–M4); they carry the [M] marker, which is weaker than [D]: an observation of a build is not a vendor's commitment. The fourth remains unverified. None is asserted here as documented.

**3.8 — Ajouts (pas des remplacements).**
- *Légende épistémique* : une entrée « **[M] Measured.** Observed on a named build under stated conditions, by a harness reproduced in the appendix. Stronger than [U], weaker than [D]: it establishes what one build did on one day, not what the vendor commits to. » — sans elle, aucun des trois marqueurs ne peut porter une mesure, et les affirmations mesurées devraient rester [U].
- *§2.1, après « five collections before exhaustion, on the upstream defaults. »* : « (That figure is the budget the API checks at creation; the collection measured in the appendix, created without a vector option, received nine.) »
- *Disclosure* : « **First**, no benchmark figures appear anywhere above » devient faux si un seul chiffre de l'annexe remonte dans le corps. Soit les chiffres restent confinés à l'annexe M1–M4 avec leurs conditions, soit la phrase devient « no benchmark figures appear in the body of this article; the appendix reports one build's measurements with their conditions ».

**3.9 — Entrées d'annexe proposées (M1–M4).** Chacune : produit et version lus depuis le nœud, 1 nœud RF = 1, VM 80 vCPU / 220 Gio, conteneur 3 Gio, memtable-résident, `commitlog_sync periodic 10 s`, harness `verify_storage_claims.py` v1.0 + 2 correctifs mécaniques, 17 septembre 2026 ; M1 : 12 colonnes, 9 index SAI ; M2 : séquence SELECT→UPDATE IF, 10/10 ; M3 : ×7,50 vs lecture ×1,56, charge HTTP constante ; M4 : 70/70 `LOCAL_QUORUM`, 30/30 `LOCAL_SERIAL`. `findings.json` contient tout.

## 4. Valeurs portées par des figures SVG — à votre charge, aucun patch produit

- **Figure 1, boîte « DATA API TIER »** : `consistency levels: not established` / `by any source consulted here` / `verify against your own build` → mesurés M4.
- **Figure 1, boîte « STORAGE — ONE ROW »** : `column names: reported, not documented` → mesurés M1 ; la boîte omet `key`, `tx_id`, `query_lexical_value`.
- **Figure 1, étape 4** : `maintain the indexes covering mutated paths` → contredit (M3).
- **Figure 1, boîte « DATA API TIER »** : `shred → N CQL statements` — mesuré : N = 1 pour `insertOne`, 2 pour `updateOne`, 2 pour `deleteOne`. Information, pas contradiction.
- **Figure 5** : `document fetched, changed in memory` et `whole document + derived columns` sont confirmés par M2 ; seule la légende HTML change (3.6).

## 5. Ce que cette expérience n'établit pas

- **Aucun coût multi-réplicas.** 1 nœud, RF = 1 : `LOCAL_QUORUM` et `LOCAL_SERIAL` sont satisfaits par un seul réplica. Le nom des niveaux est établi ; le prix d'un quorum ou d'un tour Paxos entre réplicas, non.
- **Aucun régime disque.** 0 SSTable flushée, aucune compaction traversée : toutes les latences sont des latences memtable/en cache. L'exigence « traverser les cycles de maintenance » n'est pas remplie ; la durée a suffi à tenir le débit, pas à croiser un flush.
- **Rien sur l'index vectoriel.** La sonde 2 exerce une égalité SAI sur un scalaire (`array_contains`), pas le graphe JVector cité en §4. La citation [D] reste [D] et n'est ni confirmée ni infirmée.
- **La latence d'index sous charge en dessous de ~40 ms.** L'intervalle mesuré est dominé par deux allers-retours HTTP ; le nombre de tentatives sous charge n'a pas été enregistré par le harness.
- **La séparation « une lecture » / « lecture + réécriture » par la latence seule.** La règle pré-déclarée s'applique ; c'est la trace qui établit le cycle. Un lecteur qui refuse la trace comme preuve doit tenir A3 pour INCONCLUSIVE.
- **La variance entre passes.** p50 update à 1 Ko : 19,6 ms (passe courte, collection froide), 11,5 (passe 1), 10,6 (passe 2). n = 30 par taille est petit ; les verdicts n'ont pas changé entre passes, les chiffres ont bougé de ±10 %.
- **Le confondant « niveau Data API ».** Une instance stateless unique, sans limite CPU, à 2 Gio ; le partage de la croissance entre parsing JSON côté API et stockage côté HCD n'a pas été mesuré.
- **Les défauts de configuration.** Les niveaux de cohérence observés sont ceux de data-api v1.0.33 ; s'ils sont configurables, cela n'a pas été vérifié.
- **Tout autre build.** Rien ici ne se transpose à Apache Cassandra 5.0.x/6.0, à une autre version HCD ou Data API, ni à MongoDB.
- **Tenue de dossier** : le JSON complet du contrôle en lecture de la passe 1 a été écrasé par la passe 2 (nom de fichier fixe) ; ses p50 et tailles de fil sont transcrits du journal et marqués comme tels dans `findings.json`.

## 6. État laissé sur le serveur

Keyspace `verif_stockage_20260917` conservé pour inspection (collection A : 12 000 documents de charge ; B : vide ; 18 index SAI sur 100). Tracing à 0,0 (vérifié). Aucun autre keyspace touché. À votre demande : `DROP KEYSPACE verif_stockage_20260917`.
