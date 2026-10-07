"""Graphiques des statistiques d'entrée et de sortie - Hash Code 2017."""

from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

MAX_LABELED_BARS = 50  # au-delà : ni valeurs sur les barres, ni tous les ids en X


def _int_bars(ax, values, title: str, xlabel: str, ylabel: str, color: str,
              sort_desc: bool = False) -> None:
    """Barres par indice : tous les ids en X, axe Y entier, valeur écrite sur chaque barre.

    sort_desc : trie les barres par valeur décroissante (les ids restent affichés en X).
    """
    values = np.asarray(values)
    ids = np.arange(len(values))
    if sort_desc:
        order = np.argsort(-values, kind="stable")
        values, ids = values[order], ids[order]
    n = len(values)
    bars = ax.bar(range(n), values, width=0.8, color=color)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    if n <= MAX_LABELED_BARS:
        fontsize = max(5, min(9, 300 // max(n, 1)))
        rotation = 90 if n > 20 else 0
        ax.set_xticks(range(n))
        ax.set_xticklabels(ids, fontsize=fontsize, rotation=rotation)
        ax.bar_label(bars, fmt="%d", fontsize=fontsize, rotation=rotation, padding=2)
    else:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # ticks entiers automatiques
        if sort_desc:
            xlabel = "Rang (trié par ordre décroissant)"
    if sort_desc and n <= MAX_LABELED_BARS:
        xlabel += " (trié par ordre décroissant)"
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)


def _finish(fig, save_path: str | None, show: bool) -> None:
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()


def plot_input_stats(problem, save_path: str | None = None, show: bool = True):
    """Figure de 6 graphiques décrivant les données d'entrée.

    problem : objet Problem renvoyé par read_input().
    """
    sizes = np.array(problem.video_sizes)

    req_per_video = np.zeros(problem.n_videos, dtype=np.int64)
    req_per_endpoint = np.zeros(problem.n_endpoints, dtype=np.int64)
    for video, ep, n in problem.requests:
        req_per_video[video] += n
        req_per_endpoint[ep] += n

    caches_per_endpoint = [len(e.caches) for e in problem.endpoints]
    potential_gains = [e.dc_latency - lat
                       for e in problem.endpoints for lat in e.caches.values()]

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("Statistiques d'entrée", fontsize=14)

    # 1. Répartition de la taille des vidéos
    ax[0, 0].hist(sizes, bins=40, color="#4C72B0")
    ax[0, 0].axvline(problem.cache_capacity, color="red", ls="--",
                     label=f"capacité cache ({problem.cache_capacity} Mo)")
    ax[0, 0].set(title="Taille des vidéos", xlabel="Mo", ylabel="Nb de vidéos")
    ax[0, 0].legend()

    # 2. Requêtes par vidéo (classées par popularité : longue traîne)
    ranked = np.sort(req_per_video[req_per_video > 0])[::-1]
    ax[0, 1].plot(ranked, color="#55A868")
    ax[0, 1].set(title="Requêtes par vidéo (classées)", xlabel="Rang de la vidéo",
                 ylabel="Nb de requêtes", yscale="log")

    # 3. Taille vs popularité
    ax[0, 2].scatter(sizes, req_per_video, s=6, alpha=0.5, color="#C44E52")
    ax[0, 2].set(title="Taille vs popularité", xlabel="Taille (Mo)",
                 ylabel="Nb de requêtes")

    # 4. Requêtes par endpoint (triées par ordre décroissant)
    _int_bars(ax[1, 0], req_per_endpoint, "Requêtes par endpoint",
              "Id de l'endpoint", "Nb de requêtes", "#8172B2", sort_desc=True)

    # 5. Caches connectés par endpoint (triés par ordre décroissant)
    _int_bars(ax[1, 1], caches_per_endpoint, "Caches connectés par endpoint",
              "Id de l'endpoint", "Nb de caches connectés", "#CCB974", sort_desc=True)

    # 6. Gains potentiels
    if potential_gains:
        ax[1, 2].hist(potential_gains, bins=40, color="#64B5CD")
    ax[1, 2].set(title="Gain potentiel (latence DC - latence cache)",
                 xlabel="ms", ylabel="Nb de liaisons endpoint-cache")

    _finish(fig, save_path, show)
    return fig


def plot_output_stats(stats, save_path: str | None = None, show: bool = True):
    """Figure de 6 graphiques décrivant la solution.

    stats : objet OutputStats.
    """
    p = stats.problem
    caches = list(range(p.n_caches))

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("Statistiques de sortie", fontsize=14)

    # 1. Taux de remplissage par cache
    fill = [stats.fill_rate_per_cache[c] * 100 for c in caches]
    ax[0, 0].bar(caches, fill, color="#4C72B0")
    ax[0, 0].axhline(100, color="red", ls="--", lw=1)
    ax[0, 0].set(title="Remplissage par cache", xlabel="Cache", ylabel="%",
                 ylim=(0, 110))

    # 2. Requêtes servies par cache
    ax[0, 1].bar(caches, [stats.requests_per_cache[c] for c in caches],
                 color="#55A868")
    ax[0, 1].axhline(stats.avg_requests_per_cache, color="black", ls="--", lw=1,
                     label=f"moyenne ({stats.avg_requests_per_cache:,.0f})")
    ax[0, 1].set(title="Requêtes servies par cache", xlabel="Cache",
                 ylabel="Nb de requêtes")
    ax[0, 1].legend()

    # 3. Répartition cache / datacenter
    if stats.total_requests:
        ax[0, 2].pie([stats.requests_from_cache, stats.requests_from_dc],
                     labels=["Cache", "Datacenter"], autopct="%1.1f%%",
                     colors=["#55A868", "#C44E52"], startangle=90)
    ax[0, 2].set_title("Requêtes : cache vs datacenter")

    # 4. Score vs borne supérieure
    bars = ax[1, 0].bar(["Score", "Borne sup."], [stats.score, stats.upper_bound],
                        color=["#4C72B0", "#CCB974"])
    ax[1, 0].bar_label(bars, fmt="{:,.0f}")
    ax[1, 0].set(title=f"Score vs borne sup. ({stats.score_ratio:.1%})",
                 ylabel="µs")

    # 5. Nombre de copies par vidéo placée
    copies = Counter(v for vids in stats.placement.values() for v in vids)
    dist = Counter(copies.values())
    xs = sorted(dist)
    ax[1, 1].bar(xs, [dist[x] for x in xs], color="#8172B2")
    ax[1, 1].set(title=f"Copies par vidéo (duplication {stats.duplication_rate:.1%})",
                 xlabel="Nb de copies", ylabel="Nb de vidéos")
    if xs:
        ax[1, 1].set_xticks(xs)

    # 6. Synthèse chiffrée
    capacity = p.n_caches * p.cache_capacity
    ax[1, 2].axis("off")
    ax[1, 2].text(0, 0.95, "\n".join([
        f"Caches inutilisés : {len(stats.unused_caches)} / {p.n_caches}",
        f"Remplissage moyen : {stats.avg_fill_rate:.1%}",
        f"Taille utilisée : {stats.total_used_size:,} / {capacity:,} Mo",
        f"Vidéos distinctes placées : {stats.distinct_videos:,}",
        f"Gain moyen / requête : {stats.avg_gain_ms:.2f} ms",
        f"Gain moyen / requête servie : {stats.avg_gain_ms_served:.2f} ms",
    ]), va="top", fontsize=12, family="monospace")

    _finish(fig, save_path, show)
    return fig
