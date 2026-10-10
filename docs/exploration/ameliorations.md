# Exploration — pistes d'amélioration (hors oral)

Ce dossier contient ce qui ne relève pas de nos algos tels quels : les corrections proposées par Claude, leurs mesures, et la force brute. **Rien d'ici ne va dans le diaporama ni dans l'oral.** Ça sert à discuter de ce qu'on pourrait améliorer.

En particulier, la force brute et les optimums qu'elle donne ne sont pas évoqués à l'oral : les autres groupes ne semblent pas avoir vu que les instances jouets se résolvent exactement.

Où sont les choses :

| Quoi | Où |
|---|---|
| Versions corrigées des recherches locales (enveloppes, `algos/local_search.py` n'est pas modifié) | `bench/fixes.py` |
| Mesures des versions corrigées | `bench/data/exploration/runs_fix.csv` |
| Figures | `docs/exploration/figures/`, par `python -m bench.plots_exploration` |
| Force brute (complétée par Claude à la demande) | `algos/brute_force.py` |

## 1. Corrections proposées (non appliquées à notre code)

| # | Fichier | Problème | Correction proposée |
|---|---|---|---|
| 1 | `algos/local_search.py`, fin de `random_tabu_search` et `sorted_tabu_search` | `caches = best_caches` ne modifie pas la liste de l'appelant : c'est le dernier état visité qui est évalué, pas le meilleur | `caches[:] = best_caches`, puis recalculer `caches_sizes` |
| 2 | `algos/local_search.py`, `random_tabu_search` | aucune graine : résultats non reproductibles | paramètre `seed` et `random.seed(seed)` |
| 3 | `algos/local_search.py`, `local_search` | le meilleur voisin est appliqué même s'il dégrade, et c'est l'état final qui est rendu | garder et rendre la meilleure solution rencontrée (ne pas s'arrêter au premier mouvement sans gain : un retrait à gain nul libère la place d'un ajout qui rapporte) |
| 4 | `algos/local_search.py`, `local_search` | `caches_sizes[caches.index(cache)]` renvoie le premier cache de même contenu, pas forcément le bon | `caches_sizes[cache_id]` |
| 5 | `algos/knapsack_slay.py`, `multiknapsack` | dès qu'un cache dépasse les deux limites, la fonction s'arrête pour tous les caches (score 0 sur 7 instances) | même repli glouton que `multiknapsack_bg` |
| 6 | `algos/knapsack_slay.py`, `knapsack_goulton` | renvoie un sac vide s'il y a plus de 10 000 objets, alors qu'un tri suffit | supprimer ce test |
| 7 | `algos/brute_force.py`, `is_brute_force_applicable` | le critère `N_vid * N_cache` ne mesure pas le nombre de solutions (`me_at_the_zoo` passerait pour faisable) | compter les contenus possibles par cache, comme le fait maintenant `brute_force` |

Les corrections 1 à 3 sont mesurées ci-dessous. Les autres ne le sont pas.

## 2. Recherche locale, avant et après les corrections 1 à 3

Mêmes paramètres que `main.py`, mêmes graines, même glouton de départ. Sur les 33 instances :

| | Dégradées | Inchangées | Améliorées |
|---|---|---|---|
| Descente, avant | 9 | 10 | 14 |
| Descente, après | LS_DEG | LS_SAME | LS_UP |
| Tabou aléatoire, avant | 15 | 5 | 13 |
| Tabou aléatoire, après | 0 | 16 | 17 |
| Tabou trié, avant | 10 | 11 | 12 |
| Tabou trié, après | 0 | 17 | 16 |

- Après correction, plus aucune instance n'est dégradée par le tabou.
- Hors instances jouets, les gains restent petits avec le voisinage par défaut : +4,8 % au mieux (`4990_246_84901_50`), moins de 1,5 % ailleurs.
- La correction ne rend donc pas la recherche locale compétitive face au knapsack. Elle évite surtout de perdre des points.

Figure : `figures/recherche_locale_avant_apres.png`. La même étude du voisinage que pour l'oral, mais en gardant la meilleure solution rencontrée : `figures/voisinage.png`.

## 3. Instances jouets : optimum par force brute

La force brute énumère, pour chaque cache, les ensembles maximaux de vidéos utiles, puis teste toutes les combinaisons.

| Instance | Solutions testées | Optimum | Meilleur de la promo (VBS) | Nos algos constructifs | Tabou trié corrigé |
|---|---|---|---|---|---|
| `2_2_2_1` | 2 | 951 327 | 951 327 | 951 327 | 951 327 |
| `4_2_4_2` | 6 | 982 271 | 671 392 | 655 321 | 982 271 |
| `6_2_6_2` | 20 | 998 499 | 832 174 | 499 524 | 998 499 |
| `8_2_8_2` | 70 | 991 480 | 857 014 | 567 228 | 991 480 |
| `20_2_20_2` | 184 756 | 995 902 | 524 928 | 524 928 | 524 928 |

- Sur `4_2_4_2`, `6_2_6_2` et `8_2_8_2`, le tabou trié rencontre l'optimum pendant sa recherche mais ne le rend pas (correction 1).
- `20_2_20_2` demande de monter `NB_TESTS_THRESHOLD` à 1 000 000 (1,7 s).
- Ces scores viennent de notre `compute_score`. À valider avec le juge officiel avant de les reporter dans le Sheet.

Pourquoi les algos constructifs échouent sur ces instances :

- `2_2_2_1` piège le tri par gain/taille : la petite vidéo (taille 1, 451 requêtes) passe juste devant la grosse (taille 20, 9 000 requêtes), qui ne rentre plus. Nos gloutons 1 et 2 et nos knapsacks ne tombent pas dedans.
- `4_2_4_2`, `6_2_6_2`, `8_2_8_2` piègent tout algo qui remplit les caches un par un : un endpoint voit les deux caches (1 ms et 2 ms), l'autre ne voit que le cache 0. Glouton et knapsack donnent le cache 0 au premier, qui n'y gagne qu'une milliseconde, et l'autre endpoint n'a plus rien.

## 4. Pistes à discuter

- Appliquer les corrections 1 à 3 puis relancer la recherche locale **depuis le knapsack** plutôt que depuis le meilleur glouton : c'est là que le déplacement de vidéos entre caches peut rapporter.
- Utiliser la force brute dans `main.py` sur les instances assez petites.
- Accélérer la DP du knapsack (numpy ou autre langage) : 39 % des caches ne sont pas traités en 300 s.
- Corriger `multiknapsack` (correction 5) pour que la comparaison avec et sans mise à jour porte sur toutes les instances.
