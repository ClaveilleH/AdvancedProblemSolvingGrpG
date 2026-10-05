"""Lecture des fichiers d'entrée et de sortie - Hash Code 2017 (Streaming videos)."""

from dataclasses import dataclass


@dataclass
class Endpoint:
    dc_latency: int          # latence vers le datacenter (ms)
    caches: dict             # {id_cache: latence (ms)}


@dataclass
class Problem:
    n_videos: int
    n_endpoints: int
    n_request_descs: int
    n_caches: int
    cache_capacity: int      # en Mo
    video_sizes: list        # video_sizes[v] = taille en Mo
    endpoints: list          # liste d'Endoint
    requests: list           # liste de (id_video, id_endpoint, nb_requetes)


def read_input(path: str) -> Problem:
    """Lit un fichier d'entrée (.in) et renvoie un objet Problem."""
    with open(path) as f:
        tokens = iter(f.read().split())

    def nxt() -> int:
        return int(next(tokens))

    n_videos, n_endpoints, n_req_descs, n_caches, capacity = (nxt() for _ in range(5))
    video_sizes = [nxt() for _ in range(n_videos)]

    endpoints = []
    for _ in range(n_endpoints):
        dc_latency = nxt()
        k = nxt()
        caches = {}
        for _ in range(k):
            cache_id = nxt()
            caches[cache_id] = nxt()
        endpoints.append(Endpoint(dc_latency, caches))

    requests = []
    for _ in range(n_req_descs):
        video, endpoint, count = nxt(), nxt(), nxt()
        requests.append((video, endpoint, count))

    return Problem(n_videos, n_endpoints, n_req_descs, n_caches,
                   capacity, video_sizes, endpoints, requests)


def read_output(path: str, problem: Problem | None = None) -> dict:
    """Lit un fichier de sortie (.out) et renvoie {id_cache: set(id_videos)}.

    Si `problem` est fourni, vérifie que les ids sont valides, qu'aucun cache
    n'apparaît deux fois et que la capacité n'est pas dépassée.
    """
    with open(path) as f:
        lines = [line.split() for line in f if line.strip()]

    n_used = int(lines[0][0])
    if len(lines) - 1 != n_used:
        raise ValueError(f"{n_used} caches annoncés, {len(lines) - 1} lignes trouvées")

    placement = {}
    for parts in lines[1:]:
        cache_id = int(parts[0])
        videos = [int(x) for x in parts[1:]]
        if cache_id in placement:
            raise ValueError(f"Cache {cache_id} défini plusieurs fois")
        if len(videos) != len(set(videos)):
            raise ValueError(f"Vidéo en double dans le cache {cache_id}")
        placement[cache_id] = set(videos)

    if problem is not None:
        for cache_id, videos in placement.items():
            if not 0 <= cache_id < problem.n_caches:
                raise ValueError(f"Cache {cache_id} inexistant")
            if any(not 0 <= v < problem.n_videos for v in videos):
                raise ValueError(f"Vidéo inexistante dans le cache {cache_id}")
            used = sum(problem.video_sizes[v] for v in videos)
            if used > problem.cache_capacity:
                raise ValueError(
                    f"Cache {cache_id} dépasse la capacité ({used} > {problem.cache_capacity})")

    return placement


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Statistiques et graphiques Hash Code 2017 (entrée et sortie).")
    parser.add_argument("-i", "--input", required=True,
                        help="chemin du fichier d'entrée (.in)")
    parser.add_argument("-o", "--output",
                        help="chemin du fichier de sortie (.out), optionnel")
    parser.add_argument("--plots", action=argparse.BooleanOptionalAction, default=True,
                        help="affiche les graphiques (défaut : oui, --no-plots pour les désactiver)")
    parser.add_argument("-s", "--save", metavar="NOM",
                        help="enregistre les images : NOM_input.png et/ou NOM_output.png "
                             "(NOM peut contenir un dossier, ex. resultats/kittens)")
    parser.add_argument("-w", "--which", choices=["input", "output", "both"], default=None,
                        help="quelles images afficher/enregistrer (défaut : output si -o est fourni, sinon input)")
    args = parser.parse_args()

    if args.which is not None:
        want_input = args.which in ("input", "both")
        want_output = args.which in ("output", "both")
    elif args.output:
        want_input = False
        want_output = True
    else:
        want_input = True
        want_output = False

    if args.save and want_output and not want_input and not args.output:
        parser.error("--which output nécessite un fichier de sortie (-o)")

    prob = read_input(args.input)
    if not args.output:
        print(f"Entrée : {prob.n_videos} vidéos, {prob.n_endpoints} endpoints, "
              f"{prob.n_request_descs} descriptions de requêtes, "
              f"{prob.n_caches} caches de {prob.cache_capacity} Mo")

    stats = None
    if args.output:
        placement = read_output(args.output, prob)
        print(f"Sortie : {len(placement)} caches utilisés sur {prob.n_caches}")

        from plot_metrics import OutputStats
        stats = OutputStats(prob, placement)
        print()
        print(stats.report())

    if args.plots or args.save:
        import os
        import matplotlib.pyplot as plt
        from show_metrics import plot_input_stats, plot_output_stats

        if args.save and os.path.dirname(args.save):
            os.makedirs(os.path.dirname(args.save), exist_ok=True)

        make_input = want_input
        make_output = want_output and stats is not None

        if make_input:
            path = f"{args.save}_input.png" if args.save and want_input else None
            plot_input_stats(prob, save_path=path, show=False)
            if path:
                print(f"Image enregistrée : {path}")
        if make_output:
            path = f"{args.save}_output.png" if args.save and want_output else None
            plot_output_stats(stats, save_path=path, show=False)
            if path:
                print(f"Image enregistrée : {path}")

        if args.plots:
            plt.show()  # affiche toutes les figures ensemble
        plt.close("all")


if __name__ == "__main__":
    main()
