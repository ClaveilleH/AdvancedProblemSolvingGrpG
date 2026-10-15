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

from bench.common import BEFORE_CSV, DATA_DIR, FIGURES_DIR, RUNS_CSV, GRID_CSV, FEATURES_CSV, TOY, read_csv, read_sheet

# instances du graphique des gloutons : liste vide = les NB_AUTO où les gloutons diffèrent le plus
GREEDY_INSTANCES = []
NB_AUTO = 10

ALGOS = ["Greedy", "Greedy2", "Greedy3", "KS_indep", "KS_maj", "LS", "TS", "TSS"]
LABELS = {"Greedy": "Glouton 1", "Greedy2": "Glouton 2", "Greedy3": "Glouton 3",
          "KS_indep": "Knapsack indép.", "KS_maj": "Knapsack m.à.j.",
          "LS": "local_search", "TS": "Tabou aléatoire", "TSS": "Tabou trié"}

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


def save(fig, name, directory=None):
    directory = directory or FIGURES_DIR
    os.makedirs(directory, exist_ok=True)
    path = f"{directory}/{name}.png"
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
        measured = [mean_score(rows) for algo, rows in algos.items() if algo in ALGOS]
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

    # deux versions : l'écart au meilleur score (plus bas = mieux) et la part du meilleur score atteinte (plus haut = mieux)
    for name, inverse in [("gloutons", False), ("gloutons_inverse", True)]:
        fig, ax = plt.subplots(figsize=(9, 4))
        width = 0.26
        for k, (algo, color) in enumerate(zip(greedies, [BLUE, ORANGE, AQUA])):
            xs = [i + (k - 1) * width for i in range(len(instances))]
            values = [100 - gaps[i][k] if inverse else gaps[i][k] for i in instances]
            ax.bar(xs, values, width - 0.03, color=color, label=LABELS[algo])
        ax.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right")
        ax.set_ylabel("Part du meilleur score connu (%)" if inverse else "Écart au meilleur score connu (%)")
        ax.set_title("Les trois gloutons, sur les instances où ils diffèrent le plus "
                     + ("(plus haut = mieux)" if inverse else "(plus bas = mieux)"), pad=24)
        ax.grid(axis="x", visible=False)
        ax.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2)
        save(fig, name)
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
    # deux versions de l'écart au meilleur score : plus clair = mieux, ou plus foncé = mieux
    for name, inverse in [("vue_ensemble", False), ("vue_ensemble_inverse", True)]:
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
                        if inverse:
                            level = len(bounds) - level
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
        legend = "Écart au meilleur score connu, en % (plus foncé = mieux)." if inverse else "Écart au meilleur score connu, en % (plus clair = mieux)."
        fig.text(0.01, -0.02, legend + "  * limite de temps atteinte.  « – » : pas de résultat.", color=INK2, fontsize=8)
        save(fig, name)


# ============================ 3. Recherche locale ============================

def search_gains(runs, algo, toys, field="score"):
    """{instance: gain moyen (%) de l'algo sur sa solution de départ}"""
    res = {}
    for instance, algos in runs.items():
        rows = [r for r in algos[algo] if r["status"] in ("ok", "timeout") and number(r["start_score"])]
        if rows and (instance in TOY) == toys:
            res[instance] = mean((number(r[field]) - number(r["start_score"])) / number(r["start_score"]) * 100 for r in rows)
    return res


