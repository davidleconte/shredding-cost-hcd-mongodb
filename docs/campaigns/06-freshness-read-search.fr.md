> **English abstract.** This campaign asked whether the three axes the article claims for HCD — index freshness, point reads, and filtered search — actually favour HCD when both engines are deployed on one shared host, at 1 M documents, with a 3-member MongoDB replica set (`w:majority`) against an HCD ring at `{dc1:3}`, matched resources and a cache-resident regime. Two of the three did not: point read by `_id` went to MongoDB (p50 0.53 ms wildcard / 0.62 ms default against HCD 10.4 ms, the Data API tier hop), and freshness on an ordinary secondary index was a tie, both engines returning the just-written document on the first query (40/40 on each arm). Filtered search on an undeclared field split in two: HCD's automatic SAI answered at p50 17.4 ms against a 376.7 ms collection scan on default MongoDB (21.7×), but MongoDB with a wildcard index answered at p50 0.73 ms — 23.7× faster than HCD — so what HCD buys is the dispensation from index design, not speed. The addendum then deployed `mongot` (mongodb-atlas-local 8.3.11) and the search-freshness axis went decisively to HCD: searchable on the first query (poll attempts median 1, p50 45.0 ms, HTTP-round-trip-bound) against MongoDB `$search` at a median 34 poll attempts and p50 1015.2 ms. **That 1015 ms must never be quoted on its own**: the author's own follow-up (M18, `findings_mongot_floor.json`) established that the lag is a Lucene-style refresh interval — de-synchronised p50 664.3 ms, floor 89.1 ms, max 1170.2 ms — so the first figure was the worst phase of a periodic cycle, overstated by a self-synchronised probe, and the turn-latency sweep (M19) showed MongoDB's miss rate falling to 0 % once the write-to-search gap reaches 1000 ms, which makes HCD's edge total below one second (100 % vs 0 % miss at τ=0) and moot for conversational RAG. Everything here is one build on one shared, already-loaded host (`alphadebunker`), single-client and sequential, cache-resident, no concurrency and no multi-host topology; and the freshness half ran on a single-node `atlas-local`, not the 3-member replica set used for the read and search halves.
>
> *Report body below is in French. Raw evidence: `data/raw/findings_rs_hcd.json`, `data/raw/findings_rs_mongo.json`, `data/raw/findings_mongot_freshness.json`, `data/raw/findings_hcd_vec_freshness.json`, `data/raw/findings_mongot_floor.json`, `data/raw/findings_turn_hcd.json`, `data/raw/findings_turn_mongodb.json`.*

---

# Campagne 6 — les axes revendiqués pour HCD : fraîcheur, lecture, recherche — 18 septembre 2026

## Résultat (première phrase, sans compensation)

**Mesurés sur un déploiement ordinaire, les trois axes censés favoriser HCD ne le favorisent pas comme espéré : la fraîcheur est un match nul, la lecture ponctuelle revient à MongoDB (~20×), et la recherche filtrée est partagée — HCD bat MongoDB-par-défaut (22×) mais perd contre MongoDB-wildcard (24×).** Un seul avantage structurel de HCD s'est matérialisé — l'indexation automatique évite le scan de collection sur un champ non déclaré — et MongoDB l'égale dès qu'on lui déclare un index wildcard, tout en gardant l'avantage absolu.

## Le tableau (1 M documents, même hôte, régime cache apparié, MongoDB replica set 3 membres w:majority)

| Axe | mongo-default | mongo-wildcard | **HCD** | Qui gagne |
|---|---|---|---|---|
| **A. Recherche filtrée** (champ non déclaré) p50 | **376,7 ms** (scan) | 0,73 ms (index) | **17,4 ms** (SAI auto + niveau) | HCD ≫ default (**22×**), wildcard ≫ HCD (**24×**) |
| **B. Lecture ponctuelle** (`_id`) p50 | 0,62 ms | 0,53 ms | **10,4 ms** | **MongoDB (~20×)** — saut de niveau |
| **C. Fraîcheur** (index secondaire, visibilité 1ʳᵉ requête) | attempts=1 | attempts=1 | attempts=1 | **match nul** — les deux moteurs indexent en synchrone |

