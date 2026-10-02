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

> 21:00 — consigne de l'utilisateur : continuer au-delà des 3 h, jusqu'à ce qu'il dise d'arrêter.

### Essai 9 (20:46) — grossir les groupes quand la recherche sature (vws) : ÉCHEC dans cette version
- Constat (tests de 100 s depuis la solution de l'essai 8) : les deux instances saturent avec les
  réglages actuels (vws +10, kittens +6). Sur vws, des groupes de 16 caches (fenêtre 3) donnent +66 ;
  sur kittens les gros groupes ne donnent rien ((k8,w4) +6, (k12,w2) +1).
- Idée : sur les instances peu denses, multiplier la taille des groupes par 1,5 (jusqu'à 16) quand moins
  de 25 % des 60 derniers groupes améliorent le score.
- Résultat (vws seule, 14 processus) : **616 543**, moins bien que l'essai 8 (616 646).
- Cause : avec 14 processus et des groupes de 16, il n'y a pas assez de caches libres (100 en tout) ;
  le code retombait alors sur des groupes d'un seul cache (102 825 groupes lancés, 841 gardés), ce qui
  faisait aussi grimper la taille trop vite (8 → 12 → 16 en 5 s). Corrigé à l'essai 10 : on attend
  qu'un groupe se libère au lieu de lancer un groupe d'un seul cache.

### Essai 10 (21:04) — essai 9 corrigé (attendre un groupe libre au lieu d'un groupe d'un seul cache) : PAS MIEUX
- Résultat (vws seule, 14 processus) : **616 617**, contre 616 646 à l'essai 8 : identique au bruit près.
  La taille des groupes n'est montée qu'à 8, et 3,5 fois moins de groupes ont été résolus (2 097 contre
  7 247) pour le même score. Code non gardé (retour à la version de l'essai 8).
- Enseignement : sur vws, le score final (~616 600) ne dépend ni du nombre de groupes résolus ni de leur
  taille ; c'est le plafond de ce voisinage en 18 min.

### Analyses sur kittens (21:05–21:10), sans changement de code
- Solution de l'essai 8 : 7 469 vidéos placées sur 10 000, 9 170 copies (89 % des vidéos placées n'ont
  qu'une copie), 18 vidéos par cache, caches pleins (0,7 Mo libre en moyenne). 73 % des requêtes
  (pondérées) sont servies, à 89 % de leur gain maximal.
- Borne sup facile (une copie sert tout le monde au mieux, capacité globale) : 1 199 494 — trop lâche
  pour dire quelle marge il reste.
- Cibler les paires de caches par la valeur estimée d'un échange de deux vidéos : inutile (l'estimation
  ignore les tailles, elle est positive pour 84 % des paires ; 150 paires ciblées : 2 succès, +1,6 point ;
  150 paires au hasard : 5 succès, +1,2 point). Les paires de caches sont quasiment toutes déjà optimales.

### Essai 11 (21:13–22:13) — glouton en gain / taille^alpha
- Constat (glouton + sac à dos seuls) : diviser par taille^alpha avec alpha < 1 donne un meilleur départ.
  kittens : alpha 1,2 → 1 024 087 ; 1,0 → 1 024 895 ; 0,9 → 1 025 354 ; 0,8 → 1 025 442 ;
  0,7 → **1 025 562** ; 0,6 → 1 025 224 ; 0,5 → 1 024 484 ; 0,4 → 1 023 462.
  vws : 1,0 → 610 498 ; 0,8 → 610 792 ; 0,7 → 611 128 ; 0,6 → 611 323 ; 0,5 → 611 375.
- Après 400 s de pipeline complet (7 processus) : kittens 1 025 941 (alpha 0,7) contre 1 025 481 (alpha 1) ;
  vws 615 287 contre 615 288 : l'avantage tient sur kittens, disparaît sur vws.
- Mesure complète `--seq` avec alpha = 0,7 partout : vws 616 382, kittens 1 026 234. **Total 2 659 173**,
  sous l'essai 8 (2 659 303) : +134 sur kittens, −264 sur vws. Les deux écarts sont de l'ordre du bruit.
- Suite : essai 12, alpha = 0,7 seulement sur les instances denses.

### Piste écartée (21:37) — détruire et reconstruire une zone (kittens)
- Vider 50 ou 150 caches au hasard dans la solution de l'essai 8, reconstruire par glouton (alpha 0,7)
  puis sac à dos sur tout : toujours moins bien qu'avant (−65 à −115 points pour 50 caches, −276 à −410
  pour 150), en 1 min à 1 min 30 par tentative. Abandonné.

### Essai 12 (22:13) — alpha = 0,7 seulement sur les instances denses : NON MESURÉ
- Mesure lancée puis interrompue à 22:14 à la demande de l'utilisateur (arrêt de l'exploration).
  Le code n'est pas gardé : la branche contient la version de l'essai 8, la meilleure mesurée en entier.

