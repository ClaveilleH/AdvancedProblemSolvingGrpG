# Rapport final — instance adversariale Hash Code 2017 « Streaming Videos »

Date : 2026-10-15. Tous les scores ci-dessous viennent de la **version commitée de MOI, sans aucune
modification** (`main` sur GitHub, 65d28bf ; voir §5), lancée par `harness/run_all.py` sans option.

> **AUTRE_4 n'a pas été testé.** `https://github.com/IkramB23/hashcode2017_streaming_GroupeI.git`
> renvoie 404 (dépôt privé ou supprimé). Les autres dépôts publics de l'utilisateur IkramB23 ne
> contiennent pas ce projet, et il n'en existe aucune copie dans `repos/` ni dans `sandbox/`.
> **Toutes les instances n'ont été testées que contre 3 adversaires.** Dès qu'un lien ou une archive
> sera fourni, il sera cloné en lecture seule et les instances seront relancées contre lui.

## 1. Recommandation

| | instance à soumettre | pourquoi |
|---|---|---|
| objectif principal | **`best/instance_principale_sure.in`** (95 o) | ratio ∞ **au score** contre les 3 adversaires, aucun débordement nulle part, score identique avec les 5 calculs (§4) |
| objectif de repli | **`best/instance_repli_sure.in`** (126 o) | facteur 1,04 × 10⁴, identique avec les 5 calculs |

Les instances « record » (`best/instance_principale.in`, `best/instance_repli.in`) ont de meilleures
valeurs brutes, mais elles **dépendent d'un scoreur sans débordement** : avec le juge C++ 64 bits du
dépôt (`judge/jugeCorrige.cpp`), MOI obtiendrait **−3** sur la principale. Elles sont gardées comme
variantes, avec ce risque explicite.

## 2. Résultats par instance

Légende du type de victoire : **score** = sortie valide de l'adversaire qui score réellement ce
nombre ; **overflow** = sortie valide, mais le mauvais choix vient d'un débordement dans le code de
l'adversaire ; crash et timeout : aucun cas.

### 2.1 `best/instance_principale_sure.in` — principale, sûre (famille T1) — RECOMMANDÉE

| algo | code retour | sortie | score | type | cause exacte |
|---|---|---|---|---|---|
| **MOI** | 0 | valide (`1 0` : B, vidéo 0, dans le cache 1) | **715 589 352** | — | `algos/greedy.py:10` trie les requêtes par nombre décroissant : B (2 requêtes) passe avant A (1), et `greedy.py:24` la met dans le cache le plus rapide qui a la place (cache 1) |
| AUTRE_1 | 0 | valide (`0 0` / `1 1` : B dans le leurre, A dans le cache 1) | 0 | **score** | glouton global par densité (`main.py:354`, clé `-benefit/size`) : A (densité 1/Mo) passe avant B dans le cache 1 (≈ 0,99999/Mo) ; B ne tient plus et part dans le cache leurre |
| AUTRE_2 | 0 | valide (idem) | 0 | **score** | caches dans l'ordre des index (`solution.py:100`) puis densité (`solution.py:125`) : B dans le leurre (cache 0), puis A d'abord dans le cache 1 |
| AUTRE_3 | 0 | valide (idem) | 0 | **score** | bug `served` (`Utils.cpp:56`) : B est mise dans le cache 0 (leurre, traité en premier), l'endpoint est alors marqué « servi » et le cache 1 ignore B |
| AUTRE_4 | — | — | — | **non testé : dépôt inaccessible** | — |

Pourquoi « 0 » : le gain total des trois adversaires est 3 ms pour N = 3 001 requêtes, soit
1000 × 3 / 3 001 = 0,9997 → arrondi vers le bas à **0**. C'est le score officiel (« rounding down »),
pas une erreur : leurs sorties sont valides (capacité, IDs, format vérifiés par `scorer/score.py`).
Ratio ∞, écart 715 589 352. Toutes les valeurs ≤ 2³¹ − 1, chaque terme `nb × (LD − L)` < 2³¹,
total des requêtes 3 001.

### 2.2 `best/instance_principale.in` — principale, record brut (famille T2) — VARIANTE À RISQUE

