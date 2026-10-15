# Rapport 07 — analyse du tableau de la promo et instance « promo »

> **AUTRE_4 non testé : dépôt inaccessible** (404). Instances testées contre 3 adversaires seulement.

## L'essentiel
Nouvelle instance `best/instance_promo.in` (105 o, valeurs dans les bornes de l'énoncé, aucun débordement) :

| algo | score |
|---|---|
| **MOI** (10 relances identiques) | **3 998 499** |
| AUTRE_1 (= groupe A) | 1 999 599 |
| AUTRE_2 | 1 999 599 |
| AUTRE_3 | 1 999 599 |
| substitut d'un groupe de type C (sac à dos exact par cache, 1 tour) | 1 999 599 |
| AUTRE_4 | non testé : dépôt inaccessible |

Ratio ×2,0 contre **tous**, y compris un algo à sac à dos exact. Scores identiques avec les deux juges émulés et le scoreur d'AUTRE_1.

## Analyse du tableau (docs/exel/backup_10_10_26, état au 10/10)
- G (nous) gagne ou fait jeu égal en tête sur : 2_2_2_1, 4_2_4_2, 6_2_6_2, 8_2_8_2, 20_2_20_2, big, supra, dense, dense2, INSTANCED.
  G perd nettement sur les grosses instances (kittens 0,84, realistic_large_random 0,78) et sur INSATANC2D (0,49).
- Particularités des instances gagnées :
  - 2_2_2_1 : piège de densité (une petite vidéo plus dense bloque la grosse) — A et F à 47 672, C et G à 951 327 ;
  - 6_2_6_2, 8_2_8_2 : piège d'affectation (un endpoint qui a deux caches vole le seul cache d'un autre) — A, C, F à la moitié ;
  - big, supra : un seul cache par endpoint, donc des sacs à dos indépendants que la DP exacte résout ;
  - dense, dense2 : capacité 1 000, DP exacte faisable.
- Identification : AUTRE_1 reproduit au point près les scores du groupe A sur 11 instances (les 10 relancées et me_at_the_zoo). AUTRE_3 coïncide avec C sur 5 instances jouets, pas ailleurs. AUTRE_2 ne correspond exactement à aucun groupe.
- La version actuelle de MOI (`main`) bat le meilleur score connu du tableau sur 4_2_4_2 (982 271), 6_2_6_2 (998 499) et 8_2_8_2 (991 480).

## Pourquoi le piège d'affectation, et pourquoi ×2 au plus
Le piège de densité ne bat pas les groupes qui font une DP exacte par cache (C, et MOI). Le piège
d'affectation, si : ces algos remplissent le cache partagé avec les vidéos de l'endpoint qui avait une
autre option. Un sac à dos exact cache par cache garantit néanmoins la moitié de l'optimum : ×2 est
le plafond contre ce type d'algo.
MOI s'en sort grâce à sa recherche locale, tant que les vidéos en jeu tiennent dans son voisinage
(10 vidéos les plus demandées) : k = 3 ou 4 vidéos par endpoint réussit 10/10, k = 5 et 6 dépendent du
tirage, k ≥ 10 piège MOI aussi.

## Remarques
- Cette instance reprend la structure de 6_2_6_2 de la promo (latence datacenter portée à 4 000).
- Mon solveur de repli tombe aussi dans ce piège (il reste dans l'optimum local « e0 dans le cache 0 »).
- Arbitrage avec la principale sûre : contre nos 3 dépôts, la principale sûre donne ∞, mais un groupe à
  DP exacte (type C) y serait optimal. Contre tous les groupes connus, l'instance promo donne ×2 partout.

## Vérification « aucun dépôt modifié »
```
repos/APSJeffersonStorck : status=0 lignes, diff=0 lignes OK
repos/AdvancedProblemSolvingGrpG : status=0 lignes, diff=0 lignes OK
repos/hashcode-2017-streaming-videos : status=0 lignes, diff=0 lignes OK
repos/hashcode_2017 : status=0 lignes, diff=0 lignes OK
```
