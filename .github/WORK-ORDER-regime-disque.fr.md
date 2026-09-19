# Ordre de travail — agent Claude Code sur alphadebunker

**Objet.** Fermer les deux comparaisons que `data/derived/inference.json` marque `UNDETERMINABLE`
dans le dépôt `shredding-cost-hcd-mongodb`. Ce sont celles qui portent l'affirmation architecturale
la plus forte du dossier, et leurs enregistrements n'ont gardé qu'une médiane.

**Où vous lisez ceci.** Ce fichier est versionné dans le dépôt, à
`.github/WORK-ORDER-regime-disque.fr.md`. Un `git pull` dans le clone d'alphadebunker suffit à
l'obtenir, avec la sonde et tout ce qu'il référence. Ne travaillez pas depuis une copie collée.

**État en amont.** Le dépôt est à jour côté GitHub (`419c120`, tag `v1.0-arxiv`). La sonde
`probes/disk_regime_rerun.py` y est poussée, compile, et **n'a pas tourné**.

---

## 1 · Ce qui bloque, et pourquoi la sonde telle quelle ne peut pas partir

Trois constats, établis sur la machine :

- `nodetool status` : deux datacentres. **dc1** = `p16-hcd-node1..3`, 12,6 Gio par nœud, porte les
  données. **dc2** = `node4..6`, 218 Mio. La sonde vide les bons nœuds ; la topologie ne pose pas de
  problème.
- **Aucun keyspace de la Data API n'existe** — ni `default_keyspace`, ni `cmp`, ni `data_api` parmi
  les 36 keyspaces présents.
- `SELECT count(*) FROM system_schema.indexes` rend **101**. Le garde-fou HCD refuse la création
  au-delà de **100 index SAI par nœud**, toutes keyspaces confondues — c'est une contrainte que ce
  dossier a lui-même mesurée et publiée.

Conséquence : `db.create_collection()` créerait neuf index SAI automatiques et **serait refusée**.
La sonde échouerait à sa première ligne utile.

**Règle absolue : ne supprimez aucun index, aucune table, aucun keyspace existant.** La machine est
partagée et porte 36 keyspaces de travail. Libérer de la place pour faire tourner une mesure
changerait l'état d'un système qui ne vous appartient pas, et invaliderait au passage toute autre
mesure en cours. Le contournement est ailleurs.

---

## 2 · Ce qu'il faut vérifier avant de décider

Deux commandes. Elles qualifient le 101, qui peut compter des index non-SAI que le garde-fou ignore.

```bash
docker exec p16-hcd-node1 cqlsh -e \
  "SELECT keyspace_name, kind, count(*) FROM system_schema.indexes GROUP BY keyspace_name, kind;"

docker exec p16-hcd-node1 nodetool getguardrailsconfig 2>/dev/null | grep -i sai || \
  docker exec p16-hcd-node1 grep -i -A2 'sai_indexes_total' /opt/hcd/resources/cassandra/conf/cassandra.yaml
```

**Si le compte de SAI est nettement sous 100** — par exemple si l'essentiel des 101 sont des index
`COMPOSITES` hérités — alors le garde-fou n'est pas atteint : lancez la sonde telle quelle, passez
au §4, et ignorez le §3.

**Si le compte de SAI est à 100 ou proche** — passez au §3.

---

## 3 · La variante CQL, si le garde-fou bloque

### Ce qu'elle change, et ce qu'il faut déclarer

La sonde mesure le coût de mutation de HCD dans **deux régimes** : lecture-modification-écriture
avec la ligne en memtable, puis la même avec un `nodetool flush` avant chaque cycle, ce qui force la
lecture interne sur SSTable.

Ce mécanisme est une propriété du **moteur de stockage**, pas de la Data API. Mesurer en CQL natif
plutôt qu'à travers l'interface est donc légitime, et arguablement plus propre. Mais cela change
l'objet mesuré, et **ce changement doit être écrit dans l'enregistrement**, pas laissé implicite :

> Ce qui est mesuré : le coût de régime du moteur. Ce qui ne l'est pas : le chemin Data API, dont la
> part n'est pas isolée ici et ne l'est nulle part dans ce dossier.

### Le contrat de la variante

Partez de `probes/disk_regime_rerun.py` et modifiez le strict nécessaire. **Ne réécrivez pas la
sonde.** Ce qui suit doit être préservé à l'identique :

1. **Le helper `dist()`**, qui émet `min_ms` **et** `raw_ms`. C'est la raison d'être de cette sonde :
   le helper `dist()` de `probes/rmw_postflush.py`, partagé par les autres sondes émet `n / p50 / p95 / p99 / max / stdev` et jette
   le minimum et la série, ce qui rend la séparation des supports incalculable. Vingt-trois
   enregistrements sur vingt-cinq sont perdus pour cette raison. Ne l'appelez pas, ne le réintroduisez
   pas, et ne « simplifiez » pas `dist()`.
