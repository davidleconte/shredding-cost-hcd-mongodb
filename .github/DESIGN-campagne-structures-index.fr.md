> # ✅ DESIGN COURANT — HCD — exécutable indépendamment du design MongoDB
>
> Remplace `DESIGN-campagne-dataapi-vs-cql.md` et `DESIGN-campagne-multiplicite-index.md`,
> tous deux réfutés. **Aucune contrainte d'ordre avec `DESIGN-campagne-mongodb.md`** : les deux
> campagnes ne partagent aucune ressource. Sa série et son fond sont **appariés** avec ceux de
> `DESIGN-campagne-mongodb.md` : ne changez ni l'une ni l'autre sans changer les deux documents.

---

# Design de campagne — une structure d'index ou neuf, à termes indexés appariés

**Destinataire** : l'agent Claude Code sur `alphadebunker`.
**Dépôt** : `~/shredding-cost-hcd-mongodb`, à jour.
**Durée** : **quatre à cinq heures**, dont trois d'exécution, pilote de bruit compris.
Le chiffrage tient compte du flush : 3,513 s par appel mesurés en parallèle sur trois nœuds, un appel par cycle SSTable, soit 0,8 h de flush seul à 200 cycles sur quatre tailles. Une version antérieure de ce document annonçait deux heures en comptant deux flushs par cycle et sans le pilote.
**Remplace** un design antérieur dont l'audit a montré qu'il aurait probablement confirmé son
hypothèse pour la mauvaise raison. Le §2 dit lequel et pourquoi, parce qu'il vaut mieux hériter de
l'erreur que la refaire.

---

## 1 · La question, et les trois hypothèses déjà tombées

Le dossier affirme que le coût de mutation d'un champ croît avec le contenu indexé que la mutation
ne touche pas. Trois mesures s'affrontent :

| mesure | chemin | index | croissance |
|---|---|---|---|
| campagne 3, variante B | Data API | neuf SAI automatiques | **×5,94** |
| `findings_tier.json`, bras CQL | CQL direct, **même table, mêmes neuf index** | neuf | **×4,84** |
| campagne du 19 septembre | CQL natif | **un** SAI sur `VALUES(ballast)` | **×1,05** |

**Hypothèse 1 — l'interface.** Réfutée par une mesure déjà au dépôt : le CQL direct sur la même
table croît **davantage** que la Data API. La croissance n'est pas dans le niveau d'interface.

**Hypothèse 2 — le nombre d'index ne peut pas expliquer un effet qui varie avec la taille, puisqu'il
est constant dans chaque campagne.** Raisonnement faux : le nombre est constant, mais le travail par
index croît avec le contenu. Le nombre multiplie une quantité qui dépend de la taille.

**Hypothèse 3 — le design qui précédait celui-ci.** Il faisait varier le nombre d'index en indexant
une colonne sur neuf, donc **un neuvième du contenu**. Au bas de sa plage, le bras à un index
mesurait l'indexation de 114 octets, où les coûts fixes écrasent tout. Il aurait déprimé ce bras
pour une raison sans rapport avec le nombre d'index, et **confirmé l'hypothèse pour la mauvaise
raison**.

**Ce qui reste, et que ce design teste** : neuf **structures** d'index maintenues contre une seule,
à **termes indexés appariés**.

---

## 2 · Le dispositif, et pourquoi ces tailles précises

SAI plafonne un terme indexé à 8 000 octets. On s'en sert pour apparier ce qui doit l'être.

| | bras A | bras B |
|---|---|---|
| colonnes map | `ballast_1` seule porte le contenu | `ballast_1..9`, contenu réparti également |
| index SAI | **1**, sur `VALUES(ballast_1)` | **9**, sur `VALUES(ballast_n)` |
| termes indexés | *voir tableau* | **identique au bras A** |

**Tailles** : 70,3 Ko, 140,6 Ko, 210,9 Ko et 281,2 Ko — soit 72 000, 144 000, 216 000 et
288 000 octets, multiples de 9 × 8 000.

| taille | termes, bras A | termes, bras B | structures A / B |
|---|---|---|---|
| 72 000 o | 9 | 9 | 1 / 9 |
| 144 000 o | 18 | 18 | 1 / 9 |
| 216 000 o | 27 | 27 | 1 / 9 |
| 288 000 o | 36 | 36 | 1 / 9 |

