import argparse
import os
import random

from utils import compute_score, create_results_files

OUTPUT_DIR_PATH = "instances/generated"

# bornes de l'énoncé Hash Code 2017
MAX_VIDEOS = 10000
MAX_ENDPOINTS = 1000
MAX_CACHES = 1000
MAX_VIDEO_SIZE = 1000
MAX_NB_REQUESTS = 10000

MAX_TRIES = 2000

# Un "gadget" = un cache, ses endpoints et ses vidéos, indépendant du reste de l'instance :
#   sizes     : taille de chaque vidéo du gadget
#   endpoints : (latence datacenter, latence vers le cache du gadget)
#   requests  : (video, endpoint, nb requêtes), avec des indices locaux au gadget
# Comme les gadgets ne partagent rien, l'optimum de l'instance est la somme
# des optimums de chaque gadget, et chaque gadget est un simple sac à dos.


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

def knapsack(gadget, capacity):
    """
        Sac à dos exact : la liste des vidéos qui maximise le temps gagné
    """
    best = [(0, [])] * (capacity + 1)
    for video, (size, value) in enumerate(zip(gadget["sizes"], video_values(gadget))):
        for free in range(capacity, size - 1, -1):
            candidate = best[free - size][0] + value
            if candidate > best[free][0]:
                best[free] = (candidate, best[free - size][1] + [video])
    return best[capacity][1]

def fill_in_order(gadget, capacity, order):
    """
        Remplit le cache en prenant les vidéos dans l'ordre donné, quand elles rentrent
    """
    chosen = []
    free = capacity
    for video in order:
        if video not in chosen and gadget["sizes"][video] <= free:
            chosen.append(video)
            free -= gadget["sizes"][video]
    return chosen

def count_greedy(gadget, capacity):
    """
        Même logique que greedy.py : les requêtes triées par nombre de requêtes décroissant
    """
    sorted_requests = sorted(gadget["requests"], key=lambda x: x[2], reverse=True)
    return fill_in_order(gadget, capacity, [video for video, _, _ in sorted_requests])

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

SOLVERS = [
    ("optimum", knapsack),
    ("glouton nb requetes (greedy.py)", count_greedy),
    ("glouton gain/taille", density_greedy),
    ("glouton gain", value_greedy),
]


# ============================ Génération des gadgets ============================

def split_sizes(nb_videos, total_size):
    """
        Tire nb_videos tailles aléatoires dont la somme ne dépasse pas total_size
    """
    weights = [random.uniform(0.6, 1.4) for _ in range(nb_videos)]
    return [max(1, int(w * total_size / sum(weights))) for w in weights]

def density_trap(capacity, depth, gap):
    """
        Piège pour le glouton gain/taille : une grosse vidéo qui remplit le cache (l'optimum)
        contre des petites vidéos plus denses, mais qui rapportent moins à elles toutes.
        Une fois les petites placées, il faut toutes les retirer pour faire rentrer la grosse.
    """
    endpoints = [(random.randint(600, 2000), random.randint(20, 300)) for _ in range(random.randint(1, 3))]
    nb_small = random.randint(*depth)
    # densite d'une petite video / densite de la grosse
    ratios = [random.uniform(1.15, 1.6) for _ in range(nb_small)]
    # sum(ratio * taille) = (1 - gap) * capacity, donc les petites rapportent (1 - gap) fois la grosse
    small_sizes = split_sizes(nb_small, (1 - random.uniform(*gap)) * capacity / (sum(ratios) / nb_small))
    # la grosse (video 0) ne rentre plus des qu'une petite est dans le cache
    big_size = capacity - random.randrange(min(small_sizes))

    requests = []
    for endpoint in range(len(endpoints)):
        nb_big = random.randint(4000, MAX_NB_REQUESTS)
        requests.append((0, endpoint, nb_big))
        for i in range(nb_small):
            noise = random.uniform(0.9, 1.1)
            requests.append((i + 1, endpoint, round(ratios[i] * small_sizes[i] / big_size * nb_big * noise)))

    return {"sizes": [big_size] + small_sizes, "endpoints": endpoints, "requests": requests}

def value_trap(capacity, depth, gap):
    """
        Piège pour le glouton gain : une grosse vidéo peu demandée mais par un endpoint très loin
        du datacenter, contre des vidéos moyennes très demandées par un endpoint proche (l'optimum).
        La grosse rapporte plus que chaque moyenne, mais moins que toutes les moyennes réunies.
    """
    # endpoint 0 : gros gain, endpoint 1 : petit gain
    endpoints = [(random.randint(3200, 4000), random.randint(50, 200)),
                 (random.randint(400, 500), 300)]
    big_gain = endpoints[0][0] - endpoints[0][1]
    medium_gain = endpoints[1][0] - endpoints[1][1]

    medium_sizes = split_sizes(random.randint(*depth), capacity)
    big_size = capacity - random.randrange(min(medium_sizes))

    requests = [(i + 1, 1, random.randint(3000, MAX_NB_REQUESTS)) for i in range(len(medium_sizes))]
    medium_value = medium_gain * sum(nb_requests for _, _, nb_requests in requests)
    # la grosse (video 0) rapporte (1 - gap) fois l'ensemble des moyennes
    requests.append((0, 0, round((1 - random.uniform(*gap)) * medium_value / big_gain)))

    return {"sizes": [big_size] + medium_sizes, "endpoints": endpoints, "requests": requests}

