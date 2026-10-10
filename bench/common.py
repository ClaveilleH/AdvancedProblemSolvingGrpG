"""Outils partagés par les scripts de bench : chemins, chargement des instances, évaluation."""

import csv
import glob
import os

from utils import read_input_file, make_adj_list, compute_cost, compute_score
from algos.local_search import preprocess_data

INSTANCES_DIR = "instances"
DATA_DIR = "bench/data"                 # CSV produits par le bench (suivis par git)
SOLUTIONS_DIR = "results/bench"         # solutions .out de chaque algo (ignorées par git)
FIGURES_DIR = "docs/oral/figures"

RUNS_CSV = f"{DATA_DIR}/runs.csv"
GRID_CSV = f"{DATA_DIR}/grid.csv"
FEATURES_CSV = f"{DATA_DIR}/features.csv"

GOOGLE = ["kittens", "me_at_the_zoo", "trending_today", "videos_worth_spreading"]
PROMO = [
    "custom_dejavu42", "custom_universallambda42", "custom_universallambda42_asymmetric",
    "instance1", "instance2", "4990_246_84901_50", "6970_311_100000_69", "10000_500_100000_100",
    "3860_246_84901_66", "regional_instance", "zipF_instance", "big", "supra", "INSATANC2D",
    "INSTANCED", "2_2_2_1", "4_2_4_2", "6_2_6_2", "8_2_8_2", "20_2_20_2",
    "realistic_large_clustered", "realistic_large_random", "dense", "dense2",
    "medium_mixed_lambda", "medium_skew_dense_dejavu", "medium_skew_sparse_lambda",
    "medium_flat_dense_dejavu", "medium_flat_sparse_lambda",
]
# instances jouets (2 à 20 vidéos) : à présenter à part
TOY = ["2_2_2_1", "4_2_4_2", "6_2_6_2", "8_2_8_2", "20_2_20_2"]


def select_instances(names):
    """Traduit les arguments de la ligne de commande (google, promo, all ou des noms) en liste d'instances."""
    res = []
    for name in names:
        if name == "google":
            res += GOOGLE
        elif name == "promo":
            res += PROMO
        elif name == "all":
            res += GOOGLE + PROMO
        else:
            res.append(os.path.basename(name).replace(".in", ""))
    return list(dict.fromkeys(res))


def load_instance(name):
    """Lit une instance et construit le même dictionnaire `data` que main.py."""
    parsed = read_input_file(f"{INSTANCES_DIR}/{name}.in")
    if parsed is None:
        raise FileNotFoundError(f"instance illisible : {name}")
    N_vid, N_endpoint, N_request, N_cache, S_cache, video_sizes, endpoints, caches_endpoints, requests = parsed
    data = {
        "N_vid": N_vid,
        "N_endpoint": N_endpoint,
        "N_request": N_request,
        "N_cache": N_cache,
        "N_requests": N_request,
        "S_cache": S_cache, "cache_size": S_cache,
        "video_sizes": video_sizes,
        "endpoints": endpoints,
        "caches_endpoints": caches_endpoints,
        "requests": requests,
        "adj_list": make_adj_list(N_vid, N_request, requests),
    }
    empty_caches = [[] for _ in range(N_cache)]
    _, videos_info = preprocess_data(N_vid, N_endpoint, N_request, N_cache, [S_cache] * N_cache,
                                     video_sizes, empty_caches, endpoints, requests)
    data["videos_by_popularity"] = [video[0] for video in videos_info]
    return data


def evaluate(data, caches):
    """Score, coût, taux de remplissage et validité d'une solution."""
    sizes = data["video_sizes"]
    used = [sum(sizes[v] for v in cache) for cache in caches]
    total_capacity = data["N_cache"] * data["S_cache"]
    return {
        "score": compute_score(caches, data["endpoints"], data["requests"]),
        "cost": compute_cost(caches, data["endpoints"], data["requests"]),
        "fill_rate": round(sum(used) / total_capacity, 4) if total_capacity else 0,
        "n_placed": sum(len(cache) for cache in caches),
        # une solution est valide si aucun cache ne dépasse sa capacité
        "valid": int(all(u <= data["S_cache"] for u in used)),
    }


def read_solution(path, n_caches):
    """Relit un fichier .out écrit par utils.create_results_files."""
    caches = [[] for _ in range(n_caches)]
    with open(path) as f:
        f.readline()
        for line in f:
            ids = list(map(int, line.split()))
            if ids:
                caches[ids[0]] = ids[1:]
    return caches


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_sheet():
    """
    Lit le dernier export du Google Sheet de la promo.
    Renvoie {instance: {"VBS": meilleur score connu, "G": notre score dans le Sheet}}.
    """
    paths = sorted(glob.glob("docs/exel/backup_*/*.csv"))
    if not paths:
        return {}
    with open(paths[-1], newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))

    def number(cell):
        cell = "".join(c for c in cell if c.isdigit())
        return int(cell) if cell else None

    res = {}
    header = None
    for row in rows:
        if row and row[0].startswith("instance \\ score groupe"):
            header = row
            continue
        if header is None or not row or not row[0].strip() or row[0] in ("TOTAL", "Classement Hashcode", "Classement Local"):
            continue
        name = row[0].split(" ")[0].replace(".in", "")
        vbs = number(row[header.index("VBS")])
        if vbs:
            res[name] = {"VBS": vbs, "G": number(row[header.index("G")])}
    return res
