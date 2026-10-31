# Résumé — protocole et travail réalisé

Évaluation expérimentale de nos algos pour Hash Code 2017 « Streaming Videos » (groupe G), faite le 10/10/2026. Le détail est dans `diapo.md`.

## Protocole

- **Algos mesurés** : nos 8 algos, avec les paramètres de `main.py` : gloutons 1, 2 et 3, knapsack indépendant, knapsack avec mise à jour, descente, tabou aléatoire et tabou trié (ces trois derniers lancés depuis le meilleur glouton).
- **Instances** : 33 (4 Google, 29 de la promo, dont 5 instances jouets traitées à part).
- **Machine** : Intel Core i5-7600, 24 Go de RAM, Windows 10, Python 3.11.
- **Limite** : 300 s par exécution ; à la limite, on évalue l'état des caches à cet instant.
- **Aléatoire** : 10 graines pour le tabou aléatoire, une exécution pour les autres.
- **Référence** : le meilleur score de la promo par instance (Google Sheet du 10/10).
- **Métriques** : score, écart à la référence en %, temps, gain sur la solution de départ, capacité gaspillée, branche du knapsack par cache.

## Ce qu'on a fait

1. **Caractérisé les 33 instances** : tailles, place disponible dans les caches, nombre de caches par endpoint, concentration des requêtes.
2. **Mesuré chaque algo sur chaque instance** : 561 exécutions, score et temps, au lieu de ne garder que le meilleur algo comme le fait `main.py`.
3. **Analysé les solutions des gloutons et des knapsacks** : part de la capacité occupée par des vidéos qui ne servent aucune requête, nombre de copies par vidéo, part des requêtes servies par un cache.
4. **Compté les branches du knapsack** : nombre de caches résolus par DP sur le poids, DP sur la valeur, repli glouton, ou non traités à la limite de temps.
5. **Corrigé la recherche locale** : les mesures montraient qu'elle dégradait la solution de départ sur 9 à 15 instances, parce qu'elle rendait le dernier état visité au lieu du meilleur. Corrigé dans `algos/local_search.py`, puis mesuré de nouveau.
6. **Étudié le voisinage des tabu search** sur 5 instances : 3 tailles de voisinage, 2 nombres d'itérations.
7. **Produit les figures et le diaporama** (`figures/`, `diapo.tex`).

**Mesure des stats** : outil `metrics/mesure_metrics.py` — 6 graphiques d'entrée (`read_input`) et 6 de sortie (`read_output` + `OutputStats`), affichés dans une interface graphique. Deux captures (`stats_entree_input.png`, `stats_sortie_output.png`) sont ajoutées au diaporama, dans `docs/oral/figures/` uniquement. Le code `metrics/` a été partagé avec le reste de la promo. `bench/` automatise la même mesure sur les 561 exécutions.

## Ce qu'on en retient

- Le knapsack avec mise à jour est notre meilleur algo : 5,3 % d'écart médian, meilleur algo constructif sur 21 instances sur 28. Il ne finit pas en 300 s sur 5 instances.
- La mise à jour entre caches rapporte d'autant plus que les endpoints voient de caches : rien pour 1 cache, +14 à +32 % pour 3 à 4, +72 à +95 % pour 7 à 8.
- Le repli glouton du knapsack coûte environ 3 points d'écart ; le temps de calcul est le vrai problème.
- Glouton 1 est le meilleur glouton sur 17 instances, glouton 2 sur 11, glouton 3 jamais. Chacun a une cause d'échec identifiée : taille ignorée, une seule copie par vidéo, copies inutiles.
- Depuis la correction, la recherche locale ne dégrade plus aucune instance (contre 9 à 15 avant), mais elle gagne moins de 1 % sur 26 instances sur 28. Sur trois instances jouets, le tabou trié dépasse le meilleur score de la promo. Un voisinage plus grand aide sur une instance sur cinq (+14,7 %), au prix du temps.

## Pour tout rejouer

```bash
python -m bench.features all
python -m bench.run all --timeout 300 --workers 2
python -m bench.run me_at_the_zoo zipF_instance big videos_worth_spreading medium_mixed_lambda --grid --seeds 3
python -m bench.solution_stats all
python -m bench.plots
```

Les mesures d'avant correction sont archivées dans `bench/data/exploration/`. Les pistes non retenues pour l'oral sont dans `docs/exploration/`.
