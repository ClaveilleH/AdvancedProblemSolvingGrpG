"""Trace l'exécution de MOI sans modifier son code : on enveloppe ses fonctions à l'exécution.

Usage (depuis une copie jetable du dépôt, voir trace_moi.sh) :
    python -u trace_moi.py <instance.in>

Affiche, horodaté depuis le lancement :
  - le début et la fin de chaque glouton, du knapsack et de chaque recherche locale ;
  - pour chaque sac à dos résolu : n° du cache traité, méthode (DP poids, DP valeur, glouton),
    nombre d'objets, taille de la table et durée.
"""
import sys
import time

import main as M
import algos.knapsack_slay as K

T0 = time.perf_counter()
NB = {"sacs": 0}


def log(msg):
    print(f"[{time.perf_counter() - T0:8.1f}s] {msg}", flush=True)


def wrap_phase(name, f):
    def g(*a, **k):
        log(f"DÉBUT {name}")
        t = time.perf_counter()
        r = f(*a, **k)
        log(f"FIN   {name} ({time.perf_counter() - t:.1f}s)")
        return r
    return g


def wrap_sack(kind, f):
    def g(values, weights, cap):
        NB["sacs"] += 1
        n = len(values)
        cells = n * (cap + 1) if kind == "DP poids" else (n * (sum(values) + 1) if kind == "DP valeur" else 0)
        t = time.perf_counter()
        r = f(values, weights, cap)
        log(f"  sac n°{NB['sacs']:4d} {kind:9s} n={n:5d} capacité={cap} table={cells:,} cases "
            f"-> {time.perf_counter() - t:.2f}s")
        return r
    return g


K.knapsack_weight = wrap_sack("DP poids", K.knapsack_weight)
K.knapsack_value = wrap_sack("DP valeur", K.knapsack_value)
K.knapsack_goulton = wrap_sack("glouton", K.knapsack_goulton)
for name in ["greedy", "greedy2", "greedy3", "multi_knapsack",
             "local_search", "random_tabu_search", "sorted_tabu_search"]:
    setattr(M, name, wrap_phase(name, getattr(M, name)))
log(f"constantes : KNAPSACK={M.KNAPSACK} TEST_LOCAL_SEARCH={M.TEST_LOCAL_SEARCH}")
M.main([sys.argv[1].replace("\\", "/")])
log("FIN main")