## Lecture des trois axes

**A — Recherche filtrée : le seul avantage HCD réel, et il est conditionnel.** Sur un champ non déclaré, MongoDB-par-défaut **scanne 1 M documents (377 ms)** ; HCD, qui indexe automatiquement tout champ (SAI), répond en **17 ms — 22× plus vite**. C'est la « queryabilité sans conception d'index » du §4, **vérifiée contre le MongoDB réellement déployé**. Mais MongoDB **peut** faire aussi bien : avec un index `$**`, il tombe à 0,73 ms — **24× plus vite que HCD**, car il n'a pas le saut de niveau HTTP. La paire est le résultat : HCD offre par défaut ce que MongoDB obtient en déclarant un wildcard, mais l'absolu de HCD reste plombé par son niveau.

**B — Lecture ponctuelle : MongoDB gagne, franchement.** Lire par `_id` : MongoDB 0,5–0,6 ms contre HCD 10,4 ms. Le saut de niveau Data API (HTTP + désérialisation) est un impôt de ~10 ms sur *chaque* lecture HCD que MongoDB ne paie pas. Cet axe n'est pas favorable à HCD.

**C — Fraîcheur : match nul, et l'avantage réel de HCD n'est pas mesurable ici.** Écrire puis interroger par un champ à index secondaire : les trois configurations trouvent le document **à la première requête** (attempts=1) — parité, parce que **le SAI de HCD et l'index b-tree de MongoDB sont tous deux synchrones**. L'avantage de fraîcheur que le §4 revendique pour HCD est ailleurs : son index **de recherche/vecteur (JVector) synchrone** contre le **mongot asynchrone** de MongoDB. **`mongot`/Atlas Search n'est pas déployable sur un replica set nu** (public preview, conçu pour Atlas) — donc **cet axe précis reste non mesuré**. Un match nul sur index ordinaire n'est pas une preuve contre la revendication de HCD ; c'est une parité sur un autre objet.

## Ce que cette campagne établit, et ce qu'elle n'établit pas

**Établit** : (1) l'indexation automatique de HCD est un avantage opérationnel **réel** contre le MongoDB par défaut — pas de scan sur un champ non déclaré (22× à 1 M docs) ; (2) MongoDB égale et dépasse cet avantage avec un index wildcard, et domine toute lecture par l'absence de niveau ; (3) sur index secondaire ordinaire, la fraîcheur est à parité.

