"""Recherche automatique d'instances par recuit simulé.

Usage :
    python generator/search.py --objective main   --iters 400 --seed 1 [--start best/instance_principale.in]
    python generator/search.py --objective repli  --iters 400 --seed 1 [--start best/instance_repli.in]

Une instance = (X, tailles, endpoints, requêtes). À chaque itération on applique une
mutation aléatoire (changer un nombre, ajouter/retirer une requête, un lien, une vidéo,
un endpoint, permuter deux requêtes), on répare (1 <= Lc < LD, valeurs <= 2^31-1),
on lance les 4 algos via le harness, et on accepte selon le critère de Metropolis.

Objectifs (à maximiser) :
  main  : log10(ratio) + 1e-3 * log10(écart), ratio plafonné à 1e12 (∞ compris)
  repli : log10(meilleur connu / max des 4 algos), où « meilleur connu » est
          l'optimum exact par énumération si V*C <= 16, sinon le solveur de repli.
Pénalité de taille : -1 par tranche de 100 Ko au-delà de 100 Ko.

Seed fixée : la suite de mutations est reproductible (les scores aussi, sauf la
recherche tabou non seedée de MOI, que l'on relance 3 fois en gardant son MEILLEUR score).
Les meilleures instances sont écrites dans instances/search/<objectif>_seed<k>_best.in
et l'historique dans results/search_<objectif>_seed<k>.csv.
"""
import argparse
import csv
import itertools
import math
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
sys.path.insert(0, os.path.join(ROOT, "fallback_solver"))
from run_all import run_instance  # noqa: E402
from score import read_instance, score as score_caches  # noqa: E402
import solver as fsolver  # noqa: E402

INT_MAX = 2**31 - 1
CAP_RATIO = 1e12


# ---------- représentation ----------
def to_text(inst):
    X, sizes, eps, reqs = inst
    lines = [f"{len(sizes)} {len(eps)} {len(reqs)} {inst_C(inst)} {X}", " ".join(map(str, sizes))]
    for ld, links in eps:
        lines.append(f"{ld} {len(links)}")
        lines += [f"{c} {lc}" for c, lc in links]
    lines += [f"{v} {e} {n}" for v, e, n in reqs]
    return "\n".join(lines) + "\n"


def inst_C(inst):
    return 1 + max([c for _, links in inst[2] for c, _ in links] + [0])


def from_file(path):
    d = read_instance(path)
    eps = [(d["ld"][e], sorted(d["links"][e].items())) for e in range(d["E"])]
    return [d["X"], list(d["sizes"]), eps, list(d["reqs"])]


def random_instance(rng):
    V, E, C = rng.randint(2, 5), rng.randint(2, 4), rng.randint(1, 3)
    X = rand_num(rng)
    sizes = [rand_num(rng) for _ in range(V)]
    eps = []
    for _ in range(E):
        ld = rand_num(rng, lo=2)
        cs = rng.sample(range(C), rng.randint(0, C))
        eps.append((ld, [(c, rng.randint(1, ld - 1)) for c in sorted(cs)]))
    reqs = [(rng.randrange(V), rng.randrange(E), rand_num(rng)) for _ in range(rng.randint(2, 6))]
    return repair([X, sizes, eps, reqs])


def rand_num(rng, lo=1):
    """Nombre log-uniforme entre lo et 2^31-1, avec une chance d'être un extrême."""
    r = rng.random()
    if r < 0.1:
        return INT_MAX
    if r < 0.2:
        return lo
    return max(lo, int(10 ** rng.uniform(0, math.log10(INT_MAX))))


def repair(inst):
    X, sizes, eps, reqs = inst
    X = min(max(1, X), INT_MAX)
    sizes = [min(max(1, s), INT_MAX) for s in sizes] or [1]
    neps = []
    for ld, links in eps:
        ld = min(max(2, ld), INT_MAX)
        seen = {}
        for c, lc in links:
            seen[c] = min(max(1, lc), ld - 1)
        neps.append((ld, sorted(seen.items())))
    eps = neps or [(2, [])]
    V, E = len(sizes), len(eps)
    reqs = [(v, e, min(max(1, n), INT_MAX)) for v, e, n in reqs if v < V and e < E] or [(0, 0, 1)]
    return [X, sizes, eps, reqs]


