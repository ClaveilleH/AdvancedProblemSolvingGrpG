"""Piège d'affectation (famille P), généralisation de l'instance de la promo 6_2_6_2.

Deux caches de capacité X = k (vidéos de taille 1) :
  e0 : relié au cache 0 (latence 1) ET au cache 1 (latence 2) ; demande k vidéos, n0 fois chacune
  e1 : relié au cache 0 seulement (latence 1) ;             demande k autres vidéos, n1 < n0 fois
Tous les algos qui remplissent le cache 0 en premier (ordre des index, ou meilleur gain d'abord)
y mettent les vidéos de e0, un peu plus rentables ; e1 n'a plus rien. Optimum : e1 dans le
cache 0, e0 dans le cache 1 (1 ms de moins par requête). Gain des algos piégés ≈ moitié de l'optimum.

Un algo qui fait un sac à dos exact cache par cache dans l'ordre (type groupe C) garantit au moins
la moitié de l'optimum : le facteur 2 est le maximum possible contre ce type d'algo.

Toutes les valeurs restent dans les bornes de l'énoncé et en 32 bits (LD ≤ 4000, Rn ≤ 10000).

Usage : python generator/trap_affectation.py out.in [--k 3] [--LD 1000] [--n0 10000] [--n1 9999]
"""
import argparse


def build(k, LD, n0, n1):
    V = 2 * k
    lines = [f"{V} 2 {V} 2 {k}", " ".join(["1"] * V),
             f"{LD} 2", "0 1", "1 2",
             f"{LD} 1", "0 1"]
    lines += [f"{v} 0 {n0}" for v in range(k)]
    lines += [f"{k + v} 1 {n1}" for v in range(k)]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--LD", type=int, default=1000)
    ap.add_argument("--n0", type=int, default=10000)
    ap.add_argument("--n1", type=int, default=9999)
    a = ap.parse_args()
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.k, a.LD, a.n0, a.n1))
