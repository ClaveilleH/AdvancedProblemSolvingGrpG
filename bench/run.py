"""
Bench : mesure chaque algo sur chaque instance et écrit une ligne par (instance, algo, graine).

Usage (depuis la racine) :
    python -m bench.run all                      # toutes les instances, tous les algos
    python -m bench.run google --timeout 300     # les 4 instances Google
    python -m bench.run kittens big --algos Greedy Greedy2 Greedy3
    python -m bench.run kittens --grid           # étude du voisinage des tabu search

Sorties :
    bench/data/runs.csv   (ou grid.csv avec --grid)
    results/bench/<instance>__<algo>.out   solution de chaque algo

Le bench reprend là où il s'est arrêté : une ligne déjà présente dans le CSV n'est pas relancée
(--force pour tout relancer).

Chaque exécution tourne dans son propre processus. Au bout de --timeout secondes l'algo est
interrompu et on évalue l'état des caches à cet instant (statut "timeout").
"""

import argparse
import contextlib
import csv
import multiprocessing as mp
import os
import platform
import queue
import random
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from algos.greedy import greedy
from algos.greedy2 import greedy2
from algos.greedy3 import greedy3
from algos import knapsack_slay as ks
from algos.local_search import local_search, random_tabu_search, sorted_tabu_search
from utils import create_results_files
from bench.fixes import local_search_fix, random_tabu_search_fix, sorted_tabu_search_fix
from bench.common import (DATA_DIR, SOLUTIONS_DIR, RUNS_CSV, GRID_CSV, load_instance, evaluate,
                          read_solution, read_csv, select_instances)

GREEDIES = ["Greedy", "Greedy2", "Greedy3"]
KNAPSACKS = ["KS_indep", "KS_maj"]
SEARCHES = ["LS", "TS", "TSS"]
# versions corrigées (bench/fixes.py), pour comparer avant / après
SEARCHES_FIX = ["LS_fix", "TS_fix", "TSS_fix"]
TABU = ["TS", "TSS", "TS_fix", "TSS_fix"]
RANDOM = ["TS", "TS_fix"]

# paramètres de main.py
DEFAULT_PARAMS = {
    "LS": {"nbC": 10, "nbV": 10, "it": 5},
    "TS": {"nbC": 10, "nbV": 10, "it": 100, "tabu": 7},
    "TSS": {"nbC": 10, "nbV": 10, "it": 100, "tabu": 7},
}
for _algo in SEARCHES:
    DEFAULT_PARAMS[_algo + "_fix"] = DEFAULT_PARAMS[_algo]
# étude du voisinage (--grid) : taille du voisinage (nbCaches = nbVideos) x nombre d'itérations
GRID_SIZES = [10, 30, 100]
GRID_ITERATIONS = [100, 400]

FIELDS = [
    "instance", "algo", "seed", "params", "start", "status", "time_s",
    "score", "score_best", "cost", "start_score", "fill_rate", "n_placed", "valid",
    "ks_dp_weight", "ks_dp_value", "ks_greedy", "ks_greedy_abandon", "error",
]
BRANCHES = ["ks_dp_weight", "ks_dp_value", "ks_greedy", "ks_greedy_abandon"]


def params_str(params):
    return ";".join(f"{k}={v}" for k, v in params.items())


def solution_path(instance, algo):
    return f"{SOLUTIONS_DIR}/{instance}__{algo}.out"


# ============================ Processus fils : une exécution ============================

def count_branches(counters):
    """
    Enveloppe les trois résolutions de sac à dos de knapsack_slay pour compter combien de caches
    passent par chaque branche, sans modifier le fichier d'origine.
    """
    def counted(func, index):
        def wrapper(values, weights, capacity):
            if index == 2 and len(values) > ks.LIMIT:
                counters[3] += 1        # le glouton abandonne et renvoie un sac vide
            else:
                counters[index] += 1
            return func(values, weights, capacity)
        return wrapper

    ks.knapsack_weight = counted(ks.knapsack_weight, 0)
    ks.knapsack_value = counted(ks.knapsack_value, 1)
    ks.knapsack_goulton = counted(ks.knapsack_goulton, 2)


