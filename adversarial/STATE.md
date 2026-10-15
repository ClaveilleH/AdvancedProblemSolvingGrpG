# STATE — instance adversariale Hash Code 2017

## Reprise
```bash
cd S:/dev/AdvancedProblemSolving/adversarial
export PATH=/c/msys64/mingw64/bin:$PATH          # g++ (AUTRE_3 et juge)
g++ -O2 -std=c++17 -o sandbox/bin/autre3.exe repos/APSJeffersonStorck/*.cpp   # si sandbox/ a été vidé
harness/run_all.sh best/instance_principale.in   # rejoue l'instance principale
fallback_solver/reproduce.sh                     # rejoue l'instance de repli + preuve de reproductibilité
harness/check_repos.sh                           # aucun dépôt modifié
```
Dernier rapport : `reports/LATEST.md`.

## Dépôts (clones en lecture seule dans repos/)
- MOI = AdvancedProblemSolvingGrpG (65d28bf) : best-of (3 gloutons, knapsack DP avec PGCD, LS/tabou)
- AUTRE_1 = hashcode-2017-streaming-videos : glouton paresseux global par densité marginale ; fast-fill si C>20 et Σ_lignes K > 8e6
- AUTRE_2 = hashcode_2017 : glouton par cache (ordre des index), densité marginale, 5 tours
- AUTRE_3 = APSJeffersonStorck (C++) : glouton par cache (ordre des index), tri par valeur, bug `served`, int32
- AUTRE_4 = IkramB23/hashcode2017_streaming_GroupeI : 404, ignoré

## Meilleurs résultats
| objectif | fichier | taille | résultat |
|---|---|---|---|
| principal | best/instance_principale.in (T2, generator/trap_overflow_main.py) | 45 Ko | MOI 2 147 483 646, autres 0 → ratio ∞ au score, écart 2 147 483 646 |
| repli | best/instance_repli.in (R2, trap_repli2.py --m 8 --kB 63 --kA 0) | 2 Ko | solveur 1 073 741 822 964 (borne 1 073 741 823 472), tous les algos 507 → ×2,12e9 |
| variantes | best/variantes/ | | voir best/variantes/LISEZMOI.md |

## Pistes
1. T1 (densité + leurre + bug served) : FAIT, à la borne théorique de la famille (≈2³⁰ au départage).
2. Piste PGCD (demandée) : seul MOI fait une DP, avec PGCD → personne ne s'effondre en temps.
   Retournée contre MOI pour le repli : PGCD = 1 + nombres énormes → knapsack rabattu sur glouton ;
   le solveur de repli utilise une frontière de Pareto (indépendante de la grandeur des nombres).
   Faiblesse de MOI à éviter : PGCD = 1 et table ≤ 1e8 cases → DP Python de plusieurs minutes.
3. R1 (repli) : FAIT. m=4 piège MOI 20/20 relances ; m≤3 et m=6 laissent MOI s'échapper.
4. Fast-fill AUTRE_1 : variante ff1 (55 Ko) faite, piège AUTRE_1 seul.
5. Recherche automatique : generator/search.py (recuit), en cours (seeds main 1, repli 1, repli 2).
6. Baseline officielle : FAITE (rapport 06). Timeout 1200 s ; kittens avec les gloutons seuls pour MOI.

7. Débordement long long d'AUTRE_3 (lignes non fusionnées) : FAIT, utilisé par T2 et R2 (kB ≡ 3 mod 4).

8. Recherche locale de MOI désactivée (TEST_LOCAL_SEARCH = False dans le dépôt de travail, non commité). Harness : MOI_MAIN=<main.py>. Principale et repli inchangés.

9. Kittens : le knapsack de MOI (clone `main`) tourne en DP poids, table 10 000 × 6 001 = 60 M cases, ~20 s par cache,
   soit ~2 h 45 pour 500 caches ; la recherche locale n'est jamais atteinte (trace : results/trace_kittens.log,
   outil harness/trace_moi.py). Sur demande de l'utilisateur, kittens se lance avec les gloutons seuls :
   `MOI_FLAGS="KNAPSACK=0,TEST_LOCAL_SEARCH=0" python harness/run_all.py instances/official/kittens.in`
   (constantes forcées à l'exécution, source non modifié). Meilleur glouton tracé : greedy2, 858 361.

10. FINAL (reports/FINAL.md) : main.py restauré (git checkout), recherche automatique arrêtée.
    Risque de notation : les juges C++ de judge/ débordent sur T2/R2 (MOI à −3 avec jugeCorrige).
    Instances recommandées : best/instance_principale_sure.in (T1, 95 o, ratio ∞ au score, MOI 715 589 352)
    et best/instance_repli_sure.in (R1, 126 o, solveur 20 723 000 vs 1 999 → ×1,04e4).
    Émulation des juges : scorer/judge_emulation.py. AUTRE_4 : non testé (404), à relancer dès qu'un lien arrive.

11. Analyse du tableau de la promo (rapport 07) : AUTRE_1 = groupe A. Piège d'affectation (structure 6_2_6_2,
    generator/trap_affectation.py --k 3 --LD 4000) : best/instance_promo.in, MOI 3 998 499, tous les autres
    (et un substitut de groupe à DP exacte : solver.py --max-rounds 1) 1 999 599 → ×2. MOI robuste pour k ≤ 4.
