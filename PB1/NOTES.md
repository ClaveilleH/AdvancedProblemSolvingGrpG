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
