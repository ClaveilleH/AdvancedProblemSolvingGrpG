"""Substitut d'un groupe qui fait un sac à dos exact par cache SANS diviser par le PGCD.

Usage : python harness/dp_raw_proxy.py instance.in sortie.out

Caches traités dans l'ordre des index ; pour chacun, valeurs = gains marginaux par rapport aux caches
déjà remplis ; sac à dos 0/1 exact par programmation dynamique indexée sur la capacité brute X
(table des meilleures valeurs de taille X + 1, et une table de choix de n × (X + 1) octets pour
reconstruire la solution), comme le ferait une implémentation classique.
Sur une instance ordinaire, il se comporte comme `fallback_solver/solver.py --max-rounds 1`.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scorer"))
from score import read_instance  # noqa: E402


def main():
    inst = read_instance(sys.argv[1])
    C, X, sizes, ld, links = inst["C"], inst["X"], inst["sizes"], inst["ld"], inst["links"]
    best = {}                                  # (e, v) -> meilleure latence actuelle
    content = [set() for _ in range(C)]
    for c in range(C):
        val = {}
        for v, e, n in inst["reqs"]:
            if c in links[e]:
                cur = best.get((e, v), ld[e])
                g = n * max(0, cur - links[e][c])
                if g > 0 and sizes[v] <= X:
                    val[v] = val.get(v, 0) + g
        items = sorted(val.items())
        if not items:
            continue
        dp = [0] * (X + 1)
        keep = [bytearray(X + 1) for _ in items]
        for i, (v, g) in enumerate(items):
            w = sizes[v]
            for cap in range(X, w - 1, -1):
                if dp[cap - w] + g > dp[cap]:
                    dp[cap] = dp[cap - w] + g
                    keep[i][cap] = 1
        cap = X
        for i in range(len(items) - 1, -1, -1):
            if keep[i][cap]:
                v = items[i][0]
                content[c].add(v)
                cap -= sizes[v]
        for v in content[c]:
            for vv, e, n in inst["reqs"]:
                if vv == v and c in links[e]:
                    best[(e, v)] = min(best.get((e, v), ld[e]), links[e][c])
    with open(sys.argv[2], "w", newline="\n") as f:
        used = [(c, s) for c, s in enumerate(content) if s]
        f.write(f"{len(used)}\n")
        for c, s in used:
            f.write(" ".join(map(str, [c] + sorted(s))) + "\n")


if __name__ == "__main__":
    main()
