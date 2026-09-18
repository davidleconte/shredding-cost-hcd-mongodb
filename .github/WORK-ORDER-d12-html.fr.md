# Ordre de travail — mettre le diptyque et la synthèse à jour de trois rétractations (D12, D9, D7)

**Destinataire :** l'agent en charge de `docs/article/article-part1-what-a-mutation-costs.html`,
`docs/article/article-part2-when-the-index-is-current.html` et `docs/synthesis/huit-axes.fr.html`.
**Date :** 18 septembre 2026. **Auteur de l'ordre :** la session qui a établi le fait ci-dessous.
**État de la couche Markdown :** déjà corrigée et poussée. Ce document ne concerne que le HTML.

---

## 1. Le fait établi, avec ses preuves

Le défi **D12** (dans `docs/challenges-campagne7.fr.md`) retirait au chemin CQL natif la clause
« et de pré-concevoir une table partitionnée par la clé de groupe ». **Ce retrait est annulé.
La clause est réinstaurée.** D12 reposait sur une prémisse fausse.

**Ce que D12 affirmait :** « Le bras C3b mesure précisément le cas où la table n'est *pas* alignée
sur la requête », et son tableau étiquetait C3b « non aligné ». Il en tirait que l'écart
« entre table alignée et non alignée » est de ×1,28, non distinguable du bruit
(supports recouvrants, intervalle [0,966 ; 1,421] contenant 1,0), donc que la campagne facturait un
coût de conception non soutenu par sa propre mesure.

**Preuve 1 — il n'y a qu'une table.** `probes/agg_cql_arm.py` ne contient qu'un seul `CREATE TABLE` :

```
s.execute(f"CREATE TABLE {ks}.agg_cql (cat text, id text, amt double, PRIMARY KEY (cat, id))")
```

Les deux bras l'interrogent : C3a par dix `SELECT SUM(amt) … WHERE cat=?`, C3b par un
`SELECT cat, SUM(amt) … GROUP BY cat`. Le fichier de résultats l'enregistre au singulier —
`"table": "cmp.agg_cql(cat,id,amt) PK(cat,id), RF=3, reads LOCAL_QUORUM"` — et décrit C3b comme
`"cross-partition range scan (coordinator full-scan anti-pattern)"`, c'est-à-dire une propriété de
la **portée de la requête**, pas de la disposition de la table. Dans `data/derived/inference.json`,
les deux bras portent le même `source_file`. Le registre `docs/STATISTICS.md` nomme d'ailleurs la
comparaison correctement : `AGG-CQLsweep-vs-CQLgroupby` — *sweep contre group-by*.
**C3a et C3b diffèrent par la forme de requête, pas par le schéma.**

**Preuve 2 — mesurée sur l'anneau HCD 2.0.6 le 18 septembre 2026.** Sur une table
`PRIMARY KEY (cat, id)`, `SELECT cat, SUM(amt) FROM … GROUP BY cat` est accepté. Sur une table
`PRIMARY KEY (id)`, la **même** requête est refusée :

```
InvalidRequest: code=2200 [Invalid query]
message="Group by is currently only supported on the columns of the PRIMARY KEY, got cat"
```

`ALLOW FILTERING` ne change rien : même refus. **C3b n'est exprimable que parce que la table est
pré-partitionnée par la clé de groupe.** Le bras que D12 lisait comme la réfutation de l'exigence
en est la démonstration.

**Ce qui survit de D12 :** le ×1,28 **entre les deux formes de requête** n'est pas établi, et
`agg_cql` ne conserve pas ses observations une à une. Ces deux points restent vrais et publiables.

**Ce qui tombe :** le retrait de la clause, et toute formulation parlant d'un bras « désaligné »,
« non aligné » ou « unaligned ».

---

## 2. Ce qu'il faut changer — un seul endroit

### `docs/article/article-part1-what-a-mutation-costs.html`, ligne 601, §4.5

Le paragraphe marqué `<span class="ep ep-u">U</span>` se termine actuellement par :

