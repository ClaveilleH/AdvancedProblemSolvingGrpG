import time
from copy import deepcopy
from functools import partial
import os

from utils import *
from greedy import greedy
from greedy2 import greedy2
from greedy3 import greedy3
from local_search import local_search, random_tabu_search, sorted_tabu_search, preprocess_data
from store import *
from knapsack import multi_knapsack

PRINT = True

KNAPSACK = False

BEST_OF_GREEDY = True

TEST_LOCAL_SEARCH = False

INSTANCES_DIR = "instances"
RESULTS_DIR = "results"
INSTANCES_FILES = [
    "test.in",
    "me_at_the_zoo.in",
    "trending_today.in",
    "videos_worth_spreading.in",
    "kittens.in",
]
INSTANCES_FILES = [
    "test.in",
    "custom_dejavu42.in",
    "custom_universallambda42.in",
    "custom_universallambda42_asymmetric.in",
    "instance1.in",
    "instance2.in",
    "4990_246_84901_50.in",
    "6970_311_100000_69.in",
    "10000_500_100000_100.in",
    "3860_246_84901_66.in",
    "regional_instance.in",
    "zipF_instance.in",
    "big.in",
    "supra.in",
    "INSATANC2D.in",
    "INSTANCED.in",
    "2_2_2_1.in",
    "4_2_4_2.in",
    "6_2_6_2.in",
    "8_2_8_2.in",
    "20_2_20_2.in",
    "realistic_large_clustered.in",
    "realistic_large_random.in",
    "dense.in",
    "dense2.in",
    "medium_mixed_lambda.in",
    "medium_skew_dense_dejavu.in",
    "medium_skew_sparse_lambda.in",
    "medium_flat_dense_dejavu.in",
    "medium_flat_sparse_lambda.in"
]
USED_METHODS = ["Greedy", "Greedy2", "Greedy3", "LS", "TS", "TSS"]


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
    if PRINT:
        print(f"[{time.time() - current_time:.4f}s] Base cost (no videos in caches): {base_cost}")

    current_time = time.time()
    global adj_list
    adj_list = make_adj_list(N_vid, N_request, requests)
    if PRINT:
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

    results, starts, best_greedy = best_of_greedy(data, empty_caches, empty_sizes, endpoints, requests, base_cost)
    
    if PRINT:
        print("===============================================================")

    if KNAPSACK:
        run("Multi-Knapsack", multi_knapsack, starts[""], list, data, base_cost, results)
    
    if PRINT:
        print("===============================================================")
    results["Base"] = starts[""]
    video_sizes_sorted, videos_info = preprocess_data(N_vid, N_endpoint, N_request, N_cache, empty_sizes, video_sizes, empty_caches, endpoints, requests)

    local_search_func   = partial(local_search, iteration=5, previous_moves=None, nbCaches=10, nbVideos=10, supp=True)
    tabu_search_func = partial(random_tabu_search, nb_forbidden_moves=7, iteration=100, nbCaches=10, nbVideos=10)
    sorted_tabu_search_func = partial(sorted_tabu_search, nb_forbidden_moves=7, iteration=100, nbCaches=10, nbVideos=10)

    algos = [
        ("LS", local_search_func, list),
        ("TS", tabu_search_func, set),
        ("TSS", sorted_tabu_search_func, set),
    ]
    if not TEST_LOCAL_SEARCH:
        algos = []

    # on fait tourner les algos de recherche locale sur la meilleure solution trouvée par les algos gloutons
    # if best_greedy == "Greedy": best_greedy = "g"
    # else: best_greedy = "g2"
    if BEST_OF_GREEDY:
        for label, algo, container in algos:
            run(f"{label} ({best_greedy})", algo, starts[best_greedy.lower()], container, data, base_cost, results)
    else:
        # print(starts.keys())
        for start_label in starts.keys():
            for label, algo, container in algos:
                run(f"{label} ({start_label})", algo, starts[start_label], container, data, base_cost, results)

    best_method = max(results, key=lambda x: results[x]["score"])
    # ---------- Bilan ----------
    # print_comparison_table(results, metric="score", higher_is_better=True)
    if PRINT:
        print_gap_to_best(results, metric="score", higher_is_better=True)
    # best_method = min(results, key=lambda x: results[x]["cost"])
    print(f"\nFile : {input_file.split('/')[-1]}")
    print(f"Best method: {best_method} with ({(base_cost - results[best_method]['cost']) / base_cost * 100:.2f}%) | Score: {int(results[best_method]['score'])}")

    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    if '/' in input_file:
        output_file = input_file.split('/')[-1]
    else:
        output_file = input_file
        
    output_file = output_file.split('.')[0] + '.out'
    # create_results_files(results[best_method]["caches"], f"{RESULTS_DIR}/{output_file}")
    # return results
    results[best_method]["method"] = best_method
    return results[best_method]

def best_of_greedy(data, empty_caches, empty_sizes, endpoints, requests, base_cost):
    """
    Execute tout les méthodes gloutonnes et retourne la meilleure solution.
    """
    algos = [("Greedy", greedy), ("Greedy2", greedy2), ("Greedy3", greedy3)]


    starts = { "":snapshot(empty_caches, empty_sizes, endpoints, requests) }
    results = {}

    for label, algo in algos:
        run(label, algo, starts[""], list, data, base_cost, results)
        starts[label.lower()] = results[label]

    if PRINT:
        print_gap_to_best(results, metric="score", higher_is_better=True)
    best_greedy = max(["Greedy", "Greedy2","Greedy3"], key=lambda x: results[x]["score"])

    return results, starts, best_greedy




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
    if PRINT:
        print(f"[{dt:.4f}s] {label} : {res['cost']} ({gain:.2f}%) | Score: {int(res['score'])}")

    # save_results(results, data)


def exec_all():
    all_results = {}
    tested_instances = []
    with open("results_summary.txt", "r") as f:
        for line in f:
            if line.strip() == "":
                continue
            instance_name = line.split(":")[0].strip()
            tested_instances.append(instance_name)
    f = open("results_summary.txt", "a")
    for input_file in [f"{INSTANCES_DIR}/{f}" for f in INSTANCES_FILES]:
        if input_file in tested_instances:
            print(f"Skipping {input_file} (already tested)")
            continue
        print(f"\n=== Running on {input_file} ===")
        res = main([input_file])
        all_results[input_file] = res
        f.write(f"{input_file}: method={res['method']}, score={int(res['score'])}\n")
        f.flush()
        create_results_files(res["caches"], f"{RESULTS_DIR}/{input_file.split('/')[-1].split('.')[0]}.out")
    print("\n=== Summary of all instances ===")
    for input_file, res in all_results.items():
        print(f"{input_file}: cost={res['cost']}, score={int(res['score'])}")
    f.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        results = main([f"{INSTANCES_DIR}/{INSTANCES_FILES[0]}"])  # Default input file for testing
        create_results_files(results["caches"], f"{RESULTS_DIR}/{INSTANCES_FILES[0].split('.')[0]}.out")
    elif sys.argv[1] == "all":
        PRINT = False
        exec_all()
    else:
        print(f"\n=== Running on {sys.argv[1]} ===")
        results = main(sys.argv[1:])
        create_results_files(results["caches"], f"{RESULTS_DIR}/{sys.argv[1].split('/')[-1].split('.')[0]}.out")