2. **Les règles R1 à R4**, telles qu'écrites dans la docstring. Elles sont pré-enregistrées.
   Ne les ajustez pas après avoir vu les chiffres — c'est le seul point sur lequel ce dossier n'a
   jamais transigé.
3. **`host_fingerprint()`**, et la charge moyenne au début **et** à la fin.
4. **Les limites déclarées** dans le bloc `not_met`, auxquelles vous ajoutez celle du §3 ci-dessus.

### Ce qui change

- Remplacer le client `astrapy` par `cassandra-driver` — épinglé à **3.30.1** dans
  `env/requirements.txt`. **Prenez `probes/hcd_cql_arm.py` comme modèle de connexion** : c'est le bras
  CQL direct de la campagne comparative, il ouvre le `Cluster` avec le bon `auth_provider` et le bon
  port, et sa forme d'update est exactement celle que le §3 vous demande de préserver.
- Créer un keyspace jetable, `NetworkTopologyStrategy` avec `dc1: 3` **et rien sur dc2** — inutile de
  répliquer vers un datacentre que la mesure ne lit jamais. Nom suggéré : `regime_<hex>`, supprimé
  dans le `finally`.
- Une table : `CREATE TABLE t (id text PRIMARY KEY, status text, ballast map<text,text>)`, ou
  colonnes texte séparées si cela vous paraît plus fidèle à la décomposition. **Aucun index** :
  le garde-fou n'est pas sollicité et la mesure porte sur le chemin de mutation, pas sur la
  maintenance d'index.
- La mutation sous test devient un `UPDATE t SET status=? WHERE id=?` **exécuté en `LOCAL_QUORUM`**,
  précédé du `SELECT` que la sonde chronomètre séparément comme contrôle R3.

  ⚠️ **Point de méthode, à ne pas manquer.** Les sondes du dossier émettent toutes des updates
  *conditionnels* — donc un round Paxos à chaque mutation. Si vous écrivez un `UPDATE` simple, vous
  mesurez autre chose que M10 et M15, et la comparaison aux ×5,94 et ×1,52 publiés devient invalide.
  Soit vous conservez la forme conditionnelle (`IF EXISTS` ou `IF status = ?`), soit vous mesurez les
  **deux formes** et vous le dites — cette seconde option fermerait au passage la menace **C1-bis** du
  registre (`docs/THREATS-TO-VALIDITY.md`, ligne 120), qui dit en toutes lettres : « *no probe in this
  repository ever issues a non-conditional HCD update* », et que « *the measurement that would close
  it — a non-conditional HCD update arm — was never run* ». Un bras non conditionnel, mesuré ici en
  passant, fermerait une menace ⭑⭑ du registre. **C'est de loin le meilleur rendement de toute
  l'opération, si la fenêtre de temps le permet.**

- Le flush reste `docker exec p16-hcd-node{1,2,3} nodetool flush <keyspace>`, **non chronométré**, sur
  les trois nœuds de dc1 seulement.

---

## 4 · Exécution

**Avant de lancer :**

```bash
uptime      # la campagne d'origine tournait à 14–16 de charge moyenne
```

À 14–16, c'est le bon régime : lancez. Nettement au-dessus, décalez plutôt que de mesurer et
d'expliquer ensuite.

```bash
cd ~/shredding-cost-hcd-mongodb && git pull

export DATA_API_ENDPOINT=http://127.0.0.1:8181     # variante Data API seulement
export ASTRA_DB_USERNAME=... ASTRA_DB_PASSWORD=...

python3 probes/disk_regime_rerun.py > /tmp/findings_disk_regime_rerun.json
```

**Comptez une heure.** Quatre tailles, trente-cinq répétitions par bras, deux flushs non chronométrés
par cycle sur le bras SSTable. La progression sort sur `stderr`.

**Si la sonde échoue à mi-parcours, reprenez à zéro.** Ne reprenez pas au milieu : les warm-ups ne
seraient plus comparables entre tailles, et le fichier serait inexploitable sans que rien ne le
signale.

---

## 5 · Ce qu'il faut rendre

Un fichier JSON, et rien d'autre à modifier sur la machine.

```bash
python3 -c "import json; d=json.load(open('/tmp/findings_disk_regime_rerun.json')); \
  print('arms:', list(d['result']['arms'])); print('verdicts:', d['result']['verdicts'])"
```

Puis rapatriement sur le MacBook — **ne committez pas depuis alphadebunker.**

**Rapport attendu**, en trois lignes et sans interprétation :

