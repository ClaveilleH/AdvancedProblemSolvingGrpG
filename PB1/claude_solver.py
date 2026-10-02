"""
Solveur Hash Code 2017 (Streaming Videos) -- fichiers "claude_*", séparés du reste du code.

Toutes les fonctions publiques ont la même signature que greedy / greedy2 / local_search :

    algo(data, caches, caches_sizes)

- data         : le dictionnaire construit dans main.py (N_vid, N_cache, S_cache, video_sizes, endpoints, requests, ...)
- caches       : liste (une entrée par cache) de list ou de set d'id de vidéos, modifiée en place
- caches_sizes : place restante dans chaque cache, modifiée en place

Elles partent de l'état reçu dans `caches` (vide, ou résultat d'un autre algo) et sont donc
utilisables telles quelles avec `run(...)` de main.py.

Algos :
- claude_greedy   : glouton sur les couples (cache, vidéo) triés par gain / taille, gains remis à jour après chaque ajout
- claude_knapsack : pour chaque cache, on fixe les autres et on re-remplit le cache de façon optimale (sac à dos exact), en boucle
- claude_solve    : claude_greedy puis claude_knapsack
"""
import random
import time

import numpy as np


# ######################################## INDEX ########################################

_index_cache = {}


def build_index(data):
    """
    Pré-calcul (une seule fois par instance) des tableaux numpy utilisés par les algos :
    - sav[c][e] : temps gagné par requête si l'endpoint e est servi par le cache c (0 si non relié)
    - rv, re, rn : requêtes fusionnées par couple (vidéo, endpoint), triées par vidéo
    - ptr[v]..ptr[v+1] : tranche des requêtes de la vidéo v (même idée que adj_list)
    """
    requests = data["requests"]
    cached = _index_cache.get(id(requests))
    if cached is not None and cached["requests"] is requests:
        return cached

    N_vid = data["N_vid"]
    N_cache = data["N_cache"]
    S_cache = data["S_cache"]
    endpoints = data["endpoints"]
    sizes = np.array(data["video_sizes"], dtype=np.int64)

    sav = np.zeros((N_cache, len(endpoints)), dtype=np.int64)
    for endpoint_id, (endpoint_latency, linked_caches) in enumerate(endpoints):
        for cache_id, cache_latency in linked_caches:
            if endpoint_latency - cache_latency > sav[cache_id, endpoint_id]:
                sav[cache_id, endpoint_id] = endpoint_latency - cache_latency
    linked = sav.max(axis=0) > 0 if N_cache > 0 else np.zeros(len(endpoints), dtype=bool)

    # fusion des requêtes identiques, on ignore celles qui ne peuvent rien gagner
    merged = {}
    for video_id, endpoint_id, num_requests in requests:
        if sizes[video_id] <= S_cache and linked[endpoint_id]:
            key = (video_id, endpoint_id)
            merged[key] = merged.get(key, 0) + num_requests
    keys = sorted(merged)
    rv = np.array([k[0] for k in keys], dtype=np.int64)
    re = np.array([k[1] for k in keys], dtype=np.int64)
    rn = np.array([merged[k] for k in keys], dtype=np.int64)
    ptr = np.searchsorted(rv, np.arange(N_vid + 1))

    index = {
        "requests": requests,
        "sizes": sizes,
        "sav": sav,
        "rv": rv, "re": re, "rn": rn, "ptr": ptr,
        "total_requests": sum(r[2] for r in requests),
    }
    _index_cache[id(requests)] = index
    return index


