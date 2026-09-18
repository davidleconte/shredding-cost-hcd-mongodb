> **English abstract.** This campaign asked what it costs to aggregate — count, filtered count, and `GROUP BY cat` with `SUM(amt)` — over 200,000 documents (10 categories × 20,000, fields `cat` string and `amt` double) on one shared host, MongoDB 8.0.32 as a three-member replica set `rs0` at `w:majority`+`j:true` against HCD 2.0.6 with Data API v1.0.33 on keyspace `cmp` at `{dc1:3}`. The headline is not a latency race but a capability gap: the HCD Data API command allow-list contains exactly nineteen commands (`alterTable`, `countDocuments`, `createIndex`, `createTextIndex`, `createVectorIndex`, `deleteMany`, `deleteOne`, `estimatedDocumentCount`, `find`, `findAndRerank`, `findOne`, `findOneAndDelete`, `findOneAndReplace`, `findOneAndUpdate`, `insertMany`, `insertOne`, `listIndexes`, `updateMany`, `updateOne`), and `aggregate`, `$group` and `distinct` all return `COMMAND_UNKNOWN` — there is no server-side aggregation pipeline (M20). Exact counting is capped: `countDocuments({})` and `countDocuments({cat:"c3"})` both failed with `TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the server`, on a stock container carrying no count-limit environment variable (M21); `estimatedDocumentCount()` answered in p50 6.875 ms but returned **0** while the true count was 200,000, because it is an SSTable-metadata estimate and reads zero before the memtable is flushed — pre-flush it is not approximate, it is wrong (M22). On the group-by axis every arm was verified exact against precomputed ground truth, and the medians were: MongoDB server-side `$group` p50 222.711 ms; native CQL per-partition sweep of ten queries p50 2011.399 ms; native CQL cross-partition `GROUP BY cat` p50 2568.372 ms; HCD Data API client scan-and-aggregate p50 133984.229 ms, pulling all 200,000 documents to the client (M23). That gives MongoDB / HCD-Data-API = 602×, MongoDB / CQL-best = 9.0×, CQL-best / HCD-Data-API = 66.6×, and the 602× must never be quoted as "HCD is 602× slower": the same storage engine aggregates the same corpus in about two seconds through native CQL, so the 134 seconds belong to the Data API tier, which exposes no aggregation surface and therefore forces the whole collection through the client — **and** the CQL arm is a labelled apples-to-oranges reference, because reaching it means abandoning the document model and pre-designing a table partitioned by the group key, which is exactly the index-design work the Data API's pitch is to avoid. Scope limits that travel with every number here: one shared, already-loaded host (`alphadebunker`, Intel Xeon Gold 6148, load carried from other tenants), one build of each engine, a single sequential closed-loop client, no concurrency; the HCD scan arm has **n = 3** repetitions, so its p95/p99 carry no information; and M22 is itself direct evidence that the HCD corpus was still memtable-resident at measurement time, so this is a cache regime and not a proven disk regime. Load times for the same 200,000 rows were MongoDB 4.0 s, native CQL 68.9 s, HCD Data API 185.3 s.
>
> *Report body below is in French. Raw evidence: `data/raw/findings_agg_hcd.json`, `data/raw/findings_agg_mongodb.json`, `data/raw/findings_agg_cqlref.json`. Probes: `probes/probe_aggregation.py`, `probes/agg_cql_arm.py`.*

---

# Campagne 7 — l'agrégation : compter et grouper — 18 septembre 2026

## Résultat (première phrase, sans compensation)

**Sur l'axe de l'agrégation, la Data API de HCD n'a pas de fonction à mesurer : `aggregate`, `$group` et `distinct` répondent `COMMAND_UNKNOWN`, et `countDocuments` refuse de compter au-delà de 1 000 documents — le seul chemin restant, tirer les 200 000 documents chez le client et sommer en code applicatif, met p50 133 984,229 ms contre 222,711 ms pour le `$group` côté serveur de MongoDB, soit 602×.** Et il faut le dire dans la même phrase, sinon le 602× est un mensonge par cadrage : **le moteur de stockage, lui, sait agréger** — la même somme sur le même corpus se fait en p50 2 011,399 ms en CQL natif, donc 66,6× plus vite que la Data API. Le retard appartient au **niveau** Data API, pas au moteur. Et la sortie CQL n'est pas gratuite non plus : elle exige d'abandonner le modèle document et de pré-concevoir une table partitionnée par la clé de groupe — c'est-à-dire exactement le travail de conception d'index dont l'argumentaire de la Data API promet de dispenser.

## Le tableau

