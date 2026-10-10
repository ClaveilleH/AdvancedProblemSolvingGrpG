# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Projet de groupe (groupe G) du cours Advanced Problem Solving : résolution du problème Google Hash Code 2017 « Streaming Videos » (placer des vidéos dans des caches de capacité limitée pour minimiser la latence des requêtes). L'énoncé est dans `docs/consignes/`. Le code, les commentaires et les messages de commit sont en français.

Python pur, sans dépendance pour les algos. `numpy` est requis par `trap_generate.py`, `matplotlib` et `numpy` par les graphiques de `metrics/`. Il n'y a ni tests, ni linter, ni build.

## Commandes

Tout se lance depuis la racine du dépôt, avec des chemins en `/` (le code découpe les chemins sur `/`, même sous Windows).

```bash
python main.py instances/me_at_the_zoo.in   # une instance, affichage détaillé par algo
python main.py all                          # toutes les instances de la promo (INSTANCES_FILES)
python main.py google                       # les 4 instances Google
python main.py                              # INSTANCES_FILES[0] (test.in)
```

- `all` et `google` passent `PRINT` à `False` : seule la meilleure méthode par instance est affichée et écrite dans `results/results_summary.txt`.
- `results/results_summary.txt` sert de reprise : toute instance déjà listée dedans est sautée. Pour relancer une instance, supprimer sa ligne. Le fichier doit exister (il est ouvert en lecture avant d'être complété).
- Les solutions sont écrites dans `results/<instance>.out` (ignoré par git, sauf le résumé déjà suivi).
- Les algos lancés se règlent par les constantes en tête de `main.py` (`KNAPSACK`, `TEST_LOCAL_SEARCH`, `BEST_OF_GREEDY`) et par les `partial(...)` qui fixent les paramètres de la recherche locale.

Outils annexes :

```bash
python metrics/metrics.py instances/kittens.in                 # caractéristiques d'une instance + borne supérieure du score
python -m metrics.mesure_metrics -i instances/kittens.in -o results/kittens.out --no-plots   # stats d'une solution
python -m metrics.mesure_metrics -i instances/kittens.in -o results/kittens.out -s out/kittens   # + images PNG
python trap_generate.py nom --caches 200 --capacity 500 --seed 1   # instance piège pour gloutons, optimum connu, dans instances/generated/
g++ -O2 -o judge/jugeCorrige judge/jugeCorrige.cpp && ./judge/jugeCorrige instances/x.in results/x.out   # juge officiel du cours
```

Bench de l'oral (dossier `bench/`, ajouté sans modifier les fichiers existants) :

```bash
python -m bench.features all                 # caractéristiques d'instances -> bench/data/features.csv
python -m bench.run all --timeout 300        # chaque algo sur chaque instance -> bench/data/runs.csv
python -m bench.run kittens --grid           # voisinage des tabu search -> bench/data/grid.csv
python -m bench.solution_stats all           # placements inutiles -> bench/data/solutions.csv
python -m bench.plots                        # figures de l'oral -> docs/oral/figures/
python -m bench.run all --algos LS_fix TS_fix TSS_fix   # exploration -> bench/data/exploration/runs_fix.csv
python -m bench.plots_exploration            # figures d'exploration -> docs/exploration/figures/
```

`bench.run` reprend là où il s'est arrêté (`--force` pour repartir de zéro), lance chaque exécution dans son propre processus et, à la limite de temps, évalue l'état courant des caches. Il compte les branches du knapsack en enveloppant les fonctions de `knapsack_slay` à l'exécution.

**Séparation stricte entre le travail du groupe et l'exploration.** Le diaporama et l'oral portent exclusivement sur les algos du groupe, non modifiés. Tout ce qui vient d'une modification proposée par Claude (versions corrigées de `bench/fixes.py`, colonne `score_best`, force brute complétée par Claude dans `algos/brute_force.py`) va dans `bench/data/exploration/` et `docs/exploration/`, jamais dans `bench/data/*.csv`, `docs/oral/` ni `bench/plots.py`. Ces éléments servent à discuter des améliorations possibles, pas à l'oral.

`mesure_metrics` doit être lancé avec `-m` (il importe `metrics.plot_metrics`). Les binaires présents dans `judge/` sont des ELF Linux : à recompiler ou à lancer sous WSL. `metrics/solution_metric.py` (et sa copie) ne s'exécute pas en l'état (fonction `metrics_sol` vide).

## Architecture

`main.py` orchestre tout pour une instance : lecture (`utils.read_input_file`), exécution des trois gloutons, du knapsack depuis des caches vides, puis des recherches locales depuis le meilleur glouton, et renvoie **uniquement la meilleure méthode**. Les scores et temps des autres algos ne sont conservés nulle part, seulement affichés quand `PRINT` vaut `True`.

### Contrat commun des algos (`algos/`)

Chaque algo a la signature `algo(data, caches, caches_sizes)` et **modifie `caches` et `caches_sizes` en place** ; `main.run()` ignore la valeur de retour, puis évalue l'état avec `utils.snapshot`.

- `data` est le dictionnaire construit dans `main.main()`. Plusieurs clés sont des alias (`N_request`/`N_requests`, `S_cache`/`cache_size`) car les algos n'utilisent pas tous le même nom.
- `endpoints[e] = (latence_datacenter, [(cache_id, latence), ...])`, `requests[r] = (video_id, endpoint_id, nb_requêtes)`, `adj_list[v]` = indices des requêtes portant sur la vidéo `v`.
- `caches[c]` est une `list` ou un `set` de vidéos selon l'algo : `run()` reçoit le type de conteneur attendu en paramètre (`list` pour gloutons, knapsack et `local_search`, `set` pour les deux tabu search).
- Réaffecter `caches = ...` dans un algo n'a aucun effet pour l'appelant. C'est le cas à la fin de `random_tabu_search` et `sorted_tabu_search` : la meilleure solution rencontrée (`best_caches`) est perdue et c'est le dernier état visité qui est évalué.

### Les algos

- `greedy.py` : par requête, triées par nombre de requêtes décroissant, place la vidéo dans le cache le plus rapide qui a la place.
- `greedy2.py` : par vidéo, triées par popularité, place dans le cache relié au plus grand nombre d'endpoints demandeurs.
- `greedy3.py` : par cache, parcourt ses endpoints par gain de latence décroissant.
- `knapsack_slay.py` : version utilisée (`multiknapsack_bg` importé sous le nom `multi_knapsack`). Un sac à dos par cache, traités du plus prometteur au moins prometteur ; après chaque cache, la valeur des vidéos placées est diminuée dans les caches voisins. Choisit entre la DP indexée sur le poids et la DP indexée sur la valeur selon la plus petite table, et **se rabat sur un glouton par densité** quand capacité et somme des valeurs dépassent toutes deux `LIMIT = 10000`. Poids et valeurs sont réduits par leur pgcd. En Python pur, la DP ne termine pas en temps raisonnable sur les plus grosses instances.
- `knapsack.py` : ancienne version, plus importée.
- `local_search.py` : `local_search` (descente récursive, ajouts et suppressions), `random_tabu_search` (voisinage tiré au hasard, sans graine fixée, donc non reproductible) et `sorted_tabu_search`. Le voisinage est borné par `nbCaches` et `nbVideos` : `local_search` et `sorted_tabu_search` ne regardent que les `nbCaches` **premiers** caches. Les deltas sont calculés par `utils.calculate_video_latency`, qui ne réévalue que les requêtes de la vidéo concernée.

### Coût et score

`utils.compute_cost` est la latence totale (à minimiser), `utils.compute_score` est le score Hash Code (gain moyen par requête × 1000, tronqué), à maximiser. Les gains affichés en % sont relatifs au coût sans aucun cache (`base_cost`).

`metrics/mesure_metrics.py` redéfinit son propre parseur et sa propre structure (`Problem`, `Endpoint`), indépendants de `utils.py` : les deux représentations ne sont pas interchangeables.

### Données

- `instances/` : les 4 instances Google, les instances proposées par les groupes de la promo, et des instances maison. Certaines entrées de `INSTANCES_FILES` n'ont pas de fichier dans le dépôt (`dense2.in`).
- `docs/exel/backup_*/` : export du Google Sheet de la promo (scores de chaque groupe par instance, colonne `VBS` = meilleur score connu). Le groupe est la colonne **G**. Le CSV contient deux tableaux empilés (instances Google puis instances de la promo) et, à droite, le classement Hash Code officiel sur ~2800 lignes.
- `docs/oral/` : consignes de la soutenance, plan et script (`diapo.md`), diaporama Beamer (`diapo.tex`), figures. Le diaporama doit rester éditable à la main (LaTeX, pas de solution web). Pour le code existant du groupe : proposer les corrections, ne pas les appliquer sans accord.
