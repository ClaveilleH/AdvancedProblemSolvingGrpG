# Exploration — pistes d'amélioration (hors oral)

Ce dossier contient ce qui ne va pas dans le diaporama : la force brute et les corrections qui restent à l'état de proposition.

La force brute et les optimums qu'elle donne ne sont pas évoqués à l'oral : les autres groupes ne semblent pas avoir vu que les instances jouets se résolvent exactement.

Archives, dans `bench/data/exploration/` :

| Fichier | Contenu |
|---|---|
| `runs_avant_correction.csv`, `grid_avant_correction.csv` | mesures de la recherche locale avant les corrections du 10/10 |
| `runs_fix.csv` | mesures des versions d'essai des corrections, faites avant de les appliquer ; identiques, ligne à ligne, aux mesures du code corrigé |

## 1. Corrections

| # | Fichier | Problème | Correction | État |
|---|---|---|---|---|
| 1 | `algos/local_search.py`, `random_tabu_search` et `sorted_tabu_search` | `caches = best_caches` ne modifiait pas la liste de l'appelant : c'était le dernier état visité qui était évalué | `restore_best` remet la meilleure solution dans la liste et recalcule les tailles | **appliquée le 10/10** |
| 2 | `algos/local_search.py`, `random_tabu_search` | aucune graine | paramètre optionnel `seed` | **appliquée le 10/10** |
| 3 | `algos/local_search.py`, `local_search` | le meilleur voisin est appliqué même s'il dégrade, et l'état final était rendu | la meilleure solution rencontrée est gardée au fil des appels et remise à la fin | **appliquée le 10/10** |
| 4 | `algos/local_search.py`, `local_search` | `caches_sizes[caches.index(cache)]` renvoie le premier cache de même contenu, pas forcément le bon | `caches_sizes[cache_id]` | proposée |
| 5 | `algos/knapsack_slay.py`, `multiknapsack` | dès qu'un cache dépasse les deux limites, la fonction s'arrête pour tous les caches (score 0 sur 7 instances) | même repli glouton que `multiknapsack_bg` | proposée |
| 6 | `algos/knapsack_slay.py`, `knapsack_goulton` | renvoie un sac vide s'il y a plus de 10 000 objets, alors qu'un tri suffit | supprimer ce test | proposée |
| 7 | `algos/brute_force.py`, `is_brute_force_applicable` | le critère `N_vid * N_cache` ne mesure pas le nombre de solutions | compter les contenus possibles par cache, comme le fait `brute_force` | proposée |

`main.py` n'utilise pas le paramètre `seed` : par défaut, le tabou aléatoire reste donc non reproductible.

## 2. Recherche locale, avant et après les corrections 1 à 3

Les résultats sont dans `docs/oral/diapo.md`. Sur les 33 instances :

| | Dégradées | Inchangées | Améliorées |
|---|---|---|---|
| Descente, avant | 9 | 10 | 14 |
| Descente, après | 0 | 18 | 15 |
| Tabou aléatoire, avant (moyenne de 10 graines) | 15 | 5 | 13 |
| Tabou aléatoire, après | 0 | 16 | 17 |
| Tabou trié, avant | 10 | 11 | 12 |
| Tabou trié, après | 0 | 17 | 16 |

## 3. Instances jouets : optimum par force brute

La force brute énumère, pour chaque cache, les ensembles maximaux de vidéos utiles, puis teste toutes les combinaisons.

| Instance | Solutions testées | Optimum | Meilleur de la promo (VBS) | Nos algos constructifs | Tabou trié |
|---|---|---|---|---|---|
| `2_2_2_1` | 2 | 951 327 | 951 327 | 951 327 | 951 327 |
| `4_2_4_2` | 6 | 982 271 | 671 392 | 655 321 | 982 271 |
| `6_2_6_2` | 20 | 998 499 | 832 174 | 499 524 | 998 499 |
| `8_2_8_2` | 70 | 991 480 | 857 014 | 567 228 | 991 480 |
| `20_2_20_2` | 184 756 | 995 902 | 524 928 | 524 928 | 524 928 |

- Sur `4_2_4_2`, `6_2_6_2` et `8_2_8_2`, le tabou trié atteint l'optimum depuis la correction 1.
- `20_2_20_2` demande de monter `NB_TESTS_THRESHOLD` à 1 000 000 (1,7 s).
- Ces scores viennent de notre `compute_score`. À valider avec le juge officiel avant de les reporter dans le Sheet.

Pourquoi les algos constructifs échouent sur ces instances :

- `2_2_2_1` piège le tri par gain/taille : la petite vidéo (taille 1, 451 requêtes) passe juste devant la grosse (taille 20, 9 000 requêtes), qui ne rentre plus. Nos gloutons 1 et 2 et nos knapsacks ne tombent pas dedans.
- `4_2_4_2`, `6_2_6_2`, `8_2_8_2` piègent tout algo qui remplit les caches un par un : un endpoint voit les deux caches (1 ms et 2 ms), l'autre ne voit que le cache 0. Glouton et knapsack donnent le cache 0 au premier, qui n'y gagne qu'une milliseconde, et l'autre endpoint n'a plus rien.

## 4. Pistes à discuter

- Lancer la recherche locale **depuis le knapsack** plutôt que depuis le meilleur glouton : c'est là que le déplacement de vidéos entre caches peut rapporter.
- Utiliser la force brute dans `main.py` sur les instances assez petites.
- Accélérer la DP du knapsack (numpy ou autre langage) : 39 % des caches ne sont pas traités en 300 s.
- Corriger `multiknapsack` (correction 5) pour que la comparaison avec et sans mise à jour porte sur toutes les instances.
