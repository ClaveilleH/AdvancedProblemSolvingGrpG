# Rapport 13 — instance qui ne se résout qu'avec le knapsack PGCD

> **AUTRE_4 non testé : dépôt inaccessible** (404). Instances testées contre 3 adversaires seulement.

## L'essentiel
`best/instance_knapsack_pgcd.in` (50 Ko) : piège d'affectation bruité (30 paires), vidéos fantômes, parasites
**denses** dans les caches de secours, tailles × 10⁶.

| route | score |
|---|---|
| **knapsack de MOI** (caches par valeur totale + DP exacte + division par le PGCD) | **2 355 465** = optimum |
| même tri par valeur, remplissage glouton | 1 542 411 |
| gloutons de MOI (greedy, greedy2, greedy3) | 1 765 088 |
| AUTRE_1 / AUTRE_2 / AUTRE_3 | 1 542 411 |
| sac à dos exact dans l'ordre des index (type C) | 1 542 411 |
| sac à dos exact sans PGCD | timeout (600 s) |
| recuit simulé, 4 réglages | ≤ 1 542 411 |

Ratio ×1,53 contre tous les adversaires testés. Juges émulés identiques.

## Pourquoi il faut les trois briques
1. **Ordre par valeur totale** : les vidéos fantômes font passer les caches de secours avant les caches
   partagés. Dans l'ordre des index, le cache partagé prend la grosse vidéo et e1 n'a plus rien.
2. **Sac à dos exact** : dans le cache de secours, des parasites de taille 1 ou 2 sont 15 à 60 % plus denses
   que la grosse vidéo. Un glouton les prend, et la grosse vidéo (taille de tout le cache) ne tient plus. Seul
   un sac à dos exact voit que la grosse vidéo vaut plus que tous les parasites réunis.
3. **Division par le PGCD** : capacité 6·10⁸ ; sans division, la table de la DP est hors de portée.
Les parasites nombreux bloquent aussi le recuit.

## Comparaison avec instance_greedy2_pgcd
| | route vers l'optimum | ratio |
|---|---|---|
| `instance_greedy2_pgcd` | placement selon le nombre d'endpoints demandeurs (greedy2) | ×1,66 |
| `instance_knapsack_pgcd` | tri par valeur + sac à dos exact + PGCD (knapsack_slay) | ×1,53 |

## Vérification « aucun dépôt modifié »
```
repos/APSJeffersonStorck : status=0 lignes, diff=0 lignes OK
repos/AdvancedProblemSolvingGrpG : status=0 lignes, diff=0 lignes OK
repos/hashcode-2017-streaming-videos : status=0 lignes, diff=0 lignes OK
repos/hashcode_2017 : status=0 lignes, diff=0 lignes OK
```
