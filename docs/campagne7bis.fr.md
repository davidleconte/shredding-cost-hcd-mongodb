# Campagne 7bis — le réexamen des mesures d'agrégation

> **English abstract.** Campaign 7bis re-ran the aggregation axis (M20–M23) under a pre-registered
> protocol written *before* the data were seen, with five rules (R1–R5) each specifying in advance
> what result would count as a refutation. **Three fired.** The headline reversal is R2: this
> repository had narrowed `estimatedDocumentCount() = 0` to a cold-start artefact; the measurement
> shows the estimator returns **171 267 after flush and 172 132 after major compaction against a
> true 200 000** — wrong by ~14 % in steady state, on the same corpus where MongoDB's estimator
> returns 200 000 exactly. The narrowing was wrong and is withdrawn. R4 withdraws the 46.3× ingest
> ratio: at a batch size matched to the Data API's 100-document ceiling the gap is **6.9×**. R5
> bounds the 602×: it falls to **151×** at 100 000 groups, because MongoDB's cost scales with
> group cardinality and HCD's does not. Raw per-observation series are retained on both arms, so
> this is the first document in the repository to carry real confidence intervals.

**Ce que ce document corrige d'abord, ce sont mes propres écrits**, pas ceux de l'article. Deux
affirmations publiées ici sont fausses et sont retirées ci-dessous : la réduction de M22 à un
artefact de démarrage à froid (défi D9), et ma déclaration de protocole selon laquelle un balayage
de 134 secondes ne comporte pas de phase d'échauffement.

- **Date d'exécution** — bras MongoDB `2026-09-18T13:09:59Z`, bras HCD `2026-09-18T14:01:30Z`
- **Hôte** — `alphadebunker`
- **Sonde** — `probe_agg_7bis.py`, règles R1–R5 inscrites dans le fichier avant exécution
- **Corpus** — 200 000 documents, `cat = c{i%10}`, `ukey = u{i%100000}`,
  `amt = round(((i·2654435761) mod 10⁶)/1000, 3)`, `flag = (i%3 == 0)`
- **Preuves** — `findings_agg7bis_hcd.json`, `findings_agg7bis_mongodb.json`, séries brutes incluses

---

## R2 — réfutée. Et c'est ce dépôt qu'elle réfute.

Le défi **D9**, publié dans `challenges-campagne7.fr.md`, soutenait que le zéro de
`estimatedDocumentCount()` devait être ramené à sa condition mesurée — avant le premier flush — et
que ce que vaut l'estimation en régime permanent « n'a pas été mesuré ». D9 concluait que la mesure
qui le fermerait est triviale. Elle l'était. La voici.

| phase | `estimatedDocumentCount()` | vrai | écart |
|---|---:|---:|---:|
| avant flush | **0** | 200 000 | −100 % |
| après `nodetool flush` | **171 267** | 200 000 | **−14,4 %** |
| après compaction majeure | **172 132** | 200 000 | **−13,9 %** |
| MongoDB 8.0, même corpus | **200 000** | 200 000 | **0 %** |

L'estimation ne se répare pas. Elle passe de catastrophiquement fausse à durablement fausse.
**R2 n'est pas confirmée : elle est réfutée**, et dans la direction défavorable à la plateforme.
M22 était *sous*-évaluée par ce dépôt, pas sur-évaluée, et c'est mon propre défi qui l'a adoucie à
tort. La borne de D9 — « il concerne une fenêtre de temps, pas un état durable » — est retirée :
c'est un état durable.

La ligne de comparaison compte autant que les trois premières. Un estimateur fondé sur les
métadonnées de SSTable n'est pas *tenu* d'être approximatif : sur le même corpus, au même instant,
MongoDB rend le compte exact. L'écart n'est donc pas une propriété du genre « estimation », c'est une
propriété de cette implémentation.

`countDocuments` a refusé à **chaque** phase, y compris après compaction
(`TooManyDocumentsToCountException`). Le plafond documenté de 1 000 n'est pas relevé par un
changement de régime — ce qui est cohérent avec D8, et le confirme.

---

## R4 — déclenchée. Le 46,3× d'ingestion est retiré.

