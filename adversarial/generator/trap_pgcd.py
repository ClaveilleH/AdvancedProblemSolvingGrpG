"""Instance « PGCD pur » (famille G) : des sacs à dos indépendants, difficiles, à grand facteur commun.

C caches indépendants : le cache c n'est relié qu'à l'endpoint e_c (latence 1, datacenter LD), qui
demande n vidéos qui lui sont propres. Chaque cache est donc un sac à dos 0/1 :
  - taille réduite w_i tirée dans [wmin, wmax], capacité réduite K ;
  - valeur v_i = w_i + R (« fortement corrélée ») : les petites vidéos sont un peu plus denses,
    les grosses valent plus ; les gloutons (densité ou valeur) laissent de la place perdue.
    La valeur passe par le nombre de requêtes : Rn = v_i, gain par requête LD - 1.
  - tailles réelles = g * w_i, capacité réelle X = g * K.
Un sac à dos exact qui divise par le PGCD (= g) a une table n × K ; sans division, n × g·K.
Seed fixée : même seed = même fichier. Tout reste en 32 bits (vérifié).

Usage : python generator/trap_pgcd.py out.in [--C 30] [--n 50] [--K 10000] [--w 100 1000]
        [--R 100] [--g 100000] [--LD 4001] [--seed 1]
"""
import argparse
import random

INT_MAX = 2**31 - 1


def build(C, n, K, wmin, wmax, R, g, LD, seed):
    rng = random.Random(seed)
    X = g * K
    assert X <= INT_MAX and g * wmax <= INT_MAX and (wmax + R) * (LD - 1) <= INT_MAX
    sizes, reqs = [], []
    for c in range(C):
        for _ in range(n):
            w = rng.randint(wmin, wmax)
            sizes.append(g * w)
            reqs.append((len(sizes) - 1, c, w + R))
    rng.shuffle(reqs)
    lines = [f"{len(sizes)} {C} {len(reqs)} {C} {X}", " ".join(map(str, sizes))]
    for c in range(C):
        lines += [f"{LD} 1", f"{c} 1"]
    lines += [f"{v} {e} {k}" for v, e, k in reqs]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--C", type=int, default=30)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--K", type=int, default=10000)
    ap.add_argument("--w", type=int, nargs=2, default=[100, 1000])
    ap.add_argument("--R", type=int, default=100)
    ap.add_argument("--g", type=int, default=100000)
    ap.add_argument("--LD", type=int, default=4001)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.C, a.n, a.K, a.w[0], a.w[1], a.R, a.g, a.LD, a.seed))
