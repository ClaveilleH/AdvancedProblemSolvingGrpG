# Exploration `explore/meilleur-score`

- Début : 2026-10-02 18:21:19 — fin prévue : 21:21:19 (budget 3 h)
- Mesure : `python claude_bench.py` (dans `PB1/`). Lance `claude_main.py` sur les 4 instances
  officielles (un processus par instance, timeout 20 min chacune), puis note chaque sortie avec
  le juge `judge/judgeHashCode2017.cpp` (non modifié). Score = somme des 4 scores du juge.
  La commande n'était pas précisée dans la consigne (`[COMMANDE]`), c'est celle que j'ai retenue.
- Chaque exécution repart de zéro (pas de reprise d'une solution d'un essai précédent).

## Baseline (18:24)

Glouton gain/taille + sac à dos cache par cache (`window=4`), ~20 s au total.

| Instance | Score |
|---|---:|
| me_at_the_zoo | 512 115 |
| trending_today | 499 966 |
| videos_worth_spreading | 610 574 |
| kittens | 1 024 517 |
| **Total** | **2 647 172** |

## Journal des essais

### Essai 1 (18:27) — MILP par groupes de caches (LNS) + MILP complet sur petite instance
- Idée : vider un groupe de caches voisins et le re-remplir de façon optimale avec un programme
  linéaire en nombres entiers (HiGHS via `scipy.optimize.milp`), en boucle. Sur une petite instance,
  tout résoudre d'un coup.
- Mesure courte (`CLAUDE_TIME=150`) : zoo 516 557 (optimum prouvé par le solveur, 3 s),
  vws 610 989 (+415, encore en progression), kittens inchangé, trending inchangé. **Total 2 652 029.**
- Conclusion : très efficace sur zoo et vws. Sur kittens, des groupes de 5 caches sans fenêtre de
  candidats sont trop gros (30 s par groupe sans gain) ; sur trending le MILP est inutilisable
  (tous les caches reliés à tous les endpoints). À régler dans les essais suivants.

### Essai 2 (18:33) — rangement exact quand tous les caches sont identiques
- Constat : sur `trending_today`, chaque endpoint est relié aux 100 caches avec la même latence, et la
  somme des tailles des vidéos vaut exactement la capacité totale. Une seule copie de chaque vidéo suffit.
- Idée : remplir les caches un par un exactement à ras bord (sac à dos avec valeur = taille, grosses
  vidéos d'abord, choix élargi tant que le cache n'est pas plein).
- Résultat : trending_today **500 000** (maximum théorique, toutes les requêtes servies), en 9 s.
- Premier jet raté (499 864) : 4 vidéos restaient dehors car certains caches n'étaient pas pleins ;
  corrigé en élargissant le choix des candidats.

### Essai 3 (18:47) — sac à dos exact par cache + LNS réglée (séquentielle)
- Constat : le sac à dos limité à `window=4` bridait kittens (plus la fenêtre est large, meilleur est
  le score : 8 → 1 024 521, 64 → 1 024 749, tout → 1 024 884 mais 400 s sans converger).
- Idée : sac à dos exact sur toutes les vidéos, rendu rapide en éliminant d'abord les vidéos dont le
  sort est certain (bornes de la relaxation continue, `_knapsack_reduced`). Convergence sur kittens en
  36 s au lieu de > 400 s, score 1 024 895.
- LNS : groupes de 3 caches, fenêtre de candidats 8 sur les instances denses.
- Mesure complète (900 s/instance) : zoo 516 557, trending 500 000, vws 614 213, kittens 1 025 401.
  **Total 2 656 171.**
- Pistes testées et écartées dans cet essai :
  - MILP sur toute l'instance vws : 590 577 après 900 s, bien pire que la LNS.
  - Re-remplir un groupe de caches par sacs à dos successifs (sans MILP) : 0 gain sur kittens,
    +150 sur vws en 150 s contre +990 pour le MILP.
  - Le temps part presque entièrement dans le solveur (HiGHS), pas dans la construction du modèle.

### Essai 4 (19:07) — LNS parallèle (plusieurs groupes résolus en même temps)
- Idée : le temps est passé dans le solveur, donc résoudre plusieurs groupes disjoints à la fois dans
  des processus séparés (7 par instance sur cette machine à 16 cœurs). Un résultat calculé sur un état
  entre-temps modifié est réévalué sur l'état courant et gardé seulement s'il améliore le score.
- Réglages retenus après tests de 90 s : fenêtre 4, groupes de 4 caches (kittens) ou 5 (vws).
  Testés aussi : kittens (k2,w16) 1 025 159, (k3,w8) 1 025 242, (k4,w4) 1 025 276 ;
  vws (k8,w8) 611 521, (k5,w8) 612 532, (k5,w4) 612 561.
- Mesure complète : zoo 516 557, trending 500 000, vws 616 142, kittens 1 026 036. **Total 2 658 735.**
- Les deux courbes montent encore à la fin (kittens ~ +40/min, vws ~ +10/min) : vws sature, kittens non.