Corpus : 200 000 documents, 10 catégories × 20 000, champs `cat` (texte) et `amt` (double). Même hôte (`alphadebunker`, Intel Xeon Gold 6148 @ 2,40 GHz), même session (relevés à 09:09:39, 09:29:31 et 09:33:35 UTC). MongoDB 8.0.32, replica set `rs0` à 3 membres, `w:majority` + `j:true`. HCD 2.0.6, keyspace `cmp`, RF = 3 `dc1`, neuf index SAI automatiques (`cat` couvert par `query_text_values`). Bras CQL : `cmp.agg_cql(cat, id, amt)` `PK(cat, id)`, RF = 3, lectures `LOCAL_QUORUM`. Percentiles seuls, aucune moyenne.

### Axe A/B — compter

| Bras | p50 | p95 | p99 | n | Résultat rendu | Exact ? |
|---|---|---|---|---|---|---|
| **MongoDB** `count_documents({})` | **115,009 ms** | 125,282 | 127,694 | 30 | 200 000 | **oui** |
| **MongoDB** `estimated_document_count()` | **0,408 ms** | 0,695 | 0,755 | 30 | 200 000 | oui (ici) |
| **MongoDB** `count({cat:"c3"})`, sans index (collscan) | **157,177 ms** | 197,138 | 208,394 | 30 | 20 000 | **oui** |
| **MongoDB** `count({cat:"c3"})`, avec index `cat_idx` | **12,659 ms** | 15,488 | 15,630 | 30 | 20 000 | **oui** |
| **HCD** `countDocuments({})` | — | — | — | — | **IMPOSSIBLE** | — |
| **HCD** `countDocuments({cat:"c3"})` | — | — | — | — | **IMPOSSIBLE** | — |
| **HCD** `estimatedDocumentCount()` | **6,875 ms** | 8,899 | 10,152 | 30 | **0** (vrai : 200 000) | **non** |

Les deux `countDocuments` de HCD ont échoué sur la même exception, capturée telle quelle dans `findings_agg_hcd.json` :

> `TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the server`

Le plafond est le **défaut d'usine** : d'après le rapport de campagne, le conteneur Data API ne porte aucune variable d'environnement de limite de comptage. La sonde avait pourtant demandé `upper_bound = 400 000` (`max(n*2, 1000)` dans `probe_aggregation.py`) ; le serveur l'ignore et applique son propre plafond.

### Axe C — `GROUP BY cat`, `SUM(amt)`, 10 groupes

Les quatre bras ont été vérifiés **exacts** contre une vérité terrain précalculée (10 × 20 000 lignes, somme générale 99 998 900,0 ; `C1_correct`, `C2_correct`, `C3a_correct`, `C3b_correct` tous à `true`).

| Bras | p50 | p95 | p99 | n | Ce que c'est |
|---|---|---|---|---|---|
| **MongoDB `$group` côté serveur** | **222,711 ms** | 252,075 | 285,402 | 15 | pipeline d'agrégation natif, 10 lignes rendues |
| **CQL natif — balayage par partition (10 requêtes)** | **2 011,399 ms** | 2 223,488 | 2 421,508 | 15 | *référence apples-to-oranges* (voir ci-dessous) |
| **CQL natif — `GROUP BY cat` inter-partitions** | **2 568,372 ms** | 2 703,698 | 2 728,623 | 15 | balayage complet côté coordinateur (**anti-patron**) |
| **HCD Data API — scan et agrégation chez le client** | **133 984,229 ms** | *134 990,509* | *135 079,956* | **3** | 200 000 documents tirés chez le client ; **seul chemin existant** dans le modèle document |

Les p95/p99 du bras HCD sont en italique parce qu'ils sont **dénués de sens** : n = 3 (`max(reps//10, 3)` dans la sonde). Min 133 827,164 ms, max 135 102,317 ms — l'écart total observé est de 1,3 s sur 134 s, mais trois points ne fondent pas une distribution.

### Ratios, avec leur qualification attachée

| Ratio | Valeur | Ce qu'il mesure vraiment |
|---|---|---|
| MongoDB / HCD-Data-API | **602×** | pipeline côté serveur **contre absence de pipeline** — un écart de *capacité*, pas de vitesse moteur |
| MongoDB / CQL-best | **9,0×** | deux moteurs qui agrègent réellement côté serveur, sur deux modèles de données différents |
| CQL-best / HCD-Data-API | **66,6×** | le **coût du niveau** Data API sur ce même moteur de stockage |

### Chargement des mêmes 200 000 lignes

| Bras | Temps de chargement |
|---|---|
| MongoDB | **4,0 s** |
| CQL natif | **68,9 s** |
| HCD Data API | **185,3 s** |

## Lecture des axes