**Les termes sont appariés exactement aux quatre points.** Le contenu indexé total est identique.
Seul le nombre de structures d'index varie — une contre neuf. C'est l'isolation que le design
précédent n'avait pas.

**Le prix payé** : l'amplitude de la série tombe de ×128 à ×4. Un effet réel doit rester visible sur
un facteur quatre ; s'il ne l'est pas, c'est un résultat.

**Le confondant résiduel, à déclarer** : le bras A concentre tout dans une colonne, le bras B le
répartit sur neuf. L'occupation des colonnes diffère donc, même si le contenu et les termes ne
diffèrent pas. Il n'existe pas de design sans confondant ici ; celui-ci est le plus petit qu'on
puisse choisir, et il doit figurer dans l'enregistrement.

### 2.1 La table ne doit pas contenir une seule ligne

**C'est le défaut que toutes les campagnes de ce dossier partagent, y compris M3 et M13, et qu'aucune
n'a nommé.** Un index SAI sur une table d'une ligne est une structure triviale : ni compaction
d'index, ni fusion de segments, ni contention. Ce qu'on y mesure n'est probablement pas ce que coûte
la maintenance d'un index réel.

**Chargez cent mille lignes de fond de 4 Ko** dans la même table avant de mesurer, de forme
identique mais de contenu aléatoire, puis mutez **une ligne désignée** parmi elles — celle dont la
taille varie selon la série. Le chargement n'est pas chronométré.

**Quatre kilo-octets, et cent mille lignes, ne sont pas négociables** : ce sont exactement le fond
du design MongoDB, parce que la règle M2 de ce dernier croise les facteurs de croissance des deux
moteurs et qu'un facteur obtenu sur un fond donné ne se compare pas à un facteur obtenu sur un autre.
Cela fait 400 Mio par réplica, à comparer aux 12,6 Gio déjà présents : la marge est large.

**Le seuil d'abandon est chiffré.** Si le chargement dépasse trente minutes ou si l'espace libre sur
le volume de données descend sous 20 Gio, arrêtez à dix mille lignes et **inscrivez le nombre chargé
dans l'enregistrement**. Ne jugez pas : mesurez ces deux quantités et appliquez la règle.

Enregistrez le nombre de lignes chargées et l'état des index après chargement.

### 2.2 L'entrelacement décide de la validité

La charge de l'hôte a dérivé de 16,30 à 21,58 pendant la campagne du 19 septembre. Mesurer tout le
bras A puis tout le bras B confondrait le nombre de structures avec la dérive.

Entrelacez par taille : A(72k), B(72k), A(144k), B(144k), et ainsi de suite. Enregistrez la charge
moyenne **avant chaque paire**.

Créez et détruisez les index entre les bras plutôt que de tenir deux tables : le schéma reste
identique et le `CREATE`/`DROP` n'est pas chronométré. **Chaque build porte sur cent mille lignes et
prendra du temps** — voir la règle I5.

**Régimes** : memtable, puis `nodetool flush` **scopé au keyspace de la sonde** avant chaque cycle.
Jamais global : un flush sans argument viderait les 36 keyspaces de travail de la machine.
**Forme de mutation** : conditionnelle, comme toutes les sondes du dossier. La colonne mutée,
`status`, n'est indexée dans aucun bras.

**Répétitions** : 30 chronométrées, 5 de rodage écartées.

---

### Si la campagne s'interrompt

**Reprenez à zéro. Ne reprenez jamais au milieu.**

Deux raisons, et la seconde est propre à ce design. Les cinq répétitions de rodage écartées en tête
de chaque point ne sont plus comparables entre tailles si l'anneau a été laissé dans un autre état.
Et surtout, **l'entrelacement perd tout son sens** : il existe pour que les bras d'une même taille
soient séparés de minutes, or une reprise les sépare de la durée de l'interruption. Un fichier
reconstitué de deux moitiés aurait l'air complet et confondrait le bras avec la dérive de charge —
exactement ce que l'entrelacement doit empêcher.

Détruisez le keyspace ou la base de la sonde, rechargez le fond, et relancez. Le coût est une heure ;
le coût d'un fichier faussement complet est le résultat.

**Si vous relancez, inscrivez-le dans l'enregistrement** : nombre de tentatives, et ce qui a
interrompu la précédente.

---

## 3 · Étape 0 — compter, et s'arrêter si le compte ne suffit pas