def mutate(inst, rng):
    X, sizes, eps, reqs = inst[0], list(inst[1]), [(l, list(k)) for l, k in inst[2]], list(inst[3])
    C = inst_C(inst)
    op = rng.randrange(11)
    tweak = lambda x: rand_num(rng) if rng.random() < 0.3 else max(1, int(x * 10 ** rng.uniform(-2, 2)))
    if op == 0:
        X = tweak(X)
    elif op == 1:
        i = rng.randrange(len(sizes)); sizes[i] = tweak(sizes[i])
    elif op == 2:
        e = rng.randrange(len(eps)); eps[e] = (tweak(eps[e][0]), eps[e][1])
    elif op == 3 and any(k for _, k in eps):
        e = rng.choice([i for i, (_, k) in enumerate(eps) if k])
        j = rng.randrange(len(eps[e][1])); c, lc = eps[e][1][j]
        eps[e][1][j] = (c, tweak(lc))
    elif op == 4:
        i = rng.randrange(len(reqs)); v, e, n = reqs[i]; reqs[i] = (v, e, tweak(n))
    elif op == 5:
        reqs.append((rng.randrange(len(sizes)), rng.randrange(len(eps)), rand_num(rng)))
    elif op == 6 and len(reqs) > 1:
        reqs.pop(rng.randrange(len(reqs)))
    elif op == 7:
        e = rng.randrange(len(eps)); c = rng.randrange(C + (1 if C < 6 else 0))
        eps[e][1].append((c, rng.randint(1, max(1, eps[e][0] - 1))))
    elif op == 8 and any(k for _, k in eps):
        e = rng.choice([i for i, (_, k) in enumerate(eps) if k]); eps[e][1].pop(rng.randrange(len(eps[e][1])))
    elif op == 9 and len(reqs) > 1:
        i, j = rng.sample(range(len(reqs)), 2); reqs[i], reqs[j] = reqs[j], reqs[i]
    elif op == 10:
        if rng.random() < 0.5 and len(sizes) < 12:
            sizes.append(rand_num(rng))
        elif len(eps) < 8:
            ld = rand_num(rng, lo=2); eps.append((ld, []))
    return repair([X, sizes, eps, reqs])


# ---------- évaluation ----------
def exact_opt(path):
    d = read_instance(path)
    V, C = d["V"], d["C"]
    best = 0
    for mask in itertools.product([0, 1], repeat=V * C):
        caches, ok = {}, True
        for c in range(C):
            s = {v for v in range(V) if mask[c * V + v]}
            if sum(d["sizes"][v] for v in s) > d["X"]:
                ok = False; break
            caches[c] = s
        if ok:
            best = max(best, score_caches(d, caches))
    return best


def known_best(path):
    d = read_instance(path)
    if d["V"] * d["C"] <= 16:
        return exact_opt(path)
    content = fsolver.solve(fsolver.read_instance(path), log=lambda *_: None)
    return score_caches(d, {c: s for c, s in enumerate(content)})


def evaluate(inst, objective, tmpdir):
    path = os.path.join(tmpdir, f"cand_{os.getpid()}.in")
    with open(path, "w", newline="\n") as f:
        f.write(to_text(inst))
    rows, _ = run_instance(path, timeout=60, log=False, quiet=True)
    sc = {r["algo"]: r["score"] for r in rows}
    st = {r["algo"]: r["status"] for r in rows}
    if any(s != "ok" for s in st.values()):
        return -1e9, sc, st, 0, os.path.getsize(path)   # on veut gagner au score, pas par crash
    for _ in range(2):                                   # MOI est randomisé : on garde son meilleur
        r2, _ = run_instance(path, algos=["moi"], timeout=60, log=False, quiet=True)
        sc["moi"] = max(sc["moi"], r2[0]["score"])
    size = os.path.getsize(path)
    pen = max(0, size - 100_000) / 100_000
    others = max(sc[a] for a in sc if a != "moi")
    if objective == "main":
        ratio = CAP_RATIO if others == 0 and sc["moi"] > 0 else (sc["moi"] / others if others else 0)
        ratio = min(ratio, CAP_RATIO)
        f = (math.log10(ratio) if ratio > 0 else -12) + 1e-3 * math.log10(max(1, sc["moi"] - others))
        return f - pen, sc, st, 0, size
    kb = known_best(path)
    allbest = max(sc.values())
    ratio = CAP_RATIO if allbest == 0 and kb > 0 else (kb / allbest if allbest else 0)
    f = math.log10(min(ratio, CAP_RATIO)) if ratio > 0 else -12
    return f - pen, sc, st, kb, size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objective", choices=["main", "repli"], required=True)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--start", default=None)
    ap.add_argument("--T0", type=float, default=1.0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    outdir = os.path.join(ROOT, "instances", "search")
    os.makedirs(outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="search_", dir=os.path.join(ROOT, "sandbox"))
    cur = from_file(a.start) if a.start else random_instance(rng)
    fcur, sc, st, kb, size = evaluate(cur, a.objective, tmp)
    best, fbest = cur, fcur
    tag = f"{a.objective}_seed{a.seed}"
    hist = open(os.path.join(ROOT, "results", f"search_{tag}.csv"), "w", newline="")
    w = csv.writer(hist)
    w.writerow(["iter", "f", "fbest", "moi", "autre1", "autre2", "autre3", "known_best", "bytes", "accepted"])
    for it in range(a.iters):
        T = a.T0 * (1 - it / a.iters) + 1e-3
        cand = mutate(cur, rng) if rng.random() < 0.95 else random_instance(rng)
        f, sc, st, kb, size = evaluate(cand, a.objective, tmp)
        acc = f >= fcur or rng.random() < math.exp((f - fcur) / T)
        if acc:
            cur, fcur = cand, f
        if f > fbest:
            best, fbest = cand, f
            with open(os.path.join(outdir, f"{tag}_best.in"), "w", newline="\n") as fo:
                fo.write(to_text(best))
            print(f"[{it}] nouveau meilleur f={f:.4f} scores={sc} connu={kb} {size}o", flush=True)
        w.writerow([it, round(f, 4), round(fbest, 4), sc.get("moi"), sc.get("autre1"), sc.get("autre2"),
                    sc.get("autre3"), kb, size, int(acc)])
        hist.flush()
    print(f"fin : fbest={fbest:.4f}")


if __name__ == "__main__":
    main()
