"""
Statistiques sur les solutions produites par le bench, pour expliquer les scores.

Usage (depuis la racine, après bench.run) :
    python -m bench.solution_stats all
    python -m bench.solution_stats kittens --algos Greedy Greedy2

Lit results/bench/<instance>__<algo>.out, écrit bench/data/solutions.csv.
"""

import argparse
import csv
import os

from bench.common import DATA_DIR, SOLUTIONS_DIR, load_instance, read_solution, select_instances

SOLUTIONS_CSV = f"{DATA_DIR}/solutions.csv"
ALGOS = ["Greedy", "Greedy2", "Greedy3", "KS_indep", "KS_maj"]
FIELDS = ["instance", "algo", "n_placed", "n_useless", "useless_share", "wasted_capacity_share",
          "copies_per_video", "served_by_cache_share", "fill_rate"]


def stats(data, caches):
    """
    Un placement (cache, vidéo) est inutile si aucune requête n'est servie par lui :
    chaque requête est attribuée à son cache le plus rapide (le premier en cas d'égalité).
    """
    sizes, endpoints, requests = data["video_sizes"], data["endpoints"], data["requests"]
    sets = [set(cache) for cache in caches]
    useful = [set() for _ in caches]        # vidéos utiles de chaque cache
    served, total = 0, 0

    for video_id, endpoint_id, nb_requests in requests:
        latency, linked_caches = endpoints[endpoint_id]
        total += nb_requests
        best, best_cache = latency, None
        for cache_id, cache_latency in linked_caches:
            if video_id in sets[cache_id] and cache_latency < best:
                best, best_cache = cache_latency, cache_id
        if best_cache is not None:
            served += nb_requests
            useful[best_cache].add(video_id)

    n_placed = sum(len(s) for s in sets)
    n_useless = sum(len(s) - len(u) for s, u in zip(sets, useful))
    used = sum(sizes[v] for s in sets for v in s)
    wasted = sum(sizes[v] for s, u in zip(sets, useful) for v in s - u)
    distinct = len(set().union(*sets)) if sets else 0
    capacity = data["N_cache"] * data["S_cache"]
    return {
        "n_placed": n_placed,
        "n_useless": n_useless,
        "useless_share": round(n_useless / n_placed, 4) if n_placed else 0,
        # part de la capacité totale occupée par des placements inutiles
        "wasted_capacity_share": round(wasted / capacity, 4) if capacity else 0,
        "copies_per_video": round(n_placed / distinct, 3) if distinct else 0,
        # part des requêtes servies par un cache plutôt que par le datacenter
        "served_by_cache_share": round(served / total, 4) if total else 0,
        "fill_rate": round(used / capacity, 4) if capacity else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Statistiques sur les solutions du bench")
    parser.add_argument("instances", nargs="+", help="google, promo, all, ou des noms d'instances")
    parser.add_argument("--algos", nargs="+", default=ALGOS)
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SOLUTIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for instance in select_instances(args.instances):
            paths = {algo: f"{SOLUTIONS_DIR}/{instance}__{algo}.out" for algo in args.algos}
            paths = {algo: path for algo, path in paths.items() if os.path.exists(path)}
            if not paths:
                continue
            data = load_instance(instance)
            for algo, path in paths.items():
                row = {"instance": instance, "algo": algo}
                row.update(stats(data, read_solution(path, data["N_cache"])))
                writer.writerow(row)
                f.flush()
                print(row)


if __name__ == "__main__":
    main()
