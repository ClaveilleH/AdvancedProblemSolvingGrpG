"""
Graphiques d'exploration : effet des corrections proposées (bench/fixes.py).
Ne mesure pas les algos du groupe tels quels : à ne pas utiliser dans le diaporama.

Usage (depuis la racine) :
    python -m bench.plots_exploration

Lit bench/data/runs.csv, grid.csv et bench/data/exploration/runs_fix.csv,
écrit les images dans docs/exploration/figures/.
"""

import matplotlib.pyplot as plt

from bench.common import RUNS_CSV, GRID_CSV, EXPLORATION_CSV, EXPLORATION_FIGURES_DIR
from bench.plots import (LABELS, BLUE, ORANGE, AQUA, GREY, INK, short, save, load_runs, search_gains,
                         plot_neighbourhood)

PAIRS = [("LS", "LS_fix"), ("TS", "TS_fix"), ("TSS", "TSS_fix")]


def plot_before_after(runs, fixes):
    """Recherche locale avant et après correction : combien d'instances dégradées, et quels gains."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})

    labels, counts = [], []
    for before, after in PAIRS:
        for source, algo, suffix in [(runs, before, "avant"), (fixes, after, "après")]:
            gains = {**search_gains(source, algo, False), **search_gains(source, algo, True)}
            counts.append([sum(g < -1e-9 for g in gains.values()), sum(abs(g) <= 1e-9 for g in gains.values()),
                           sum(g > 1e-9 for g in gains.values())])
            labels.append(f"{LABELS[before]}, {suffix}")
    ys = [0, 1, 2.4, 3.4, 4.8, 5.8]
    start = [0] * len(ys)
    for k, (name, color) in enumerate([("Dégradée", ORANGE), ("Inchangée", GREY), ("Améliorée", BLUE)]):
        values = [c[k] for c in counts]
        left.barh(ys, values, left=start, height=0.75, color=color, label=name, edgecolor="white", linewidth=1.5)
        for y, x0, v in zip(ys, start, values):
            if v:
                left.text(x0 + v / 2, y, str(v), ha="center", va="center", fontsize=9, color="white" if k != 1 else INK)
        start = [x0 + v for x0, v in zip(start, values)]
    left.set_yticks(ys, labels)
    left.invert_yaxis()
    left.set_xlabel("Nombre d'instances")
    left.set_title("Solution de départ dégradée ou améliorée ?", pad=24)
    left.grid(axis="y", visible=False)
    left.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)

    after = {algo: search_gains(fixes, algo, False) for _, algo in PAIRS}
    instances = sorted(after["TS_fix"], key=lambda i: max(after[a].get(i, 0) for a in after), reverse=True)[:8]
    width = 0.26
    for k, ((before, algo), color) in enumerate(zip(PAIRS, [BLUE, AQUA, ORANGE])):
        xs = [i + (k - 1) * width for i in range(len(instances))]
        right.bar(xs, [after[algo].get(i, 0) for i in instances], width - 0.03, color=color, label=LABELS[before])
    right.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right", fontsize=8)
    right.set_ylabel("Gain sur le glouton de départ (%)")
    right.set_title("Gain après correction, hors instances jouets", pad=24)
    right.grid(axis="x", visible=False)
    right.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)
    fig.tight_layout()
    save(fig, "recherche_locale_avant_apres", EXPLORATION_FIGURES_DIR)


def main():
    runs = load_runs(RUNS_CSV)
    fixes = load_runs(EXPLORATION_CSV)
    if any(fixes[i]["TS_fix"] for i in list(fixes)):
        plot_before_after(runs, fixes)
    # même étude du voisinage que pour l'oral, mais avec la meilleure solution rencontrée
    plot_neighbourhood(load_runs(GRID_CSV), field="score_best", directory=EXPLORATION_FIGURES_DIR,
                       title="Tabu search corrigée (meilleure solution rencontrée) : voisinage et itérations")


if __name__ == "__main__":
    main()
