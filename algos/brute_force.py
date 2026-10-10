from itertools import product

from utils import calculate_video_latency, compute_cost

PRINT = True
NB_TESTS_THRESHOLD = 1000000

def useful_videos(data, cache_id):
    """
    Vidéos qui peuvent rapporter quelque chose dans ce cache : demandées par un endpoint
    relié au cache par un lien plus rapide que le datacenter, et assez petites pour y rentrer.
    """
    endpoints = data["endpoints"]
    # endpoints pour lesquels ce cache fait mieux que le datacenter
    fast_endpoints = {endpoint_id for endpoint_id, cache_latency in data["caches_endpoints"][cache_id]
                      if cache_latency < endpoints[endpoint_id][0]}
    videos = {video_id for video_id, endpoint_id, _ in data["requests"] if endpoint_id in fast_endpoints}
    return sorted(v for v in videos if data["video_sizes"][v] <= data["S_cache"])


def candidate_sets(data, cache_id, limit):
    """
    Tous les contenus possibles d'un cache qu'il est utile de tester : les ensembles de vidéos
    utiles qui tiennent dans le cache et qui sont maximaux (plus aucune vidéo utile ne rentre).
    Ajouter une vidéo ne dégrade jamais le score, donc un ensemble non maximal ne peut pas faire mieux.
    Renvoie None s'il y en a plus que `limit` ou si l'exploration est trop longue.
    """
    sizes = data["video_sizes"]
    videos = useful_videos(data, cache_id)
    n = len(videos)
    if n > 500:     # profondeur de récursion trop grande, et de toute façon beaucoup trop d'ensembles
        return None
    # remaining_sizes[i] = taille totale des vidéos i, i+1, ..., n-1
    remaining_sizes = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        remaining_sizes[i] = remaining_sizes[i + 1] + sizes[videos[i]]

    res = []
    budget = [50 * limit]   # nombre maximal d'appels à explore

    def explore(i, chosen, capacity, smallest_skipped):
        """capacity = place restante, smallest_skipped = taille de la plus petite vidéo écartée."""
        budget[0] -= 1
        if budget[0] < 0 or len(res) > limit:
            return
        # même en prenant tout ce qui reste, une vidéo écartée rentrerait encore : jamais maximal
        if smallest_skipped <= capacity - remaining_sizes[i]:
            return
        if i == n:
            res.append(set(chosen))
            return
        video_id = videos[i]
        if sizes[video_id] <= capacity:
            chosen.append(video_id)
            explore(i + 1, chosen, capacity - sizes[video_id], smallest_skipped)
            chosen.pop()
        explore(i + 1, chosen, capacity, min(smallest_skipped, sizes[video_id]))

    explore(0, [], data["S_cache"], float("inf"))
    if budget[0] < 0 or len(res) > limit:
        return None
    return res


def brute_force(data, empty_caches, empty_sizes, endpoints=None, requests=None, base_cost=None):
    """
    Brute force algorithm to find the optimal solution.
    Args:
        data (dict): A dictionary containing the problem data.
        empty_caches (list): A list of empty caches.
        empty_sizes (list): A list of empty sizes for each cache.
        endpoints (list): A list of endpoints.
        requests (list): A list of requests.
        base_cost (int): The base cost without any videos in caches.
    Returns:
        tuple: A tuple containing the best caches and sizes found by the brute force algorithm.
    """
    N_vid, N_cache = data["N_vid"], data["N_cache"]
    # main.run() n'appelle les algos qu'avec (data, caches, caches_sizes)
    if endpoints is None:
        endpoints = data["endpoints"]
    if requests is None:
        requests = data["requests"]
    if base_cost is None:
        base_cost = compute_cost(empty_caches, endpoints, requests)
    best_cost = base_cost
    best_caches = empty_caches
    best_sizes = empty_sizes

    # contenus à tester pour chaque cache ; le nombre de solutions est le produit de leurs nombres
    candidates = []
    nb_tests = 1
    for cache_id in range(N_cache):
        sets = candidate_sets(data, cache_id, NB_TESTS_THRESHOLD)
        if sets is None or nb_tests * len(sets) > NB_TESTS_THRESHOLD:
            if PRINT:
                print(f"Brute force is not applicable for this instance (more than {NB_TESTS_THRESHOLD} solutions to test).")
            return best_caches, best_sizes
        nb_tests *= len(sets)
        candidates.append(sets)
    if PRINT:
        print(f"Brute force: {nb_tests} solutions to test")

    # on essaie toutes les combinaisons d'un contenu par cache et on garde la moins coûteuse
    best_combination = None
    for combination in product(*candidates):
        cost = compute_cost(combination, endpoints, requests)
        if cost < best_cost:
            best_cost = cost
            best_combination = combination

    if best_combination is not None:
        video_sizes = data["video_sizes"]
        best_caches = [sorted(cache) for cache in best_combination]
        best_sizes = [data["S_cache"] - sum(video_sizes[v] for v in cache) for cache in best_caches]
        # les algos modifient caches et caches_sizes en place (voir main.run)
        for cache_id in range(N_cache):
            empty_caches[cache_id] = best_caches[cache_id]
            empty_sizes[cache_id] = best_sizes[cache_id]

    return best_caches, best_sizes

def is_brute_force_applicable(data):
    nb_tests = data["N_vid"] * data["N_cache"]
    if nb_tests > NB_TESTS_THRESHOLD:
        if PRINT:
            print(f"Brute force is not applicable for this instance (N_vid * N_cache = {nb_tests} > {NB_TESTS_THRESHOLD}).")
        return False
    return True

if __name__ == "__main__":
    PRINT = True
    from sys import argv
    from utils import read_input_file, compute_cost, make_adj_list, compute_score
    if len(argv) != 2:
        input_file = "instances/test.in"
    else:
        input_file = argv[1]

    N_vid, N_endpoint, N_request, N_cache, S_cache, video_sizes, endpoints, caches_endpoints, requests = read_input_file(input_file)
    empty_caches = [[] for _ in range(N_cache)]  # la liste des videos stockés dans chaque cache
    empty_sizes = [S_cache] * N_cache  # la taille restante de chaque cache
    adj_list = make_adj_list(N_vid, N_request, requests)

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
            "adj_list": adj_list,
        }

    base_cost = compute_cost(empty_caches, endpoints, requests)
    best_caches, best_sizes = brute_force(data, empty_caches, empty_sizes, endpoints, requests, base_cost)
    if best_caches is None or best_sizes is None:
        print("Brute force did not find a better solution than the base cost.")
    score = compute_score(best_caches, endpoints, requests)
    if PRINT:
        print(f"Final score: {score}")
    