def plot_local_search(runs):
    """Recherche locale : combien d'instances dégradées ou améliorées, et de combien."""
    algos = ["LS", "TS", "TSS"]
    if not any(runs[i]["TS"] for i in runs):
        return
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1, 1.25]})

    # à gauche : nombre d'instances dégradées / inchangées / améliorées (toutes instances)
    counts = []
    for algo in algos:
        gains = {**search_gains(runs, algo, False), **search_gains(runs, algo, True)}
        counts.append([sum(g < -1e-9 for g in gains.values()), sum(abs(g) <= 1e-9 for g in gains.values()),
                       sum(g > 1e-9 for g in gains.values())])
    ys = range(len(algos))
    start = [0] * len(algos)
    for k, (name, color) in enumerate([("Dégradée", ORANGE), ("Inchangée", GREY), ("Améliorée", BLUE)]):
        values = [c[k] for c in counts]
        left.barh(ys, values, left=start, height=0.6, color=color, label=name, edgecolor="white", linewidth=1.5)
        for y, x0, v in zip(ys, start, values):
            if v:
                left.text(x0 + v / 2, y, str(v), ha="center", va="center", fontsize=9, color="white" if k != 1 else INK)
        start = [x0 + v for x0, v in zip(start, values)]
    left.set_yticks(ys, [LABELS[a] for a in algos])
    left.invert_yaxis()
    left.set_xlabel("Nombre d'instances")
    left.set_title("Solution de départ dégradée ou améliorée ?", pad=24)
    left.grid(axis="y", visible=False)
    left.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)

    # à droite : gain sur les instances non jouets où il se passe le plus de choses
    gains = {algo: search_gains(runs, algo, False) for algo in algos}
    instances = sorted(gains["TS"], key=lambda i: max(abs(gains[a].get(i, 0)) for a in algos), reverse=True)[:8]
    width = 0.26
    for k, (algo, color) in enumerate(zip(algos, [BLUE, AQUA, ORANGE])):
        xs = [i + (k - 1) * width for i in range(len(instances))]
        right.bar(xs, [gains[algo].get(i, 0) for i in instances], width - 0.03, color=color, label=LABELS[algo])
    right.axhline(0, color=INK2, linewidth=0.8)
    right.set_xticks(range(len(instances)), [short(i) for i in instances], rotation=30, ha="right", fontsize=8)
    right.set_ylabel("Gain sur le glouton de départ (%)")
    right.set_title("Gain ou perte", pad=24)
    right.grid(axis="x", visible=False)
    right.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)
    fig.tight_layout()
    save(fig, "recherche_locale")


def plot_before_after(runs, before):
    """Recherche locale avant et après les corrections du 10/10 : combien d'instances dégradées."""
    algos = ["LS", "TS", "TSS"]
    if not any(before[i]["TS"] for i in list(before)):
        return
    labels, counts = [], []
    for algo in algos:
        for source, suffix in [(before, "avant"), (runs, "après")]:
            gains = {**search_gains(source, algo, False), **search_gains(source, algo, True)}
            counts.append([sum(g < -1e-9 for g in gains.values()), sum(abs(g) <= 1e-9 for g in gains.values()),
                           sum(g > 1e-9 for g in gains.values())])
            labels.append(f"{LABELS[algo]}, {suffix}")
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ys = [0, 1, 2.4, 3.4, 4.8, 5.8]
    start = [0] * len(ys)
    for k, (name, color) in enumerate([("Dégradée", ORANGE), ("Inchangée", GREY), ("Améliorée", BLUE)]):
        values = [c[k] for c in counts]
        ax.barh(ys, values, left=start, height=0.75, color=color, label=name, edgecolor="white", linewidth=1.5)
        for y, x0, v in zip(ys, start, values):
            if v:
                ax.text(x0 + v / 2, y, str(v), ha="center", va="center", fontsize=9, color="white" if k != 1 else INK)
        start = [x0 + v for x0, v in zip(start, values)]
    ax.set_yticks(ys, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Nombre d'instances (sur 33)")
    ax.set_title("Recherche locale avant et après correction : solution de départ dégradée ou améliorée ?", pad=24)
    ax.grid(axis="y", visible=False)
    ax.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)
    save(fig, "recherche_locale_avant_apres")


def plot_seeds(runs, nb=10):
    """Tabou aléatoire : dispersion du gain selon la graine, sur les instances non jouets où il varie le plus."""
    gains = {}
    for instance, algos in runs.items():
        rows = [r for r in algos["TS"] if r["status"] in ("ok", "timeout") and number(r["start_score"])]
        if len(rows) > 1 and instance not in TOY:
            gains[instance] = [(number(r["score"]) - number(r["start_score"])) / number(r["start_score"]) * 100 for r in rows]
    instances = sorted(gains, key=lambda i: max(gains[i]) - min(gains[i]), reverse=True)[:nb]
    instances = [i for i in instances if max(gains[i]) > min(gains[i])]
    if not instances:
        return
    fig, ax = plt.subplots(figsize=(9, 0.36 * len(instances) + 1.3))
    for y, instance in enumerate(instances):
        values = gains[instance]
        ax.plot([min(values), max(values)], [y, y], color=GREY, linewidth=2, zorder=2, solid_capstyle="round")
        # léger décalage vertical par graine, pour distinguer les graines qui donnent le même résultat
        ax.scatter(values, [y + (k - (len(values) - 1) / 2) * 0.05 for k in range(len(values))], s=26, color=AQUA,
                   edgecolor="white", linewidth=0.6, zorder=3, label="seed" if y == 0 else None)
        ax.scatter([mean(values)], [y], marker="|", s=260, color=INK, linewidth=1.8, zorder=4, label="Moyenne" if y == 0 else None)
    ax.set_yticks(range(len(instances)), [short(i) for i in instances], fontsize=8)
    ax.set_ylim(len(instances) - 0.4, -0.6)
    ax.set_xlabel("Gain sur le glouton de départ (%)")
    nb_seeds = max(len(v) for v in gains.values())
    ax.set_title(f"Tabou aléatoire selon la seed ({nb_seeds} seeds/instance)", pad=24)
    ax.grid(axis="y", visible=False)
    ax.legend(ncols=2, loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2, fontsize=8)
    save(fig, "tabou_graines")