1. Les verdicts R1 à R4 tels que la sonde les a calculés, sans les commenter.
2. La charge moyenne au début et à la fin.
3. Tout ce qui a divergé du plan : une taille en `FAILED`, un flush qui a échoué, un timeout.

**Ne concluez pas à la place du dossier.** Si R3 se déclenche — contrôle de lecture à moins de 20 %
de la croissance de l'update — le résultat est `INCONCLUSIF` par la règle de contrôle de la campagne
elle-même, celle qui a invalidé la variante A de M3. C'est une issue acceptable et prévue ; ce n'est
pas un échec à corriger en ajustant quoi que ce soit.

---

## 6 · Ce que cette mesure ne lèvera pas

À déclarer dans l'enregistrement, pas à découvrir après :

- **Pas de root**, donc pas de vidage du cache de pages. Les SSTables fraîchement écrites sont petites
  et chaudes : on exerce le chemin de lecture SSTable, pas des déplacements de tête. Cette limite est
  héritée de `probes/rmw_postflush.py` et n'est pas réparée ici.
- **Client unique séquentiel**, en boucle fermée, comme partout dans ce dossier. Les percentiles sont
  des percentiles de temps de service à utilisation négligeable, pas des queues sous charge.
- **Un hôte, partagé, sous charge de fond non contrôlée.** D'où l'enregistrement de la charge au début
  et à la fin : pour que la dérive soit lisible plutôt que supposée.

---

## 7 · Une seconde campagne, indépendante — le bras MongoDB hors cache

**À ne lancer qu'après la première**, et seulement si elle s'est bien passée. Les deux mesures sont
indépendantes ; les enchaîner dans la même session ne gagne rien et brouille les deux.

`probes/mongo_regime_rerun.py` ferme une asymétrie que le dossier porte depuis le début :
**le moteur décomposant a été mesuré dans trois régimes, le comparateur dans un seul.** Tous les
enregistrements MongoDB de `data/raw/` sont en cache. La conclusion « le coefficient est un artefact
de régime » s'appuie donc sur un moteur mesuré trois fois et un moteur mesuré une fois.

Trois issues sont ouvertes, et **la troisième n'est pas exclue** :

- MongoDB se dégrade autant hors cache → l'écart de 3 à 13 fois se réduit, et l'axe mutation doit
  être réénoncé avec son régime ;
- il se dégrade moins → l'écart s'élargit et le constat du dossier se renforce sur une preuve qu'il
  n'a pas aujourd'hui ;
- il se dégrade davantage → **la direction pourrait s'inverser à certaines tailles**.

```bash
export MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"
python3 probes/mongo_regime_rerun.py > /tmp/findings_mongo_regime.json
```

**Vérifiez d'abord que le replica set est debout** — il n'a pas tourné depuis la campagne
comparative : `docker ps --format '{{.Names}}' | grep mongo`. Sinon,
`env/docker-compose.mongodb-rs.yml` le reconstruit, et `REPRODUCING.md` dit ce que ce fichier fixe et
ce qu'il devine.

**Le point délicat, et il est déclaré dans la sonde.** Il n'existe aucun moyen supporté de vider le
cache WiredTiger sans redémarrer `mongod`, ce qui changerait plus que le cache. La sonde utilise donc
une pression de ballast — une collection de plusieurs fois la taille du cache, lue de bout en bout —
et **vérifie l'éviction bras par bras** en lisant le compteur `pages read into cache`. Un bras où ce
compteur ne bouge pas est enregistré `NOT_EVICTED` et **n'est pas rapporté**. Ne contournez pas ce
garde-fou : un bras non évincé qui serait rapporté comme évincé serait le pire résultat possible de
toute l'opération.

**Ce qui compte pour la comparaison, c'est la règle R2** : le rapport des *facteurs de croissance*,
pas des latences. Si MongoDB croît à moins de 20 % de HCD, l'expression « artefact de régime » vaut
pour les deux moteurs et doit être réénoncée comme une propriété du stockage en général, pas de la
décomposition. **Cette mesure-là doit être prise sur le même hôte que la première**, sans quoi le
rapport mélange moteur et matériel.

---

## 7 · Le critère de succès, et il est objectif

Après rapatriement et ajout au manifeste, sur le MacBook :

```bash
python3 .github/scripts/check_inference.py
```

Il rend aujourd'hui `3 not decidable from summary statistics`. **Il doit en rendre moins.** C'est la
mesure du succès de la première campagne, et elle ne dépend d'aucune appréciation.

Pour la seconde, le critère est différent et tout aussi objectif : `docs/THREATS-TO-VALIDITY.md`
porte la menace **L10** à deux étoiles, qui dit que le comparateur n'a jamais été mesuré hors cache.
Un enregistrement dont aucun bras ne porte `NOT_EVICTED` la ferme.