| bras | lots | durée | rapport à HCD |
|---|---:|---:|---:|
| HCD Data API | 100 (plafond produit) | **206,96 s** | — |
| MongoDB | 100 (apparié au plafond) | **29,85 s** | **6,9×** |
| MongoDB | 10 000 (natif) | **4,07 s** | 50,9× |

Le 46,3× publié en campagne 7 comparait le plafond d'appel de la Data API au lot natif de MongoDB.
À taille de lot appariée, le rapport tombe à **6,9×**. Les deux nombres sont vrais, mais ils ne
mesurent pas la même chose : **6,9× est le coût du moteur**, 50,9× est le coût du moteur multiplié
par une contrainte de protocole. Publier 46,3× sans dire lequel des deux on décrit est une
confusion, et c'est exactement ce que le défi D13 annonçait.

HCD à lots de 100 : 2 000 appels, **103,481 ms par appel**, 966,4 documents par seconde.

---

## R5 — déclenchée. Le 602× est borné à sa forme de requête.

Le coût de MongoDB dépend de la cardinalité du regroupement. Le coût de HCD, non : il est dominé par
le transport de 200 000 documents vers le client, quel que soit ce qu'on en fait ensuite.

| forme de requête | MongoDB p50 | HCD p50 | rapport | IC 95 % (bootstrap) | supports |
|---|---:|---:|---:|:---:|:---:|
| `$group` sur `cat` — 10 groupes | 227,539 ms | 132,897 s | **584×** | [577 ; 592] | disjoints |
| `$group` sur `ukey` — 100 000 groupes | 878,206 ms | 132,897 s | **151×** | [148 ; 153] | disjoints |
| filtre `flag` puis `$group` — 10 groupes | 218,395 ms | 132,897 s | **609×** | [599 ; 617] | disjoints |

Mann-Whitney : z = −4,58 dans les trois cas — la valeur plancher pour n₁ = 30 et n₂ = 14, les
supports étant entièrement disjoints. Les trois formes rendent le résultat correct des deux côtés
(10 / 100 000 / 10 lignes, sommes vérifiées contre la vérité terrain calculée en Python).

Le rapport est **divisé par 3,9** entre dix groupes et cent mille. Écrire « 602× » sans dire
« à dix groupes » est une extrapolation depuis la forme de requête la plus favorable. La direction
tient partout — 151× reste un écart de deux ordres de grandeur — mais l'amplitude est une propriété
de la requête choisie, pas du moteur seul.

**Les index de MongoDB ne changent rien**, ce qui clôt D10 dans l'autre sens aussi : avec
`cat_idx` + `ukey_idx` + `flag_idx` présents, les mêmes trois formes coûtent 234,977 / 901,552 /
186,284 ms. Un index sur la clé de regroupement ne sert pas un `$sum` sur un autre champ.

---

## R1 — non déclenchée, mais elle me prend en défaut

R1 demandait si `n = 3` sur le bras HCD était représentatif ; le seuil de déclenchement était un
écart de plus de ±20 % à `n = 15`.

| | p50 | σ |
|---|---:|---:|
| campagne 7, n = 3 | 133 984,229 ms | 567,7 ms |
| campagne 7bis, n = 15 | **132 985,311 ms** | 3 618,681 ms |
| campagne 7bis, n = 14 (sans le premier balayage) | 132 896,7 ms | 835,1 ms |

Écart **−0,7 %**. R1 n'est pas déclenchée : le `n = 3` d'origine était représentatif, et le défi D6
avait raison de ne pas en faire un point de rupture.

**Mais ma déclaration de protocole était fausse.** J'avais écrit, pour justifier l'absence de rodage :
*« sur un balayage de 134 secondes, il n'y a pas de phase d'échauffement significative »*. Je ne
l'avais pas mesuré. La série dit le contraire :

```
147138,5 | 133877,9  131814,9  132321,8  133620,0  132379,2  133350,3  132162,2
           131753,5  133718,6  132808,2  134271,6  132604,3  132985,3  134286,2
```

Le premier balayage est à **+10,7 %** de la médiane des quatorze autres. L'écart-type tombe de
3 618,7 ms à 835,1 ms quand on le retire — c'est-à-dire que **presque toute la variance de la série
est ce seul point**. Il y avait bien une phase d'échauffement ; je l'ai niée sans l'avoir observée.

