# Oral — plan du diaporama et du script

Oral lundi 12/10/2026, 20 min : 2 min algo, 8 min évaluation expérimentale, 10 min de questions (voir `consignes.txt`).
Diaporama : `diapo.tex` (Beamer, éditable à la main). Figures : `figures/`, régénérées par `python -m bench.plots`.

**Tout ce qui est ici porte sur nos algos non modifiés.** Les corrections proposées par Claude, leurs mesures et la force brute sont dans `docs/exploration/` et ne vont pas dans l'oral.

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

- L'oral et le diaporama portent exclusivement sur notre travail : nos algos, non modifiés.
- Autorisé : créer de nouveaux fichiers qui génèrent de la donnée en réutilisant les fonctions existantes (dossier `bench/`).
- Autorisé : proposer des modifications quand le code est faux. Elles sont proposées, pas appliquées, et rangées dans `docs/exploration/`.
- La force brute n'est pas évoquée à l'oral.
- Le diaporama reste éditable à la main : LaTeX, pas de solution web.
- Pas de phrases toutes faites dans le script : seulement les grandes lignes.

## Protocole expérimental

| Élément | Choix |
|---|---|
| Machine | Intel Core i5-7600 (4 cœurs, 3,5 GHz), 24 Go de RAM, Windows 10, Python 3.11.1 |
| Instances | 4 Google + 29 de la promo ; les 5 instances jouets (2 à 20 vidéos) sont présentées à part |
| Algos | Glouton 1, 2, 3 ; knapsack indépendant ; knapsack avec mise à jour ; descente, tabou aléatoire, tabou trié (lancés depuis le meilleur glouton), avec les paramètres de `main.py` |
| Limite | 300 s par exécution ; à la limite, on évalue l'état des caches à cet instant |
| Aléatoire | 10 graines pour le tabou aléatoire, 1 exécution pour les algos déterministes |
| Parallélisme | 2 instances traitées en même temps (les temps sont donc un peu surestimés) |
| Métriques | score, écart au meilleur score connu en %, temps, gain sur la solution de départ, capacité gaspillée, branche du knapsack par cache |
| Référence | meilleur score de la promo par instance (VBS du Google Sheet, export du 10/10) |

Commandes :

