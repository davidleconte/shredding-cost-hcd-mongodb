> # ✅ DESIGN COURANT — MongoDB — exécutable indépendamment du design HCD
>
> **Aucune contrainte d'ordre entre les deux designs** : machines virtuelles différentes, garde-fou
> d'index différent, aucune donnée commune. Si la campagne HCD est bloquée faute de places d'index,
> celle-ci part quand même.
>
> **En revanche, la séquence interne à ce document est obligatoire** : question B avec un cache
> réduit, puis redémarrage, puis question A avec le cache par défaut. Le §2.3 dit pourquoi.
>
> Sa série (72 000 à 288 000 octets) et son fond (100 000 documents de 4 Ko) sont **imposés par**
> `DESIGN-campagne-structures-index.md`, parce que la règle M2 croise les facteurs de croissance
> des deux moteurs. Ne changez ni l'une ni l'autre sans changer les deux documents.

---

# Design de campagne — MongoDB : structures d'index, et le hors-cache qui a échoué

**Destinataire** : l'agent Claude Code sur `alphadebunker`.
**Dépôt** : `~/shredding-cost-hcd-mongodb`, à jour.
**Durée** : **quatre heures**, dont trois d'exécution, pilote de bruit et redémarrage compris.
Une version antérieure annonçait deux heures et demie, sans le pilote de bruit ni le doublement du nombre de cycles.
**Indépendant** du design HCD `DESIGN-campagne-structures-index.md` : ni machine virtuelle
commune, ni contrainte de garde-fou partagée.

**Mais ses deux questions ne sont pas indépendantes entre elles, et l'ordre est imposé.** Elles
exigent des tailles de cache WiredTiger incompatibles : la question B a besoin d'un cache minuscule
pour que l'éviction soit possible, la question A a besoin d'un cache de production pour que son fond
y tienne. **Un redémarrage les sépare, et il n'est pas optionnel** — voir le §2.3.

---

## 1 · Deux questions, et la première décide de la thèse du dossier

### Question A — le coût vient-il de la décomposition, ou du nombre d'index ?

Le dossier affirme que décomposer un document coûte à l'écriture. Si l'on établit côté HCD que la
croissance suit le **nombre de structures d'index**, alors ce n'est plus un coût de décomposition :
c'est un coût d'indexation, et il s'appliquerait à n'importe quel moteur maintenant neuf index.
**Deux thèses très différentes, et sans bras MongoDB on ne peut pas les distinguer.**

Ce que le dossier a déjà, et qui suggère la piste sans la trancher :

| structures d'index | pente mesurée |
|---|---|
| 0 — `mongo-default`, rien hors `_id` | 0,0098 ms/KiB |
| 1 — `mongo-wildcard`, couvre tous les champs | 0,0176 ms/KiB |
| 9 — HCD Data API | 0,778 ms/KiB |

Passer de zéro à une structure **double presque** la pente. Mais l'extrapolation linéaire à neuf
donne 0,080 ms/KiB, soit **dix fois moins que HCD**. Donc le nombre de structures n'absorberait
qu'une partie de l'écart — ou les deux moteurs ne paient pas la même chose par structure.

C'est une extrapolation sur deux points. Elle justifie de mesurer, pas de conclure.

### Question B — le comparateur hors cache, campagne à reprendre

`probes/mongo_regime_rerun.py` a tourné le 19 septembre et **a échoué** : six bras sur huit marqués
`NOT_EVICTED`. Le ballast a pourtant fait pression — 158 072 pages évincées — mais le compteur
`pages read into cache` n'a pas bougé pendant les bras.

La menace **L10** du registre reste donc ouverte : le comparateur n'a jamais été mesuré hors cache,
alors que HCD l'a été dans deux régimes. **L'asymétrie qui fragilise l'axe mutation tient toujours.**

---

## 2 · Question B d'abord, parce qu'elle a un correctif et qu'il est simple

La sonde n'a pas échoué par maladresse : elle déclarait d'avance qu'il n'existe aucun moyen supporté
de vider le cache WiredTiger sans redémarrer `mongod`, et que redémarrer changerait plus que le
cache. Ce raisonnement valait pour l'anneau HCD, partagé et portant 36 keyspaces de travail.