Les deux lectures sont publiées ci-dessus. La conclusion ne bouge pas (132 985 contre 132 897, soit
0,07 %), mais une justification de protocole fausse reste fausse même quand elle ne coûte rien, et
elle aurait pu coûter cher sur une mesure moins robuste.

---

## R3 — le régime de stockage ne change presque rien

| régime | n | p50 |
|---|---:|---:|
| cache (avant flush) | 14 | 132 896,7 ms |
| après flush + compaction majeure | 5 | **130 127,0 ms** — **−2,1 %** |

Série post-compaction : 130 669,6 · 131 128,3 · 129 465,4 · 130 127,0 · 129 039,9.

C'est la confirmation directe de la décomposition du défi D7. Si le coût du balayage était dominé
par la lecture du stockage, sortir du régime cache le dégraderait nettement. Il l'améliore de 2,1 %.
Le coût est le **transport** : 10 000 pages de 20 documents à 13,398 ms la page. La campagne 7
était en régime cache, comme le rapport le disait, et cette condition n'était pas ce qui portait le
résultat.

---

## Correction de comptage : l'anneau n'était pas au-dessus du garde-fou de deux, il est pile dessus

Avant 7bis, j'ai relevé « 102 index SAI par nœud contre un garde-fou à 100 ». Le relevé comptait les
lignes de la sortie `cqlsh` avec `grep -cE '^\s+\S+'`, ce qui **capture aussi la ligne d'en-tête**
`index_name`. Le vrai compte est de **101 lignes**, dont exactement **100 `StorageAttachedIndex`** ;
la 101ᵉ est `system.PaxosUncommittedIndex`, un index `CUSTOM` qui n'est pas un SAI et que le
garde-fou ne compte pas.

L'anneau est donc à **100/100** : exactement au plafond, et non deux au-dessus. Le mécanisme décrit
était juste — aucune collection nouvelle (9 SAI) ne peut naître sans libérer d'abord, ce qui a rendu
nécessaire la suppression temporaire des vingt index `supply_chain_hcd` — mais le nombre publié
était faux de deux, par une faute de comptage de ma part et non par un état du cluster.

---

## Ce que la campagne 7bis change dans le dépôt

| avant 7bis | après 7bis |
|---|---|
| D9 : le zéro de M22 est une propriété du démarrage à froid | **retiré** — l'estimation reste fausse de 14 % après flush et compaction |
| 46,3× d'écart d'ingestion | **retiré** — 6,9× à lot apparié ; 50,9× à lot natif, et il faut dire lequel |
| 602× d'écart d'agrégation | **borné** — 584× à 10 groupes, 151× à 100 000 ; direction inchangée |
| `n = 3` sur le bras HCD | **validé** à n = 15, écart −0,7 % |
| « pas de phase d'échauffement » (ma déclaration) | **retiré** — le premier balayage est à +10,7 % |
| « 102 SAI par nœud » (mon relevé) | **corrigé** — 100 SAI, pile au plafond |
| aucun intervalle de confiance sur l'axe agrégation | trois IC bootstrap, supports disjoints, z = −4,58 |

Ce qui ne bouge pas : il n'existe pas de pipeline d'agrégation côté serveur dans la Data API, le
balayage client est le seul chemin du modèle document, et l'écart reste d'au moins deux ordres de
grandeur sur les trois formes mesurées.

---

## Restauration de l'anneau

Effectuée et vérifiée après la campagne, comme à chaque fois :

- keyspace `cmp` supprimé — absent de `system_schema.indexes` et de `system_schema.keyspaces`
- vingt index `supply_chain_hcd` recréés depuis la capture prise avant leur suppression ;
  **les vingt noms sont identiques à la capture**, vérifiés un à un par `diff`
- total revenu à 101 lignes sur `node1`, `node2` et `node3` — la valeur d'avant la campagne
- instantanés purgés sur les six nœuds ; le seul présent était `dropped-1789740349405-agg7b`,
  créé par mon propre `DROP KEYSPACE` à 14:05:49, aucun instantané préexistant n'a été touché
- probabilité de tracing remise à `0.0` sur les six nœuds
- conteneurs de campagne retirés : `cmp-mongo1`, `cmp-mongo2`, `cmp-mongo3`, `p16-data-api` ;
  **`rh-data-api` n'a pas été touché** et reste `Up 13 days (healthy)`
- aucun volume orphelin ; six nœuds `UN`