Le bras B demande neuf places. Le garde-fou est à cent, toutes keyspaces confondues, et la source
qui fait foi est `system_views.settings` — **pas** `nodetool getguardrailsconfig`, qui affiche le
seuil par table sous la clé du seuil total.

```bash
docker exec p16-hcd-node1 cqlsh -e \
  "SELECT count(*) FROM system_schema.indexes WHERE kind='CUSTOM' ALLOW FILTERING;"
```

**Neuf places libres ou plus** → la campagne part. **Moins de neuf** → arrêtez-vous et signalez-le.

**Ne supprimez rien pour faire de la place.** La campagne du 19 septembre a retiré neuf index d'un
keyspace tiers ; c'était une déviation de son ordre de travail, consignée comme telle dans la note
arXiv. Ne la reproduisez pas. Si ces index ont été recréés, les places sont reprises et la campagne
est bloquée — c'est un arbitrage pour David, pas pour vous.

---

### Le protocole d'appariement, et pourquoi il remplace la règle d'origine

**La séparation des supports ne peut pas détecter l'effet cherché.** C'est un calcul, pas une
opinion : sur les bras réels du dossier, l'étendue médiane vaut **84 % de la médiane**, donc la
disjonction exige un rapport supérieur à ×1,84. L'effet attendu est de l'ordre de ×1,05.

Simulation à trente cycles, bruit multiplicatif calibré sur les mesures existantes :

| effet vrai | séparation des supports | test apparié des signes |
|---|---|---|
| +5 % | **0 %** | 42 % |
| +10 % | **0 %** | 94 % |
| +29 % | **0 %** | 100 % |
| +84 % | **0 %** | 100 % |

La séparation ne détecte rien, **même à +84 %**. Écrire une règle qui rendra « non établi » quel que
soit le résultat réel, puis conclure à l'absence d'effet, serait une expérience non concluante par
construction.

**Le protocole change donc.** Les bras diffèrent par une seule chose — le nombre de structures
d'index — sur le **même document**, dans le **même cycle**. L'appariement est donc disponible, et il
élimine la variance commune : charge de la machine, état du cache, dérive de l'hôte.

**Un cycle apparié** est défini au paragraphe suivant, et il repose sur deux tables plutôt que
sur un changement d'index en cours de route — la raison y est donnée. L'ordre des deux bras à
l'intérieur du cycle est **tiré au sort à chaque cycle** — sans quoi un effet d'échauffement
progressif serait indiscernable d'un effet de bras.

**Nombre de cycles** : **200**, et non 30. Justification, même simulation :

| cycles | puissance à +5 %, seuil brut | puissance à +5 %, seuil corrigé pour 16 comparaisons |
|---|---|---|
| 30 | 42 % | — |
| 80 | 81 % | — |
| 120 | 94 % | 76 % |
| **200** | **100 %** | **96 %** |

Deux cents cycles appariés par point, cinq de rodage écartés, **sur un seul niveau de taille si le
temps manque** — mieux vaut un point à pleine puissance que quatre points incapables de conclure.

**Correction de comparaisons multiples.** Seize comparaisons côté HCD. Le seuil de chaque test des
signes est **0,05 / 16 / 2 = 0,0016** en bilatéral. Appliquez-le et inscrivez-le dans
l'enregistrement ; ne rapportez jamais un seuil non corrigé.

**Ce qui reste de la séparation des supports.** Elle est conservée comme **critère fort**, rapportée
à côté du test apparié : là où elle passe, la direction est certaine sans aucune hypothèse. Là où
elle échoue, le test apparié décide. Elle ne peut plus être le critère unique.

---

### Le dispositif apparié : deux tables, jamais du DDL en cours de mesure

**Une version antérieure de ce design demandait de muter la même ligne par un bras puis par l'autre.
C'est inexécutable** : les bras diffèrent par le nombre d'index, donc passer de l'un à l'autre
exigerait de créer huit index puis de les détruire, **à chaque cycle** — 25 600 opérations de schéma
sur un anneau partagé. L'erreur est signalée ici parce qu'elle n'est visible qu'une fois le
protocole écrit.

**Le dispositif correct** : **deux tables**, chargées à l'identique, dans le même keyspace.

| | table A | table B |
|---|---|---|
| schéma | identique | identique |
| fond | les mêmes 100 000 lignes de 4 Ko, mêmes clés, même contenu | idem |
| index | **1** | **9** |

