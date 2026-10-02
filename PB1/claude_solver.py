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
import os
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


def _knapsack_reduced(item_sizes, item_gains, capacity, lower_bound):
    """
    Sac à dos 0/1 exact sur beaucoup d'objets : on élimine d'abord ceux dont le sort est certain.
    Objets triés par densité, s = premier objet qui ne rentre plus (objet "de rupture"). La relaxation
    continue donne une borne sup de la valeur si on force un objet dedans (ou dehors) ; si cette borne est
    sous lower_bound (valeur d'une solution connue), l'objet est fixé dehors (ou dedans). Le sac à dos
    par programmation dynamique ne porte plus que sur les objets restants.
    Retourne (valeur, indices pris) ; la valeur peut être < lower_bound si rien de mieux n'existe.
    """
    n = len(item_sizes)
    sizes_f = item_sizes.astype(np.float64)
    gains_f = item_gains.astype(np.float64)
    density = gains_f / np.maximum(sizes_f, 1e-9)
    order = np.argsort(-density, kind="stable")
    cum_w = np.cumsum(sizes_f[order])
    s = int(np.searchsorted(cum_w, capacity, side="right"))  # objets order[:s] rentrent tous
    if s >= n:
        return int(item_gains.sum()), list(range(n))
    w_before = cum_w[s - 1] if s > 0 else 0.0
    p_before = gains_f[order[:s]].sum()
    d_break = density[order[s]]
    residual = capacity - w_before

    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)
    inside = rank < s
    # borne si on force l'objet dedans (pour ceux hors du préfixe) ou dehors (pour ceux du préfixe)
    bound = np.where(inside,
                     p_before - gains_f + (residual + sizes_f) * d_break,
                     p_before + gains_f + (residual - sizes_f) * d_break)
    decided = bound < lower_bound - 1e-6
    fixed_in = np.flatnonzero(decided & inside)
    core = np.flatnonzero(~decided)
    core_capacity = capacity - int(item_sizes[fixed_in].sum())
    value, chosen = _knapsack(item_sizes[core], item_gains[core], core_capacity)
    return value + int(item_gains[fixed_in].sum()), list(fixed_in) + [int(core[i]) for i in chosen]


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
    else:
        # exact sur toutes les vidéos, après élimination par bornes (l'ancien contenu sert de borne inf)
        new_value, chosen = _knapsack_reduced(sizes[candidates], gains[candidates], capacity, max(old_value, 0))
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


# ######################################## MILP (sous-ensemble de caches) ########################################

def _snapshot_state(state):
    return state.member.copy(), state.remaining.copy(), state.cur.copy()


def _restore_state(state, saved):
    state.member[:], state.remaining[:], state.cur[:] = saved


