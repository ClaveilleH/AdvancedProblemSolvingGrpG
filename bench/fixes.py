"""
Versions corrigées des recherches locales, pour mesurer l'effet des corrections proposées
sans modifier algos/local_search.py. Chaque fonction enveloppe l'originale.

Corrections (voir docs/oral/diapo.md) :
  1. les tabu search rendent la meilleure solution rencontrée, pas le dernier état visité ;
  2. la graine est un paramètre ;
  3. la descente rend la meilleure solution rencontrée, elle aussi.
"""

import random

from algos.local_search import local_search, random_tabu_search, sorted_tabu_search
from utils import compute_cost


def _restore(data, caches, caches_sizes, solution):
    """Remet `solution` dans `caches` (en place) et recalcule la place restante de chaque cache."""
    sizes = data["video_sizes"]
    for cache_id, cache in enumerate(solution):
        caches[cache_id] = cache
        caches_sizes[cache_id] = data["S_cache"] - sum(sizes[v] for v in cache)


def random_tabu_search_fix(data, caches, caches_sizes, nb_forbidden_moves, iteration=10, nbCaches=None, nbVideos=None, seed=None):
    if seed is not None:
        random.seed(seed)
    best = random_tabu_search(data, caches, caches_sizes, nb_forbidden_moves, iteration, nbCaches, nbVideos)
    _restore(data, caches, caches_sizes, best)
    return best


def sorted_tabu_search_fix(data, caches, caches_sizes, nb_forbidden_moves, iteration=10, nbCaches=None, nbVideos=None):
    best = sorted_tabu_search(data, caches, caches_sizes, nb_forbidden_moves, iteration, nbCaches, nbVideos)
    _restore(data, caches, caches_sizes, best)
    return best


def local_search_fix(data, caches, caches_sizes, iteration=10, nbCaches=None, nbVideos=None, supp=False):
    """
    Descente : un mouvement à la fois, en gardant la meilleure solution rencontrée.
    On ne s'arrête pas au premier mouvement sans gain : retirer une vidéo inutile ne rapporte rien
    sur le moment mais libère la place d'un ajout qui rapporte.
    """
    best_cost = compute_cost(caches, data["endpoints"], data["requests"])
    best = [list(cache) for cache in caches]
    for _ in range(iteration):
        local_search(data, caches, caches_sizes, iteration=1, previous_moves=None,
                     nbCaches=nbCaches, nbVideos=nbVideos, supp=supp)
        cost = compute_cost(caches, data["endpoints"], data["requests"])
        if cost < best_cost:
            best_cost = cost
            best = [list(cache) for cache in caches]
    _restore(data, caches, caches_sizes, best)
    return caches, caches_sizes