Un cycle apparié mute la ligne *r* dans A, chronomètre, mute la ligne *r* dans B, chronomètre, et
enregistre la différence. **Aucun DDL ne tourne pendant la mesure.** L'ordre des deux tables à
l'intérieur du cycle est tiré au sort à chaque cycle.

Trois bénéfices, dont deux n'étaient pas cherchés. L'appariement est préservé — même instant, même
charge, même état de cache. **Un seul `nodetool flush` du keyspace couvre les deux tables**, donc un
flush par cycle et non deux. Et les index sont construits une fois pour toutes, avant la campagne,
ce qui retire la règle sur les constructions inachevées.

Coût : 0,76 Gio par réplica pour les deux fonds, face aux 12,6 Gio déjà présents.

### Le pilote de bruit, obligatoire avant de fixer le nombre de cycles

**Le tableau de puissance ci-dessus repose sur une hypothèse non vérifiée** : que le bruit soit
multiplicatif et largement **commun aux deux bras** d'un même cycle. C'est l'hypothèse la plus
favorable possible à l'appariement. Si le bruit est majoritairement indépendant, l'appariement ne
gagne presque rien et deux cents cycles ne suffisent plus.

**Mesurez-la avant de vous y fier, et sur le bon objet.** Un pilote qui corrélerait les deux bras du
traitement confondrait la structure du bruit avec l'effet cherché : si les bras diffèrent réellement
— c'est l'hypothèse testée — le traitement déforme la corrélation qu'on croit mesurer.

**Le pilote tourne donc sur deux bras identiques.** Trente cycles à une seule taille, où chaque cycle
mute la ligne dans la table A, puis **de nouveau dans la table A**. Les deux mesures d'un cycle ne
diffèrent alors que par le bruit, ce qui est exactement ce qu'on veut estimer. Puis :

1. corrélation de Spearman entre les deux mesures d'un même cycle, sur les trente cycles ;
2. écart-type des **différences** appariées, rapporté à la médiane ;
3. nombre de cycles de la campagne recalculé sur cette valeur observée, et non sur la simulation
   ci-dessus.

**Si la corrélation est faible — disons sous 0,3 — dites-le et recalculez.** Rapporter une puissance
issue d'un modèle de bruit inventé serait exactement le défaut que ce dossier reproche ailleurs.

Le pilote est enregistré dans le fichier de sortie, avec ses trente observations.

### Le test : Wilcoxon signé, et les signes en second

Le test des signes est robuste mais jette la magnitude. **Rapportez le Wilcoxon signé** — plus
puissant à effectif égal — **et la médiane des différences appariées avec son intervalle bootstrap**,
qui est la taille d'effet qu'un lecteur peut utiliser. Le test des signes reste comme repli si la
distribution des différences est trop asymétrique pour Wilcoxon.

### Charger les deux tables, et pourquoi l'ordre compte

« Chargées à l'identique » ne suffit pas. Charger A puis B laisserait B avec des SSTables plus
jeunes et moins compactées, donc une différence de latence qui n'aurait rien à voir avec le nombre
d'index.

**Chargez-les en alternance, par lots de mille lignes** : mille dans A, mille dans B, et ainsi de
suite jusqu'à cent mille de chaque. Puis, **avant toute mesure** :

```bash
# compaction majeure des deux tables, non chronométrée
docker exec p16-hcd-node1 nodetool compact <keyspace>
# puis vérifier que les deux tables sont dans un état comparable
docker exec p16-hcd-node1 nodetool tablestats <keyspace> | \
  grep -E 'Table:|SSTable count|Space used \(live\)'
```

**Si les comptes de SSTables des deux tables diffèrent de plus du double, ne mesurez pas** :
relancez la compaction, ou signalez-le et arrêtez-vous. Inscrivez les deux comptes dans
l'enregistrement, avant et après la campagne.

### Ce que neuf index font au cache, et que cette campagne ne sépare pas

La table B porte neuf structures d'index sur disque en plus de ses données. Elle occupe donc plus de
cache que la table A, et la lecture interne de son cycle lire-modifier-écrire peut être plus lente
**pour une raison qui n'est pas la maintenance d'index** : ses données de base sont simplement moins
résidentes.

C'est en partie le traitement lui-même — porter neuf index *est* coûteux en cache. Mais **ce design
ne peut pas distinguer « écrire les index coûte » de « les index chassent les données du cache »**,
et il ne faut pas laisser un lecteur croire qu'il le fait.