def call_algo(algo, params, data, caches, sizes):
    if algo == "Greedy":
        return greedy(data, caches, sizes)
    if algo == "Greedy2":
        return greedy2(data, caches, sizes)
    if algo == "Greedy3":
        return greedy3(data, caches, sizes)
    if algo == "KS_indep":
        return ks.multiknapsack(data, caches, sizes)
    if algo == "KS_maj":
        return ks.multiknapsack_bg(data, caches, sizes)
    if algo == "LS":
        return local_search(data, caches, sizes, iteration=params["it"], previous_moves=None,
                            nbCaches=params["nbC"], nbVideos=params["nbV"], supp=True)
    if algo == "TS":
        return random_tabu_search(data, caches, sizes, nb_forbidden_moves=params["tabu"],
                                  iteration=params["it"], nbCaches=params["nbC"], nbVideos=params["nbV"])
    if algo == "TSS":
        return sorted_tabu_search(data, caches, sizes, nb_forbidden_moves=params["tabu"],
                                  iteration=params["it"], nbCaches=params["nbC"], nbVideos=params["nbV"])
    if algo == "LS_fix":
        return local_search_fix(data, caches, sizes, iteration=params["it"],
                                nbCaches=params["nbC"], nbVideos=params["nbV"], supp=True)
    if algo == "TS_fix":
        return random_tabu_search_fix(data, caches, sizes, nb_forbidden_moves=params["tabu"],
                                      iteration=params["it"], nbCaches=params["nbC"], nbVideos=params["nbV"])
    if algo == "TSS_fix":
        return sorted_tabu_search_fix(data, caches, sizes, nb_forbidden_moves=params["tabu"],
                                      iteration=params["it"], nbCaches=params["nbC"], nbVideos=params["nbV"])
    raise ValueError(f"algo inconnu : {algo}")


def child(task, out_queue, ready, counters):
    """Charge l'instance, lance l'algo avec une limite de temps et renvoie les mesures."""
    res = {"status": "ok"}
    try:
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            data = load_instance(task["instance"])
            if task["start"]:
                start = read_solution(solution_path(task["instance"], task["start"]), data["N_cache"])
                res["start_score"] = evaluate(data, start)["score"]
            else:
                start = [[] for _ in range(data["N_cache"])]
            # même conteneur que dans main.py : des ensembles pour les deux tabu search, des listes sinon
            container = set if task["algo"] in TABU else list
            caches = [container(c) for c in start]
            sizes = [data["S_cache"] - sum(data["video_sizes"][v] for v in c) for c in caches]

            count_branches(counters)
            random.seed(task["seed"])
            box = {}

            def target():
                try:
                    box["ret"] = call_algo(task["algo"], task["params"], data, caches, sizes)
                except BaseException:
                    box["error"] = traceback.format_exc(limit=3)

            thread = threading.Thread(target=target, daemon=True)
            ready.set()
            t = time.perf_counter()
            thread.start()
            thread.join(task["timeout"])
            res["time_s"] = round(time.perf_counter() - t, 4)

            if thread.is_alive():
                res["status"] = "timeout"
            elif "error" in box:
                res["status"] = "error"
                res["error"] = box["error"].strip().splitlines()[-1]

            # état des caches à la fin (ou au moment de l'interruption)
            final = [list(c) for c in caches]
            res.update(evaluate(data, final))
            res["score_best"] = res["score"]
            # les tabu search renvoient la meilleure solution rencontrée, qui n'est pas forcément
            # l'état final laissé dans `caches`
            ret = box.get("ret")
            if task["algo"] in TABU and isinstance(ret, list):
                res["score_best"] = evaluate(data, ret)["score"]
            if task["save"] and res["status"] != "error":
                os.makedirs(SOLUTIONS_DIR, exist_ok=True)
                create_results_files(final, solution_path(task["instance"], task["algo"]))
    except BaseException:
        res = {"status": "error", "error": traceback.format_exc(limit=3).strip().splitlines()[-1]}
    out_queue.put(res)
    out_queue.close()
    out_queue.join_thread()
    os._exit(0)     # l'algo tourne peut-être encore dans son thread : on coupe tout


# ============================ Processus parent ============================

def run_task(task):
    ctx = mp.get_context("spawn")
    out_queue, ready, counters = ctx.Queue(), ctx.Event(), ctx.Array("i", 4)
    process = ctx.Process(target=child, args=(task, out_queue, ready, counters), daemon=True)
    process.start()
    # le chargement de l'instance n'est pas compté dans la limite de temps
    while not ready.wait(1) and process.is_alive():
        pass
    # garde-fou si le fils ne répond plus : limite de temps + marge pour l'évaluation
    deadline = time.time() + task["timeout"] + 300
    res = None
    while res is None and time.time() < deadline:
        try:
            res = out_queue.get(timeout=1)
        except queue.Empty:
            if not process.is_alive():
                try:
                    res = out_queue.get(timeout=1)
                except queue.Empty:
                    res = {"status": "crash", "error": f"code de sortie {process.exitcode} (mémoire ?)"}
    if res is None:
        res = {"status": "timeout", "time_s": task["timeout"], "error": "fils interrompu de force"}
    process.terminate()
    process.join()

    row = {field: "" for field in FIELDS}
    row.update({"instance": task["instance"], "algo": task["algo"], "seed": task["seed"],
                "params": params_str(task["params"]), "start": task["start"]})
    row.update(res)
    for i, field in enumerate(BRANCHES):
        row[field] = counters[i] if task["algo"] in KNAPSACKS else ""
    return row


