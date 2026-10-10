"""
Graphiques de l'oral, à partir des CSV du bench.

Usage (depuis la racine) :
    python -m bench.plots

Lit bench/data/runs.csv, grid.csv, features.csv, solutions.csv et le Google Sheet (score VBS),
écrit les images dans docs/oral/figures/.
"""

import os
from collections import defaultdict
from statistics import mean, pstdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bench.common import DATA_DIR, FIGURES_DIR, RUNS_CSV, GRID_CSV, FEATURES_CSV, TOY, read_csv, read_sheet

# instances du graphique des gloutons : liste vide = les NB_AUTO où les gloutons diffèrent le plus
GREEDY_INSTANCES = []
NB_AUTO = 10

ALGOS = ["Greedy", "Greedy2", "Greedy3", "KS_indep", "KS_maj", "LS", "TS", "TSS"]
LABELS = {"Greedy": "Glouton 1", "Greedy2": "Glouton 2", "Greedy3": "Glouton 3",
          "KS_indep": "Knapsack indép.", "KS_maj": "Knapsack m.à.j.",
          "LS": "Descente", "TS": "Tabou aléatoire", "TSS": "Tabou trié"}

# couleurs fixes par rôle (palette catégorielle : bleu, orange, aqua, jaune)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY = "#b9b8b2"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"]

plt.rcParams.update({
    "figure.dpi": 200, "savefig.bbox": "tight", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False,
})


def save(fig, name):
    os.makedirs(FIGURES_DIR, exist_ok=True)
    path = f"{FIGURES_DIR}/{name}.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"Image enregistrée : {path}")


def short(name):
    return name if len(name) <= 22 else name[:20] + "…"


def number(value):
    return float(value) if value not in ("", None) else None


def load_runs(path):
    """{instance: {algo: [lignes du CSV]}}"""
    res = defaultdict(lambda: defaultdict(list))
    for row in read_csv(path):
        res[row["instance"]][row["algo"]].append(row)
    return res


def mean_score(rows, field="score"):
    values = [number(row[field]) for row in rows if row["status"] in ("ok", "timeout") and number(row[field]) is not None]
    return mean(values) if values else None


def gap(score, reference):
    """Écart au score de référence, en %."""
    if score is None or not reference:
        return None
    return (reference - score) / reference * 100


def reference_scores(runs):
    """Score de référence par instance : le VBS du Sheet, sinon le meilleur score mesuré."""
    sheet = read_sheet()
    res = {}
    for instance, algos in runs.items():
        measured = [mean_score(rows, "score_best") for rows in algos.values()]
        measured = [s for s in measured if s is not None]
        res[instance] = max([sheet.get(instance, {}).get("VBS") or 0] + measured)
    return res


# ============================ 1. Gloutons ============================

def plot_greedies(runs, ref):
    greedies = ["Greedy", "Greedy2", "Greedy3"]
    gaps = {}
    for instance, algos in runs.items():
        values = [gap(mean_score(algos[a]), ref[instance]) for a in greedies]
        if None not in values and instance not in TOY:
            gaps[instance] = values
    if not gaps:
        return
    instances = GREEDY_INSTANCES or sorted(gaps, key=lambda i: max(gaps[i]) - min(gaps[i]), reverse=True)[:NB_AUTO]
    instances = [i for i in instances if i in gaps]

    fig, ax = plt.subplots(figsize=(9, 4))
    width = 0.26
    for k, (algo, color) in enumerate(zip(greedies, [BLUE, ORANGE, AQUA])):
        xs = [i + (k - 1) * width for i in range(len(instances))]
        ax.bar(xs, [gaps[i][k] for i in instances], width - 0.03, color=color, label=LABELS[algo])
    ax.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right")
    ax.set_ylabel("Écart au meilleur score connu (%)")
    ax.set_title("Les trois gloutons, sur les instances où ils diffèrent le plus (plus bas = mieux)", pad=24)
    ax.grid(axis="x", visible=False)
    ax.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2)
    save(fig, "gloutons")
    return instances