> An earlier revision of this sentence added that it also means designing a table partitioned by the
> group key in advance. The data do not support that clause: the table designed for the query and a
> cross-partition `GROUP BY` against it differ by ×1.28 at the median, their supports overlap, and the
> interval of their ratio contains one.⁵² At this scale the partitioning choice does not separate from
> noise, and the penalty is withdrawn. What survives is the half that matters.

**C'est le seul retrait de la clause dans tout le corpus non-Markdown, et il est faux.** Remarquer
que la phrase concède déjà elle-même « a cross-partition `GROUP BY` **against it** » — contre la
table conçue pour la requête — puis raisonne comme si les deux nombres chiffraient deux conceptions.

Remplacement suggéré, à adapter au registre de l'article :

> Reaching it also means designing a table partitioned by the group key in advance. An earlier
> revision withdrew that clause, on the ground that the table designed for the query and a
> cross-partition `GROUP BY` **against that same table** differ by only ×1.28 at the median, with
> overlapping supports and a ratio interval containing one.⁵² The withdrawal was an error of object
> rather than of arithmetic: both figures come from one table, and what separates them is the shape
> of the query, not the design of the schema. Against a table not partitioned by the group key, that
> second query is not slower — it is refused by the engine. The clause stands.

Contraintes sur ce remplacement :
- le marqueur épistémique du paragraphe peut rester `U` pour le ×1,28, mais l'affirmation
  « refused by the engine » est **mesurée** — si la convention du diptyque l'exige, la marquer `M` ;
- l'appel de note `⁵²` doit être conservé : la note 52 documente l'analyse de séparation des
  supports, qui reste exacte et reste la source du ×1,28 et de son intervalle ;
- ne pas introduire de note nouvelle sans vérifier l'ancrage (voir §4).

---

## 3. Ce qu'il ne faut PAS changer — et qui avait raison

Ces passages affirment la clause. **Ils étaient corrects et le redeviennent formellement.**
Les laisser tels quels.

| Fichier | Ligne | Contenu | Statut |
|---|---|---|---|
| `article-part1` | 1180 | annexe M23, « *Not established: … since it requires a table partitioned by the group key in advance* » | **avait raison** — c'est la ligne que le retrait de la 601 contredisait |
| `article-part1` | 1178 | « native CQL over **a table** designed for the query », puis les deux routes | correct, et c'est la preuve 1 énoncée dans l'annexe |
| `article-part1` | 605 | la doctrine : données « stored partitioned, sorted, denormalised and filtered **in advance** » (note 53) | correct |
| `article-part1` | 1163 | « store pre-computed answers …, roughly a table per query » | correct |
| `article-part2` | 923 | ligne « Aggregating by group » du tableau à huit axes | **ne contient ni la clause ni son retrait** — rien à faire |
| `huit-axes.fr.html` | 158, 259-266 | « données stockées partitionnées … *à l'avance* », « ni l'une ni l'autre des deux voies mesurées », « une table d'agrégats maintenue à l'écriture » | corrects — la synthèse ne porte **aucun** retrait |

**Point important pour la cohérence :** l'article se contredisait. La ligne 601 retirait la clause ;
la ligne 1180, 579 lignes plus loin, l'utilisait comme motif vivant. Corriger la 601 supprime la
contradiction **sans toucher** à la 1180. La synthèse française, elle, n'a jamais porté le retrait :
elle redevient cohérente avec l'article sans être modifiée.

---

## 4. Contraintes de vérification

Après toute modification, faire passer :

```bash
python3 .github/scripts/check_article_refs.py docs/article/article-part1-what-a-mutation-costs.html docs/article/article-part2-when-the-index-is-current.html
```

Il doit rendre `clean — every reference resolves, numbering dense, tables agree`. Il vérifie en
particulier : chaque ancre de note a un élément de liste et chaque élément est cité ; les tableaux
partagés entre les deux volets sont **identiques** ; la numérotation des figures est dense et ordonnée.
Si une vérification échoue, **ne pas contourner et ne pas modifier le script** — corriger le texte.