**Il ne vaut pas ici.** Le replica set a été reconstruit pour l'occasion depuis
`env/docker-compose.mongodb-rs.yml`. Il n'est partagé avec personne, ne porte aucune donnée tierce,
et rien ne s'oppose à le redémarrer avec un cache volontairement petit.

### Le correctif

`command:` ne fixe aujourd'hui aucune taille, donc WiredTiger prend la moitié des 8 Gio du
conteneur, soit 3,5 Gio — d'où un ballast de plus de 10 Gio pour espérer évincer, et un échec.

Ajoutez `--wiredTigerCacheSizeGB 0.25` aux trois membres :

```yaml
command: ["mongod", "--replSet", "rs0", "--bind_ip_all", "--port", "27017",
          "--wiredTigerCacheSizeGB", "0.25"]
```

Puis reconstruisez, réinitialisez le replica set, et **vérifiez que la valeur est prise** avant
toute mesure :

**Avant de taper quoi que ce soit** : ce `down` ne doit toucher que les trois membres de ce fichier
de composition. Vérifiez-le, depuis la racine du dépôt et pas d'ailleurs :

```bash
cd ~/shredding-cost-hcd-mongodb
docker compose -f env/docker-compose.mongodb-rs.yml config --services
```

Attendu : les trois services MongoDB, et **rien d'autre**. Si un nom d'anneau HCD apparaît,
arrêtez-vous : vous n'êtes pas dans le bon répertoire.

**Règle absolue, la même que pour le design HCD : ne supprimez aucun conteneur, aucun volume, aucune
base qui ne soit pas de ce fichier de composition.** La machine est partagée et porte un anneau HCD
à six nœuds avec 36 keyspaces de travail. Le `down` ci-dessous est le seul arrêt de service autorisé
par ce design, et il est borné à `-f env/docker-compose.mongodb-rs.yml`.

```bash
docker compose -f env/docker-compose.mongodb-rs.yml down
docker compose -f env/docker-compose.mongodb-rs.yml up -d
# réinitialisation du replica set — écrite ici plutôt que renvoyée à une procédure orale
mongosh --quiet --port 27017 --eval 'rs.initiate({_id:"rs0", members:[
  {_id:0, host:"127.0.0.1:27017"},
  {_id:1, host:"127.0.0.1:27018"},
  {_id:2, host:"127.0.0.1:27019"}]})'
# attendre qu un primaire soit elu avant toute mesure
mongosh --quiet --port 27017 --eval 'while(!db.hello().isWritablePrimary){sleep(500)}; print("primaire pret")'
mongosh --quiet --eval 'db.serverStatus().wiredTiger.cache["maximum bytes configured"]'
```

Attendu : environ 268 435 456. **Si un autre nombre sort, arrêtez-vous** — la mesure suivante serait
sans valeur.

Un cache de 256 Mio rend l'éviction triviale : le ballast de la sonde, calculé à trois fois le cache
configuré, tombe à 768 Mio et s'écrit en quelques secondes.

### Ce qui ne change pas

**Ne modifiez pas `mongo_regime_rerun.py`.** Son garde-fou — vérifier l'éviction par
`pages read into cache` plutôt que la supposer — est ce qui a rendu l'échec du 19 septembre lisible
au lieu de le transformer en faux résultat. C'est la partie de la sonde qui a bien fonctionné.

Relancez-la telle quelle après le redémarrage :

```bash
export MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"
python3 probes/mongo_regime_rerun.py > /tmp/findings_mongo_regime_v2.json
```

**Critère de succès, objectif** : aucun bras ne porte `NOT_EVICTED`. Si six bras le portent encore
malgré un cache de 256 Mio, l'explication n'est pas la taille du cache et il faut le dire plutôt que
de réduire davantage.

### Ce que ce changement coûte, et qu'il faut déclarer

Un cache de 256 Mio n'est pas une configuration de production. Les chiffres **en cache** de cette
campagne ne sont plus comparables à ceux des campagnes précédentes, qui tournaient à 3,5 Gio. Seule
la **comparaison interne** — en cache contre hors cache, même déploiement, même session — est
exploitable, et c'est précisément ce que la règle R2 de la sonde demande.