def plot_greedy_waste(instances, solutions):
    """Part de la capacité occupée par des vidéos qui ne servent aucune requête, sur les mêmes instances."""
    greedies = ["Greedy", "Greedy2", "Greedy3"]
    instances = [i for i in instances or [] if all((i, a) in solutions for a in greedies)]
    if not instances:
        return
    fig, ax = plt.subplots(figsize=(9, 4))
    width = 0.26
    for k, (algo, color) in enumerate(zip(greedies, [BLUE, ORANGE, AQUA])):
        xs = [i + (k - 1) * width for i in range(len(instances))]
        ax.bar(xs, [float(solutions[(i, algo)]["wasted_capacity_share"]) * 100 for i in instances], width - 0.03,
               color=color, label=LABELS[algo])
    ax.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right")
    ax.set_ylabel("Capacité gaspillée (%)")
    ax.set_title("Part de la capacité occupée par des vidéos qui ne servent aucune requête", pad=24)
    ax.grid(axis="x", visible=False)
    ax.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2)
    save(fig, "gloutons_gaspillage")


# ============================ 2. Vue d'ensemble ============================

def timed_out(rows):
    return any(row["status"] == "timeout" for row in rows)


def plot_heatmap(runs, ref):
    instances = sorted((i for i in runs if i not in TOY), key=lambda i: i.lower())
    if not instances:
        return
    bounds = [1, 3, 6, 12, 25]          # classes d'écart, en %
    half = (len(instances) + 1) // 2
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.33 * half + 1.4))
    for ax, part in zip(axes, [instances[:half], instances[half:]]):
        for y, instance in enumerate(part):
            for x, algo in enumerate(ALGOS):
                rows = runs[instance][algo]
                value = gap(mean_score(rows), ref[instance]) if rows else None
                if value is None:
                    color, text, dark = "#f0efec", "–", False
                else:
                    level = sum(value > b for b in bounds)
                    color, text, dark = SEQUENTIAL[level], f"{value:.1f}" + ("*" if timed_out(rows) else ""), level >= 3
                ax.add_patch(plt.Rectangle((x + 0.03, y + 0.06), 0.94, 0.88, color=color, linewidth=0))
                ax.text(x + 0.5, y + 0.5, text, ha="center", va="center", fontsize=8, color="white" if dark else INK)
        ax.set_xlim(0, len(ALGOS))
        ax.set_ylim(len(part), 0)
        ax.set_xticks([x + 0.5 for x in range(len(ALGOS))], [LABELS[a] for a in ALGOS], rotation=30, ha="left", fontsize=8)
        ax.xaxis.tick_top()
        ax.set_yticks([y + 0.5 for y in range(len(part))], [short(i) for i in part], fontsize=8)
        ax.tick_params(length=0)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.tight_layout()
    fig.text(0.01, -0.02, "Écart au meilleur score connu, en % (plus clair = mieux).  * limite de temps atteinte.  « – » : pas de résultat.",
             color=INK2, fontsize=8)
    save(fig, "vue_ensemble")


# ============================ 3. Recherche locale ============================

def search_gains(runs, algo, toys):
    """{instance: gain moyen (%) de l'algo sur sa solution de départ}"""
    res = {}
    for instance, algos in runs.items():
        rows = [r for r in algos[algo] if r["status"] in ("ok", "timeout") and number(r["start_score"])]
        if rows and (instance in TOY) == toys:
            res[instance] = mean((number(r["score"]) - number(r["start_score"])) / number(r["start_score"]) * 100 for r in rows)
    return res


def plot_local_search(runs):
    """Recherche locale avant et après correction : combien d'instances dégradées, et quels gains."""
    pairs = [("LS", "LS_fix"), ("TS", "TS_fix"), ("TSS", "TSS_fix")]
    if not any(runs[i]["TS_fix"] for i in runs):
        return
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})

    # à gauche : nombre d'instances dégradées / inchangées / améliorées (toutes instances)
    labels, counts = [], []
    for before, after in pairs:
        for algo, suffix in [(before, "avant"), (after, "après")]:
            gains = {**search_gains(runs, algo, False), **search_gains(runs, algo, True)}
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

    # à droite : gain après correction, sur les instances non jouets où il est le plus grand
    after = {algo: search_gains(runs, algo, False) for _, algo in pairs}
    instances = sorted(after["TS_fix"], key=lambda i: max(after[a].get(i, 0) for a in after), reverse=True)[:8]
    width = 0.26
    for k, ((before, algo), color) in enumerate(zip(pairs, [BLUE, AQUA, ORANGE])):
        xs = [i + (k - 1) * width for i in range(len(instances))]
        right.bar(xs, [after[algo].get(i, 0) for i in instances], width - 0.03, color=color, label=LABELS[before])
    right.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right", fontsize=8)
    right.set_ylabel("Gain sur le glouton de départ (%)")
    right.set_title("Gain après correction, hors instances jouets", pad=24)
    right.grid(axis="x", visible=False)
    right.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)
    fig.tight_layout()
    save(fig, "recherche_locale")


