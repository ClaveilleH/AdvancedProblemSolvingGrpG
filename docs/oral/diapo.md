# Oral — plan du diaporama et du script

Oral lundi 12/10/2026, 20 min : 2 min algo, 8 min évaluation expérimentale, 10 min de questions (voir `consignes.txt`).
Diaporama : `diapo.tex` (Beamer, éditable à la main). Figures : `figures/`, régénérées par `python -m bench.plots`.

## Ce qu'on veut dire (décidé le 10/10)

1. **Présenter nos algos**, rapidement, avec leurs particularités.
2. **Comparer les gloutons** sur les instances les plus intéressantes (graphique à colonnes) et chercher les raisons de leur efficacité ou inefficacité.
3. **Tabu search** : est-ce améliorable ou non ? (étude du voisinage et du nombre d'itérations)
4. **Knapsack** : deux hypothèses à explorer.
   - La mise à jour entre caches rapporte d'autant plus que les endpoints partagent des caches.
   - Le knapsack perd son avantage quand il se rabat sur le glouton.
   - Attention : il peut y avoir énormément de caches, donc pas de liste par cache. On donne des **statistiques** : X caches par telle branche, Y caches par telle autre.
5. **SWOT** (exigé par la consigne).

## Règles de travail avec Claude

- Autorisé : créer de nouveaux fichiers qui génèrent de la donnée en réutilisant les fonctions existantes (dossier `bench/`).
- Autorisé : proposer des modifications quand le code est faux. Les modifications sont proposées, pas appliquées.
- Le diaporama reste éditable à la main : LaTeX, pas de solution web.
- Pas de phrases toutes faites dans le script : seulement les grandes lignes.

## Protocole expérimental

| Élément | Choix |
|---|---|
| Machine | voir `bench/data/machine.txt` (écrit par le bench) |
| Instances | 4 Google + 29 de la promo ; les 5 instances jouets (2 à 20 vidéos) sont présentées à part |
| Algos | Glouton 1, 2, 3 ; knapsack indépendant ; knapsack avec mise à jour ; descente, tabou aléatoire, tabou trié (lancés depuis le meilleur glouton) |
| Limite | 300 s par exécution ; à la limite, on évalue l'état des caches à cet instant |
| Aléatoire | 10 graines pour le tabou aléatoire, 1 exécution pour les algos déterministes |
| Métriques | score, écart au meilleur score connu (VBS du Sheet) en %, temps, gain sur la solution de départ, taux de remplissage, branche du knapsack par cache |
| Référence | VBS = meilleur score de la promo par instance (export du Google Sheet) |

Commandes :

```bash
python -m bench.features all              # caractéristiques des instances
python -m bench.run all --timeout 300     # tous les algos, toutes les instances
python -m bench.run kittens --grid        # étude du voisinage des tabu search
python -m bench.solution_stats all        # placements inutiles, copies par vidéo
python -m bench.plots                     # figures de l'oral
```

## Diaporama (10 min, 12 diapos)

| # | Diapo | Contenu | Figure | Durée |
|---|---|---|---|---|
| 1 | Titre | groupe G, sujet | | 0:10 |
| 2 | Le problème | vidéos, caches, endpoints ; ce qu'on maximise | schéma de l'énoncé | 0:25 |
| 3 | Nos algos | tableau : idée et particularité de chacun | | 1:25 |
| 4 | Protocole | machine, instances, limite de temps, graines, métriques | | 0:50 |
| 5 | Vue d'ensemble | écart au VBS, algo × instance | `vue_ensemble` | 0:40 |
| 6 | Gloutons : résultats | colonnes sur les instances où ils diffèrent le plus | `gloutons` | 1:00 |
| 7 | Gloutons : pourquoi | causes liées aux caractéristiques d'instance | `capacite` | 0:50 |
| 8 | Recherche locale : constat | gain sur le départ ; état final contre meilleure solution | `recherche_locale` | 0:55 |
| 9 | Recherche locale : améliorable ? | voisinage et itérations | `voisinage` | 0:50 |
| 10 | Knapsack : quelle branche ? | part des caches par branche | `knapsack_branches` | 1:00 |
| 11 | Knapsack : mise à jour | gain selon le recouvrement des caches | `knapsack_maj` | 0:45 |
| 12 | SWOT et conclusion | tableau 2×2 | | 1:10 |

Diapos de secours pour les questions : compromis temps / qualité (`temps_qualite`), tableau complet des scores, détail des corrections proposées, complexité des deux DP.

## Script (grandes lignes)

**1–2. Problème** (0:35)
- Placer des vidéos dans des caches de capacité limitée.
- Score : latence moyenne économisée par requête.

**3. Algos** (1:25)
- Glouton 1 : par requête, les plus grosses d'abord, dans le cache le plus rapide qui a la place.
- Glouton 2 : par vidéo, les plus populaires d'abord, dans le cache vu par le plus d'endpoints demandeurs.
- Glouton 3 : par cache, endpoints par gain de latence décroissant.
- Knapsack indépendant : un sac à dos par cache, sans concertation, donc des doublons entre caches voisins.
- Knapsack avec mise à jour : caches traités du plus prometteur au moins prometteur, valeurs des vidéos déjà placées revues à la baisse chez les voisins.
- Deux DP exactes (indexée sur le poids ou sur la valeur), choix de la plus petite table, repli sur un glouton au-delà de 10 000.
- Recherche locale depuis le meilleur glouton : descente, tabou aléatoire, tabou trié. Mouvements : ajout ou retrait d'une vidéo.

**4. Protocole** (0:50)
- Une machine, une limite de temps identique, tout est rejouable par une commande.
- Pourquoi le VBS comme référence : pas d'optimum connu, la borne supérieure est trop lâche.
- Pourquoi 10 graines : le tabou aléatoire change de score d'une exécution à l'autre.

**5. Vue d'ensemble** (0:40)
- Qui gagne où, en une image.
- Annoncer les trois zooms : gloutons, recherche locale, knapsack.

**6–7. Gloutons** (1:50)
- Lequel gagne, et sur quelles instances l'ordre s'inverse.
- Causes à relier aux caractéristiques : place disponible dans les caches, nombre de caches par endpoint, concentration des requêtes.
- Limite commune : aucun ne raisonne en gain par Mo.

**8–9. Recherche locale** (1:45)
- Constat : gain quasi nul hors instances jouets.
- Première cause : voisinage de 100 mouvements sur des millions possibles.
- Deuxième cause : l'état renvoyé est le dernier visité, pas le meilleur.
- Ce que change un voisinage plus grand, et à quel coût en temps.
- Réponse à « est-ce améliorable ? ».

**10–11. Knapsack** (1:45)
- Répartition des caches par branche : DP poids, DP valeur, repli glouton, non traités à la limite de temps.
- Lien entre branche et écart au VBS.
- Gain de la mise à jour en fonction du nombre de caches par endpoint.
- Coût : DP en Python pur, table en nombre d'objets × capacité.

**12. SWOT** (1:10)
- Forces, faiblesses, opportunités, menaces : deux ou trois points chacun, chacun appuyé sur un résultat montré avant.

## Résultats à reporter dans les diapos

À remplir après `python -m bench.run all` et `python -m bench.plots`.

- Gloutons :
- Recherche locale :
- Knapsack, branches :
- Knapsack, mise à jour :
- SWOT :

## Corrections de code proposées (non appliquées)

À trancher avant de figer les mesures : chaque correction change les scores.

| # | Fichier | Problème | Correction proposée |
|---|---|---|---|
| 1 | `algos/local_search.py`, fin de `random_tabu_search` et `sorted_tabu_search` | `caches = best_caches` ne modifie pas la liste de l'appelant : c'est le dernier état visité qui est évalué, pas le meilleur. Mesuré sur me_at_the_zoo, graine 0 : départ 471 938, état final 464 737, meilleur rencontré 471 938. | `caches[:] = best_caches`, puis recalculer `caches_sizes` |
| 2 | `algos/local_search.py`, `random_tabu_search` | aucune graine : résultats non reproductibles (6_2_6_2 varie de 665 833 à 832 158 selon la graine) | paramètre `seed` et `random.seed(seed)` |
| 3 | `algos/local_search.py`, `local_search` | le meilleur voisin est appliqué même s'il n'améliore rien (ajout à gain nul, ou retrait qui dégrade) | s'arrêter quand le meilleur delta est >= 0 |
| 4 | `algos/local_search.py`, `local_search` | `caches_sizes[caches.index(cache)]` renvoie le premier cache de même contenu, pas forcément le bon | `caches_sizes[cache_id]` |
| 5 | `algos/knapsack_slay.py`, `multiknapsack` | dès qu'un cache dépasse les deux limites, la fonction s'arrête pour tous les caches (score 0 sur trending_today) | même repli glouton que `multiknapsack_bg` |
| 6 | `algos/knapsack_slay.py`, `knapsack_goulton` | renvoie un sac vide s'il y a plus de 10 000 objets, alors qu'un tri suffit | supprimer ce test |

Constat qui n'est pas un bug mais qui explique des scores : le glouton 1 replace une vidéo dans un cache plus lent quand le cache le plus rapide qui la contient est plein. Sur trending_today, 37 % de la capacité est occupée par des vidéos qui ne servent aucune requête (99 % pour le glouton 3).