---

### 2.3 La séquence, et pourquoi elle n'est pas négociable

| | question B — hors cache | question A — structures |
|---|---|---|
| cache WiredTiger | **256 Mio**, imposé | **par défaut**, ≈ 3,5 Gio |
| données chargées | ballast de 768 Mio | fond de 100 000 documents à 4 Ko, soit 400 Mio |
| tient en cache ? | non, c'est le but | **oui**, et c'est la condition |

Un fond de 400 Mio dans un cache de 256 Mio déborderait de seize fois. La question A tournerait
alors partiellement hors cache **sans que rien ne le signale**, et confondrait le nombre d'index
avec le régime — exactement le défaut que la question B existe pour mesurer.

**Faites donc la question B d'abord, avec son cache réduit. Puis retirez le
`--wiredTigerCacheSizeGB`, redémarrez, vérifiez que le cache est revenu à sa valeur par défaut, et
seulement alors lancez la question A.**

```bash
mongosh --quiet --eval 'db.serverStatus().wiredTiger.cache["maximum bytes configured"]'
```

Attendu pour la question A : environ 3,7 × 10⁹. **Si le nombre est proche de 2,7 × 10⁸, le
redémarrage n'a pas pris et la question A ne doit pas être lancée.**

Inscrivez la valeur relevée dans chacun des deux enregistrements. C'est le paramètre qui rend les
deux campagnes non comparables entre elles, et il doit être lisible dans les fichiers plutôt que
déduit de ce document.

---

## 3 · Question A — le bras à structures multiples

### Dispositif

Une collection, neuf champs de même forme, **trois bras qui ne diffèrent que par le nombre d'index
déclarés**.

| | bras 1 | bras 4 | bras 9 |
|---|---|---|---|
| champs | `f1..f9`, tous présents | identiques | identiques |
| index | 1, sur `f1` | 4, sur `f1..f4` | 9, sur `f1..f9` |
| champ muté | `status`, **jamais indexé** | idem | idem |

**Le contenu indexé doit être apparié entre les bras**, sans quoi vous mesurez le volume et non le
nombre — c'est l'erreur qu'un design HCD antérieur a commise et qui aurait confirmé l'hypothèse pour
la mauvaise raison.

Répartissez donc le contenu total sur les **neuf champs dans les trois bras**, et n'indexez que les
un, quatre ou neuf premiers. Le contenu indexé diffère alors d'un facteur neuf entre bras 1 et
bras 9 — c'est inévitable si les champs sont indexés individuellement.

**Le bras « une structure » doit être un index _wildcard_, pas un index composé.** Un composé sur
neuf champs de 14 Ko est légal — MongoDB a retiré la limite de taille de clé d'index en 4.2 — mais il
produirait une clé unique de 126 Ko contre des pages WiredTiger d'environ 32 Ko, donc un traitement
de débordement qui est un autre chemin de code. On mesurerait une pathologie contre un cas normal.

Le `wildcard` est la bonne réponse : **une structure qui couvre tous les champs**, sans clé
surdimensionnée. Le dossier le mesure déjà à 0,0176 ms/KiB, ce qui donne au bras un point de
comparaison antérieur.

| | bras wildcard | bras 4 | bras 9 |
|---|---|---|---|
| index | **1** — `{"$**": 1}` | 4 simples, `f1..f4` | 9 simples, `f1..f9` |
| contenu couvert | les neuf champs | quatre | les neuf |

Le bras 4 reste utile comme point intermédiaire, avec son confondant déclaré : il ne couvre que
quatre champs sur neuf. Les deux bras qui décident sont **wildcard contre 9**, à contenu couvert
identique.

**Tailles** : **72 000, 144 000, 216 000 et 288 000 octets** — soit 70,3 / 140,6 / 210,9 / 281,2 Ko.

Ces valeurs ne sont pas choisies pour MongoDB, qui n'a aucune contrainte de taille de terme : elles
sont **imposées par le design HCD**, où elles apparient exactement les termes indexés entre les
bras. La règle M2 croise les facteurs de croissance des deux moteurs, et **deux facteurs obtenus sur
des plages différentes ne se comparent pas**. La même série est donc obligatoire des deux côtés.

