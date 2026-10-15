"""Substitut d'un groupe qui aurait une bonne recherche locale : recuit simulé générique.

Usage : python harness/ls_proxy.py instance.in depart.out sortie.out [--iters 300000] [--seed 1] [--T0 auto]

Part d'une solution (par ex. la sortie piégée d'AUTRE_1, ou un fichier vide « 0 ») et applique des
mouvements aléatoires, chacun évalué exactement (on ne recalcule que les requêtes des vidéos touchées) :
  - ajouter une vidéo à un cache (si elle tient),
  - retirer une vidéo d'un cache,
  - échanger : retirer une vidéo d'un cache et en mettre une autre (si elle tient),
  - déplacer une vidéo d'un cache vers un autre.
Les vidéos candidates d'un cache sont celles que demandent ses endpoints (voisinage « intelligent »).
Acceptation de Metropolis, température décroissante géométriquement de T0 à T0/1e4. On garde la
meilleure solution vue. Seed fixée : reproductible.
"""
import argparse
import math
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scorer"))
from score import read_instance, read_solution, score  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance"); ap.add_argument("start"); ap.add_argument("out")
    ap.add_argument("--iters", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--T0", type=float, default=None)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    inst = read_instance(a.instance)
    C, X, sizes, ld, links = inst["C"], inst["X"], inst["sizes"], inst["ld"], inst["links"]
    by_video = {}
    for v, e, n in inst["reqs"]:
        by_video.setdefault(v, []).append((e, n))
    cand = [set() for _ in range(C)]
    for v, lst in by_video.items():
        for e, _ in lst:
            for c in links[e]:
                if sizes[v] <= X:
                    cand[c].add(v)
    cand = [sorted(s) for s in cand]
    caches, err = read_solution(a.start, inst)
    content = [set(caches.get(c, ())) for c in range(C)]
    used = [sum(sizes[v] for v in s) for s in content]
    useful = [c for c in range(C) if cand[c]]

    def gain(v):
        g = 0
        for e, n in by_video.get(v, ()):
            best = ld[e]
            for c, lc in links[e].items():
                if lc < best and v in content[c]:
                    best = lc
            g += n * (ld[e] - best)
        return g

    cur = sum(gain(v) for v in by_video)
    best_val, best_sol = cur, [set(s) for s in content]
    T0 = a.T0 or max(1.0, cur / max(1, len(inst["reqs"])) )   # ~ gain moyen d'une requête-description
    for it in range(a.iters):
        T = T0 * (1e-4) ** (it / a.iters)
        c = rng.choice(useful)
        r = rng.random()
        changes = []                       # liste de (cache, vidéo, +1 ajout / -1 retrait)
        if r < 0.3:
            v = rng.choice(cand[c])
            if v in content[c]:
                changes = [(c, v, -1)]
            elif used[c] + sizes[v] <= X:
                changes = [(c, v, +1)]
        elif r < 0.7 and content[c]:
            u = rng.choice(sorted(content[c])); v = rng.choice(cand[c])
            if v not in content[c] and used[c] - sizes[u] + sizes[v] <= X:
                changes = [(c, u, -1), (c, v, +1)]
        elif content[c]:
            v = rng.choice(sorted(content[c])); c2 = rng.choice(useful)
            if c2 != c and v not in content[c2] and used[c2] + sizes[v] <= X:
                changes = [(c, v, -1), (c2, v, +1)]
        if not changes:
            continue
        vids = {v for _, v, _ in changes}
        before = sum(gain(v) for v in vids)
        for cc, v, s in changes:
            (content[cc].add if s > 0 else content[cc].discard)(v); used[cc] += s * sizes[v]
        delta = sum(gain(v) for v in vids) - before
        if delta >= 0 or rng.random() < math.exp(delta / T):
            cur += delta
            if cur > best_val:
                best_val, best_sol = cur, [set(s) for s in content]
        else:
            for cc, v, s in reversed(changes):
                (content[cc].discard if s > 0 else content[cc].add)(v); used[cc] -= s * sizes[v]
    with open(a.out, "w", newline="\n") as f:
        used_c = [(c, s) for c, s in enumerate(best_sol) if s]
        f.write(f"{len(used_c)}\n")
        for c, s in used_c:
            f.write(" ".join(map(str, [c] + sorted(s))) + "\n")
    print(score(inst, {c: s for c, s in enumerate(best_sol)}))


if __name__ == "__main__":
    main()
