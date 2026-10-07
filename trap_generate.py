import argparse
import os
import random

import numpy as np

from algos.greedy import greedy
from utils import compute_score, create_results_files

OUTPUT_DIR_PATH = "instances/generated"

# bornes de l'énoncé Hash Code 2017
MAX_VIDEOS = 10000
MAX_ENDPOINTS = 1000
MAX_CACHES = 1000
MAX_VIDEO_SIZE = 1000
MAX_NB_REQUESTS = 10000
MAX_LATENCY = 4000
MAX_CACHE_LATENCY = 500

# greedy.py traite les requêtes par nombre de requêtes décroissant : chaque vidéo de la solution
# plantée a une (seule) ligne au-dessus de ce seuil, toutes les autres lignes sont en dessous.
# Les vidéos plantées remplissent exactement leur cache, donc quand greedy.py arrive aux autres
# lignes tous les caches sont pleins et plus rien ne bouge.
THRESHOLD = 5000
# nombre de requêtes max des lignes de remplissage
NOISE_MAX_NB_REQUESTS = 5

MAX_TRIES = 2000
MAX_REPAIRS = 10

# Un "gadget" = un cache, ses endpoints et ses vidéos :
#   sizes     : taille de chaque vidéo du gadget
#   endpoints : (latence datacenter, latence vers le cache du gadget)
#   requests  : (video, endpoint, nb requêtes), avec des indices locaux au gadget
# Chaque gadget est un sac à dos dont l'optimum est connu. Les liens secondaires et les
# requêtes de remplissage ajoutés ensuite sont trop faibles pour changer cet optimum,
# ce qui est vérifié à la fin par certify().


# ============================ Résolution d'un gadget ============================

def video_values(gadget):
    """
        Temps gagné par chaque vidéo du gadget si elle est mise dans le cache
    """
    values = [0] * len(gadget["sizes"])
    for video, endpoint, nb_requests in gadget["requests"]:
        latency, cache_latency = gadget["endpoints"][endpoint]
        values[video] += nb_requests * (latency - cache_latency)
    return values

def knapsack(sizes, values, capacity):
    """
        Sac à dos exact : retourne (temps gagné maximum, liste des vidéos choisies)
    """
    best = [(0, [])] * (capacity + 1)
    for video, (size, value) in enumerate(zip(sizes, values)):
        for free in range(capacity, size - 1, -1):
            candidate = best[free - size][0] + value
            if candidate > best[free][0]:
                best[free] = (candidate, best[free - size][1] + [video])
    return best[capacity]

def fill_in_order(gadget, capacity, order):
    """
        Remplit le cache en prenant les vidéos dans l'ordre donné, quand elles rentrent
    """
    chosen = []
    free = capacity
    for video in order:
        if gadget["sizes"][video] <= free:
            chosen.append(video)
            free -= gadget["sizes"][video]
    return chosen

def density_greedy(gadget, capacity):
    """
        Glouton classique : les vidéos triées par temps gagné / taille décroissant
    """
    values = video_values(gadget)
    order = sorted(range(len(values)), key=lambda v: values[v] / gadget["sizes"][v], reverse=True)
    return fill_in_order(gadget, capacity, order)

def value_greedy(gadget, capacity):
    """
        Autre glouton classique : les vidéos triées par temps gagné décroissant
    """
    values = video_values(gadget)
    order = sorted(range(len(values)), key=lambda v: values[v], reverse=True)
    return fill_in_order(gadget, capacity, order)

TRAPPED_GREEDY = [
    ("glouton gain/taille (estimation)", density_greedy),
    ("glouton gain (estimation)", value_greedy),
]


# ============================ Génération des gadgets ============================

def split_sizes(nb_videos, total_size):
    """
        Tire nb_videos tailles aléatoires dont la somme ne dépasse pas total_size
    """
    weights = [random.uniform(0.6, 1.4) for _ in range(nb_videos)]
    return [max(1, int(w * total_size / sum(weights))) for w in weights]