class Bench:
    def __init__(self, csv_path, timeout, force):
        self.csv_path = csv_path
        self.timeout = timeout
        self.lock = threading.Lock()
        self.rows = [] if force else read_csv(csv_path)
        os.makedirs(DATA_DIR, exist_ok=True)
        if force or not os.path.exists(csv_path):
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def find(self, instance, algo, seed, params):
        key = (instance, algo, str(seed), params_str(params))
        for row in self.rows:
            if (row["instance"], row["algo"], str(row["seed"]), row["params"]) == key:
                return row
        return None

    def run(self, instance, algo, seed=0, params=None, start="", save=True):
        params = params or {}
        row = self.find(instance, algo, seed, params)
        if row is not None:
            return row
        row = run_task({"instance": instance, "algo": algo, "seed": seed, "params": params,
                        "start": start, "timeout": self.timeout, "save": save})
        with self.lock:
            self.rows.append(row)
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
            print(f"{instance:<38} {algo:<9} graine={seed} {params_str(params):<28} "
                  f"{row['status']:<8} {row['time_s']:>9}s  score={row['score']} {row['error']}", flush=True)
        return row

    def best_greedy(self, instance):
        """Le meilleur glouton sert de point de départ aux recherches locales, comme dans main.py."""
        rows = [self.run(instance, algo) for algo in GREEDIES]
        rows = [row for row in rows if row["status"] == "ok"]
        if not rows:
            return None
        return max(rows, key=lambda row: int(row["score"]))["algo"]


def bench_instance(bench, instance, algos, seeds):
    for algo in GREEDIES + KNAPSACKS:
        if algo in algos:
            bench.run(instance, algo)
    searches = [algo for algo in SEARCHES + SEARCHES_FIX if algo in algos]
    if not searches:
        return
    start = bench.best_greedy(instance)
    if start is None:
        return
    for algo in searches:
        # seule la tabu search aléatoire dépend de la graine
        for seed in range(seeds if algo in RANDOM else 1):
            bench.run(instance, algo, seed, DEFAULT_PARAMS[algo], start, save=False)


def grid_instance(bench, instance, seeds):
    start = bench.best_greedy(instance)
    if start is None:
        return
    for size in GRID_SIZES:
        for iterations in GRID_ITERATIONS:
            params = {"nbC": size, "nbV": size, "it": iterations, "tabu": 7}
            bench.run(instance, "TSS", 0, params, start, save=False)
            for seed in range(seeds):
                bench.run(instance, "TS", seed, params, start, save=False)


def write_machine_info(timeout, workers):
    with open(f"{DATA_DIR}/machine.txt", "w", encoding="utf-8") as f:
        f.write(f"machine : {platform.processor()}\n")
        f.write(f"coeurs  : {os.cpu_count()}\n")
        f.write(f"systeme : {platform.platform()}\n")
        f.write(f"python  : {sys.version.split()[0]} ({platform.python_implementation()})\n")
        f.write(f"limite de temps par execution : {timeout} s\n")
        f.write(f"executions en parallele : {workers}\n")


def main():
    parser = argparse.ArgumentParser(description="Mesure chaque algo sur chaque instance")
    parser.add_argument("instances", nargs="+", help="google, promo, all, ou des noms d'instances")
    parser.add_argument("--algos", nargs="+", default=GREEDIES + KNAPSACKS + SEARCHES + SEARCHES_FIX,
                        choices=GREEDIES + KNAPSACKS + SEARCHES + SEARCHES_FIX)
    parser.add_argument("--timeout", type=int, default=300, help="limite de temps par exécution, en secondes")
    parser.add_argument("--seeds", type=int, default=10, help="nombre de graines pour la tabu search aléatoire")
    parser.add_argument("--workers", type=int, default=1,
                        help="instances traitées en parallèle (les temps mesurés sont moins fiables au-delà de 1)")
    parser.add_argument("--grid", action="store_true", help="étude du voisinage des tabu search")
    parser.add_argument("--force", action="store_true", help="efface le CSV et relance tout")
    args = parser.parse_args()

    instances = select_instances(args.instances)
    bench = Bench(GRID_CSV if args.grid else RUNS_CSV, args.timeout, args.force)
    write_machine_info(args.timeout, args.workers)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        if args.grid:
            futures = [pool.submit(grid_instance, bench, instance, args.seeds) for instance in instances]
        else:
            futures = [pool.submit(bench_instance, bench, instance, args.algos, args.seeds) for instance in instances]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