def plot_neighbourhood(grid):
    """Effet de la taille du voisinage et du nombre d'itérations, une vignette par instance."""
    instances = [i for i in grid if grid[i]["TS"]]
    if not instances:
        return
    fig, axes = plt.subplots(1, len(instances), figsize=(2.7 * len(instances), 3.6), sharey=False, squeeze=False)
    for ax, instance in zip(axes[0], instances):
        series = defaultdict(lambda: defaultdict(list))        # (algo, itérations) -> taille -> gains
        for algo in ["TS", "TSS"]:
            for r in grid[instance][algo]:
                if r["status"] not in ("ok", "timeout") or not number(r["start_score"]):
                    continue
                params = dict(p.split("=") for p in r["params"].split(";"))
                gain = (number(r["score_best"]) - number(r["start_score"])) / number(r["start_score"]) * 100
                series[(algo, int(params["it"]))][int(params["nbC"])].append(gain)
        for (algo, iterations), points in sorted(series.items()):
            sizes = sorted(points)
            ax.plot(sizes, [mean(points[s]) for s in sizes], marker="o", markersize=5, linewidth=2,
                    color=AQUA if algo == "TS" else ORANGE, linestyle="-" if iterations == max(i for _, i in series) else "--",
                    label=f"{LABELS[algo]}, {iterations} itérations")
        ax.set_xscale("log")
        ax.set_xticks(sizes, [str(s) for s in sizes])
        ax.minorticks_off()
        ax.set_title(short(instance), fontsize=10)
        ax.set_xlabel("Taille du voisinage")
        ax.tick_params(labelsize=8)
    axes[0][0].set_ylabel("Gain sur le glouton de départ (%)")
    handles, names = axes[0][-1].get_legend_handles_labels()
    fig.legend(handles, names, ncols=4, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("Tabu search corrigée : effet de la taille du voisinage (caches = vidéos) et du nombre d'itérations",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    save(fig, "voisinage")


# ============================ 4. Knapsack ============================

def plot_knapsack_branches(runs, features):
    """Nombre de caches traités par chaque branche du knapsack avec mise à jour."""
    rows = []
    for instance, algos in runs.items():
        if not algos["KS_maj"] or instance in TOY or instance not in features:
            continue
        r = algos["KS_maj"][0]
        counts = [int(r[f] or 0) for f in ["ks_dp_weight", "ks_dp_value", "ks_greedy", "ks_greedy_abandon"]]
        nb_caches = int(features[instance]["C"])
        rows.append((instance, counts + [max(0, nb_caches - sum(counts))], nb_caches, r["status"]))
    if not rows:
        return
    rows.sort(key=lambda row: (row[1][2] + row[1][3]) / row[2])

    fig, ax = plt.subplots(figsize=(10, 0.19 * len(rows) + 1.2))
    names = ["DP sur le poids", "DP sur la valeur", "Glouton (repli)", "Abandon (sac vide)", "Non traité (limite de temps)"]
    colors = [BLUE, AQUA, ORANGE, YELLOW, GREY]
    left = [0] * len(rows)
    for k in range(5):
        shares = [row[1][k] / row[2] * 100 for row in rows]
        if not any(shares):
            continue
        ax.barh(range(len(rows)), shares, left=left, height=0.7, color=colors[k], label=names[k], edgecolor="white", linewidth=1)
        left = [l + s for l, s in zip(left, shares)]
    ax.set_yticks(range(len(rows)), [f"{short(row[0])}  ({row[2]} caches)" for row in rows], fontsize=7)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Part des caches (%)")
    ax.set_title("Knapsack avec mise à jour : quelle résolution pour quels caches ?")
    ax.grid(axis="y", visible=False)
    ax.legend(ncols=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    save(fig, "knapsack_branches")


def plot_knapsack_update(runs, features):
    """Gain de la mise à jour entre caches, en fonction du nombre de caches par endpoint."""
    points = []
    for instance, algos in runs.items():
        if instance in TOY or instance not in features or not algos["KS_indep"] or not algos["KS_maj"]:
            continue
        indep, maj = algos["KS_indep"][0], algos["KS_maj"][0]
        if indep["status"] != "ok" or maj["status"] != "ok" or not number(indep["score"]):
            continue
        gain = (number(maj["score"]) - number(indep["score"])) / number(indep["score"]) * 100
        points.append((float(features[instance]["caches_per_endpoint"]), gain, instance))
    if not points:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter([p[0] for p in points], [p[1] for p in points], s=45, color=BLUE, edgecolor="white", linewidth=1, zorder=3)
    for x, y, instance in sorted(points, key=lambda p: -abs(p[1]))[:3]:
        ax.annotate(short(instance), (x, y), xytext=(6, 4), textcoords="offset points", fontsize=7, color=INK2)
    ax.axhline(0, color=INK2, linewidth=0.8)
    # échelle linéaire jusqu'à 10 %, logarithmique au-delà : quelques gains dépassent 100 %
    ax.set_yscale("symlog", linthresh=10)
    ax.set_yticks([0, 5, 10, 100, 1000], ["0", "5", "10", "100", "1000"])
    ax.set_ylim(bottom=-2)
    ax.set_xlabel("Nombre moyen de caches par endpoint")
    ax.set_ylabel("Gain de score de la mise à jour (%)")
    ax.set_title("La mise à jour entre caches rapporte-t-elle plus quand les caches se recouvrent ?")
    save(fig, "knapsack_maj")


# ============================ 5. Temps et capacité ============================

def plot_time_gap(runs, ref):
    families = [("Gloutons", ["Greedy", "Greedy2", "Greedy3"], BLUE),
                ("Knapsack", ["KS_indep", "KS_maj"], ORANGE),
                ("Recherche locale", ["LS", "TS", "TSS"], AQUA)]
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, algos, color in families:
        xs, ys = [], []
        for instance in runs:
            if instance in TOY:
                continue
            for algo in algos:
                rows = [r for r in runs[instance][algo] if number(r["time_s"]) is not None]
                value = gap(mean_score(rows), ref[instance])
                if rows and value is not None:
                    xs.append(max(mean(number(r["time_s"]) for r in rows), 1e-3))
                    ys.append(value)
        ax.scatter(xs, ys, s=28, color=color, edgecolor="white", linewidth=0.8, label=label, zorder=3)
    ax.set_xscale("log")
    ax.set_xlabel("Temps d'exécution (s, échelle log)")
    ax.set_ylabel("Écart au meilleur score connu (%)")
    ax.set_title("Compromis temps / qualité (un point = un algo sur une instance)")
    ax.legend()
    save(fig, "temps_qualite")


def plot_capacity(runs, ref, features):
    """Écart du meilleur glouton et du knapsack en fonction de la place disponible dans les caches."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, algos, color in [("Meilleur glouton", ["Greedy", "Greedy2", "Greedy3"], BLUE), ("Knapsack m.à.j.", ["KS_maj"], ORANGE)]:
        done, cut = [], []
        for instance in runs:
            if instance in TOY or instance not in features:
                continue
            gaps = [(gap(mean_score(runs[instance][a]), ref[instance]), timed_out(runs[instance][a])) for a in algos if runs[instance][a]]
            gaps = [g for g in gaps if g[0] is not None]
            if gaps:
                value, interrupted = min(gaps)
                (cut if interrupted else done).append((float(features[instance]["capacity_ratio"]), value))
        ax.scatter([p[0] for p in done], [p[1] for p in done], s=40, color=color, edgecolor="white", linewidth=1, label=label, zorder=3)
        if cut:
            ax.scatter([p[0] for p in cut], [p[1] for p in cut], s=40, facecolor="none", edgecolor=color, linewidth=1.5,
                       label=f"{label}, limite de temps atteinte", zorder=3)
    ax.set_xscale("log")
    ax.set_xlabel("Capacité totale des caches / volume total des vidéos (échelle log)")
    ax.set_ylabel("Écart au meilleur score connu (%)")
    ax.set_title("La contrainte de capacité explique-t-elle les écarts ?")
    ax.legend(fontsize=8)
    save(fig, "capacite")


def main():
    runs = load_runs(RUNS_CSV)
    grid = load_runs(GRID_CSV)
    features = {row["instance"]: row for row in read_csv(FEATURES_CSV)}
    ref = reference_scores(runs)

    solutions = {(row["instance"], row["algo"]): row for row in read_csv(f"{DATA_DIR}/solutions.csv")}
    plot_greedy_waste(plot_greedies(runs, ref), solutions)
    plot_heatmap(runs, ref)
    plot_local_search(runs)
    plot_neighbourhood(grid)
    plot_knapsack_branches(runs, features)
    plot_knapsack_update(runs, features)
    plot_time_gap(runs, ref)
    plot_capacity(runs, ref, features)


if __name__ == "__main__":
    main()