**Répétitions** : 30 chronométrées, 5 de rodage écartées. **Write concern** : `majority` + journalling, comme partout dans ce dossier.
**Mutation** : un `$set` sur `status`.

### L'entrelacement

La charge de l'hôte a dérivé de 17,57 à 25,25 pendant la campagne MongoDB du 19 septembre — la plus
forte dérive des trois. **Mesurer un bras entier puis le suivant confondrait le nombre d'index avec
la dérive.**

Entrelacez par taille : wildcard(72 k), 4(72 k), 9(72 k), puis wildcard(144 k), et ainsi de suite. Créez et
détruisez les index entre les bras. **Enregistrez la charge avant chaque triplet.**

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

**Un cycle apparié** est défini au paragraphe suivant, et il repose sur deux collections plutôt que
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

### Le dispositif apparié : deux collections, jamais de création d'index en cours de mesure

**Une version antérieure de ce design demandait de muter la même ligne par un bras puis par l'autre.
C'est inexécutable** : les bras diffèrent par le nombre d'index, donc passer de l'un à l'autre
exigerait de créer huit index puis de les détruire, **à chaque cycle** — 25 600 opérations de schéma
sur le replica set. L'erreur est signalée ici parce qu'elle n'est visible qu'une fois le
protocole écrit.

**Le dispositif correct** : **deux collections**, chargées à l'identique, dans le même keyspace.

| | collection A | collection B |
|---|---|---|
| schéma | identique | identique |
| fond | les mêmes 100 000 documents de 4 Ko, mêmes clés, même contenu | idem |
| index | **1** | **9** |

Un cycle apparié mute le document *r* dans A, chronomètre, mute le document *r* dans B, chronomètre, et
enregistre la différence. **Aucune création ni destruction d'index ne tourne pendant la mesure.** L'ordre des deux collections à
l'intérieur du cycle est tiré au sort à chaque cycle.

Trois bénéfices, dont deux n'étaient pas cherchés. L'appariement est préservé — même instant, même
charge, même état de cache. **Un seul flush de la base couvre les deux collections**, donc un
flush par cycle et non deux. Et les index sont construits une fois pour toutes, avant la campagne,
ce qui retire la règle sur les constructions inachevées.

Coût : 0,76 Gio par membre pour les deux fonds, face aux 12,6 Gio déjà présents.

### Le pilote de bruit, obligatoire avant de fixer le nombre de cycles

**Le tableau de puissance ci-dessus repose sur une hypothèse non vérifiée** : que le bruit soit
multiplicatif et largement **commun aux deux bras** d'un même cycle. C'est l'hypothèse la plus
favorable possible à l'appariement. Si le bruit est majoritairement indépendant, l'appariement ne
gagne presque rien et deux cents cycles ne suffisent plus.

**Mesurez-la avant de vous y fier, et sur le bon objet.** Un pilote qui corrélerait les deux bras du traitement confondrait la structure du bruit avec l'effet cherché : si les bras diffèrent réellement
— c'est l'hypothèse testée — le traitement déforme la corrélation qu'on croit mesurer.

**Le pilote tourne donc sur deux bras identiques.** Trente cycles à une seule taille, où chaque cycle
mute le document dans la collection A, puis **de nouveau dans la collection A**. Les deux mesures d'un cycle ne
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

### Charger les deux collections, et pourquoi l'ordre compte

« Chargées à l'identique » ne suffit pas. Charger A puis B laisserait B avec des SSTables plus
jeunes et moins compactées, donc une différence de latence qui n'aurait rien à voir avec le nombre
d'index.

**Chargez-les en alternance, par lots de mille documents** : mille dans A, mille dans B, et ainsi de
suite jusqu'à cent mille de chaque. Puis, **avant toute mesure** :

```bash
# compaction majeure des deux collections, non chronométrée
docker exec p16-hcd-node1 nodetool compact <keyspace>
# puis vérifier que les deux collections sont dans un état comparable
docker exec p16-hcd-node1 nodetool collectionstats <keyspace> | \
  grep -E 'Table:|SSTable count|Space used \(live\)'
```