def neutral(capacity):
    """
        Gadget sans piège, pour noyer les autres : des vidéos de même taille et un seul endpoint,
        tous les gloutons y trouvent l'optimum.
    """
    size = capacity // random.randint(2, 6)
    nb_videos = capacity // size + random.randint(1, 4)
    requests = [(video, 0, random.randint(100, MAX_NB_REQUESTS)) for video in range(nb_videos)]
    return {"sizes": [size] * nb_videos, "endpoints": [(random.randint(600, 2000), random.randint(20, 300))], "requests": requests}

def is_valid(gadget, capacity, trapped_greedy, gap_min):
    """
        Vérifie que greedy.py trouve l'optimum du gadget,
        et que le glouton piégé y perd au moins gap_min
    """
    video_of = {}
    for video, _, nb_requests in gadget["requests"]:
        if not 1 <= nb_requests <= MAX_NB_REQUESTS:
            return False
        # deux videos avec le meme nombre de requetes : l'ordre de greedy.py dependrait du fichier
        if video_of.setdefault(nb_requests, video) != video:
            return False

    values = video_values(gadget)
    optimum = sum(values[v] for v in knapsack(gadget, capacity))
    if sum(values[v] for v in count_greedy(gadget, capacity)) != optimum:
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
    raise RuntimeError("Impossible de générer un gadget valide, essayer une capacité plus grande ou un gap plus petit")


# ============================ Assemblage de l'instance ============================

def assemble(gadgets, capacity):
    """
        Regroupe les gadgets en une seule instance en mélangeant tous les identifiants.
        Retourne aussi, pour chaque solveur, sa solution sur l'instance complète.
    """
    nb_videos = sum(len(g["sizes"]) for g in gadgets)
    nb_endpoints = sum(len(g["endpoints"]) for g in gadgets)
    video_ids = random.sample(range(nb_videos), nb_videos)
    endpoint_ids = random.sample(range(nb_endpoints), nb_endpoints)
    cache_ids = random.sample(range(len(gadgets)), len(gadgets))

    video_sizes = [0] * nb_videos
    endpoints = [None] * nb_endpoints
    requests = []
    solutions = {label: [[] for _ in gadgets] for label, _ in SOLVERS}

    first_video = 0
    first_endpoint = 0
    for gadget, cache_id in zip(gadgets, cache_ids):
        for video, size in enumerate(gadget["sizes"]):
            video_sizes[video_ids[first_video + video]] = size
        for endpoint, (latency, cache_latency) in enumerate(gadget["endpoints"]):
            endpoints[endpoint_ids[first_endpoint + endpoint]] = (latency, [(cache_id, cache_latency)])
        for video, endpoint, nb_requests in gadget["requests"]:
            requests.append((video_ids[first_video + video], endpoint_ids[first_endpoint + endpoint], nb_requests))
        for label, solver in SOLVERS:
            solutions[label][cache_id] = [video_ids[first_video + video] for video in solver(gadget, capacity)]
        first_video += len(gadget["sizes"])
        first_endpoint += len(gadget["endpoints"])

    random.shuffle(requests)
    return video_sizes, endpoints, requests, solutions

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
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if not 0 < args.capacity <= MAX_VIDEO_SIZE:
        parser.error(f"la capacité doit être entre 1 et {MAX_VIDEO_SIZE} (taille max d'une vidéo, la grosse vidéo remplit le cache)")
    if args.density + args.value > 1:
        parser.error("--density + --value doit être <= 1")

    random.seed(args.seed)

    nb_density = round(args.caches * args.density)
    nb_value = round(args.caches * args.value)
    gadgets = []
    for i in range(args.caches):
        if i < nb_density:
            gadgets.append(generate_gadget(lambda: density_trap(args.capacity, args.depth, args.gap), args.capacity, density_greedy, args.gap[0]))
        elif i < nb_density + nb_value:
            gadgets.append(generate_gadget(lambda: value_trap(args.capacity, args.depth, args.gap), args.capacity, value_greedy, args.gap[0]))
        else:
            gadgets.append(generate_gadget(lambda: neutral(args.capacity), args.capacity, None, 0))

    video_sizes, endpoints, requests, solutions = assemble(gadgets, args.capacity)

    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)
    instance_path = f"{OUTPUT_DIR_PATH}/{args.name}.in"
    optimum_path = f"{OUTPUT_DIR_PATH}/{args.name}_optimum.out"
    write_instance(instance_path, args.capacity, args.caches, video_sizes, endpoints, requests)
    create_results_files(solutions["optimum"], optimum_path)

    print(f"Instance : {instance_path} ({len(video_sizes)} videos, {len(endpoints)} endpoints, {len(requests)} requetes, {args.caches} caches de {args.capacity})")
    print(f"Solution optimale : {optimum_path}")
    if len(video_sizes) > MAX_VIDEOS or len(endpoints) > MAX_ENDPOINTS or args.caches > MAX_CACHES:
        print("/!\\ l'instance dépasse les bornes de l'énoncé Hash Code")

    optimum = compute_score(solutions["optimum"], endpoints, requests)
    for label, _ in SOLVERS:
        score = compute_score(solutions[label], endpoints, requests)
        print(f"{label:<32} | score: {score:>14.2f} | écart: {(score - optimum) / optimum * 100:>7.2f}%")


if __name__ == "__main__":
    main()