Puis la suite complète, depuis la racine du dépôt :

```bash
for c in check_evidence_manifest check_links check_raw_json check_probe_syntax check_inference check_figure_traceability; do python3 .github/scripts/$c.py >/dev/null 2>&1 && echo "$c OK" || echo "$c ÉCHEC"; done
```

---

## 5. La couche HTML est périmée sur TROIS rétractations, pas une

Un contre-audit adverse mené le 18 septembre 2026 a établi que le diptyque et la synthèse n'ont suivi
aucune des rétractations récentes. `grep -c 7bis` sur les trois fichiers HTML rend **0**. Traiter
chaque rétractation comme un geste distinct, avec sa propre vérification, et **ne pas les mélanger
dans un même commit**.

### 5a. D12 — c'est l'objet du §2 ci-dessus. Un seul endroit : `article-part1:601`.

### 5b. D9 — réfuté par la campagne 7bis, le HTML porte encore la version affaiblie

Deux endroits dans `article-part1` :

- **ligne 603**, corps §4.5 : « *That is a cold-start property — what the estimate returns in steady
  state, after flush and compaction, was not measured* »
- **ligne 1174**, annexe M22 : « *Scoped by the adversarial pass (D9): this is a cold-start property.
  What the estimate returns in steady state, after flush and compaction, was not measured* »

**Les deux sont faux depuis le 18 septembre 2026.** La mesure a été faite : après `nodetool flush`
l'estimation vaut **171 267**, après compaction majeure **172 132**, contre 200 000 réels — une
erreur d'environ 14 % qui ne décroît pas, sur un corpus où l'estimateur de MongoDB rend 200 000
exactement. Le défaut est **permanent**, pas un artefact de démarrage. M22 était *sous*-évaluée par
le défi D9, pas surévaluée. Source : `docs/campagne7bis.fr.md`, et `docs/challenges-campagne7.fr.md`
où D9 porte désormais « ⛔ RÉFUTÉ ».

Conséquence sur le marqueur épistémique : le passage de la ligne 603 porte `U` pour « cold-start
property ». Après correction, l'affirmation devient **mesurée** — marqueur `M`.

### 5c. D7 — le diptyque publie la décomposition périmée

Le diptyque porte encore la **version périmée** de la décomposition du défi D7, à deux endroits :

- `article-part1`, ligne 599 : « *section 4.4 measured one Data API read at 10.4 ms — ten thousand of
  those are 104 seconds, three quarters of the total* »
- `article-part1`, ligne 1179 : « *at the 10.4 ms per Data API read measured in M15, those account for
  about 104 s, three quarters of the 134* »

Or `docs/THREATS-TO-VALIDITY.md`, entrée D7, enregistre que cette décomposition-là est fausse :

> The first draft of that challenge decomposed the 134 s using M16's point-read p50 — a different
> operation, a different collection, a different campaign — and produced a 30 s residue that was an
> artefact of the wrong constant. The correct decomposition needs no import:
> 133 984.229 ms ÷ 10 000 pages = **13.398 ms per page**, no residue.

Le diptyque publie donc l'importation d'une constante étrangère et son reliquat de 30 s, que le
dossier a explicitement retirés. **Ce défaut n'a rien à voir avec D12** : il est antérieur et porte sur une
autre mesure. Il est signalé ici parce qu'il se trouve dans le même paragraphe que la correction
demandée au §2 — raison de plus pour le traiter dans un geste distinct, avec sa propre vérification.

---

## 6. Un point que le §3 ne couvre pas : la certification du README

`README.md` ligne 217 certifie que le diptyque « *carr[ies] the corrections this repository forced* ».
Tant que 5a, 5b et 5c ne sont pas faits, cette phrase est fausse. Elle redeviendra vraie quand les
trois gestes auront été passés — pas avant, et il ne faut pas l'amender pour la rendre vraie à bon
compte.