class _State:
    """Etat courant : member[c][v] = vidéo v dans le cache c, cur[r] = gain actuel par requête r."""

    def __init__(self, data, caches):
        self.index = build_index(data)
        self.N_vid = data["N_vid"]
        self.N_cache = data["N_cache"]
        self.S_cache = data["S_cache"]
        sizes = self.index["sizes"]

        self.member = np.zeros((self.N_cache, self.N_vid), dtype=bool)
        for cache_id, cache in enumerate(caches):
            if cache:
                self.member[cache_id, list(cache)] = True
        # on ne fait pas confiance à caches_sizes : la place restante est recalculée
        self.remaining = self.S_cache - self.member @ sizes

        self.cur = np.zeros(len(self.index["rv"]), dtype=np.int64)
        for video_id in np.flatnonzero(self.member.any(axis=0)):
            self.refresh_video(video_id)

    def refresh_video(self, video_id):
        """Recalcule le gain courant des requêtes de video_id à partir des caches qui la contiennent."""
        index = self.index
        lo, hi = index["ptr"][video_id], index["ptr"][video_id + 1]
        if lo == hi:
            return
        holders = np.flatnonzero(self.member[:, video_id])
        if len(holders) == 0:
            self.cur[lo:hi] = 0
        else:
            self.cur[lo:hi] = index["sav"][np.ix_(holders, index["re"][lo:hi])].max(axis=0)

    def cache_gains(self, cache_id):
        """gain[v] = temps total gagné en ajoutant la vidéo v au cache cache_id (les autres caches fixés)."""
        index = self.index
        delta = index["sav"][cache_id, index["re"]] - self.cur
        np.maximum(delta, 0, out=delta)
        gains = np.bincount(index["rv"], weights=delta * index["rn"], minlength=self.N_vid)
        return np.rint(gains).astype(np.int64)

    def saved(self):
        return int((self.cur * self.index["rn"]).sum())

    def score(self):
        total = self.index["total_requests"]
        return self.saved() * 1000 // total if total > 0 else 0

    def write_back(self, caches, caches_sizes):
        """Recopie l'état dans les structures de main.py (en gardant list ou set)."""
        for cache_id in range(self.N_cache):
            container = type(caches[cache_id])
            caches[cache_id] = container(int(v) for v in np.flatnonzero(self.member[cache_id]))
            caches_sizes[cache_id] = int(self.remaining[cache_id])


def claude_score(data, caches):
    """Score Hash Code (entier) d'une solution, version rapide de utils.compute_score."""
    return _State(data, caches).score()


def claude_cost(data, caches):
    """Même valeur que utils.compute_cost, en version rapide."""
    index = build_index(data)
    cached = _index_cache.get(("base_cost", id(data["requests"])))
    if cached is None:
        endpoints = data["endpoints"]
        cached = sum(n * endpoints[e][0] for _, e, n in data["requests"])
        _index_cache[("base_cost", id(data["requests"]))] = cached
    return cached - _State(data, caches).saved()


# ######################################## GREEDY ########################################

def _greedy(state):
    index = state.index
    sizes, sav, re, rn, ptr = index["sizes"], index["sav"], index["re"], index["rn"], index["ptr"]
    member, remaining, cur = state.member, state.remaining, state.cur
    sizes_div = np.maximum(sizes, 1e-9)  # TestGenerate peut produire des vidéos de taille 0

    # density[c][v] = gain / taille du couple (c, v), 0 si le couple est impossible
    density = np.zeros((state.N_cache, state.N_vid))
    for cache_id in range(state.N_cache):
        row = state.cache_gains(cache_id) / sizes_div
        row[sizes > remaining[cache_id]] = 0
        row[member[cache_id]] = 0
        density[cache_id] = row

    # meilleur couple par cache ; les gains ne font que baisser donc une valeur périmée
    # reste une borne sup, on ne recalcule la ligne que quand elle arrive en tête
    rows = np.arange(state.N_cache)
    best_vid = density.argmax(axis=1)
    best_val = density[rows, best_vid]
    dirty = np.zeros(state.N_cache, dtype=bool)

    while True:
        cache_id = int(best_val.argmax())
        if best_val[cache_id] <= 0:
            break
        if dirty[cache_id]:
            best_vid[cache_id] = density[cache_id].argmax()
            best_val[cache_id] = density[cache_id, best_vid[cache_id]]
            dirty[cache_id] = False
            continue

        video_id = int(best_vid[cache_id])
        member[cache_id, video_id] = True
        remaining[cache_id] -= sizes[video_id]

        lo, hi = ptr[video_id], ptr[video_id + 1]
        ends = re[lo:hi]
        np.maximum(cur[lo:hi], sav[cache_id, ends], out=cur[lo:hi])

        # seuls les gains de cette vidéo changent (dans tous les caches)
        column = (np.maximum(sav[:, ends] - cur[lo:hi], 0) * rn[lo:hi]).sum(axis=1) / sizes_div[video_id]
        column[member[:, video_id]] = 0
        column[remaining < sizes[video_id]] = 0
        density[:, video_id] = column
        dirty[best_vid == video_id] = True

        # et les vidéos qui ne rentrent plus dans ce cache
        density[cache_id, sizes > remaining[cache_id]] = 0
        dirty[cache_id] = True


def claude_greedy(data, caches, caches_sizes):
    """
    Glouton : on ajoute à chaque étape le couple (cache, vidéo) de meilleur gain / taille,
    le gain étant le temps réellement gagné vu ce qui est déjà placé.
    """
    state = _State(data, caches)
    _greedy(state)
    state.write_back(caches, caches_sizes)
    return caches


