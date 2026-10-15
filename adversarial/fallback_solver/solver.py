"""Solveur de repli : ascension cache par cache avec sac à dos EXACT.

Usage : python fallback_solver/solver.py instance.in sortie.out [--max-rounds 50]

Idée (détails et justification dans README.md) :
  1. On part de caches vides.
  2. On parcourt les caches dans l'ordre des index. Pour le cache c, on fixe le
     contenu de tous les autres caches et on calcule, pour chaque vidéo v, le
     gain qu'apporterait v si elle était dans c (gain marginal par rapport aux
     autres caches seulement). Le meilleur contenu de c est alors un sac à dos
     0/1 exact : poids = tailles, valeurs = ces gains, capacité = X.
  3. On remplace le contenu de c par la solution du sac à dos si elle est
     strictement meilleure que le contenu actuel. Le score global ne peut donc
     que monter.
  4. On recommence des tours complets tant qu'un tour améliore quelque chose.

Le sac à dos est résolu exactement par la méthode de Nemhauser–Ullmann :
on maintient la liste des couples (poids, valeur) non dominés. Sa taille ne
dépend pas de la grandeur des nombres (contrairement à une DP indexée sur la
capacité ou sur la valeur), seulement de la structure des objets.

Aucun aléatoire : même entrée = même sortie.
"""
import argparse
from collections import defaultdict

# Au-delà de ce nombre de couples non dominés, la frontière de Pareto devient
# trop coûteuse : on garde alors le meilleur de deux heuristiques classiques
# (glouton par densité, meilleur objet seul), qui garantissent la moitié de
# l'optimum. Ce garde-fou ne sert pas sur l'instance de repli (frontière < 50).
FRONTIER_CAP = 200_000


def read_instance(path):
    with open(path, "rb") as f:
        it = iter(f.read().split())
    nxt = lambda: int(next(it))
    V, E, R, C, X = nxt(), nxt(), nxt(), nxt(), nxt()
    sizes = [nxt() for _ in range(V)]
    ld, links = [], []
    for _ in range(E):
        l, k = nxt(), nxt()
        ld.append(l)
        d = {}
        for _ in range(k):
            c, lc = nxt(), nxt()
            d[c] = min(lc, d.get(c, lc))
        links.append(d)
    # requêtes identiques (même vidéo, même endpoint) fusionnées
    agg = defaultdict(int)
    for _ in range(R):
        v, e, n = nxt(), nxt(), nxt()
        agg[v, e] += n
    reqs = [(v, e, n) for (v, e), n in agg.items()]
    return V, E, C, X, sizes, ld, links, reqs


def knapsack_exact(items, capacity):
    """Sac à dos 0/1 exact par frontière de Pareto (Nemhauser–Ullmann).

    items : liste de (id, poids, valeur), valeurs > 0, poids <= capacity.
    Renvoie (valeur optimale, ensemble des id choisis).
    Chaque état de la frontière est (poids, valeur, id_objet, état_parent) :
    la chaîne des parents redonne les objets choisis sans copier d'ensembles.
    """
    frontier = [(0, 0, None, None)]          # trié par poids croissant, valeur croissante
    for oid, w, val in items:
        shifted = [(fw + w, fv + val, oid, st) for st in frontier
                   for fw, fv in [(st[0], st[1])] if fw + w <= capacity]
        # fusion des deux listes triées par poids, en gardant les non dominés
        merged, i, j = [], 0, 0
        best_v = -1
        while i < len(frontier) or j < len(shifted):
            if j == len(shifted) or (i < len(frontier) and
                                     (frontier[i][0], -frontier[i][1]) <= (shifted[j][0], -shifted[j][1])):
                cand = frontier[i]; i += 1
            else:
                cand = shifted[j]; j += 1
            if cand[1] > best_v:                 # strictement plus de valeur pour un poids >=
                merged.append(cand)
                best_v = cand[1]
        frontier = merged
        if len(frontier) > FRONTIER_CAP:
            return knapsack_half_approx(items, capacity)
    best = frontier[-1]                          # valeur max (la frontière est croissante)
    chosen, st = set(), best
    while st[2] is not None:
        chosen.add(st[2])
        st = st[3]
    return best[1], chosen


def knapsack_half_approx(items, capacity):
    """Garde-fou : meilleur entre glouton par densité et meilleur objet seul."""
    order = sorted(items, key=lambda t: (-t[2] / t[1], t[0]))
    tot_w = tot_v = 0
    bag = set()
    for oid, w, val in order:
        if tot_w + w <= capacity:
            bag.add(oid); tot_w += w; tot_v += val
    single = max(items, key=lambda t: (t[2], -t[0]))
    if single[2] > tot_v:
        return single[2], {single[0]}
    return tot_v, bag


def solve(inst, max_rounds=50, log=print):
    V, E, C, X, sizes, ld, links, reqs = inst
    cache_eps = [[] for _ in range(C)]          # cache -> [(endpoint, latence)]
    for e, d in enumerate(links):
        for c, lc in d.items():
            cache_eps[c].append((e, lc))
    reqs_by_ep = defaultdict(list)              # endpoint -> [(vidéo, nb)]
    for v, e, n in reqs:
        reqs_by_ep[e].append((v, n))
    content = [set() for _ in range(C)]

    def best_without(e, v, c):
        """Meilleure latence pour (e, v) en ignorant le cache c."""
        best = ld[e]
        for c2, l2 in links[e].items():
            if c2 != c and l2 < best and v in content[c2]:
                best = l2
        return best

    def gains_for(c):
        g = defaultdict(int)
        for e, lc in cache_eps[c]:
            for v, n in reqs_by_ep[e]:
                b = best_without(e, v, c)
                if lc < b:
                    g[v] += n * (b - lc)
        return g

    for rnd in range(1, max_rounds + 1):
        improved = False
        for c in range(C):
            g = gains_for(c)
            current = sum(g.get(v, 0) for v in content[c])
            items = [(v, sizes[v], val) for v, val in sorted(g.items())
                     if val > 0 and sizes[v] <= X]
            if not items:
                continue
            val, bag = knapsack_exact(items, X)
            if val > current:
                content[c] = bag
                improved = True
        log(f"tour {rnd} : {'amélioration' if improved else 'stable'}")
        if not improved:
            break
    return content


def write_output(path, content):
    used = [(c, s) for c, s in enumerate(content) if s]
    with open(path, "w", newline="\n") as f:
        f.write(f"{len(used)}\n")
        for c, s in used:
            f.write(" ".join(map(str, [c] + sorted(s))) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("output")
    ap.add_argument("--max-rounds", type=int, default=50)
    a = ap.parse_args()
    write_output(a.output, solve(read_instance(a.instance), a.max_rounds))
