# Ordre de travail — mettre le diptyque et la synthèse à jour des rétractations

**Destinataire :** l'agent en charge de `docs/article/article-part1-what-a-mutation-costs.html`,
`docs/article/article-part2-when-the-index-is-current.html` et `docs/synthesis/huit-axes.fr.html`.
**Émis le 18 septembre 2026**, contre le commit `f8ac6a3`.
**État de la couche Markdown :** à jour et poussée. Ce document ne concerne que les trois HTML.

`grep -c 7bis docs/article/*.html docs/synthesis/*.html` rend **0** sur les trois fichiers. La couche
Markdown a été corrigée quatre fois aujourd'hui et le HTML n'a pas bougé depuis `2e9e0b0`. Le diptyque
est donc en retard de plusieurs rétractations, **et il se contredit lui-même** en au moins un endroit.

---

## Règles du travail

1. **Sept gestes indépendants**, listés au §2. **Un commit par geste.** Ne pas les mélanger : chacun
   porte sur une mesure différente, et un lecteur doit pouvoir voir lequel a bougé.
2. **Ne réécris pas les deux volets.** Chaque geste nomme une ou deux lignes. Tout le reste du
   diptyque reste tel quel — y compris les passages du §3, qui avaient raison.
3. **Les marqueurs épistémiques** du diptyque sont `D` (documenté), `M` (mesuré), `U` (non vérifié).
   Chaque geste dit lequel s'applique après correction. Ne pas en changer un sans raison énoncée.
4. **Les appels de note existants sont conservés.** Si un remplacement retire un appel, dis-le au
   lieu de le faire.
5. **Après chaque geste**, les deux commandes du §4 doivent passer. Si une vérification échoue,
   **ne la contourne pas et ne modifie pas le script** — corrige le texte.
6. Si un renvoi te paraît ambigu, **ne devine pas** : liste le cas et demande.

---

## Geste 1 — D12 : le retrait de la clause est annulé

**Où :** `part1`, ligne **601**, paragraphe `<span class="ep ep-u">U</span>` du §4.5. Il se termine par :

> An earlier revision of this sentence added that it also means designing a table partitioned by the
> group key in advance. The data do not support that clause: the table designed for the query and a
> cross-partition `GROUP BY` against it differ by ×1.28 at the median, their supports overlap, and the
> interval of their ratio contains one.⁵² At this scale the partitioning choice does not separate from
> noise, and the penalty is withdrawn. What survives is the half that matters.

**Ce qui ne va pas.** C'est le seul retrait de la clause dans tout le corpus non-Markdown, et il est
faux. Le défi D12 appelait C3b « le bras non aligné ». Il n'y a qu'**une table** dans le bras CQL :
`probes/agg_cql_arm.py` ne contient qu'un `CREATE TABLE`, `agg_cql(cat, id, amt) PRIMARY KEY (cat, id)`,
et le fichier de résultats l'enregistre au singulier. C3a et C3b l'interrogent toutes deux : elles
diffèrent par la **forme de requête**, pas par le schéma — comme le registre du dépôt les nomme depuis
toujours, `AGG-CQLsweep-vs-CQLgroupby`. Noter que la phrase concède déjà elle-même « a cross-partition
`GROUP BY` **against it** », puis raisonne comme si les deux nombres chiffraient deux conceptions.

**Et c'est mesuré, avec preuve publiée** — `data/raw/findings_cql_groupby_expressibility.json`, sonde
`probes/cql_groupby_expressibility.py`, règles R1–R3 fixées avant exécution. Sur une table
`PRIMARY KEY (id)`, le `GROUP BY cat` de C3b est **refusé** : `InvalidRequest code=2200, "Group by is
currently only supported on the columns of the PRIMARY KEY, got cat"`, et `ALLOW FILTERING` n'y change
rien. C3b n'est exprimable que **parce que** la table est pré-partitionnée.

**⚠ La règle R3 s'est déclenchée et restreint l'argument. Elle doit voyager avec lui.** Le refus porte
sur la forme `GROUP BY` de C3b, **pas** sur la forme *sweep* de C3a : `SELECT SUM(amt) … WHERE cat='c3'`
contre une table `PRIMARY KEY (id)` est refusée jusqu'à ce qu'on ajoute `ALLOW FILTERING`, puis passe.
Or C3a est le bras qui produit le 2 011 ms de tête. Donc ce qui est catégoriquement inexprimable sans
pré-partitionnement, c'est le bras que D12 appelait « non aligné », et lui seul.

**Remplacement proposé**, à adapter au registre :

> Reaching it also means designing a table partitioned by the group key in advance. An earlier revision
> withdrew that clause, on the ground that the table designed for the query and a cross-partition
> `GROUP BY` **against that same table** differ by only ×1.28 at the median, with overlapping supports
> and a ratio interval containing one.⁵² The withdrawal was an error of object rather than of
> arithmetic: both figures come from one table, and what separates them is the shape of the query, not
> the design of the schema. Against a table not partitioned by the group key, that second query is not
> slower — the engine refuses it outright. The clause stands, with one limit: the *per-partition sweep*
> that produced the two-second figure does run against an unpartitioned table, once `ALLOW FILTERING`
> is added, at a cost not measured here.

