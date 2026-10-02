"""
Lanceur des algos de claude_solver.py, même usage que main.py :

    python claude_main.py                      -> instances/test.in
    python claude_main.py instances/kittens.in
    python claude_main.py all

Les solutions sont écrites dans results/<instance>_claude.out (format du juge).
"""
import os
import time
from copy import deepcopy
from functools import partial

from utils import read_input_file, make_adj_list, create_results_files, print_gap_to_best
from claude_solver import claude_greedy, claude_knapsack, claude_best, claude_score, claude_cost

INSTANCES_DIR = "instances"
RESULTS_DIR = "results"
# temps accordé à claude_best par instance (la consigne : moins de 20 min par exécution, lecture et écriture comprises)
TIME_LIMIT = int(os.environ.get("CLAUDE_TIME", 900))
INSTANCES_FILES = [
    "test.in",
    "me_at_the_zoo.in",
    "trending_today.in",
    "videos_worth_spreading.in",
    "kittens.in",
]


def claude_snapshot(data, caches, caches_sizes):
    """Même dictionnaire que utils.snapshot, mais calculé avec numpy (utils.compute_cost est trop lent sur kittens)."""
    return {
        "cost": claude_cost(data, caches),
        "score": claude_score(data, caches),
        "caches": deepcopy(caches),
        "caches_sizes": deepcopy(caches_sizes),
    }


def run(label, algo, start, container, data, base_cost, results):
    """Lance `algo` depuis l'état `start` et enregistre le résultat (même rôle que main.run)."""
    caches = [container(c) for c in start["caches"]]
    sizes = deepcopy(start["caches_sizes"])

    t = time.time()
    algo(data, caches, sizes)
    dt = time.time() - t

    res = claude_snapshot(data, caches, sizes)
    results[label] = res
    gain = (base_cost - res["cost"]) / base_cost * 100 if base_cost else 0.0
    print(f"[{dt:.4f}s] {label} : {res['cost']} ({gain:.2f}%) | Score: {res['score']}")


def main(args):
    if len(args) != 1:
        print("Usage: python claude_main.py <input_file>")
        return

    input_file = args[0]
    N_vid, N_endpoint, N_request, N_cache, S_cache, video_sizes, endpoints, requests = read_input_file(input_file)
    empty_caches = [[] for _ in range(N_cache)]
    empty_sizes = [S_cache] * N_cache

    data = {
        "N_vid": N_vid,
        "N_endpoint": N_endpoint,
        "N_request": N_request,
        "N_cache": N_cache,
        "N_requests": N_request,
        "S_cache": S_cache, "cache_size": S_cache,
        "video_sizes": video_sizes,
        "endpoints": endpoints,
        "requests": requests,
        "adj_list": make_adj_list(N_vid, N_request, requests),
    }

    results = {}
    results["Base"] = claude_snapshot(data, empty_caches, empty_sizes)
    base_cost = results["Base"]["cost"]

    run("ClaudeBest", partial(claude_best, time_limit=TIME_LIMIT, verbose=True), results["Base"], set, data, base_cost, results)

    print_gap_to_best(results, metric="score", higher_is_better=True)
    best_method = min(results, key=lambda x: results[x]["cost"])

    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    output_file = os.path.basename(input_file).split('.')[0] + '_claude.out'
    create_results_files(results[best_method]["caches"], f"{RESULTS_DIR}/{output_file}")
    print(f"\nBest method: {best_method} | Score: {results[best_method]['score']} -> {RESULTS_DIR}/{output_file}")
    return results[best_method]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        main([f"{INSTANCES_DIR}/{INSTANCES_FILES[0]}"])
    elif sys.argv[1] == "all":
        results = {}
        for input_file in [f"{INSTANCES_DIR}/{f}" for f in INSTANCES_FILES]:
            print(f"\n=== Running on {input_file} ===")
            results[input_file] = main([input_file])
        print("\n=== Summary of all instances ===")
        for input_file, res in results.items():
            print(f"{input_file}: cost={res['cost']}, score={res['score']}")
        print(f"Total score: {sum(res['score'] for res in results.values())}")
    else:
        main(sys.argv[1:])
