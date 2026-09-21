import time
from copy import deepcopy
from functools import partial

from utils import compute_cost, make_adj_list, read_input_file, print_comparison_table, compute_score
from greedy import greedy
from greedy2 import greedy2
from local_search import local_search, random_tabu_search, sorted_tabu_search, preprocess_data


def snapshot(caches, caches_sizes, endpoints, requests):
    return {
        "cost": compute_cost(caches, endpoints, requests),
        "score": compute_score(caches, endpoints, requests),
        "caches": deepcopy(caches),
        "caches_sizes": deepcopy(caches_sizes),
    }


def run(label, algo, start, container, data, base_cost, results):
    """Lance `algo` depuis l'état `start` et enregistre le résultat."""
    caches = [container(c) for c in start["caches"]]   # list ou set selon l'algo
    sizes = deepcopy(start["caches_sizes"])

    t = time.time()
    algo(data, caches, sizes)
    dt = time.time() - t

    res = snapshot(caches, sizes, data["endpoints"], data["requests"])
    results[label] = res
    gain = (base_cost - res["cost"]) / base_cost * 100
    print(f"[{dt:.4f}s] {label} : {res['cost']} ({gain:.2f}%) | Score: {res['score']:.2f}")




def main(args):
    if len(args) != 1:
        print("Usage: python greedy.py <input_file>")
        return

    # ========================== INIT ==========================

    
    input_file = args[0]
    N_vid, N_endpoint, N_request, N_cache, S_cache, video_sizes, endpoints, requests = read_input_file(input_file)
    empty_caches = [[] for _ in range(N_cache)]  # la liste des videos stockés dans chaque cache
    empty_sizes = [S_cache] * N_cache  # la taille restante de chaque cache

    current_time = time.time()
    base_cost = compute_cost(empty_caches, endpoints, requests)
    print(f"[{time.time() - current_time:.4f}s] Base cost (no videos in caches): {base_cost}")

    current_time = time.time()
    global adj_list
    adj_list = make_adj_list(N_vid, N_request, requests)
    print(f"[{time.time() - current_time:.4f}s] Adjacency list created")

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
        "adj_list": adj_list,
    }

    results = {}
    starts = { "":snapshot(empty_caches, empty_sizes, endpoints, requests) }
    results["Base"] = starts[""]

    for label, algo in [("Greedy", greedy), ("Greedy2", greedy2)]:
        run(label, algo, starts[""], list, data, base_cost, results)
    starts["g"] = results["Greedy"]
    starts["g2"] = results["Greedy2"]

    video_sizes_sorted, videos_info = preprocess_data(N_vid, N_endpoint, N_request, N_cache, empty_sizes, video_sizes, empty_caches, endpoints, requests)

    local_search_func   = partial(local_search, iteration=5, previous_moves=None, nbCaches=10, nbVideos=10, supp=True)
    tabu_search_func = partial(random_tabu_search, nb_forbidden_moves=7, iteration=100, nbCaches=10, nbVideos=10)
    sorted_tabu_search_func = partial(sorted_tabu_search, nb_forbidden_moves=7, iteration=100, nbCaches=10, nbVideos=10)

    algos = [
        ("LS", local_search_func, list),
        ("TS", tabu_search_func, set),
        ("TSS", sorted_tabu_search_func, set),
    ]

    for label, algo, container in algos:
        for start_label in ["", "g", "g2"]:
            run(f"{label} ({start_label})", algo, starts[start_label], container, data, base_cost, results)


    # ---------- Bilan ----------
    print_comparison_table(results, metric="score", higher_is_better=True)
    best_method = min(results, key=lambda x: results[x]["cost"])
    print(f"\nBest method: {best_method} with cost {results[best_method]['cost']} and improvement of "
          f"{base_cost - results[best_method]['cost']} ({(base_cost - results[best_method]['cost']) / base_cost * 100:.2f}%) | Score: {results[best_method]['score']:.2f}")


def test_fct(data, caches, caches_sizes, fonction, fonction_name):
    current_time = time.time()
    fonction(data, caches, caches_sizes)
    time_taken = time.time() - current_time
    pass

if __name__ == "__main__":
    import sys
    # if len(sys.argv) < 2:
    #     main(["instances/me_at_the_zoo.in"])  # Default input file for testing
    # else:
        # main(sys.argv[1:])
    main(sys.argv[1:]) or main(["instances/me_at_the_zoo.in"])  # Default input file for testing