```bash
python -m bench.features all              # caractéristiques des instances
python -m bench.run all --timeout 300 --workers 2    # tous les algos, toutes les instances
python -m bench.run me_at_the_zoo zipF_instance big videos_worth_spreading medium_mixed_lambda --grid --seeds 3
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
| 5 | Vue d'ensemble | écart au meilleur score connu, algo × instance | `vue_ensemble` | 0:40 |
| 6 | Gloutons : résultats | colonnes sur les instances où ils diffèrent le plus | `gloutons` | 1:00 |
| 7 | Gloutons : pourquoi | capacité gaspillée, place disponible | `gloutons_gaspillage` ou `capacite` | 0:50 |
| 8 | Recherche locale : constat | instances dégradées / améliorées, gains | `recherche_locale` | 0:55 |
| 9 | Recherche locale : améliorable ? | voisinage et itérations | `voisinage` | 0:50 |
| 10 | Knapsack : quelle branche ? | part des caches par branche | `knapsack_branches` | 1:00 |
| 11 | Knapsack : mise à jour | gain selon le nombre de caches par endpoint | `knapsack_maj` | 0:45 |
| 12 | SWOT et conclusion | tableau 2×2 | | 1:10 |

Diapos de secours pour les questions : compromis temps / qualité (`temps_qualite`), place disponible (`capacite`), complexité des deux DP.

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
- Pourquoi le meilleur score de la promo comme référence : pas d'optimum connu, la borne supérieure est trop lâche.
- Pourquoi 10 graines : le tabou aléatoire change de score d'une exécution à l'autre.

**5. Vue d'ensemble** (0:40)
- Le knapsack avec mise à jour domine ; les gloutons prennent le relais quand il ne finit pas.
- Annoncer les trois zooms : gloutons, recherche locale, knapsack.

**6–7. Gloutons** (1:50)
- Glouton 1 meilleur glouton sur 17 instances, glouton 2 sur 11, glouton 3 jamais.
- Glouton 2 : une seule copie par vidéo. Gagne quand tout endpoint voit tout cache, perd quand chaque endpoint voit peu de caches.
- Glouton 3 : mêmes vidéos recopiées dans les caches d'un même endpoint, capacité gaspillée.
- Glouton 1 : ignore la taille des vidéos. Bon quand la place est abondante ou les requêtes concentrées.

**8–9. Recherche locale** (1:45)
- Constat : dégrade la solution de départ sur 9 à 15 instances sur 33, gains inférieurs à 1 % presque partout.
- Cause 1 : voisinage de 100 mouvements sur des millions possibles.
- Cause 2 (à décider si on la dit) : l'état rendu est le dernier visité.
- Voisinage plus grand : gain net sur une instance sur cinq, à un coût en temps qui explose pour le tabou trié.
- Réponse : améliorable à la marge par les paramètres, pas au niveau du knapsack.

**10–11. Knapsack** (1:45)
- Répartition des caches par branche : DP poids, DP valeur, repli glouton, non traités à la limite de temps.
- Le repli glouton coûte peu ; le vrai problème est le temps.
- Gain de la mise à jour en fonction du nombre de caches par endpoint.
- Coût : DP en Python pur, table en nombre de vidéos × capacité.

**12. SWOT** (1:10)
- Deux ou trois points par case, chacun appuyé sur un résultat montré avant.

## Résultats (nos algos, non modifiés)

Bench du 10/10 : 33 instances, 561 exécutions. Les pourcentages d'écart sont calculés hors instances jouets (28 instances), par rapport au meilleur score de la promo.

### Vue d'ensemble

| Algo | Écart médian | Instances à moins de 5 % | Temps médian | Temps max |
|---|---|---|---|---|
| Glouton 1 | 27,6 % | 8 | 0,1 s | 6 s |
| Glouton 2 | 54,6 % | 3 | 0,4 s | 17 s |
| Glouton 3 | 90,9 % | 0 | 0,03 s | 10 s |
| Knapsack indépendant | 64,6 % | 3 | 34 s | 300 s (limite) |
| Knapsack avec mise à jour | 5,3 % | 14 | 27 s | 300 s (limite) |
| Descente | 21,8 % | 9 | 5 s | 211 s |
| Tabou aléatoire | 21,8 % | 9 | 0,02 s | 14 s |
| Tabou trié | 21,8 % | 9 | 0,3 s | 61 s |

- Le knapsack avec mise à jour est le meilleur algo constructif (ou ex aequo) sur 21 instances sur 28.
- Les trois recherches locales ont le même écart médian : elles partent du meilleur glouton et ne le changent presque pas.

### Gloutons

- Meilleur glouton : glouton 1 sur 17 instances, glouton 2 sur 11, glouton 3 jamais.
- **Glouton 2** place chaque vidéo une seule fois (1,0 copie par vidéo sur toutes les instances).
  - `trending_today` (chaque endpoint voit les 100 caches) : 100 % des requêtes servies par un cache, écart 0 %.
  - `videos_worth_spreading` (5 caches par endpoint) : 15 % des requêtes servies, écart 79 %.
  - `dense` : 32 % des requêtes servies, écart 92 %.
- **Glouton 3** recopie les mêmes vidéos : 23 copies par vidéo sur `kittens` (74 % de la capacité occupée par des vidéos qui ne servent aucune requête), 100 copies sur `trending_today` (99 %).
- **Glouton 1** ne regarde pas la taille des vidéos.
  - Place abondante (capacité ≥ 5 fois le volume des vidéos) : écart 2,3 % et 1,3 % (`10000_500_100000_100`, `3860_246_84901_66`).
  - Place rare et requêtes peu concentrées (`custom_*`, `medium_*`) : écart de 65 à 86 %.
  - Exception : `dense` et `dense2`, place très rare mais 80 à 93 % des requêtes sur 10 % des vidéos, écart 0 %.
  - Il gaspille aussi de la place : 37 % de la capacité sur `trending_today`.

### Recherche locale (paramètres de `main.py`)

| | Instances dégradées | Inchangées | Améliorées |
|---|---|---|---|
| Descente | 9 | 10 | 14 |
| Tabou aléatoire (moyenne de 10 graines) | 15 | 5 | 13 |
| Tabou trié | 10 | 11 | 12 |

- Hors instances jouets, un seul gain dépasse 1 % : `4990_246_84901_50` (+1,5 % descente, +4,8 % tabou aléatoire, +3,3 % tabou trié).
- Pertes notables : descente à 0 sur `2_2_2_1` (départ 951 327), tabou trié −1,7 % sur `dense2`.
- Le tabou aléatoire n'est pas reproductible : sur `4_2_4_2`, l'écart-type entre graines vaut 26 % du score moyen ; sur `6_2_6_2`, 13 %.

### Étude du voisinage (tabu search, 5 instances)

Voisinage = nombre de caches et de vidéos examinés à chaque itération (10, 30 ou 100), avec 100 ou 400 itérations.

- `medium_mixed_lambda` : le tabou aléatoire passe de 0 % à +14,6 % de gain (voisinage 100, 400 itérations, 6,5 s). Il reste loin du knapsack sur cette instance.
- `videos_worth_spreading` : +0,75 % au mieux (tabou aléatoire, 54 s). Le tabou trié atteint la limite de 300 s dès le voisinage 30 avec 400 itérations.
- `me_at_the_zoo` : +1,25 % au mieux, mais −2,7 % pour le tabou aléatoire avec 400 itérations et un voisinage de 10.
- `zipF_instance`, `big` : aucun gain, quel que soit le réglage.

### Knapsack : branches

Sur les 3 860 caches des 28 instances, pour le knapsack avec mise à jour :

| Branche | Caches | Part |
|---|---|---|
| DP sur le poids | 1 493 | 39 % |
| DP sur la valeur | 583 | 15 % |
| Repli glouton | 296 | 8 % |
| Non traités à la limite de 300 s | 1 488 | 39 % |

- Il ne finit pas sur 5 instances : `kittens` (15 caches traités sur 500), `realistic_large_clustered` (12 sur 500), `realistic_large_random` (15 sur 500), `videos_worth_spreading` (70 sur 100), `custom_universallambda42_asymmetric`.
- Quand il finit (23 instances), son écart médian est de 4,5 %.
- 16 instances entièrement en DP : écart médian 3,0 %, il bat le meilleur glouton sur 11.
- 7 instances avec repli glouton : écart médian 5,9 %, il bat le meilleur glouton sur 4. Les deux où il perd nettement : `10000_500_100000_100` (5,6 % contre 2,3 %) et `3860_246_84901_66` (6,9 % contre 1,3 %), les deux instances où la place est la plus abondante.
- L'hypothèse « il perd son avantage en repli glouton » n'est donc que partiellement vérifiée : le repli coûte environ 3 points, le temps de calcul coûte beaucoup plus.

### Knapsack : mise à jour entre caches

Sur les 21 instances où les deux versions finissent :

- Le knapsack indépendant fait 0 sur 7 instances : il s'arrête pour tous les caches dès que la capacité et la somme des valeurs dépassent 10 000.
- 1 cache par endpoint (`supra`) : aucun gain, les deux versions sont identiques.
- 3 à 4 caches par endpoint : +14 à +32 % (`me_at_the_zoo`, `regional_instance`, `zipF_instance`, `custom_dejavu42`, `medium_*_sparse`).
- 7 à 8 caches par endpoint : +72 à +95 % (`medium_mixed_lambda`, `medium_*_dense`).
- 25 caches par endpoint (`INSTANCED`) : score multiplié par 11.
- Exceptions : `dense`, `dense2` (10 caches par endpoint) et `custom_universallambda42` (13) : gain nul ou inférieur à 1 %.
- La mise à jour supprime les doublons : sur `me_at_the_zoo`, la capacité occupée par des vidéos inutiles passe de 31 % à 1 %.

### SWOT

| | Positif | Négatif |
|---|---|---|
| **Interne** | **Forces** : knapsack avec mise à jour à 5,3 % d'écart médian, meilleur constructif sur 21 instances sur 28 ; gloutons en moins d'une seconde ; algos complémentaires, `main.py` garde le meilleur par instance | **Faiblesses** : knapsack non terminé en 300 s sur 5 instances (39 % des caches non traités) ; recherche locale qui dégrade le départ sur 9 à 15 instances et gagne moins de 1 % ; tabou aléatoire non reproductible ; glouton 3 jamais compétitif |
| **Externe** | **Opportunités** : voisinage plus grand (+14,6 % sur une instance) ; lancer la recherche locale depuis le knapsack plutôt que depuis un glouton ; DP plus rapide (numpy, langage compilé) ; glouton au gain par Mo | **Menaces** : capacités plus grandes (table de DP en vidéos × capacité, repli au-delà de 10 000) ; limite de temps plus stricte (27 s médian contre 0,1 s) ; instances pièges où tous nos algos constructifs donnent le même score |