**Si les tailles de stockage des deux collections diffèrent de plus de 10 %, ne mesurez pas** :
relancez la compaction, ou signalez-le et arrêtez-vous. Inscrivez les deux comptes dans
l'enregistrement, avant et après la campagne.

### Ce que neuf index font au cache, et que cette campagne ne sépare pas

La collection B porte neuf structures d'index sur disque en plus de ses données. Elle occupe donc plus de
cache que la collection A, et la lecture interne de son cycle lire-modifier-écrire peut être plus lente
**pour une raison qui n'est pas la maintenance d'index** : ses données de base sont simplement moins
résidentes.

C'est en partie le traitement lui-même — porter neuf index *est* coûteux en cache. Mais **ce design
ne peut pas distinguer « écrire les index coûte » de « les index chassent les données du cache »**,
et il ne faut pas laisser un lecteur croire qu'il le fait.

**Relevez donc, par collection et avant chaque bloc de cycles** : le nombre de SSTables, l'espace vif, et
le taux de succès du cache de documents si l'anneau l'expose. Publiez-les à côté des latences. Si la
collection B montre un taux de succès nettement inférieur, la différence de latence est au moins en
partie un effet de cache et doit être rapportée comme telle.

### Le mesurande : chronomètre client, et trace serveur

La latence observée côté client agrège le transport, la coordination, le round de consensus et la
maintenance d'index. Conclure sur la maintenance d'index à partir d'elle, c'est attribuer à un terme
ce qui est mesuré sur la somme.

**Le dossier sait déjà faire mieux.** Côté MongoDB, l'équivalent est le profileur : `db.setProfilingLevel(2)` enregistre `millis` et
`execStats` par opération dans `system.profile`.

**Activez le traçage sur un sous-échantillon**, dix cycles sur les deux cents, et enregistrez pour
chacun la durée côté serveur en plus de la durée côté client. Le traçage a un coût : il ne doit
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
| **M1** | **Test apparié des signes** sur les différences entre bras, 200 cycles, seuil corrigé pour le nombre de comparaisons effectivement faites. Non significatif ⇒ l'effet est sous le seuil détectable, **ce qui n'est pas une absence d'effet**. Rapportez la médiane des différences appariées et son intervalle bootstrap. |
| **M2** | **La règle qui porte la thèse du dossier.** Comparez la médiane des différences appariées **wildcard contre 9** chez MongoDB à la même quantité chez HCD, toutes deux en proportion de leur propre médiane de base. Si les deux moteurs répondent au nombre de structures dans le même sens et le même ordre de grandeur relatif, **le coût mesuré est celui de l'indexation et non de la décomposition**, et l'affirmation centrale du dossier change de nature. Si MongoDB ne répond pas alors que HCD répond, la décomposition redevient l'explication. **Cette comparaison croisée n'est licite que si les deux campagnes ont tourné avec la même série, le même fond et le même nombre de cycles** — c'est la raison de leur appariement. |
| **M3** | Contrôle de lecture de même taille **dans le même cycle apparié**, les trois bras. S'il croît à moins de 20 % de la croissance de l'update, ce bras est INCONCLUSIF par la règle de contrôle de la campagne. |
| **M4** | Moins de 25 observations sur 30 achevées ⇒ le point est FAILED, pas résumé. |
| **M5** | *Retirée.* Cette règle était héritée du design HCD, où un SAI se construit en arrière-plan. `createIndex` est synchrone côté pilote MongoDB : il rend la main quand l'index est construit. La conserver aurait suggéré un risque qui n'existe pas ici. |

**M2 a trois issues et les trois se publient.** Aucune n'est un échec.

---

## 5 · La table ne doit pas contenir une seule ligne

**C'est le défaut que toutes les campagnes de ce dossier partagent et qu'aucune n'avait nommé.** Un
index sur une collection d'un document est une structure triviale : ni fusion, ni contention.

Chargez **cent mille documents de fond** de forme identique et de contenu aléatoire, puis mutez un
document désigné. Le chargement n'est pas chronométré. Enregistrez le nombre de documents et la
taille des index après chargement.