def density_trap(capacity, depth, gap, latency):
    """
        Piège pour le glouton gain/taille : une grosse vidéo qui remplit le cache (l'optimum)
        contre des petites vidéos plus denses, mais qui rapportent moins à elles toutes.
        Une fois les petites placées, il faut toutes les retirer pour faire rentrer la grosse.
    """
    endpoints = [(random.randint(*latency), random.randint(1, 60)) for _ in range(random.randint(1, 3))]
    nb_small = random.randint(*depth)
    # densite d'une petite video / densite de la grosse
    ratios = [random.uniform(1.15, 1.6) for _ in range(nb_small)]
    # sum(ratio * taille) = (1 - gap) * capacity, donc les petites rapportent (1 - gap) fois la grosse
    small_sizes = split_sizes(nb_small, (1 - random.uniform(*gap)) * capacity / (sum(ratios) / nb_small))

    requests = []
    for endpoint in range(len(endpoints)):
        # la grosse (video 0) n'est au-dessus du seuil que pour le premier endpoint
        if endpoint == 0:
            nb_big = random.randint(THRESHOLD + 1, MAX_NB_REQUESTS)
        else:
            nb_big = random.randint(THRESHOLD // 5, THRESHOLD)
        requests.append((0, endpoint, nb_big))
        for i in range(nb_small):
            noise = random.uniform(0.9, 1.1)
            requests.append((i + 1, endpoint, max(1, round(ratios[i] * small_sizes[i] / capacity * nb_big * noise))))

    return {"sizes": [capacity] + small_sizes, "endpoints": endpoints, "requests": requests}

def value_trap(capacity, depth, gap, latency):
    """
        Piège pour le glouton gain : une grosse vidéo peu demandée mais par un endpoint qui gagne
        beaucoup à passer par le cache, contre des vidéos moyennes très demandées par un endpoint
        qui y gagne peu (l'optimum). La grosse rapporte plus que chaque moyenne, mais moins que
        toutes les moyennes réunies.
    """
    medium_sizes = split_sizes(random.randint(*depth), capacity)
    medium_sizes[-1] += capacity - sum(medium_sizes)
    requests = [(i + 1, 1, random.randint(THRESHOLD + 1, MAX_NB_REQUESTS)) for i in range(len(medium_sizes))]
    nb_medium_requests = sum(nb_requests for _, _, nb_requests in requests)

    # endpoint 0 : gros gain, endpoint 1 : petit gain, choisi pour que la grosse (video 0)
    # reste sous le seuil tout en rapportant (1 - gap) fois l'ensemble des moyennes
    endpoints = [(random.randint(latency[1] * 9 // 10, latency[1]), random.randint(1, 20))]
    big_gain = endpoints[0][0] - endpoints[0][1]
    kept = 1 - random.uniform(*gap)
    medium_gain = max(1, round(random.randint(THRESHOLD * 3 // 5, THRESHOLD) * big_gain / (kept * nb_medium_requests)))
    cache_latency = random.randint(100, 300)
    endpoints.append((cache_latency + medium_gain, cache_latency))
    requests.append((0, 0, round(kept * medium_gain * nb_medium_requests / big_gain)))

    return {"sizes": [capacity] + medium_sizes, "endpoints": endpoints, "requests": requests}

def neutral(capacity, latency):
    """
        Gadget sans piège, pour noyer les autres : des vidéos de même taille et un seul endpoint,
        tous les gloutons y trouvent l'optimum.
    """
    nb_planted = random.choice([k for k in range(2, 11) if capacity % k == 0] or [1])
    nb_videos = nb_planted + random.randint(1, 4)
    requests = []
    for video in range(nb_videos):
        if video < nb_planted:
            requests.append((video, 0, random.randint(THRESHOLD + 1, MAX_NB_REQUESTS)))
        else:
            requests.append((video, 0, random.randint(100, THRESHOLD * 4 // 5)))
    return {"sizes": [capacity // nb_planted] * nb_videos, "endpoints": [(random.randint(*latency), random.randint(1, 60))], "requests": requests}

def is_valid(gadget, capacity, trapped_greedy, gap_min):
    """
        Vérifie que les vidéos au-dessus du seuil (celles que greedy.py place en premier)
        remplissent exactement le cache et sont l'optimum du gadget,
        et que le glouton piégé y perd au moins gap_min
    """
    if any(not 1 <= nb_requests <= MAX_NB_REQUESTS for _, _, nb_requests in gadget["requests"]):
        return False
    planted = [video for video, _, nb_requests in gadget["requests"] if nb_requests > THRESHOLD]
    if len(set(planted)) != len(planted) or sum(gadget["sizes"][v] for v in planted) != capacity:
        return False

    values = video_values(gadget)
    optimum, _ = knapsack(gadget["sizes"], values, capacity)
    if sum(values[v] for v in planted) != optimum:
        return False
    if trapped_greedy is None:
        return True
    return sum(values[v] for v in trapped_greedy(gadget, capacity)) <= (1 - gap_min) * optimum

def generate_gadget(make, capacity, trapped_greedy, gap_min):
    """
        Tire des gadgets jusqu'à en obtenir un valide
    """
    for _ in range(MAX_TRIES):
        gadget = make()
        if is_valid(gadget, capacity, trapped_greedy, gap_min):
            return gadget
    raise RuntimeError("Impossible de générer un gadget valide, essayer une capacité plus grande, plus de leurres (--depth) ou un gap plus petit")


# ============================ Assemblage de l'instance ============================

def secondary_latency(latency, home_gain=None):
    """
        Latence d'un lien secondaire : un gain faible devant celui du cache principal de l'endpoint
    """
    if home_gain is None:
        home_gain = latency
    return latency - max(1, round(random.uniform(0.02, 0.08) * home_gain))

def assemble(gadgets, capacity, latency_range, nb_videos, nb_endpoints, nb_requests, nb_links):
    """
        Regroupe les gadgets en une seule instance en mélangeant tous les identifiants, puis complète
        jusqu'aux tailles demandées avec du remplissage : chaque endpoint est relié à nb_links caches
        (le sien + des liens secondaires à faible gain), des vidéos et des endpoints en plus,
        et des requêtes aléatoires avec très peu de requêtes.
    """
    nb_caches = len(gadgets)
    nb_videos = max(nb_videos, sum(len(g["sizes"]) for g in gadgets))
    nb_endpoints = max(nb_endpoints, sum(len(g["endpoints"]) for g in gadgets))
    video_ids = random.sample(range(nb_videos), nb_videos)
    endpoint_ids = random.sample(range(nb_endpoints), nb_endpoints)
    cache_ids = random.sample(range(nb_caches), nb_caches)

    video_sizes = [0] * nb_videos
    endpoints = [None] * nb_endpoints   # [latence, [[cache, latence], ...]]
    home_cache = [None] * nb_endpoints
    home_videos = [[] for _ in gadgets]
    requests = []
    solutions = {label: [[] for _ in gadgets] for label, _ in TRAPPED_GREEDY}

    first_video = 0
    first_endpoint = 0
    for gadget, cache_id in zip(gadgets, cache_ids):
        for video, size in enumerate(gadget["sizes"]):
            video_sizes[video_ids[first_video + video]] = size
            home_videos[cache_id].append(video_ids[first_video + video])
        for endpoint, (latency, cache_latency) in enumerate(gadget["endpoints"]):
            endpoint_id = endpoint_ids[first_endpoint + endpoint]
            links = [[cache_id, cache_latency]]
            for other in random.sample([c for c in range(nb_caches) if c != cache_id], nb_links - 1):
                links.append([other, secondary_latency(latency, latency - cache_latency)])
            endpoints[endpoint_id] = [latency, links]
            home_cache[endpoint_id] = cache_id
        for video, endpoint, nb_requests_line in gadget["requests"]:
            requests.append((video_ids[first_video + video], endpoint_ids[first_endpoint + endpoint], nb_requests_line))
        for label, solver in TRAPPED_GREEDY:
            solutions[label][cache_id] = [video_ids[first_video + video] for video in solver(gadget, capacity)]
        first_video += len(gadget["sizes"])
        first_endpoint += len(gadget["endpoints"])

    # videos et endpoints de remplissage
    for i in range(first_video, nb_videos):
        video_sizes[video_ids[i]] = random.randint(1, capacity)
    for i in range(first_endpoint, nb_endpoints):
        latency = random.randint(*latency_range)
        endpoints[endpoint_ids[i]] = [latency, [[c, secondary_latency(latency)] for c in random.sample(range(nb_caches), nb_links)]]

    # requetes de remplissage
    pairs = set((video, endpoint) for video, endpoint, _ in requests)
    while len(requests) < min(nb_requests, nb_videos * nb_endpoints):
        video, endpoint = random.randrange(nb_videos), random.randrange(nb_endpoints)
        if (video, endpoint) not in pairs:
            pairs.add((video, endpoint))
            requests.append((video, endpoint, random.randint(1, NOISE_MAX_NB_REQUESTS)))

    for _, links in endpoints:
        random.shuffle(links)
    random.shuffle(requests)
    return video_sizes, endpoints, requests, home_cache, home_videos, solutions

def certify(capacity, video_sizes, endpoints, requests, home_cache, home_videos):
    """
        Calcule une borne supérieure du temps gagné et la solution plantée.

        Le temps gagné par une solution est au plus la somme, sur chaque cache, des temps gagnés par
        ses vidéos prises isolément, donc au plus la somme des sacs à dos de chaque cache.
        La solution plantée met dans chaque cache le meilleur sac à dos parmi les vidéos de son gadget.
        Si aucun cache ne fait mieux avec les vidéos des autres gadgets, elle atteint la borne : elle
        est optimale. Sinon on divise par 2 le gain des liens secondaires vers ce cache et on recommence.

        Retourne (borne, temps gagné par la solution plantée, solution plantée, nb de caches non prouvés)
    """
    requests_of = [[] for _ in endpoints]
    for video, endpoint, nb_requests in requests:
        requests_of[endpoint].append((video, nb_requests))
    linked = [[] for _ in home_videos]
    for endpoint, (_, links) in enumerate(endpoints):
        for link in links:
            linked[link[0]].append((endpoint, link))

    def check(cache_id):
        values = {}
        for endpoint, link in linked[cache_id]:
            gain = endpoints[endpoint][0] - link[1]
            for video, nb_requests in requests_of[endpoint]:
                values[video] = values.get(video, 0) + nb_requests * gain

        best = np.zeros(capacity + 1, dtype=np.int64)
        for video, value in values.items():
            size = video_sizes[video]
            if size <= capacity:
                best[size:] = np.maximum(best[size:], best[:capacity + 1 - size] + value)

        home = home_videos[cache_id]
        planted_value, chosen = knapsack([video_sizes[v] for v in home], [values.get(v, 0) for v in home], capacity)
        return int(best[capacity]), planted_value, [home[i] for i in chosen]

    results = [None] * len(home_videos)
    to_check = range(len(home_videos))
    for repair in range(MAX_REPAIRS + 1):
        for cache_id in to_check:
            results[cache_id] = check(cache_id)
        to_check = [c for c in to_check if results[c][0] > results[c][1]]
        if not to_check or repair == MAX_REPAIRS:
            break
        for cache_id in to_check:
            for endpoint, link in linked[cache_id]:
                if home_cache[endpoint] != cache_id:
                    latency = endpoints[endpoint][0]
                    link[1] = latency - max(1, (latency - link[1]) // 2)

    upper_bound = sum(r[0] for r in results)
    planted_value = sum(r[1] for r in results)
    return upper_bound, planted_value, [r[2] for r in results], len(to_check)

def write_instance(file_path, capacity, nb_caches, video_sizes, endpoints, requests):
    """
        Crée un fichier Txt contenant l'instance
    """
    with open(file_path, "w") as fichier:
        fichier.write(f"{len(video_sizes)} {len(endpoints)} {len(requests)} {nb_caches} {capacity}\n")
        fichier.write(" ".join(map(str, video_sizes)) + "\n")
        for latency, linked_caches in endpoints:
            fichier.write(f"{latency} {len(linked_caches)}\n")
            for cache_id, cache_latency in linked_caches:
                fichier.write(f"{cache_id} {cache_latency}\n")
        for request in requests:
            fichier.write(f"{request[0]} {request[1]} {request[2]}\n")

def main():
    parser = argparse.ArgumentParser(description="Génère une instance piégée pour les gloutons classiques, avec son optimum")
    parser.add_argument("name", nargs="?", default="trap", help="nom de l'instance (sans extension)")
    parser.add_argument("--caches", type=int, default=200, help="nombre de caches (un gadget par cache)")
    parser.add_argument("--capacity", type=int, default=500, help="capacité des caches")
    parser.add_argument("--density", type=float, default=0.45, help="proportion de pièges pour le glouton gain/taille")
    parser.add_argument("--value", type=float, default=0.45, help="proportion de pièges pour le glouton gain (le reste est sans piège)")
    parser.add_argument("--depth", type=int, nargs=2, default=[4, 8], metavar=("MIN", "MAX"), help="nombre de vidéos leurres par piège")
    parser.add_argument("--gap", type=float, nargs=2, default=[0.1, 0.3], metavar=("MIN", "MAX"), help="perte du glouton piégé sur un gadget")
    parser.add_argument("--latency", type=int, nargs=2, default=[350, 500], metavar=("MIN", "MAX"),
                        help="latence datacenter des endpoints : plus elle est haute, plus tous les scores sont hauts (max 500 conseillé avec --links > 1)")
    parser.add_argument("--links", type=int, default=1, help="nombre de caches reliés à chaque endpoint")
    parser.add_argument("--videos", type=int, default=0, help="nombre total de vidéos (complété avec des vidéos de remplissage)")
    parser.add_argument("--endpoints", type=int, default=0, help="nombre total d'endpoints (complété avec des endpoints de remplissage)")
    parser.add_argument("--requests", type=int, default=0, help="nombre total de lignes de requêtes (complété avec des requêtes de remplissage)")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if not 0 < args.capacity <= MAX_VIDEO_SIZE:
        parser.error(f"la capacité doit être entre 1 et {MAX_VIDEO_SIZE} (taille max d'une vidéo, la grosse vidéo remplit le cache)")
    if args.density + args.value > 1:
        parser.error("--density + --value doit être <= 1")
    if not 100 <= args.latency[0] <= args.latency[1]:
        parser.error("--latency : il faut 100 <= MIN <= MAX")
    if not 1 <= args.links <= args.caches:
        parser.error("--links doit être entre 1 et le nombre de caches")

    random.seed(args.seed)

    nb_density = round(args.caches * args.density)
    nb_value = round(args.caches * args.value)
    gadgets = []
    for i in range(args.caches):
        if i < nb_density:
            gadgets.append(generate_gadget(lambda: density_trap(args.capacity, args.depth, args.gap, args.latency), args.capacity, density_greedy, args.gap[0]))
        elif i < nb_density + nb_value:
            gadgets.append(generate_gadget(lambda: value_trap(args.capacity, args.depth, args.gap, args.latency), args.capacity, value_greedy, args.gap[0]))
        else:
            gadgets.append(generate_gadget(lambda: neutral(args.capacity, args.latency), args.capacity, None, 0))

    video_sizes, endpoints, requests, home_cache, home_videos, solutions = assemble(
        gadgets, args.capacity, args.latency, args.videos, args.endpoints, args.requests, args.links)
    upper_bound, planted_value, planted, nb_unproven = certify(args.capacity, video_sizes, endpoints, requests, home_cache, home_videos)

    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)
    instance_path = f"{OUTPUT_DIR_PATH}/{args.name}.in"
    optimum_path = f"{OUTPUT_DIR_PATH}/{args.name}_optimum.out"
    write_instance(instance_path, args.capacity, args.caches, video_sizes, endpoints, requests)
    create_results_files(planted, optimum_path)

    print(f"Instance : {instance_path} ({len(video_sizes)} videos, {len(endpoints)} endpoints, {len(requests)} requetes, "
          f"{args.caches} caches de {args.capacity}, {args.links} caches par endpoint)")
    print(f"Solution plantée : {optimum_path}")
    max_cache_latency = max(cache_latency for _, links in endpoints for _, cache_latency in links)
    if (len(video_sizes) > MAX_VIDEOS or len(endpoints) > MAX_ENDPOINTS or args.caches > MAX_CACHES
            or max(latency for latency, _ in endpoints) > MAX_LATENCY or max_cache_latency > MAX_CACHE_LATENCY):
        print("/!\\ l'instance dépasse les bornes de l'énoncé Hash Code")
    if nb_unproven:
        print(f"/!\\ solution plantée non prouvée optimale dans {nb_unproven} caches, l'optimum est entre elle et la borne supérieure")
    else:
        print("La solution plantée atteint la borne supérieure : elle est optimale")

    # greedy.py sur l'instance complete
    greedy_caches = [[] for _ in range(args.caches)]
    data = {"requests": requests, "N_requests": len(requests), "N_cache": args.caches, "video_sizes": video_sizes, "endpoints": endpoints}
    greedy(data, greedy_caches, [args.capacity] * args.caches)

    bound = upper_bound * 1000 / sum(nb_requests for _, _, nb_requests in requests)
    scores = [("borne supérieure", bound), ("solution plantée", compute_score(planted, endpoints, requests)),
              ("greedy.py", compute_score(greedy_caches, endpoints, requests))]
    scores += [(label, compute_score(solutions[label], endpoints, requests)) for label, _ in TRAPPED_GREEDY]
    for label, score in scores:
        print(f"{label:<34} | score: {score:>14.2f} | écart: {(score - bound) / bound * 100:>7.2f}%")


if __name__ == "__main__":
    main()