---

## Résumé final (arrêt à 22:14, après 3 h 53 ; budget initial de 3 h prolongé par l'utilisateur à 21:00)

### Score
| Instance | Baseline | Final (essai 8) | Gain |
|---|---:|---:|---:|
| me_at_the_zoo | 512 115 | 516 557 | +4 442 |
| trending_today | 499 966 | 500 000 | +34 |
| videos_worth_spreading | 610 574 | 616 646 | +6 072 |
| kittens | 1 024 517 | 1 026 100 | +1 583 |
| **Total** | **2 647 172** | **2 659 303** | **+12 131** |

Scores donnés par le juge, avec `python claude_bench.py --seq` (36 min au total, 18 min par instance).
Pour comparaison, le premier du classement 2017 (`results_doc/hashcode_2017.csv`) est à 2 651 999.

Sur les deux grosses instances, deux lancements identiques diffèrent d'environ ±150 points (recherche
parallèle dont le déroulement dépend de la charge de la machine). Avec `python claude_bench.py`
(les 4 instances en même temps, 7 processus chacune, 18 min) le total mesuré est 2 658 900.

### Meilleure méthode (`claude_best` dans `claude_solver.py`)
1. Glouton sur les couples (cache, vidéo) par gain / taille.
2. Sac à dos exact cache par cache jusqu'à convergence, accéléré par élimination des vidéos dont le
   sort est certain (bornes de la relaxation continue).
3. Puis selon l'instance :
   - caches tous identiques (trending_today) : rangement exact, toutes les requêtes servies ;
   - petite instance (me_at_the_zoo) : programme linéaire en nombres entiers sur tout le problème,
     optimum prouvé par le solveur ;
   - sinon (vws, kittens) : recherche à voisinage large. On vide un groupe de 4 ou 5 caches voisins et
     on le re-remplit de façon optimale par MILP (HiGHS via scipy), sur les vidéos les plus denses
     (fenêtre 4). Plusieurs groupes sont résolus en parallèle ; chaque résultat est réévalué sur l'état
     courant et gardé seulement s'il améliore le score.

### Ce qui a rapporté, par ordre d'importance
- LNS par MILP sur des groupes de caches (essais 1, 3) : l'essentiel du gain sur vws.
- MILP complet sur la petite instance (essai 1) : +4 442.
- Parallélisation de la LNS (essais 4, 8) : environ +2 500 puis +400.
- Sac à dos exact au lieu de la fenêtre 4 (essai 3) : +380 sur kittens avant LNS.
- Rangement exact pour trending_today (essai 2) : +34, maximum atteint.

### Pistes explorées non concluantes (à ne pas refaire telles quelles)
- MILP sur toute l'instance vws : 590 577 en 900 s.
- Re-remplir un groupe de caches par sacs à dos successifs au lieu d'un MILP : 0 gain sur kittens.
- Choix des groupes (ressemblance des latences, caches « désirés », échanges estimés), mouvements à
  score égal, tailles de groupe et de fenêtre : aucun effet au-delà du bruit (essai 5, analyses kittens).
- Grossir les groupes quand la recherche sature (essais 9 et 10) : pas mieux sur vws.
- Construction par prix des caches / relaxation lagrangienne (essai 6) : nettement pire.
- Détruire et reconstruire 50 à 150 caches sur kittens : toujours moins bien.

### Pistes restantes
- **Glouton en gain / taille^0,7 sur kittens** (essais 11 et 12) : la piste la plus prometteuse.
  kittens a donné 1 026 234 (contre 1 026 100) dans une mesure complète, et +460 à 400 s. À confirmer
  par une mesure complète avec alpha = 0,7 sur kittens seulement et 1,0 sur vws ; attention au bruit de
  ±150, il faudrait plusieurs lancements par réglage.
- Les deux grosses instances saturent avec ce voisinage (vws ~616 600, kittens ~1 026 100 à 1 026 200) :
  plus de temps ou plus de cœurs ne rapportent presque plus rien. Pour aller plus loin il faut un autre
  type de mouvement, par exemple un voisinage centré sur les vidéos (re-décider dans quels caches va un
  ensemble de vidéos) ou une relaxation linéaire globale suivie d'un arrondi.
- Aucune borne supérieure serrée n'a été calculée : on ne sait pas quelle marge il reste sur kittens et
  vws (la seule borne calculée sur kittens, 1 199 494, est trop lâche pour conclure).
- Rendre la recherche parallèle reproductible (ordre d'application fixe) pour comparer les réglages
  sans bruit.