**N'établit pas** : (1) **la fraîcheur de recherche/vecteur** — l'axe le plus tranchant du §4 pour HCD — faute de `mongot` déployable ; (2) rien de la **recherche vectorielle ANN** elle-même (M7 n'a pu que borner la fraîcheur vectorielle HCD sous le plancher HTTP) ; (3) rien de l'**agrégation** ; (4) le comportement à concurrence, multi-client, ou multi-hôte ; (5) un seul hôte, une build de chaque, régime cache. Le saut de niveau HCD (~10 ms) est un composant que MongoDB n'a pas dans ce dispositif — il pèse sur B et sur l'absolu de A.

## Synthèse des deux campagnes comparatives (5 et 6)

| Axe | Gagnant | Marge | Réserve |
|---|---|---|---|
| Mutation d'un champ (C5) | **MongoDB** | 40× moteur / 44× pile | taux memtable (C2) |
| Lecture ponctuelle (C6-B) | **MongoDB** | ~20× | saut de niveau HCD |
| Recherche, champ **déclaré/wildcard** (C6-A) | **MongoDB** | ~24× | saut de niveau HCD |
| Recherche, champ **non déclaré** (C6-A) | **HCD** | ~22× | MongoDB l'égale avec un wildcard |
| Fraîcheur, index **ordinaire** (C6-C) | **nul** | — | parité synchrone |
| Fraîcheur, **recherche/vecteur** (§4) | **non mesuré** | — | mongot non déployable |

**Net honnête : sur ce dispositif, MongoDB gagne la majorité des axes mesurés ; le seul avantage HCD confirmé est l'indexation automatique contre le MongoDB par défaut ; et l'axe où HCD est structurellement le plus fort — la fraîcheur de recherche synchrone — reste hors de portée de la mesure.**

## État de l'anneau
MongoDB démonté (3 conteneurs + réseau). Anneau HCD à l'identique : `cmp` supprimé, snapshots purgés (6 nœuds), 20 index `supply_chain_hcd` recréés (101 au total), Data API retirée, tracing 0.0. Reliquat inchangé : `system.paxos` ~13 Gio/nœud dc1.

---

## Addendum — fraîcheur de RECHERCHE, mongot déployé (18 septembre 2026)

Le déploiement `mongot` a réussi (image officielle `mongodb/mongodb-atlas-local`, MongoDB 8.3.11, Atlas Search fonctionnel — index READY, `$search` validé). L'axe le plus tranchant du §4 pour HCD est enfin mesurable, même hôte, même session.

**Résultat — HCD gagne cet axe, décisivement.**

| | Écriture → cherchable (p50) | Visible à la 1ʳᵉ requête ? |
|---|---|---|
| **HCD** (JVector, index sur le chemin d'écriture) | **~45 ms** (borné par l'aller-retour HTTP) | **oui — attempts médian = 1** |
| **MongoDB `$search`** (mongot, ingestion async par change stream) | **~1015 ms** | **non — médiane 34 tentatives** |
| MongoDB `find({_id})` (index ordinaire, synchrone) | 1,3 ms | oui |

**Un document tout juste écrit est invisible à `$search` de MongoDB pendant ~1 seconde**, alors qu'il est immédiatement trouvable par `_id`. HCD n'a pas cette fenêtre : son index de recherche est synchrone sur le chemin d'écriture (attempts=1). C'est **exactement la « propriété de correction » du §4.1** : un système RAG qui écrit un fait et le cherche au tour suivant le trouve immédiatement sur HCD, et le manque pendant ~1 s sur MongoDB `$search` — « une mauvaise réponse, pas une réponse lente ».

**Réserves déclarées.** (1) `mongot` a tourné en **replica set à un membre** (`atlas-local`), donc `w:majority` y est trivial — mais le lag async est une propriété par-déploiement de mongot, pas du nombre de réplicas, donc le ~1 s est représentatif. (2) HCD a ~45 ms d'aller-retour HTTP incompressible ; **son index n'a aucun lag** (attempts=1), le 45 ms est le plancher de mesure, pas un délai d'index. (3) HCD JVector (vecteur) contre MongoDB `$search` (texte) : deux chemins de recherche, mais la même architecture synchrone-vs-asynchrone est ce qui est mesuré. (4) le lag mongot dépend de la charge et de la configuration ; ~1 s est la valeur au repos sur ce déploiement.

## Bilan final des deux campagnes comparatives, corrigé

| Axe | Gagnant | Marge |
|---|---|---|
| Mutation d'un champ (C5) | MongoDB | 40× moteur |
| Lecture ponctuelle (C6-B) | MongoDB | ~20× |
| Recherche, champ déclaré/wildcard (C6-A) | MongoDB | ~24× |
| Recherche, champ non déclaré (C6-A) | HCD | ~22× |
| Fraîcheur, index ordinaire (C6-C) | nul | — |
| **Fraîcheur de RECHERCHE (C6 addendum)** | **HCD** | **synchrone vs ~1 s de lag async** |

**Net honnête et enfin complet : MongoDB domine la mutation et la lecture brute ; HCD domine la fraîcheur de recherche — l'axe pour lequel sa décomposition et son indexation sur le chemin d'écriture sont conçues, et l'axe que privilégient les charges RAG.** Aucun moteur ne gagne partout ; le choix dépend de l'axe, ce qui est précisément la thèse du diptyque.