**Relevez donc, par table et avant chaque bloc de cycles** : le nombre de SSTables, l'espace vif, et
le taux de succès du cache de lignes si l'anneau l'expose. Publiez-les à côté des latences. Si la
table B montre un taux de succès nettement inférieur, la différence de latence est au moins en
partie un effet de cache et doit être rapportée comme telle.

### Le mesurande : chronomètre client, et trace serveur

La latence observée côté client agrège le transport, la coordination, le round de consensus et la
maintenance d'index. Conclure sur la maintenance d'index à partir d'elle, c'est attribuer à un terme
ce qui est mesuré sur la somme.

**Le dossier sait déjà faire mieux.** `findings_tier.json` porte une décomposition par traces de
coordinateur — `method2_trace`, avec `coord_select_p50_ms`, `coord_update_p50_ms` — obtenue en
lisant `system_traces.sessions` et `system_traces.events`.

**Activez le traçage sur un sous-échantillon**, dix cycles sur les deux cents, et enregistrez pour
chacun la durée côté coordinateur en plus de la durée côté client. Le traçage a un coût : il ne doit
**jamais** porter sur les cycles chronométrés. Les dix cycles tracés sont supplémentaires et
identifiés comme tels dans le fichier.

Ce que cela permet : si la différence appariée côté client est de 3 ms et que la différence côté
coordinateur est de 3 ms, elle est dans le moteur. Si elle est de 3 ms côté client et de 0,2 ms côté
coordinateur, elle est ailleurs — et l'expérience aurait conclu faux sans cette vérification.

### Une ligne mutée, et ce que cela borne

La ligne sous test est mutée deux cents fois de suite. Ses SSTables et ses entrées d'index restent
chaudes tout du long, ce qu'aucune charge réelle ne fait.

**Correctif partiel, à appliquer** : désignez **vingt** lignes au lieu d'une, tirées au sort dans le
fond, et faites tourner les cycles sur elles en rotation. Chaque ligne est alors mutée dix fois, pas
deux cents. Cela ne reproduit pas une charge réelle, mais cela supprime le cas dégénéré où une seule
entrée d'index est réécrite en boucle.

**Ce que cela ne corrige pas**, et qu'il faut déclarer : vingt lignes sur cent mille restent un
accès concentré. Le résultat porte sur la mutation répétée d'un petit ensemble chaud.

### Randomisation

L'ordre des tailles était croissant et fixe dans les designs précédents, donc un échauffement
progressif de l'anneau aurait été indiscernable d'un effet de taille.

**Tirez au sort l'ordre des tailles**, et **tirez au sort l'ordre des deux bras à l'intérieur de
chaque cycle apparié**. Enregistrez la graine du générateur dans le fichier, pour que l'ordre soit
reproductible par un tiers.

---

## 4 · Règles de décision, fixées avant tout chiffre

| | énoncé |
|---|---|
| **I1** | **Test apparié des signes** sur les différences bras B moins bras A, 200 cycles, seuil corrigé 0,0016. Significatif ⇒ le nombre de structures fait une différence de coût à cette taille. Non significatif ⇒ l'effet, s'il existe, est sous le seuil détectable à 200 cycles, **ce qui n'est pas la même chose qu'une absence d'effet** et doit s'écrire ainsi. Rapportez la médiane des différences appariées et son intervalle bootstrap. |
| **I2** | **La règle qui décide.** Si I1 est significative à au moins trois des quatre tailles, avec une médiane de différences de même signe partout, **la croissance du coût est établie comme fonction du nombre de structures d'index**, à termes appariés. Si I1 n'est significative nulle part, l'effet est inférieur à ce que 200 cycles détectent — dites-le en ces termes et donnez la borne supérieure que la puissance permet, jamais « pas d'effet ». Si les signes s'opposent selon la taille, ne lissez pas : rapportez-les tels quels. |
| **I3** | Contrôle de lecture de même taille **dans le même cycle apparié**, les deux bras. S'il croît à moins de 20 % de la croissance de l'update, ce bras est INCONCLUSIF par la règle de contrôle de la campagne — celle qui avait invalidé la variante A de M3. |
| **I4** | Moins de 25 observations sur 30 achevées ⇒ le point est FAILED, pas résumé. |
| **I5** | **Un index dont la construction n'est pas terminée invalide son bras.** Vérifiez-le par la requête ci-dessous, jamais par une attente arbitraire. Si l'état n'est pas lisible, rapportez le bras `BUILD_UNVERIFIED` plutôt que de supposer. |