À 128 Ko par document, cent mille documents feraient 12,8 Gio par membre — impossible dans un
conteneur de 8 Gio. **Chargez le fond à taille fixe et modeste** : **4 Ko par document, cent mille
documents, soit 400 Mio** — exactement le fond du design HCD, pour la même raison que la série : un
facteur de croissance obtenu sur un fond de 400 Mio ne se compare pas à un facteur obtenu sur un
fond dix-huit fois plus gros. Cela tient dans le cache de production de 3,5 Gio, qui est la
configuration imposée à la question A par le §2.3 — et cela ne tiendrait pas dans les 256 Mio de la
question B, ce qui est la raison de la séquence.

Seule la taille du **document muté** varie. C'est le contenu indexé de la ligne mutée qui est la
variable ; le fond n'est là que pour donner aux index une structure non triviale.

---

## 6 · Livrable

Deux fichiers, et rien d'autre à modifier sur la machine :
`/tmp/findings_mongo_regime_v2.json` pour la question B, `/tmp/findings_mongo_structures.json` pour
la question A. **Ne committez pas depuis alphadebunker.**

Chacun doit porter : les mesures ; la taille de cache configurée, relevée et non supposée ; la liste
des index de chaque bras et leur temps de construction ; le nombre de documents de fond ; la charge
avant chaque triplet ; et les verdicts tels que la sonde les a calculés.

**Rapport en trois lignes par question, sans interprétation** : les verdicts, la dérive de charge,
ce qui a divergé du plan.

**Ne concluez pas à la place du dossier.** Si M3 se déclenche, c'est une issue prévue. Si l'éviction
échoue encore malgré 256 Mio, c'est un résultat et il se rapporte tel quel.

---

## 7 · Limites, déclarées d'avance

- **L'effet d'index et l'effet de cache ne sont pas séparés.** Le bras à neuf structures occupe
  plus de mémoire que celui à une, donc une partie de l'écart mesuré peut venir de ce que ses
  données de base sont moins résidentes, et non de l'écriture des index. Les compteurs de
  stockage et de cache sont relevés par bloc pour que le lecteur en juge, mais le design ne les
  distingue pas.
- **Un cache de 256 Mio n'est pas une production.** Les chiffres en cache de la question B ne sont
  comparables qu'entre eux, jamais aux campagnes précédentes à 3,5 Gio.
- **Les deux questions ne sont pas comparables entre elles.** Elles tournent sous des caches
  différents par construction — 256 Mio contre 3,5 Gio — et c'est la condition de leur validité
  respective. Ne croisez jamais un chiffre de l'une avec un chiffre de l'autre.
- **Le bras `wildcard` et les bras à index simples ne couvrent pas le contenu de la même façon.**
  Un wildcard indexe tous les champs par une structure unique ; neuf index simples indexent les
  mêmes champs par neuf structures. Le contenu couvert est apparié, la façon de le couvrir non.
  C'est le confondant résiduel de la question A et il n'est pas supprimable.
- **Neuf index simples ne sont pas les neuf SAI de HCD**, qui portent sur des cibles de natures
  différentes — `entries(map)`, `values(set)`, tailles de tableau. La comparaison inter-moteurs de
  M2 porte sur la **forme de la réponse au nombre**, pas sur des coûts absolus comparables.
- **Le fond est à taille fixe**, seule la ligne mutée varie. C'est ce qui permet de tenir cent mille
  documents dans la mémoire disponible, et cela signifie que l'index de fond ne grandit pas avec la
  série.
- **Client unique séquentiel en boucle fermée.** Les percentiles sont des temps de service à
  utilisation négligeable, pas des queues sous charge.
- **Hôte partagé, charge dérivante** — la plus forte des trois campagnes du 19 septembre, d'où
  l'entrelacement, qui atténue sans supprimer.
- **`pymongo` n'était épinglé nulle part** — lacune que le dossier s'attribue sous D-ENV-1. Relevez
  la version résolue et inscrivez-la dans l'enregistrement.
- **Rien ici ne touche `mongot`** ni l'axe de fraîcheur de recherche. Sa réserve d'édition
  `localDev` reste entière et demande un déploiement de recherche de production, qui n'existe pas
  sur cette machine.