def _reoptimize_milp(state, free_caches, time_limit=60, rel_gap=0.0, window=None):
    """
    Vide les caches de free_caches et les re-remplit ensemble de façon optimale (programme linéaire
    en nombres entiers, solveur HiGHS de scipy), les autres caches étant fixés.
    x[c,v] = 1 si la vidéo v est dans le cache c ; y[r,c] = part de la requête r servie par c.
    Retourne le temps gagné en plus (0 si le solveur ne fait pas mieux : on remet l'ancien contenu).
    """
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import coo_matrix

    index = state.index
    sizes, sav, rv, re, rn = index["sizes"], index["sav"], index["rv"], index["re"], index["rn"]
    free_caches = np.asarray(free_caches)
    before = state.saved()
    saved = _snapshot_state(state)

    touched = np.flatnonzero(state.member[free_caches].any(axis=0))
    state.member[free_caches] = False
    for video_id in touched:
        state.refresh_video(video_id)

    # variables y : (requête, cache libre) avec un gain positif par rapport aux caches fixés
    delta = sav[free_caches][:, re] - state.cur  # (k, R)
    np.maximum(delta, 0, out=delta)
    if window is not None:
        # comme dans le sac à dos : par cache, seulement les vidéos les plus denses + l'ancien contenu
        size_div = np.maximum(sizes, 1e-9)
        for k in range(len(free_caches)):
            gains = np.bincount(rv, weights=delta[k] * rn, minlength=state.N_vid)
            order = np.argsort(-(gains / size_div), kind="stable")
            order = order[gains[order] > 0]
            allowed = np.zeros(state.N_vid, dtype=bool)
            allowed[order[np.cumsum(sizes[order]) <= window * state.S_cache]] = True
            allowed[saved[0][free_caches[k]]] = True
            delta[k, ~allowed[rv]] = 0
    yk, yr = np.nonzero(delta > 0)
    if len(yk) == 0:
        _restore_state(state, saved)
        return 0
    ycoef = (delta[yk, yr] * rn[yr]).astype(np.float64)
    ny = len(yk)

    # variables x : couples (cache libre, vidéo) utiles
    pair_key = yk.astype(np.int64) * state.N_vid + rv[yr]
    pairs, y_to_x = np.unique(pair_key, return_inverse=True)
    nx = len(pairs)
    xk, xv = pairs // state.N_vid, pairs % state.N_vid

    rows, cols, vals, ub = [], [], [], []
    # y <= x
    r0 = np.arange(ny)
    rows += [r0, r0]; cols += [nx + r0, y_to_x]; vals += [np.ones(ny), -np.ones(ny)]
    ub.append(np.zeros(ny))
    n_rows = ny
    # somme des y d'une requête <= 1
    req_ids, req_row = np.unique(yr, return_inverse=True)
    rows.append(n_rows + req_row); cols.append(nx + r0); vals.append(np.ones(ny))
    ub.append(np.ones(len(req_ids)))
    n_rows += len(req_ids)
    # capacité
    rows.append(n_rows + xk); cols.append(np.arange(nx)); vals.append(sizes[xv].astype(np.float64))
    ub.append(np.full(len(free_caches), float(state.S_cache)))
    n_rows += len(free_caches)

    A = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n_rows, nx + ny)).tocsr()
    ub = np.concatenate(ub)
    cost = np.concatenate([np.zeros(nx), -ycoef])
    integrality = np.concatenate([np.ones(nx), np.zeros(ny)])
    res = milp(cost, constraints=LinearConstraint(A, -np.inf, ub), integrality=integrality, bounds=Bounds(0, 1),
               options={"time_limit": time_limit, "mip_rel_gap": rel_gap})
    state.milp_optimal = res.status == 0
    if res.x is None:
        _restore_state(state, saved)
        return 0

    chosen = res.x[:nx] > 0.5
    state.member[free_caches[xk[chosen]], xv[chosen]] = True
    state.remaining[free_caches] = state.S_cache - state.member[free_caches] @ sizes
    if (state.remaining[free_caches] < 0).any():
        _restore_state(state, saved)
        return 0
    for video_id in np.unique(xv[chosen]):
        state.refresh_video(video_id)
    after = state.saved()
    if after <= before:
        _restore_state(state, saved)
        return 0
    return after - before


def claude_milp(data, caches, caches_sizes, free_caches=None, time_limit=60, rel_gap=0.0):
    """Re-remplit de façon optimale les caches de free_caches (tous par défaut) : à réserver aux petites instances."""
    state = _State(data, caches)
    if free_caches is None:
        free_caches = list(range(state.N_cache))
    _reoptimize_milp(state, free_caches, time_limit, rel_gap)
    state.write_back(caches, caches_sizes)
    return caches


# ######################################## LNS ########################################

def _reoptimize_group_knapsack(state, group):
    """
    Variante rapide de _reoptimize_milp : on vide tous les caches du groupe, puis on les re-remplit
    l'un après l'autre par sac à dos exact (dans l'ordre donné). Annulé si le résultat n'est pas meilleur.
    """
    before = state.saved()
    saved = _snapshot_state(state)
    group = np.asarray(group)
    touched = np.flatnonzero(state.member[group].any(axis=0))
    state.member[group] = False
    state.remaining[group] = state.S_cache
    for video_id in touched:
        state.refresh_video(video_id)
    for cache_id in group:
        _reoptimize_cache(state, int(cache_id), None)
    after = state.saved()
    if after <= before:
        _restore_state(state, saved)
        return 0
    return after - before


def _lns(state, time_limit, group_size=5, milp_time=30, window=None, seed=0, verbose=False, mode="milp"):
    """
    Recherche à voisinage large : on tire un petit groupe de caches "voisins" (qui partagent des endpoints),
    on le re-remplit de façon optimale avec _reoptimize_milp, et on recommence jusqu'à time_limit secondes.
    Le score ne peut que monter.
    """
    rng = np.random.default_rng(seed)
    start = time.time()
    linked = (state.index["sav"] > 0).astype(np.float64)
    related = linked @ linked.T  # nombre d'endpoints en commun
    np.fill_diagonal(related, 0)
    n_calls = 0
    last_print = start
    while time.time() - start < time_limit:
        first = int(rng.integers(state.N_cache))
        weights = related[first]
        k = min(group_size, state.N_cache) - 1
        if k > 0 and (weights > 0).sum() >= k:
            others = rng.choice(state.N_cache, size=k, replace=False, p=weights / weights.sum())
            group = [first] + [int(c) for c in others]
        else:
            group = [first]
        budget = min(milp_time, time_limit - (time.time() - start))
        if budget <= 0.5:
            break
        if mode == "milp":
            _reoptimize_milp(state, group, budget, 0.0, window)
        else:
            _reoptimize_group_knapsack(state, group)
        n_calls += 1
        if verbose and time.time() - last_print > 30:
            last_print = time.time()
            print(f"---> lns {n_calls} groupes : score {state.score()} [{time.time() - start:.0f}s]", flush=True)
    if verbose:
        print(f"---> lns fin, {n_calls} groupes : score {state.score()} [{time.time() - start:.0f}s]", flush=True)