```sql
SELECT index_name, is_queryable, is_building
FROM system_views.indexes
WHERE keyspace_name = '<keyspace de la sonde>' ALLOW FILTERING;
```

Si cette vue n'existe pas sur ce build, `nodetool listsnapshots` et `sjk` ne répondront pas non plus
à la question : cherchez dans `system_schema.indexes` et dans les journaux du nœud, et **dites ce
que vous avez utilisé**. Une règle pré-enregistrée qui nomme le mauvais instrument ne peut pas être
appliquée — c'est un défaut trouvé dans la version précédente de ce design.

**I2 a trois issues et les trois se publient.** Aucune n'est un échec.

---

## 5 · Ce qui doit être repris tel quel

Partez de la sonde de la campagne du 19 septembre. **Ne réécrivez pas** :

1. **`dist()` avec `min_ms` et `raw_ms`.** C'est la raison d'être de toutes ces campagnes :
   l'auxiliaire partagé du dépôt jette le minimum et la série, et vingt-trois enregistrements sur
   vingt-cinq sont perdus pour cette raison.
2. **`separated()` et `ratio_interval()`**, à l'identique.
3. **`host_fingerprint()`**, plus la charge avant chaque paire.
4. **Le flush scopé au keyspace de la sonde.**
5. **Le bloc `not_met`**, auquel vous ajoutez les limites du §7.

---

## 6 · Livrable

`/tmp/findings_index_structures.json`, et rien d'autre à modifier sur la machine.
**Ne committez pas depuis alphadebunker.**

Doit contenir : les mesures ; la liste exacte des `CREATE CUSTOM INDEX` de chaque bras et leur temps
de construction ; le nombre de lignes de fond chargées ; le compte d'index avant et après ; la
charge avant chaque paire ; l'état `is_building` relevé avant chaque bras ; et les verdicts I1 à I5
tels que la sonde les a calculés.

**Rapport en trois lignes, sans interprétation** : les verdicts, la dérive de charge, ce qui a
divergé du plan.

**Ne concluez pas à la place du dossier.** Si I3 se déclenche, c'est une issue prévue. Si l'étape 0
refuse les places, ou si la table de fond ne tient pas, la campagne n'a pas lieu — et cela se
rapporte comme un résultat.

---

## 7 · Limites, déclarées d'avance

- **L'effet d'index et l'effet de cache ne sont pas séparés.** Le bras à neuf structures occupe
  plus de mémoire que celui à une, donc une partie de l'écart mesuré peut venir de ce que ses
  données de base sont moins résidentes, et non de l'écriture des index. Les compteurs de
  stockage et de cache sont relevés par bloc pour que le lecteur en juge, mais le design ne les
  distingue pas.
- **L'occupation des colonnes diffère entre les bras.** Le contenu et les termes indexés sont
  appariés ; leur répartition sur une colonne ou neuf ne l'est pas. C'est le confondant résiduel et
  il n'est pas supprimable.
- **Neuf `VALUES(map)` ne sont pas les neuf de la Data API**, qui portent sur
  `entries(query_text_values)`, `values(exist_keys)`, `array_contains`, `array_size` et d'autres
  cibles de natures différentes. Ce design isole le **nombre de structures** en tenant le **type**
  constant. Il ne dit rien du type ; si le résultat est plat, c'est la piste suivante.
- **L'amplitude est ×4, non ×128.** Un effet faible pourrait s'y perdre. Le choix est délibéré :
  l'appariement des termes valait cette perte.
- **Cent mille lignes ne sont pas une table de production**, mais c'est cinq ordres de grandeur de
  plus que toutes les campagnes précédentes de ce dossier, qui mutaient une ligne unique.
- **Pas de root**, donc pas de vidage du cache de pages : on exerce le chemin de lecture SSTable,
  pas des déplacements de tête.
- **Client unique séquentiel en boucle fermée.** Les percentiles sont des temps de service à
  utilisation négligeable.
- **Hôte partagé, charge dérivante**, d'où l'entrelacement — qui atténue sans supprimer.
- **Le round Paxos est présent dans les deux bras** et n'est pas isolé ici. Il l'a été séparément :
  ×1,18 à ×2,84 sur SSTable.