| algo | code retour | sortie | score (exact) | type | cause exacte |
|---|---|---|---|---|---|
| **MOI** | 0 | valide (`0 1` : B, vidéo 1, dans le cache 0) | **2 147 483 646** | — | requêtes fusionnées (`utils.py`, `merged`) : B (3 × (2³¹−1) requêtes) est la plus demandée, `greedy` la place en premier |
| AUTRE_1 | 0 | valide (`0 0` : A seule) | 0 | **score** | densité de A juste au-dessus de celle de B (`main.py:354`) |
| AUTRE_2 | 0 | valide (`0 0`) | 0 | **score** | idem (`solution.py:125`) |
| AUTRE_3 | 0 | valide (`0 0`) | 0 | **overflow** | `Utils.cpp:58` cumule `saved * count` dans un `long long` sans fusionner les lignes ; après la 3e ligne de B la somme vaut −4 611 686 037 754 740 730 (valeurs par ligne : 4,6e18, 9,2e18, puis débordement), B est triée en dernier et ne tient plus |
| AUTRE_4 | — | — | — | **non testé : dépôt inaccessible** | — |

Gain des adversaires : 6 442 450 939 ms pour N = 6 442 450 939 001 requêtes → 0,99999999984 → 0.
**Risque majeur** : le gain de MOI (1,38 × 10¹⁹) dépasse 2⁶³. `jugeCorrige.cpp` (64 bits) donnerait
**−3** à MOI ; `judgeHashCode2017.cpp` (termes 32 bits) donnerait 1 288 747 937 à MOI et
−429 582 645 aux autres. La victoire contre AUTRE_3 passe par un débordement de son code.

### 2.3 `best/instance_repli_sure.in` — repli, sûre (famille R1) — RECOMMANDÉE

| algo | code retour | score | cause exacte |
|---|---|---|---|
| **solveur de repli** | 0 | **20 723 000** (borne sup. 20 724 800) | sac à dos exact par frontière de Pareto, cache par cache |
| MOI | 0 | 1 999 (10 relances identiques) | `greedy`/`greedy2` : A₁ plus demandée que B ; `greedy3` : pose J ; knapsack : PGCD des tailles = 1 et nombres énormes, rabattu sur le glouton par densité (`knapsack_slay.py`) ; recherches locales : 5 retraits dégradants nécessaires |
| AUTRE_1 | 0 | 1 999 | densité (A₁, J avant B) |
| AUTRE_2 | 0 | 1 799 | densité, caches dans l'ordre des index |
| AUTRE_3 | 0 | 1 999 | bug `served` via le cache leurre (`Utils.cpp:56`) |
| AUTRE_4 | — | **non testé : dépôt inaccessible** | — |

Type : **score** pour tous (sorties valides, aucun débordement). Facteur solveur / meilleur ≈ 1,04 × 10⁴.

### 2.4 `best/instance_repli.in` — repli, record brut (famille R2) — VARIANTE À RISQUE

| algo | code retour | score (exact) | type | cause exacte |
|---|---|---|---|---|
| **solveur de repli** | 0 | **1 073 741 822 964** (borne 1 073 741 823 472) | — | idem |
| MOI | 0 | 507 (15 relances identiques) | score | mêmes causes que 2.3, avec m = 8 petites vidéos (la liste tabou ne bloque que 7 retours) |
| AUTRE_1 / AUTRE_2 | 0 | 507 / 507 | score | densité |
| AUTRE_3 | 0 | 507 | **overflow** | `Utils.cpp:58`, 63 lignes de B, somme négative |
| AUTRE_4 | — | — | **non testé : dépôt inaccessible** | — |

Facteur ≈ 2,12 × 10⁹. **Risque** : le gain du solveur dépasse 2⁶³ ; `jugeCorrige.cpp` lui donnerait −1 500.

## 3. Reproductibilité du solveur de repli
Deux exécutions par instance, sorties comparées octet par octet (`fallback_solver/reproduce.sh`) :

| instance | score exéc. 1 | score exéc. 2 | SHA-256 (identiques) |
|---|---|---|---|
| repli sûre | 20 723 000 | 20 723 000 | 39c4e6c3…c14cac |
| repli record | 1 073 741 822 964 | 1 073 741 822 964 | cfabffaa…48f92c |

Le solveur n'utilise aucun aléatoire. `fallback_solver/README.md` explique l'algorithme, sa
complexité, la commande exacte, et pourquoi les quatre algos testés plafonnent (à 507 sur la
variante record, à 1 999 / 1 799 sur la variante sûre) ; il précise qu'AUTRE_4 n'a pas été testé.

