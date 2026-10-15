"""Scoreur indépendant Hash Code 2017 « Streaming Videos ».

Usage : python scorer/score.py instance.in solution.out [--json]

Valide la sortie (format, IDs, doublons, capacité) puis calcule le score
officiel : somme des Rn * (LD - L) sur toutes les descriptions de requêtes,
multipliée par 1000, divisée par le nombre total de requêtes, arrondie vers
le bas. Tout est en entiers Python (pas de flottant, pas d'overflow).
Une sortie invalide vaut 0 et la raison est renvoyée.
"""
import json
import sys


def read_instance(path):
    with open(path, "rb") as f:
        tok = f.read().split()
    it = iter(tok)
    nxt = lambda: int(next(it))
    V, E, R, C, X = nxt(), nxt(), nxt(), nxt(), nxt()
    sizes = [nxt() for _ in range(V)]
    ld = []
    links = []          # links[e] = {cache: latence}, on garde la plus petite si doublon
    for _ in range(E):
        l, k = nxt(), nxt()
        ld.append(l)
        d = {}
        for _ in range(k):
            c, lc = nxt(), nxt()
            d[c] = min(lc, d.get(c, lc))
        links.append(d)
    reqs = [(nxt(), nxt(), nxt()) for _ in range(R)]
    return dict(V=V, E=E, R=R, C=C, X=X, sizes=sizes, ld=ld, links=links, reqs=reqs)


def check_instance(inst):
    """Renvoie la liste des incohérences de l'instance (vide si cohérente)."""
    pb = []
    V, E, C = inst["V"], inst["E"], inst["C"]
    if min(V, E, C) < 1 or inst["X"] < 1:
        pb.append("V, E, C, X doivent être >= 1")
    if any(s < 1 for s in inst["sizes"]):
        pb.append("taille de vidéo < 1")
    for e, (l, d) in enumerate(zip(inst["ld"], inst["links"])):
        for c, lc in d.items():
            if not 0 <= c < C:
                pb.append(f"endpoint {e}: cache {c} hors bornes")
            if not 1 <= lc < l:
                pb.append(f"endpoint {e}: latence cache {lc} pas dans [1, LD={l}[")
    for v, e, n in inst["reqs"]:
        if not (0 <= v < V and 0 <= e < E and n > 0):
            pb.append(f"requête invalide {(v, e, n)}")
    return pb


def read_solution(path, inst):
    """Renvoie (caches: dict c -> set(v), erreur ou None)."""
    try:
        with open(path, "r") as f:
            lines = [ln for ln in f.read().split("\n")]
    except OSError as ex:
        return {}, f"sortie illisible: {ex}"
    while lines and lines[-1].strip() == "":
        lines.pop()
    if not lines:
        return {}, "sortie vide"
    try:
        n = int(lines[0].strip())
    except ValueError:
        return {}, "première ligne non entière"
    if not 0 <= n <= inst["C"]:
        return {}, f"N={n} hors de [0, C]"
    if len(lines) - 1 != n:
        return {}, f"N={n} mais {len(lines) - 1} lignes de caches"
    caches = {}
    for ln in lines[1:]:
        try:
            nums = [int(x) for x in ln.split()]
        except ValueError:
            return {}, f"ligne non entière: {ln[:50]!r}"
        if not nums:
            return {}, "ligne de cache vide"
        c, vids = nums[0], nums[1:]
        if not 0 <= c < inst["C"]:
            return {}, f"cache {c} hors bornes"
        if c in caches:
            return {}, f"cache {c} décrit deux fois"
        if any(not 0 <= v < inst["V"] for v in vids):
            return {}, f"vidéo hors bornes dans le cache {c}"
        if len(set(vids)) != len(vids):
            return {}, f"vidéo répétée dans le cache {c}"
        used = sum(inst["sizes"][v] for v in vids)
        if used > inst["X"]:
            return {}, f"cache {c} dépasse la capacité ({used} > {inst['X']})"
        caches[c] = set(vids)
    return caches, None


def score(inst, caches):
    saved = 0
    total = 0
    for v, e, n in inst["reqs"]:
        best = inst["ld"][e]
        for c, lc in inst["links"][e].items():
            if lc < best and v in caches.get(c, ()):
                best = lc
        saved += n * (inst["ld"][e] - best)
        total += n
    return (saved * 1000) // total if total else 0


def evaluate(inst_path, out_path, inst=None):
    inst = inst or read_instance(inst_path)
    caches, err = read_solution(out_path, inst)
    if err:
        return {"valid": False, "score": 0, "error": err}
    return {"valid": True, "score": score(inst, caches), "error": None}


if __name__ == "__main__":
    res = evaluate(sys.argv[1], sys.argv[2])
    if "--json" in sys.argv:
        print(json.dumps(res))
    else:
        print(res["score"] if res["valid"] else f"INVALIDE ({res['error']}) -> 0")