**A — compter exactement : HCD ne le fait pas, MongoDB le fait cher. [M] M21.** `countDocuments` est bien dans la liste des dix-neuf commandes autorisées, mais il refuse au-delà de 1 000 documents sur ce build en configuration d'usine. Il n'y a donc **aucun** moyen, dans le modèle document de la Data API, d'obtenir le cardinal exact d'une collection de 200 000 documents. Le contrepoint qui doit accompagner ce constat, parce qu'il est défavorable à MongoDB : le comptage exact de MongoDB **n'est pas bon marché non plus** — `count_documents({})` coûte p50 115,009 ms parce que c'est un balayage, et le comptage filtré sans index coûte p50 157,177 ms. MongoDB gagne cet axe parce qu'il **répond**, pas parce qu'il répond vite. Et il ne descend à 12,659 ms qu'après **déclaration d'un index** (`cat_idx`, créé après la mesure par défaut) — donc lui aussi paie la conception d'index sur cet axe.

**A′ — l'estimation de HCD n'est pas approximative, elle est fausse. [M] M22.** `estimatedDocumentCount()` a répondu en p50 6,875 ms et a rendu **0** alors que la collection contenait 200 000 documents. C'est une lecture des métadonnées de SSTables : avant flush de la memtable, il n'y a rien dans les métadonnées, donc l'estimation est nulle. Le mot « estimé » suggère une marge d'erreur ; ici il n'y a pas de marge, il y a une réponse fausse, et rien dans l'API ne signale la condition. Un applicatif qui teste `if count == 0` sur une collection fraîchement chargée conclut que la collection est vide. À titre de comparaison, `estimated_document_count()` de MongoDB, qui lit aussi des métadonnées, a rendu 200 000 exactement en p50 0,408 ms sur ce corpus — ce qui ne prouve pas qu'il soit toujours juste, seulement qu'il l'était ici. **Corollaire méthodologique, et il joue contre l'auteur** : ce zéro est la preuve directe que le corpus HCD était encore en memtable au moment de la mesure. Toute cette campagne est donc en **régime cache**, non en régime disque prouvé — la même réserve que celle qui entache le taux par kio des campagnes 1, 3 et 5.

**B — l'absence de pipeline est le résultat, pas la latence. [M] M20.** La liste d'autorisation des commandes de la Data API contient exactement dix-neuf entrées (`alterTable`, `countDocuments`, `createIndex`, `createTextIndex`, `createVectorIndex`, `deleteMany`, `deleteOne`, `estimatedDocumentCount`, `find`, `findAndRerank`, `findOne`, `findOneAndDelete`, `findOneAndReplace`, `findOneAndUpdate`, `insertMany`, `insertOne`, `listIndexes`, `updateMany`, `updateOne`). `aggregate`, `$group` et `distinct` répondent `COMMAND_UNKNOWN`. Il n'existe donc **aucune** manière de faire calculer une somme par groupe au serveur. Le seul chemin est celui qu'a emprunté la sonde : `find({}, projection={cat, amt})` paginé, et la somme en code applicatif. D'après le rapport de campagne, la pagination par défaut rend 20 documents par page, soit de l'ordre de 10 000 allers-retours HTTP pour un seul balayage. La campagne 6 a mesuré le coût d'un aller-retour Data API à p50 10,4 ms sur une lecture ponctuelle (M16) ; **la décomposition du 134 s en un terme « allers-retours » et un terme « moteur » n'a pas été mesurée dans cette campagne**, et je ne la calcule pas ici — je constate seulement que le nombre d'allers-retours est la variable qui distingue ce bras de tous les autres.

**C — le 602× et sa réfutation, dans la même phrase. [M] M23.** MongoDB agrège 200 000 documents en 10 groupes en p50 222,711 ms côté serveur. La Data API de HCD met p50 133 984,229 ms pour le même résultat exact — 602×. **Ce chiffre ne dit pas que le moteur de stockage de HCD est 602× plus lent :** le même moteur, sur la même machine, sur le même corpus, fait la même agrégation en p50 2 011,399 ms en CQL natif (9,0× MongoDB) et en p50 2 568,372 ms en `GROUP BY` inter-partitions (un anti-patron reconnu : balayage complet côté coordinateur, qui reste ici en dessous de trois secondes). L'écart de 66,6× entre le CQL natif et la Data API est le **coût d'un niveau qui n'expose pas la fonction** et contraint donc à traverser le réseau avec la collection entière. C'est une lacune d'API, pas une limite dure du moteur.

**C′ — et la sortie CQL n'est pas une réponse pour le modèle document.** Le bras CQL porte dans son propre fichier de résultats l'étiquette qui le disqualifie comme comparaison : *« APPLES-TO-ORANGES REFERENCE — native CQL, NOT the HCD document model / Data API. Requires abandoning the document model and pre-designing a table partitioned by the group key. »* La table `agg_cql(cat, id, amt)` avec `PK(cat, id)` a été **conçue pour cette requête** : dix partitions, une par catégorie. C'est exactement la conception de schéma que l'argumentaire « queryabilité sans conception d'index » du §4 — vérifié favorablement en campagne 6 sur la recherche filtrée — promet d'éviter. Les deux moitiés de ce constat doivent voyager ensemble : **le moteur sait agréger, et y accéder coûte le modèle document.**