**Marqueur :** le ×1,28 reste `U`. Le refus et l'acceptation sous `ALLOW FILTERING` sont **mesurés** :
si la convention du diptyque l'exige, scinder le paragraphe pour porter `M` sur cette moitié.

---

## Geste 2 — D7 : la décomposition publiée est celle que le dossier a retirée

**Où :** deux endroits, le même contenu.

- `part1`, ligne **601**, plus haut dans le même paragraphe que le geste 1 :
  « *section 4.4 measured one Data API read at 10.4 ms — ten thousand of those are 104 seconds, three
  quarters of the total* »
- `part1`, ligne **1179**, annexe M23 : « *at the 10.4 ms per Data API read measured in M15, those
  account for about 104 s, three quarters of the 134* »

**Ce qui ne va pas.** `docs/THREATS-TO-VALIDITY.md`, entrée D7, enregistre que cette décomposition est
fausse : elle importe la p50 d'une lecture ponctuelle — *autre opération, autre collection, autre
campagne* — et produit un reliquat de 30 s qui est un artefact de la mauvaise constante. La
décomposition correcte n'importe rien : **133 984,229 ms ÷ 10 000 pages = 13,398 ms par page, sans
reliquat.** Le diptyque publie donc l'importation et son reliquat, que le dossier a explicitement
retirés.

**Marqueur :** la décomposition correcte est arithmétique sur une mesure publiée — `M`.

**Attention :** les autres occurrences de « 10.4 ms » dans `part1` (lignes 565 et 613) et dans la
synthèse (ligne 132) portent sur la lecture ponctuelle M16 et sont **justes**. Ne pas y toucher.

---

## Geste 3 — D9 : le zéro de l'estimation n'est pas une propriété de démarrage à froid

**Où :** deux endroits.

- `part1`, ligne **603**, corps §4.5 : « *That is a cold-start property — what the estimate returns in
  steady state, after flush and compaction, was not measured* »
- `part1`, ligne **1174**, annexe M22 : « *Scoped by the adversarial pass (D9): this is a cold-start
  property. What the estimate returns in steady state, after flush and compaction, was not measured,
  and the finding must be read as a window rather than a permanent state.* »

**Ce qui ne va pas.** La campagne 7bis a fait la mesure que ces deux phrases déclarent absente. Après
`nodetool flush` l'estimation vaut **171 267** ; après compaction majeure, **172 132** ; contre 200 000
réels. Une erreur d'environ **14 % qui ne décroît pas**, sur un corpus où l'estimateur de MongoDB rend
200 000 exactement. **Le défaut est permanent, pas un artefact de démarrage**, et M22 était
*sous*-évaluée par le défi D9, pas surévaluée. Source : `docs/campagne7bis.fr.md` ; D9 porte désormais
« ⛔ RÉFUTÉ » dans `docs/challenges-campagne7.fr.md`.

**Marqueur :** `U` → **`M`**. C'est mesuré.

---

## Geste 4 — le 602× est borné à sa forme de requête

**Où :** trois endroits dans `part1`.

- ligne **601** : « *That is a factor of six hundred* »
- ligne **607** : « *a reader who takes the 602 as a statement about engines has taken it wrongly* »
- ligne **1178**, annexe M23 : « *Ratios: 602× between MongoDB and the interface* »

**Ce qui ne va pas.** Le 602× vaut **à dix groupes**. La campagne 7bis a mesuré la même comparaison à
trois cardinalités : **584×** à 10 groupes, **151×** à 100 000 groupes, **609×** filtrée — intervalles
bootstrap [577 ; 592], [148 ; 153], [599 ; 617], supports disjoints. Le coût de MongoDB suit la
cardinalité du regroupement ; celui de HCD non, étant dominé par le transport. Le rapport est **divisé
par 3,9** entre dix groupes et cent mille. La direction tient partout — 151× reste deux ordres de
grandeur — mais l'amplitude est une propriété de la requête choisie.

La ligne 607 reste juste et devient plus forte : elle dit déjà qu'il ne faut pas lire le 602 comme un
énoncé sur les moteurs. Lui ajouter qu'il ne faut pas non plus le lire comme un énoncé sur
l'agrégation en général.

---

## Geste 5 — deux réserves de M23 sont levées, une troisième tient

**Où :** `part1`, lignes **1174**, **1178** et **1180**, annexe.

- **`n = 3` est levée.** La ligne 1178 écrit « *median 133 984 ms (n = 3, spread 0.4 %)* » et la 1180
  « *the n = 3 figure's tail percentiles, which carry no information (D6)* ». Rejoué à **n = 15**, la
  médiane HCD est **132 985,311 ms**, soit **−0,7 %** : le n = 3 était représentatif. Les percentiles
  de queue restent non informatifs à n = 3 — cette moitié-là tient —, mais la réserve sur la médiane
  tombe.