def plot_neighbourhood(grid, field="score", directory=None,
                       title="Tabu search : effet de la taille du voisinage (caches = vidéos) et du nombre d'itérations"):
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
                gain = (number(r[field]) - number(r["start_score"])) / number(r["start_score"]) * 100
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
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    save(fig, "voisinage", directory)


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
    # dense et dense2 sont au même endroit : une seule étiquette pour les deux
    same = [p[2] for p in points if p[:2] == next((q[:2] for q in points if q[2] == "dense"), None)]
    if same:
        x, y = next(p[:2] for p in points if p[2] == "dense")
        ax.annotate(", ".join(sorted(same)), (x, y), xytext=(0, -12), textcoords="offset points", ha="center", fontsize=7, color=INK2)
    ax.axhline(0, color=INK2, linewidth=0.8)
    # échelle linéaire jusqu'à 10 %, logarithmique au-delà : quelques gains dépassent 100 %
    ax.set_yscale("symlog", linthresh=10)
    ax.set_yticks([0, 5, 10, 100, 1000], ["0", "5", "10", "100", "1000"])
    ax.set_ylim(bottom=-2)
    ax.set_xlabel("Nombre moyen de caches par endpoint")
    ax.set_ylabel("Gain de score de la mise à jour (%)")
    ax.set_title("La mise à jour entre caches rapporte-t-elle plus quand les caches se recouvrent ?")
    save(fig, "knapsack_maj")


def plot_knapsack_gcd(features):
    """Division par le pgcd : sur combien de caches change-t-elle quelque chose ?"""
    rows = []
    for instance, f in features.items():
        if instance in TOY or f.get("ks_gcd_value_caches") in ("", None):
            continue
        nb_caches, reduced, changed = int(f["C"]), int(f["ks_gcd_value_caches"]), int(f["ks_gcd_branch_changes"])
        rows.append((instance, [changed, reduced - changed, nb_caches - reduced], nb_caches))
    if not rows:
        return
    rows.sort(key=lambda row: ((row[1][0] + row[1][1]) / row[2], row[1][0]))

    fig, ax = plt.subplots(figsize=(10, 0.19 * len(rows) + 1.4))
    names = ["pgcd des valeurs > 1 et la résolution change", "pgcd des valeurs > 1, même résolution",
             "pgcd des valeurs = 1 (rien à diviser)"]
    left = [0] * len(rows)
    for k, color in enumerate([ORANGE, BLUE, GREY]):
        shares = [row[1][k] / row[2] * 100 for row in rows]
        ax.barh(range(len(rows)), shares, left=left, height=0.7, color=color, label=names[k], edgecolor="white", linewidth=1)
        left = [l + s for l, s in zip(left, shares)]
    for y, row in enumerate(rows):
        if row[1][0]:
            ax.text(101, y, f"{row[1][0]} cache{'s' if row[1][0] > 1 else ''} sur {row[2]}", va="center", fontsize=7, color=ORANGE)
    ax.set_yticks(range(len(rows)), [f"{short(row[0])}  ({row[2]} caches)" for row in rows], fontsize=7)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Part des caches (%)")
    weights = sum(int(f["ks_gcd_weight"]) > 1 for i, f in features.items() if i not in TOY)
    ax.set_title("Division par le pgcd : sur combien de caches change-t-elle quelque chose ?\n"
                 f"pgcd des poids > 1 sur {weights} instance sur {len(rows)}")
    ax.grid(axis="y", visible=False)
    ax.legend(ncols=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    save(fig, "knapsack_pgcd")


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
    plot_before_after(runs, load_runs(BEFORE_CSV))
    plot_seeds(runs)
    plot_neighbourhood(grid)
    plot_knapsack_branches(runs, features)
    plot_knapsack_update(runs, features)
    plot_knapsack_gcd(features)
    plot_time_gap(runs, ref)
    plot_capacity(runs, ref, features)


if __name__ == "__main__":
    main()
