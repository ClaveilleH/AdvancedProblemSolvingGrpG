"""
Caractéristiques des instances, à croiser avec les scores des algos.

Usage (depuis la racine) :
    python -m bench.features all
    python -m bench.features google kittens

Écrit bench/data/features.csv (une ligne par instance).
"""

import csv
import os
import sys

from algos import knapsack_slay as ks
from bench.common import DATA_DIR, FEATURES_CSV, load_instance, select_instances

FIELDS = [
    "instance", "V", "E", "R", "C", "X", "total_requests",
    "capacity_ratio", "videos_per_cache", "caches_per_endpoint", "endpoints_per_cache",
    "top10_share", "upper_bound",
    "ks_gcd_weight", "ks_pred_dp_weight", "ks_pred_dp_value", "ks_pred_greedy", "ks_pred_dp_cells",
]


def knapsack_prediction(data):
    """
    Branche que prendrait multiknapsack_bg pour chaque cache avec les valeurs initiales
    (avant toute mise à jour), sans lancer la programmation dynamique.
    Renvoie aussi le nombre total de cases des tables de DP, qui explique les temps de calcul.
    """
    weight, gcd_weight = ks.preprocess_weight_genius(data)
    values, _ = ks.preprocess_values_genius(data)
    capacity = data["S_cache"] // gcd_weight
    counts = {"dp_weight": 0, "dp_value": 0, "greedy": 0}
    cells = 0
    for cache_id in range(data["N_cache"]):
        objects = [i for i in range(data["N_vid"]) if values[cache_id][i] > 0 and weight[i] <= capacity]
        sum_values = sum(values[cache_id][i] for i in objects)
        if sum_values > ks.LIMIT and capacity > ks.LIMIT:
            counts["greedy"] += 1
        elif sum_values > capacity:
            counts["dp_weight"] += 1
            cells += (len(objects) + 1) * (capacity + 1)
        else:
            counts["dp_value"] += 1
            cells += (len(objects) + 1) * (sum_values + 1)
    return gcd_weight, counts, cells


def features(name):
    data = load_instance(name)
    sizes, endpoints, requests = data["video_sizes"], data["endpoints"], data["requests"]
    V, E, C, X = data["N_vid"], data["N_endpoint"], data["N_cache"], data["S_cache"]

    total_requests = sum(n for _, _, n in requests)
    per_video = [0] * V
    best_gain = 0
    for video_id, endpoint_id, n in requests:
        per_video[video_id] += n
        latency, linked_caches = endpoints[endpoint_id]
        best_gain += n * max([latency - cache_latency for _, cache_latency in linked_caches] + [0])
    per_video.sort(reverse=True)
    nb_links = sum(len(linked_caches) for _, linked_caches in endpoints)

    gcd_weight, counts, cells = knapsack_prediction(data)
    return {
        "instance": name, "V": V, "E": E, "R": data["N_request"], "C": C, "X": X,
        "total_requests": total_requests,
        # > 1 : toutes les vidéos tiendraient dans l'ensemble des caches
        "capacity_ratio": round(C * X / sum(sizes), 4),
        "videos_per_cache": round(X / (sum(sizes) / V), 2),
        "caches_per_endpoint": round(nb_links / E, 2),
        "endpoints_per_cache": round(nb_links / C, 2),
        # part des requêtes portant sur les 10 % de vidéos les plus demandées
        "top10_share": round(sum(per_video[:max(1, V // 10)]) / total_requests, 4),
        # borne supérieure du score : chaque requête servie par son meilleur cache, sans contrainte de capacité
        "upper_bound": int(best_gain * 1000 / total_requests),
        "ks_gcd_weight": gcd_weight,
        "ks_pred_dp_weight": counts["dp_weight"],
        "ks_pred_dp_value": counts["dp_value"],
        "ks_pred_greedy": counts["greedy"],
        "ks_pred_dp_cells": cells,
    }


def main():
    names = select_instances(sys.argv[1:] or ["all"])
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FEATURES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for name in names:
            row = features(name)
            writer.writerow(row)
            f.flush()
            print(row)


if __name__ == "__main__":
    main()