# ---------- version parallèle ----------

_WORKER = {}


def _worker_solve(group, member_bits, cur, milp_time, window):
    """Dans un processus fils : re-remplit `group` à partir de l'état reçu, renvoie le nouveau contenu ou None."""
    state = _WORKER["state"]
    state.member = np.unpackbits(member_bits, axis=1, count=state.N_vid).astype(bool)
    state.cur = cur.astype(np.int64)
    state.remaining = state.S_cache - state.member @ state.index["sizes"]
    if _reoptimize_milp(state, group, milp_time, 0.0, window) <= 0:
        return group, None
    return group, np.packbits(state.member[group], axis=1)


def _apply_group(state, group, rows_bits):
    """Applique un contenu calculé sur un état peut-être périmé ; annulé s'il n'améliore pas l'état actuel."""
    before = state.saved()
    saved = _snapshot_state(state)
    rows = np.unpackbits(rows_bits, axis=1, count=state.N_vid).astype(bool)
    changed = np.flatnonzero((state.member[group] != rows).any(axis=0))
    state.member[group] = rows
    state.remaining[group] = state.S_cache - rows @ state.index["sizes"]
    for video_id in changed:
        state.refresh_video(video_id)
    if state.saved() <= before:
        _restore_state(state, saved)
        return False
    return True


def _lns_parallel(state, time_limit, group_size=3, milp_time=30, window=None, seed=0, verbose=False, workers=None):
    """
    Comme _lns, mais plusieurs groupes (disjoints) sont résolus en même temps dans des processus séparés.
    Un résultat peut avoir été calculé sur un état déjà modifié par un autre groupe : il est donc réévalué
    sur l'état courant et n'est gardé que s'il améliore vraiment le score.
    """
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

    if workers is None:
        workers = max(1, (os.cpu_count() - 2) // 2)
    rng = np.random.default_rng(seed)
    start = time.time()
    linked = (state.index["sav"] > 0).astype(np.float64)
    related = linked @ linked.T
    np.fill_diagonal(related, 0)

    _WORKER["state"] = state  # hérité par fork : l'index n'est pas recopié
    pool = ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("fork"))
    busy = np.zeros(state.N_cache, dtype=bool)
    pending = set()
    n_done = n_kept = 0
    last_print = start

    def submit():
        free = np.flatnonzero(~busy)
        if len(free) == 0:
            return False
        first = int(rng.choice(free))
        weights = related[first] * ~busy
        weights[first] = 0
        k = min(group_size, state.N_cache) - 1
        group = [first]
        if k > 0 and (weights > 0).sum() >= k:
            group += [int(c) for c in rng.choice(state.N_cache, size=k, replace=False, p=weights / weights.sum())]
        busy[group] = True
        budget = min(milp_time, time_limit - (time.time() - start))
        pending.add(pool.submit(_worker_solve, group, np.packbits(state.member, axis=1), state.cur.astype(np.int32), budget, window))
        return True

    try:
        while True:
            while len(pending) < workers and time.time() - start < time_limit - 1 and submit():
                pass
            if not pending:
                break
            finished, _ = wait(pending, timeout=1, return_when=FIRST_COMPLETED)
            for future in finished:
                pending.discard(future)
                group, rows_bits = future.result()
                busy[group] = False
                n_done += 1
                if rows_bits is not None and _apply_group(state, group, rows_bits):
                    n_kept += 1
            if time.time() - start >= time_limit:
                break
            if verbose and time.time() - last_print > 30:
                last_print = time.time()
                print(f"---> lns {n_done} groupes ({n_kept} gardés) : score {state.score()} [{time.time() - start:.0f}s]", flush=True)
    finally:
        for future in pending:
            future.cancel()
        processes = list((getattr(pool, "_processes", None) or {}).values())
        pool.shutdown(wait=False, cancel_futures=True)
        for process in processes:  # les MILP en cours ne servent plus à rien
            process.terminate()
        _WORKER.clear()
    if verbose:
        print(f"---> lns fin, {n_done} groupes ({n_kept} gardés) : score {state.score()} [{time.time() - start:.0f}s]", flush=True)


def claude_lns(data, caches, caches_sizes, time_limit=60, group_size=5, milp_time=30, window=None, seed=0, verbose=False):
    """Recherche à voisinage large (groupes de caches re-remplis exactement) pendant time_limit secondes."""
    state = _State(data, caches)
    _lns(state, time_limit, group_size, milp_time, window, seed, verbose)
    state.write_back(caches, caches_sizes)
    return caches


# ######################################## CACHES IDENTIQUES ########################################