- **Le régime cache est levé.** La ligne 1174 finit par « *The zero is also direct evidence that this
  whole campaign ran cache-resident.* » C'est vrai, et la campagne 7bis a mesuré l'axe **après flush et
  compaction majeure** : le balayage y coûte **130 127,0 ms**, soit **2,1 % de moins** qu'en cache. Le
  régime n'était donc pas ce qui portait le résultat.
- **Ce qui tient :** l'étiquette pommes-contre-oranges du bras CQL, et la ligne 1180 (voir §3).

---

## Geste 6 — « no confidence interval anywhere » est faux

**Où :** `part2`, ligne **1012**, paragraphe *What none of it transposes to* :
« *No concurrency, no multiple clients, no wide-area topology, **no confidence interval anywhere**.* »

**Ce qui ne va pas.** La campagne 7bis conserve ses observations — `raw_ms`, chaque mesure dans l'ordre
d'exécution — et publie de vrais intervalles bootstrap ainsi qu'un test de rang. Quatre fichiers sur
trente-neuf conservent leurs observations. La formulation correcte est **« sur un axe seulement »** :
les trente-quatre autres fichiers ont perdu les leurs et c'est irréversible.

---

## Geste 7 — la synthèse dit « régime cache sauf une campagne »

**Où :** `docs/synthesis/huit-axes.fr.html`, ligne **94** : « *régime cache sauf une campagne* ».
Depuis 7bis, l'axe agrégation a lui aussi été mesuré hors cache. Reformuler au pluriel, ou nommer les
deux campagnes.

---

## §3 — Ce qu'il ne faut **PAS** changer, et qui avait raison

| Fichier | Ligne | Contenu | Pourquoi |
|---|---|---|---|
| `part1` | **1180** | « *Not established: the native CQL route …, since it requires a table partitioned by the group key in advance* » | **Avait raison.** C'est la ligne que le retrait de la 601 contredisait. Le diptyque se contredisait lui-même à 579 lignes d'écart ; corriger la 601 supprime la contradiction **sans y toucher**. |
| `part1` | 1178 | « native CQL over **a table** designed for the query », puis les deux routes | Correct — c'est la preuve du geste 1 énoncée dans l'annexe : une table, deux routes. |
| `part1` | 605 | la doctrine : données « *stored partitioned, sorted, denormalised and filtered in advance* » (note 53) | Correct, et indépendant de D12. |
| `part1` | 1163 | « *store pre-computed answers …, roughly a table per query* » | Correct. |
| `part1` | 565, 613 | « 10.4 ms » | Lecture ponctuelle M16, autre mesure. Ne pas confondre avec le geste 2. |
| `part2` | 923 | ligne « Aggregating by group » du tableau à huit axes | Ne porte ni la clause ni son retrait. |
| `synthèse` | 158, 259-266 | « données stockées partitionnées … *à l'avance* », « ni l'une ni l'autre des deux voies mesurées », « une table d'agrégats maintenue à l'écriture » | Corrects. La synthèse n'a **jamais** porté le retrait : elle redevient cohérente avec l'article sans être modifiée. |

---

## §4 — Vérification, après **chaque** geste

```bash
python3 .github/scripts/check_article_refs.py docs/article/article-part1-what-a-mutation-costs.html docs/article/article-part2-when-the-index-is-current.html
```

Doit rendre `clean — every reference resolves, numbering dense, tables agree`. Il vérifie que chaque
ancre de note a un élément de liste et réciproquement, que **les tableaux partagés entre les deux
volets sont identiques**, et que la numérotation des figures est dense. Ce contrôle tourne désormais
en CI comme **job 10** : un diptyque incohérent fait échouer la CI.

Puis la suite complète, depuis la racine du dépôt :

```bash
for c in check_evidence_manifest check_links check_raw_json check_probe_syntax check_probe_citations check_artifact_table check_inference check_figure_traceability; do python3 .github/scripts/$c.py >/dev/null 2>&1 && echo "$c OK" || echo "$c ÉCHEC"; done
```

**Vérifie sur un clone propre, pas seulement dans ton arbre de travail** — `git clone . /tmp/verif &&
cd /tmp/verif && …`. Trois défauts de ce dépôt aujourd'hui sont passés en local et ont échoué en CI
pour cette seule raison.

---

## §5 — Le point que ces gestes ne couvrent pas

`README.md` ligne 217 certifie que le diptyque « *carr[ies] the corrections this repository forced* ».
Tant que les sept gestes ne sont pas faits, cette phrase est fausse. Elle redeviendra vraie quand ils
le seront — **et il ne faut pas l'amender pour la rendre vraie à bon compte.**

Et la cause de fond, qu'il vaut mieux nommer que répéter : la CI vérifie sept documents Markdown et la
cohérence *interne* du diptyque. Rien ne vérifie l'**accord** entre le HTML et la couche Markdown. Ces
sept gestes sont la conséquence de cette absence, pas de la négligence d'un rédacteur.
