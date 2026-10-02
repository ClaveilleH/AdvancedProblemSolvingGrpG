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

### Essai 5 (19:23–19:40) — variantes de la LNS en fin de course : NON CONCLUANT, rien gardé
Tests de 120 s en repartant de la solution de l'essai 4 (script hors dépôt), 7 processus.
Référence : kittens +34, vws +84. L'écart entre deux lancements identiques est de l'ordre de ±20,
donc aucune de ces variantes ne se distingue :
- accepter les mouvements à score égal (plateaux) : kittens +19, vws +115 ;
- choisir les caches du groupe selon la ressemblance de leurs latences (au lieu du nombre d'endpoints
  communs) : kittens +16 / +26, vws +143 ;
- choisir les caches où les vidéos du premier cache « seraient mieux » : kittens +26 / +10, vws +91 ;
- groupes plus gros avec fenêtre plus petite : kittens (k6,w3) +13, (k8,w2) +14 ; vws (k8,w4) +54,
  (k12,w4) +36, (k8,w8) +37.
Conclusion : le choix des groupes n'est pas le facteur limitant ; inutile d'y revenir.

### Essai 6 (19:41) — construction par « prix » des caches (relaxation lagrangienne) : ÉCHEC, abandonné
- Idée : donner un prix par Mo à chaque cache, placer chaque vidéo dans le cache où gain − prix × taille
  est le meilleur, ajuster les prix selon la charge, puis réparer par sac à dos.
- Résultat (script hors dépôt, 30 itérations) : les charges ne convergent pas (≈ 3 fois la capacité en
  moyenne, tout le monde se rue sur les mêmes caches). Après réparation + sac à dos : kittens 1 008 809
  (contre 1 024 895 pour glouton + sac à dos), vws 608 542 (contre 610 498).
- Conclusion : bien pire que le glouton comme point de départ. Il faudrait un vrai schéma de
  sous-gradient et un sous-problème par vidéo mieux résolu ; pas rentable dans le temps restant.

### Essai 7 (19:43) — plus de temps par instance (900 s → 1080 s de recherche)
- Chaque exécution reste sous 20 min (1081 s mesurés, lecture et écriture comprises).
- Mesure complète : zoo 516 557, trending 500 000, vws 616 437, kittens 1 025 906. **Total 2 658 900.**
- À noter : kittens fait un peu moins bien qu'à l'essai 4 (1 026 036) malgré 3 min de plus. La recherche
  parallèle n'est pas reproductible au point près (l'ordre d'arrivée des résultats dépend de la charge
  de la machine) : l'écart entre deux lancements identiques est d'environ ±150 sur kittens.
  Le gain de cet essai (+165 au total) vient de vws (+295) et reste dans cet ordre de grandeur.

### Essai 8 (20:02) — une instance à la fois, 14 processus chacune (`claude_bench.py --seq`)
- Idée : au lieu de lancer kittens et vws en même temps (7 processus chacune), les lancer l'une après
  l'autre pour que chacune ait presque tous les cœurs. Même limite de temps par instance (1080 s),
  mais la mesure complète dure 36 min au lieu de 18. Le juge est inchangé.
- Mesure : zoo 516 557, trending 500 000, vws 616 646, kittens 1 026 100. **Total 2 659 303.**
- Conclusion : gain modeste (+403). Sur kittens, deux fois plus de groupes essayés (11 150 contre ~5 000)
  pour seulement +~100 à +200 : la recherche sature autour de 1 026 100 avec ce voisinage.
  vws montait encore d'environ +1,4 point/s à la fin.
