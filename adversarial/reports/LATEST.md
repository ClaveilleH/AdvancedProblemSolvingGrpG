# Rapport 10 — instance « PGCD pur »

> **AUTRE_4 non testé : dépôt inaccessible** (404). Instances testées contre 3 adversaires seulement.

## L'essentiel
`best/instance_pgcd.in` (30 Ko, `generator/trap_pgcd.py --seed 1`) : 30 sacs à dos indépendants (un cache, un
endpoint, 50 vidéos chacun), valeurs « fortement corrélées » (valeur = taille réduite + 100), tailles et capacité
multipliées par g = 10⁵ (capacité 10⁹ = 10 000 × g).

| algo | score | type |
|---|---|---|
| **MOI** (stable, sans recherche locale aussi) | **1 562 573** = optimum | — |
| AUTRE_1 / AUTRE_2 | 1 525 969 | score (glouton par densité : place perdue) |
| AUTRE_3 | 1 361 211 | score (tri par valeur) |
| sac à dos exact sans PGCD (substitut) | — | **crash** : MemoryError (table 50 × 10⁹) |
| recuit simulé, 4 réglages | 1 417 365 à 1 562 283 | score ; **0 cache sur 30** résolu exactement |

Juges émulés et scoreur exact identiques (tout en 32 bits).

## Pourquoi seul le PGCD réussit
- Chaque cache est un sac à dos où la meilleure combinaison est fine à trouver : les gloutons laissent de la
  place, et le recuit s'arrête juste en dessous de l'optimum dans chaque cache.
- La seule méthode exacte de MOI (DP) n'est faisable qu'après division par le PGCD (table 50 × 10 000).
- Pour faire jeu égal, une recherche locale devrait réussir les 30 caches au point près.

## Limites
- Un groupe qui divise aussi par le PGCD, ou qui résout le sac à dos exactement autrement (DP sur les
  valeurs, séparation-évaluation, frontière de Pareto comme mon solveur), trouve aussi l'optimum : égalité.
- L'écart avec le meilleur recuit est faible (290 points) : l'instance garantit la 1re place, pas un grand ratio.
- Tailles jusqu'à 10⁸ et capacité 10⁹ : hors des bornes historiques (retirées par les profs).

## Vérification « aucun dépôt modifié »
```
repos/APSJeffersonStorck : status=0 lignes, diff=0 lignes OK
repos/AdvancedProblemSolvingGrpG : status=0 lignes, diff=0 lignes OK
repos/hashcode-2017-streaming-videos : status=0 lignes, diff=0 lignes OK
repos/hashcode_2017 : status=0 lignes, diff=0 lignes OK
```