# ######################################## KNAPSACK ########################################

def _knapsack(item_sizes, item_gains, capacity):
    """Sac à dos 0/1 exact. Retourne (valeur, indices des objets pris)."""
    n = len(item_sizes)
    dp = np.zeros(capacity + 1, dtype=np.int64)
    keep = np.zeros((n, capacity + 1), dtype=bool)
    for i in range(n):
        s, g = int(item_sizes[i]), int(item_gains[i])
        if s == 0:
            dp += g
            keep[i] = True
            continue
        cand = dp[:-s] + g
        better = cand > dp[s:]
        keep[i, s:] = better
        np.copyto(dp[s:], cand, where=better)

    chosen = []
    w = capacity
    for i in range(n - 1, -1, -1):
        if keep[i, w]:
            chosen.append(i)
            w -= int(item_sizes[i])
    return int(dp[capacity]), chosen


def _reoptimize_cache(state, cache_id, window):
    """
    Vide le cache cache_id et le re-remplit de façon optimale, les autres caches étant fixés.
    Retourne le temps gagné en plus (>= 0, l'ancien contenu reste une solution possible).
    """
    index = state.index
    sizes, sav, rv, re = index["sizes"], index["sav"], index["rv"], index["re"]
    capacity = state.S_cache

    old = np.flatnonzero(state.member[cache_id])
    state.member[cache_id, old] = False
    for video_id in old:
        state.refresh_video(video_id)

    gains = state.cache_gains(cache_id)
    old_value = int(gains[old].sum()) if state.remaining[cache_id] >= 0 else -1

    candidates = np.flatnonzero((gains > 0) & (sizes <= capacity))
    if window is not None and len(candidates) > 0:
        # on ne garde que les vidéos les plus denses (window fois la capacité) + l'ancien contenu
        order = candidates[np.argsort(-(gains[candidates] / np.maximum(sizes[candidates], 1e-9)), kind="stable")]
        selected = order[np.cumsum(sizes[order]) <= window * capacity]
        candidates = np.union1d(selected, old[gains[old] > 0])

    new_value, chosen = _knapsack(sizes[candidates], gains[candidates], capacity)
    if new_value > old_value:
        new = candidates[chosen]
    else:
        new, new_value = old, old_value

    state.member[cache_id, new] = True
    state.remaining[cache_id] = capacity - sizes[new].sum()
    in_cache = state.member[cache_id, rv]
    np.maximum(state.cur, np.where(in_cache, sav[cache_id, re], 0), out=state.cur)
    return new_value - old_value


def _knapsack_passes(state, max_passes, time_limit, window, seed, verbose):
    rng = random.Random(seed)
    start = time.time()
    order = list(range(state.N_cache))
    for pass_id in range(max_passes):
        rng.shuffle(order)
        improvement = 0
        for cache_id in order:
            if time_limit is not None and time.time() - start > time_limit:
                return
            improvement += _reoptimize_cache(state, cache_id, window)
        if verbose:
            print(f"---> knapsack pass {pass_id + 1} : +{improvement} | score {state.score()} [{time.time() - start:.1f}s]")
        if improvement == 0:
            return


def claude_knapsack(data, caches, caches_sizes, max_passes=50, time_limit=None, window=4, seed=0, verbose=False):
    """
    Recherche locale par cache : on prend les caches un par un et on remplace leur contenu
    par la solution optimale du sac à dos (gain de chaque vidéo calculé avec les autres caches fixés).
    Le coût ne peut que baisser. On s'arrête quand une passe complète n'améliore plus rien.

    window : on limite le sac à dos aux vidéos les plus denses (taille cumulée <= window * capacité),
             None = toutes les vidéos (exact mais beaucoup plus lent).
    """
    state = _State(data, caches)
    _knapsack_passes(state, max_passes, time_limit, window, seed, verbose)
    state.write_back(caches, caches_sizes)
    return caches


def claude_solve(data, caches, caches_sizes, max_passes=50, time_limit=None, window=4, seed=0, verbose=False):
    """claude_greedy puis claude_knapsack."""
    state = _State(data, caches)
    _greedy(state)
    if verbose:
        print(f"---> greedy : score {state.score()}")
    _knapsack_passes(state, max_passes, time_limit, window, seed, verbose)
    state.write_back(caches, caches_sizes)
    return caches