**Une asymétrie de chargement qu'il faut noter sans la surinterpréter.** Les mêmes 200 000 lignes ont mis 4,0 s côté MongoDB, 68,9 s en CQL natif et 185,3 s à travers la Data API. Ces trois chiffres ne sont pas des mesures instrumentées de débit d'écriture (pas de percentiles, un seul relevé chacun, client séquentiel, durabilités différentes selon les chemins) : ils sont rapportés parce qu'ils figurent dans les trois fichiers de résultats et parce qu'ils vont dans le même sens que M13 (campagne 5), pas parce qu'ils constituent une mesure du chemin d'écriture.

## Ce que cette campagne établit, et ce qu'elle n'établit pas

**Établit.**
1. **[M] M20 — il n'y a pas d'agrégation côté serveur dans la Data API de HCD 2.0.6 / v1.0.33.** `aggregate`, `$group`, `distinct` = `COMMAND_UNKNOWN`, liste d'autorisation à dix-neuf commandes. C'est un fait structurel, indépendant du matériel, de la charge et du régime ; il ne dépend d'aucun percentile et survit à tous les challenges de méthode du dossier.
2. **[M] M21 — le comptage exact est plafonné à 1 000 documents** sur un conteneur d'usine, filtré comme non filtré, malgré un `upper_bound` client de 400 000.
3. **[M] M22 — `estimatedDocumentCount()` rend 0 avant flush** alors que la collection en contient 200 000. Faux, pas approximatif.
4. **[M] M23 — l'agrégation par la seule voie disponible coûte p50 133 984,229 ms** contre 222,711 ms pour MongoDB (602×), **et** p50 2 011,399 ms pour le même moteur en CQL natif (66,6× entre les deux chemins HCD). Les quatre bras sont exacts contre la vérité terrain.
5. La lacune comblée : le dossier déclarait depuis la campagne 5 que « rien de l'agrégation » n'était mesuré (campagnes 5 et 6, section « n'établit pas »). Cette case est désormais remplie — et c'est l'axe le plus défavorable à HCD de tout le dossier.

**N'établit pas.**
1. **Rien sur un régime disque.** M22 prouve le contraire : la memtable HCD n'avait pas été vidée. Aucun flush forcé, aucune compaction traversée.
2. **Rien sur la concurrence.** Client unique, séquentiel, boucle fermée — la violation n° 1 de la norme en six points que le diptyque impose aux autres (§10), déjà relevée par l'audit adverse.
3. **Aucune décomposition du 134 s.** La part des ~10 000 allers-retours HTTP, celle de la désérialisation client et celle du moteur n'ont pas été séparées. Le 66,6× localise le coût dans le niveau ; il ne le ventile pas.
4. **Une distribution pour le bras HCD.** n = 3. Le p50 est une médiane de trois points ; les p95/p99 du tableau ne doivent pas être cités.
5. **Rien sur une Data API dimensionnée.** Conteneur unique co-localisé, comme en campagne 4 — l'absolu ne se transpose pas à un niveau dimensionné pour la production, même si la **lacune de capacité** (M20), elle, s'y transpose intégralement.
6. **Rien sur les agrégations que HCD pourrait servir autrement** : `findAndRerank`, les index vectoriels, ou une pile analytique externe (Presto, Spark) branchée sur le même anneau. Le constat porte sur la Data API telle qu'exposée, pas sur toutes les manières d'interroger HCD.
7. **Rien de généralisable à une autre version.** Une liste d'autorisation est une décision de produit ; elle peut changer d'un build à l'autre. Le chiffre qui résiste au temps est le mécanisme (« pas de pipeline ⇒ le corpus traverse le client »), pas la liste.
8. **L'hôte reste partagé et chargé** (`system.paxos` ~13 Gio/nœud `dc1` en reliquat des campagnes 3-4, charge tierce). Les absolus HCD sont un plafond bruité, jamais une mesure propre — réserve I1/I6 de l'audit adverse, valable ici comme ailleurs.

## État de l'anneau

Keyspace `cmp` supprimé. Les 20 index SAI de `supply_chain_hcd` recréés verbatim. Les 3 conteneurs MongoDB retirés. Le conteneur Data API de la campagne retiré. Snapshots purgés et tracing remis à 0 sur les six nœuds. Reliquat inchangé : `system.paxos` ~13 Gio/nœud `dc1`.