## 4. Scoreurs et débordements
- `scorer/score.py` : entiers Python (précision arbitraire), aucun débordement possible ; valide
  format, IDs, doublons et capacité.
- Second calcul indépendant : `score.py` du dépôt AUTRE_1 (Python, autre code). Identique sur toutes les sorties.
- Juges C++ du dépôt MOI (`judge/`), qui plantent sous Windows (segfault, même sur me_at_the_zoo) :
  émulés au bit près par `scorer/judge_emulation.py`.
  - `judgeHashCode2017.cpp` (ajouté le 07/10, commit 5532589, probablement le juge d'origine ; rien
    dans `docs/` ne dit lequel les profs utilisent) : `int totalRequest`, terme `nb*(LD-L)` en int 32 bits.
  - `jugeCorrige.cpp` : tout en `long long` (64 bits).
- Sur les deux instances **sûres**, les cinq calculs (exact, AUTRE_1, deux juges, harness) donnent
  exactement les mêmes scores. Sur les deux instances record, les juges C++ débordent (§2.2, §2.4).
- Marge : le score de MOI sur la principale sûre vaut 715 589 352, soit 3 × moins que 2³¹ − 1.

## 5. Modification de `main.py` (historique)
- **Demande** : message « Desactive le local search dans mon algo, il sert a rien et rajoute du
  temps », envoyé après la baseline de trending_today (rapport 05, vers 18:45). Raison donnée : la
  recherche locale « sert à rien et rajoute du temps ».
- **Effet** : `TEST_LOCAL_SEARCH = False` dans `S:\dev\AdvancedProblemSolving\main.py` (branche
  `oral`), jamais commité.
- **Restauration** (à la demande, 19:24) : `git checkout main.py` ; `git status --short main.py` et
  `git diff main.py` sont vides ; le fichier est identique octet par octet au `main.py` de `main`.
- Tous les scores de ce rapport ont été relancés avec cette version commitée, sans `MOI_MAIN` ni
  `MOI_FLAGS`. Ils sont identiques à ceux obtenus sans recherche locale.
- Remarque : la branche locale `oral` (1a4723b) est en retard sur `main` (65d28bf) : `utils.py` et
  `algos/knapsack_slay.py` y diffèrent (pas de fusion des requêtes en double). Les instances T2/R2
  supposent la fusion (version `main`) ; T1/R1 (sûres) n'en dépendent pas.

## 6. Risques connus
1. **AUTRE_4 non testé** (dépôt inaccessible) : aucune garantie contre lui.
2. Les « 0 » reposent sur l'arrondi vers le bas d'un gain moyen < 1 µs (0,9997 sur la sûre). Un
   scoreur qui arrondirait au plus proche donnerait 1 aux adversaires : le ratio deviendrait
   715 589 352 au lieu de ∞, toujours gagné au score.
3. Instances record : débordement des juges C++ (MOI à −3 sur la principale avec le juge 64 bits)
   et victoire contre AUTRE_3 par débordement de son propre code. À ne soumettre que si la notation
   utilise un calcul exact.
4. Requêtes de remplissage : un endpoint sans cache porte la majorité des requêtes. C'est permis
   par le format (l'exemple de l'énoncé en contient un), mais c'est ce qui ramène les autres à 0.
5. Valeurs hors des bornes historiques de l'énoncé (bornes retirées par les profs) ; une variante
   entièrement dans les bornes existe (`best/variantes/t1_bornes_officielles_inf.in`, ratio ∞,
   MOI 249).
6. Le juge du cours (C++) n'a pas pu être exécuté sous Windows ; son comportement est émulé.

## 7. Aucun dépôt modifié
Voir la vérification en fin de fichier (`harness/check_repos.sh`).

### Vérification (2026-10-15 19:29)
```
repos/APSJeffersonStorck : status=0 lignes, diff=0 lignes OK
repos/AdvancedProblemSolvingGrpG : status=0 lignes, diff=0 lignes OK
repos/hashcode-2017-streaming-videos : status=0 lignes, diff=0 lignes OK
repos/hashcode_2017 : status=0 lignes, diff=0 lignes OK
dépôt de travail : 0 modification(s) sur main.py
```
