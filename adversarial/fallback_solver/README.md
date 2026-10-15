# Solveur de repli : ascension cache par cache avec sac à dos exact

## Commande exacte

```bash
cd adversarial
python fallback_solver/solver.py best/instance_repli.in best/repli_sorties/solver_run1.out
python scorer/score.py best/instance_repli.in best/repli_sorties/solver_run1.out
# preuve de reproductibilité (2 exécutions, comparaison octet par octet, scores, borne) :
fallback_solver/reproduce.sh
```

Python 3 standard, aucune dépendance, **aucun aléatoire** : même entrée, même sortie, même score
(vérifié : deux exécutions, sorties identiques, SHA-256 identiques, voir
`best/repli_sorties/reproductibilite.txt`). L'instance se régénère avec
`python generator/trap_repli2.py best/instance_repli.in --m 8 --kB 63 --kA 0`.

## Résultat sur l'instance de repli (`best/instance_repli.in`, 2 Ko)

| | score |
|---|---|
| borne supérieure (chaque requête servie par son cache le plus rapide, sans capacité) | 1 073 741 823 472 |
| **ce solveur** | **1 073 741 822 964** (à 5·10⁻¹⁰ près de la borne) |
| MOI, version commitée sans modification (meilleur de 15 relances, toutes identiques) | 507 |
| AUTRE_1 | 507 |
| AUTRE_2 | 507 |
| AUTRE_3 | 507 |
| AUTRE_4 | non testé : dépôt inaccessible (404) |

Le solveur fait environ **2,1 × 10⁹ fois mieux** que le meilleur des quatre algos testés (MOI, AUTRE_1,
AUTRE_2, AUTRE_3). AUTRE_4 n'a pas pu être testé : son dépôt renvoie une erreur 404.

### Pourquoi les quatre algos plafonnent tous à exactement 507
Tous laissent B hors du cache et gardent A₁ (et J pour certains). Le score vaut alors
1000 × (gain de A₁ + gain de J + petites vidéos) / N, avec N ≈ 2 × 63 × (2³¹−1) requêtes (B et A₁) :
- gain de A₁ = 63 × (2³¹−1) + 1 requêtes × 1 ms ≈ N/2, ce qui donne à lui seul 499 ;
- gain de J = 2³¹−2 ms (une requête), soit ≈ 1000 × 2³¹ / N ≈ 7,9 de plus ;
- les 7 petites vidéos ajoutent 7 ms au total, invisible après arrondi.
1000 × (A₁ + J) / N arrondi vers le bas = 507 pour les quatre : ils construisent tous la même
solution à une vidéo négligeable près.

## L'idée en trois phrases

1. On part de caches vides et on prend les caches un par un (ordre des index).
2. Pour le cache `c`, on gèle tous les autres caches, on calcule pour chaque vidéo le gain qu'elle
   apporterait **en plus** de ce que les autres caches offrent déjà, et on choisit le contenu de `c`
   par un **sac à dos 0/1 résolu exactement**. On ne remplace le contenu que si c'est strictement
   mieux, donc le score ne baisse jamais.
3. On refait des tours complets jusqu'à ce qu'un tour n'améliore plus rien.

## Le sac à dos exact sans DP sur la capacité