def _pack_identical(state):
    """
    Cas particulier (trending_today) : tous les caches sont équivalents pour tous les endpoints.
    Mettre une vidéo dans un cache ou un autre rapporte pareil, et une seule copie suffit : le problème
    devient un rangement des vidéos utiles dans les caches. On remplit les caches un par un, chacun
    exactement à ras bord si possible (sac à dos avec valeur = taille, grosses vidéos d'abord).
    Ne garde le résultat que s'il est meilleur. Retourne True si appliqué.
    """
    index = state.index
    sizes, sav, rv, re, rn = index["sizes"], index["sav"], index["rv"], index["re"], index["rn"]
    used_endpoints = np.unique(re)
    if state.N_cache == 0 or len(used_endpoints) == 0:
        return False
    if (sav[:, used_endpoints].min(axis=0) != sav[:, used_endpoints].max(axis=0)).any():
        return False

    before = state.saved()
    saved = _snapshot_state(state)
    capacity = state.S_cache

    value = np.bincount(rv, weights=sav[0, re] * rn, minlength=state.N_vid)
    items = np.flatnonzero((value > 0) & (sizes <= capacity))
    # si tout ne rentre pas, on ne garde que les vidéos les plus denses
    items = items[np.argsort(-(value[items] / np.maximum(sizes[items], 1e-9)), kind="stable")]
    items = items[np.cumsum(sizes[items]) <= capacity * state.N_cache]
    left = list(items[np.argsort(-sizes[items], kind="stable")])  # grosses vidéos d'abord

    state.member[:] = False
    for cache_id in range(state.N_cache):
        if not left:
            break
        everything = np.array(left)
        cumulated = np.cumsum(sizes[everything])
        factor = 3
        while True:
            # on élargit le choix tant que le cache n'est pas plein à ras bord
            arr = everything[:int(np.searchsorted(cumulated, factor * capacity)) + 1]
            filled, chosen = _knapsack(sizes[arr], sizes[arr], capacity)
            if filled == capacity or len(arr) == len(everything):
                break
            factor *= 2
        taken = arr[chosen]
        state.member[cache_id, taken] = True
        taken_set = set(int(v) for v in taken)
        left = [v for v in left if int(v) not in taken_set]

    state.remaining[:] = capacity - state.member @ sizes
    state.cur[:] = 0
    for video_id in np.flatnonzero(state.member.any(axis=0)):
        state.refresh_video(video_id)
    if state.saved() <= before:
        _restore_state(state, saved)
        return False
    return True


# ######################################## PIPELINE ########################################

SMALL_MILP_PAIRS = 5000  # en dessous, on résout toute l'instance d'un coup


def claude_best(data, caches, caches_sizes, time_limit=900, group_size=3, milp_time=30, lns_window="auto", seed=0, verbose=False):
    """
    Meilleure méthode : glouton, sac à dos par cache, puis selon l'instance
    - caches tous identiques : rangement exact (_pack_identical) ;
    - petite instance : résolution exacte de tout le problème ;
    - sinon : recherche à voisinage large jusqu'à time_limit secondes (temps total de la fonction).
    """
    start = time.time()
    state = _State(data, caches)
    _greedy(state)
    if verbose:
        print(f"---> greedy : score {state.score()}", flush=True)
    _knapsack_passes(state, 200, time_limit / 4, None, seed, False)
    if verbose:
        print(f"---> knapsack : score {state.score()} [{time.time() - start:.0f}s]", flush=True)

    used = np.unique(state.index["re"])
    sav = state.index["sav"]
    identical = len(used) > 0 and not (sav[:, used].min(axis=0) != sav[:, used].max(axis=0)).any()
    if identical:
        _pack_identical(state)
        if verbose:
            print(f"---> caches identiques, rangement exact : score {state.score()}", flush=True)
        state.write_back(caches, caches_sizes)
        return caches

    index = state.index
    n_pairs = len(np.unique(index["rv"])) * state.N_cache
    done = False
    if n_pairs <= SMALL_MILP_PAIRS:
        state.milp_optimal = False
        _reoptimize_milp(state, list(range(state.N_cache)), max(1, min(120, time_limit - (time.time() - start))))
        done = state.milp_optimal
        if verbose:
            print(f"---> milp complet (optimal prouvé : {done}) : score {state.score()}", flush=True)
    if not done:
        if lns_window == "auto":
            # instance dense (chaque cache voit beaucoup de requêtes) : on limite les candidats du MILP
            links_per_cache = (index["sav"][:, index["re"]] > 0).sum() / max(1, state.N_cache)
            lns_window = 8 if links_per_cache > 50000 else None
        _lns(state, time_limit - (time.time() - start), group_size, milp_time, lns_window, seed, verbose)
    state.write_back(caches, caches_sizes)
    return caches
