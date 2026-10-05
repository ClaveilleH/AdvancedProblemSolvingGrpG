import sys
from greedy import greedy
from utils import read_input_file


def infos_sol(data, caches):
    """
    Calcule les latences (défaut, optimale, solution) par requête, par vidéo,
    par endpoint et au total. Toutes les latences sont pondérées par le
    nombre de requêtes.
    """
    requests = data["requests"]
    endpoints = data["endpoints"]
    N_videos = data["N_vid"]
    N_endpoints = data["N_endpoint"]

    # set() pour des tests d'appartenance en O(1)
    cache_sets = [set(c) for c in caches]

    total_default = total_optimal = total_solution = 0
    total_requests = 0

    metrics_per_request = []                    # (défaut, optimal, solution)
    metrics_per_video = [(0, 0, 0)] * N_videos
    metrics_per_endpoint = [(0, 0, 0)] * N_endpoints

    for vid_id, endpoint_id, num_requests in requests:
        dc_latency, linked_caches = endpoints[endpoint_id]

        default = dc_latency * num_requests
        optimal = default      # meilleure latence possible (vidéo dans le meilleur cache)
        solution = default     # latence réelle avec notre solution

        for cache_id, cache_latency in linked_caches:
            weighted = cache_latency * num_requests
            optimal = min(optimal, weighted)
            if vid_id in cache_sets[cache_id]:
                solution = min(solution, weighted)

        total_default += default
        total_optimal += optimal
        total_solution += solution
        total_requests += num_requests

        metrics_per_request.append((default, optimal, solution))

        d, o, s = metrics_per_video[vid_id]
        metrics_per_video[vid_id] = (d + default, o + optimal, s + solution)

        d, o, s = metrics_per_endpoint[endpoint_id]
        metrics_per_endpoint[endpoint_id] = (d + default, o + optimal, s + solution)

    total_metrics = (total_default, total_optimal, total_solution)
    return (metrics_per_request, metrics_per_video,
            metrics_per_endpoint, total_metrics, total_requests)


def compute_score(total_default, total_solution, total_requests):
    """Score officiel Hash Code 2017 : gain moyen par requête, en microsecondes."""
    if total_requests == 0:
        return 0
    return int((total_default - total_solution) / total_requests * 1000)

def metrics_sol(infos):
    



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python metrics.py <fichier_input>")
        sys.exit(1)

    input_file = sys.argv[1]
    print(f"Lecture du fichier : {input_file}")

    (N_vid, N_endpoint, N_request, N_cache, S_cache,
     video_sizes, endpoints, requests) = read_input_file(input_file)

    data = {
        "N_vid": N_vid,
        "N_endpoint": N_endpoint,
        "N_request": N_request,
        "N_requests": N_request,       # alias conservé pour compatibilité avec greedy
        "N_cache": N_cache,
        "S_cache": S_cache,
        "cache_size": S_cache,         # alias conservé pour compatibilité avec greedy
        "video_sizes": video_sizes,
        "endpoints": endpoints,
        "requests": requests,
    }

    empty_caches = [[] for _ in range(N_cache)]  # vidéos stockées dans chaque cache
    empty_sizes = [S_cache] * N_cache            # espace restant dans chaque cache

    caches = greedy(data, empty_caches, empty_sizes)

    (metrics_per_request, metrics_per_video,
     metrics_per_endpoint, total_metrics, total_requests) = infos_sol(data, caches)

    total_default, total_optimal, total_solution = total_metrics

    print("\n=== Caches ===")
    for i, c in enumerate(caches):
        print(f"Cache {i} : {c}")

    print("\n=== Métriques globales (défaut, optimal, solution) ===")
    print(total_metrics)

    print(f"\nNombre total de requêtes : {total_requests}")
    print(f"Score de la solution     : {compute_score(total_default, total_solution, total_requests)}")
    print(f"Score optimal théorique  : {compute_score(total_default, total_optimal, total_requests)}")

    # Décommenter pour le détail (très verbeux sur les gros jeux de données)
    print("Par requête :", metrics_per_request)
    print("Par vidéo   :", metrics_per_video)
    print("Par endpoint:", metrics_per_endpoint)