Une DP classique a une table de taille (nb d'objets) × (capacité) ou × (somme des valeurs). Ici la
capacité vaut 2³¹−1, les tailles sont 1 et 2³¹−1 (PGCD = 1) et les valeurs dépassent 10²⁰ : aucune
des deux tables n'est envisageable, et diviser par le PGCD ne réduit rien.

On utilise donc la **frontière de Pareto** (Nemhauser–Ullmann) : on garde la liste des couples
(poids total, valeur totale) qu'aucun autre couple ne domine (pas plus lourd ET plus rentable).
Ajouter un objet = décaler toute la liste de (poids, valeur) de l'objet, fusionner avec l'ancienne
liste, et retirer les couples dominés. La réponse est le dernier couple qui tient dans le cache.
La taille de cette liste dépend de la structure des objets, **pas de la grandeur des nombres** :
sur l'instance de repli elle reste de l'ordre de la dizaine de couples.

Garde-fou (inutilisé ici) : si la frontière dépasse `FRONTIER_CAP = 200 000` couples, on prend le
meilleur entre le glouton par densité et le meilleur objet seul, qui garantit au moins la moitié de
l'optimum du sac à dos. La constante borne seulement la mémoire.

## L'instance et pourquoi chacun échoue

Un seul cache de capacité X = 2³¹−1 (`generator/trap_repli2.py`, famille R2) :

- **B** : taille X, remplit exactement le cache. 63 lignes de 2³¹−1 requêtes depuis eB, gain
  2³¹−2 ms chacune : B vaut presque tout le score.
- **A₁** : taille 1, demandée par eA 63 × (2³¹−1) + 1 fois avec un gain de 1 ms : un peu **plus
  demandée** que B après fusion des lignes, et de **densité** (gain / taille) un peu plus grande.
  Sa valeur totale est dérisoire devant celle de B.
- **A₂..A₈** : taille 1, une requête chacune, valeur négligeable.
- **J** : taille 1, une seule requête depuis eB, listée avant B.

| algo | ce qu'il fait | pourquoi c'est faux |
|---|---|---|
| AUTRE_1, AUTRE_2 (gloutons par densité) | prennent A₁ et J d'abord | B ne tient plus |
| AUTRE_3 (tri par valeur) | ne fusionne pas les lignes : la valeur de B, cumulée sur 63 lignes dans un `long long`, déborde et devient négative | B est triée en dernier et ne tient plus |
| MOI `greedy` (tri par nombre de requêtes) | A₁ d'abord (plus demandée) | B ne tient plus |
| MOI `greedy2` (tri par popularité) | idem | idem |
| MOI `greedy3` (une vidéo par endpoint et par cache) | pose J pour eB | B n'est jamais posée |
| MOI `knapsack_slay` | PGCD des tailles = 1, les deux tables dépassent LIMIT | se rabat sur le glouton par densité |
| MOI recherches locales | il faudrait retirer 9 vidéos (J, A₁..A₈) avant d'ajouter B | la descente refuse de dégrader, la liste tabou ne bloque que 7 retours en arrière (avec 7 petites vidéos ou moins, MOI s'en sort) |

Le solveur, lui, évalue **le contenu entier** du cache d'un coup : le sac à dos exact compare
« B seul » à « J + A₁..A₈ » et prend B.

## Complexité

Un tour coûte O(Σ_c Σ_{e relié à c} (nb de vidéos demandées par e) × K) pour les gains marginaux
(K = nombre de caches de l'endpoint), plus un sac à dos par cache en O(n × F), où n est le nombre de
vidéos candidates et F la taille de la frontière de Pareto (pire cas exponentiel, petit ici). Le
nombre de tours est borné par `--max-rounds` (50 par défaut) et chaque tour qui continue a
strictement amélioré le score, donc l'algorithme termine.

Ce solveur vise l'instance de repli, ce n'est pas un concurrent général : sur me_at_the_zoo il fait
500 513 (entre MOI, 499 296, et AUTRE_1, 507 906), et sur les grosses instances la frontière de
Pareto peut grossir jusqu'au garde-fou.

## Risque de notation et variante sûre (`best/instance_repli_sure.in`, 126 octets)

L'instance ci-dessus repose sur des sommes qui dépassent 2⁶³ (c'est ce qui fait déborder AUTRE_3).
Un scoreur C++ en 64 bits les calcule mal : `judge/jugeCorrige.cpp` donnerait −1 500 au solveur, et
`judge/judgeHashCode2017.cpp` (termes en `int` 32 bits) un nombre sans signification (voir
`scorer/judge_emulation.py`). Si la notation se fait avec un tel juge, utiliser la variante sûre :

| | score (identique : scoreur exact, scoreur d'AUTRE_1, les deux juges émulés) |
|---|---|
| borne supérieure | 20 724 800 |
| **ce solveur** | **20 723 000** |
| MOI (10 relances identiques) / AUTRE_1 / AUTRE_2 / AUTRE_3 | 1 999 / 1 999 / 1 799 / 1 999 |
| AUTRE_4 | non testé : dépôt inaccessible |

Facteur ≈ 1,04 × 10⁴. Construction R1 (`generator/trap_repli.py --m 4 --nB 20724 --LDB 103621`) : au
lieu du débordement, AUTRE_3 est piégé par un **cache leurre** (cache 0, gain 1 ms) traité avant le
cache utile ; son tableau `served` (Utils.cpp, ligne 56) lui fait ensuite ignorer B dans le cache 1.
Chaque terme `nb × (LD − L)` et le total des requêtes tiennent en 32 bits. Le facteur est plus faible
parce que la valeur de B (un seul terme) est plafonnée à 2³¹ − 1.
Reproductibilité : `fallback_solver/reproduce.sh best/instance_repli_sure.in best/repli_sure_sorties`
(deux exécutions, SHA-256 identiques, `best/repli_sure_sorties/reproductibilite.txt`).
