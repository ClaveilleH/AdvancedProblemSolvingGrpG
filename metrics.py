#!/usr/bin/env python3
"""
Analyseur de métriques pour les instances du problème Hash Code 2017
(Streaming Videos to Cache Servers).

Usage:
    python hashcode_metrics.py [fichier.in]

Si aucun fichier n'est précisé, le script cherche automatiquement
un fichier d'entrée dans le dossier courant (voir AUTO_DETECT_PATTERNS).

Format d'entrée attendu :
    V E R C X
    <V tailles de vidéos>
    E blocs :
        Dl K
        K lignes : Lc Yc
    R lignes : Rv Re Rn
"""

import sys
import os
import glob
import statistics
from collections import defaultdict

# ============================================================
# CONFIGURATION — à modifier selon les besoins
# ============================================================

# --- Activation/désactivation des blocs de métriques ---
ENABLE_STRUCTURE         = True   # V, E, R, C, X, ratios globaux
ENABLE_VIDEOS            = True   # distribution des tailles de vidéos
ENABLE_ENDPOINTS         = True   # connectivité endpoints/caches, latences
ENABLE_REQUESTS          = True   # distribution des requêtes
ENABLE_CACHE_GRAPH       = True   # degré des caches, densité du graphe
ENABLE_THEORETICAL_BOUND = True   # bornes de score théoriques (upper bound)

# --- Paramétrage des "top/bottom N" ---
# Évite d'inonder le terminal sur les gros jeux de données : on
# n'affiche jamais une liste brute complète, seulement des extrêmes.
SHOW_TOP_BOTTOM = True   # active l'affichage des extrêmes
TOP_N    = 10            # nombre d'éléments les plus grands à afficher
BOTTOM_N = 10            # nombre d'éléments les plus petits à afficher

# --- Détection automatique du fichier d'entrée ---
# Motifs cherchés dans AUTO_DETECT_DIR, par ordre de priorité.
AUTO_DETECT_PATTERNS = ["*.in", "*.txt"]
AUTO_DETECT_DIR = "."

# --- Garde-fou pour les très gros jeux de données ---
# Au-delà de ce nombre de lignes de requêtes (R, pas la somme des Rn),
# les métriques les plus coûteuses (écart-type, médiane exacte) sont
# calculées sur un échantillon plutôt que sur la totalité.
LARGE_R_THRESHOLD = 2_000_000
SAMPLE_SIZE_FOR_LARGE_R = 200_000

# ============================================================


def find_input_file():
    for pattern in AUTO_DETECT_PATTERNS:
        matches = sorted(glob.glob(os.path.join(AUTO_DETECT_DIR, pattern)))
        if matches:
            if len(matches) > 1:
                print(
                    f"[info] Plusieurs fichiers trouvés pour '{pattern}', "
                    f"utilisation de : {matches[0]}",
                    file=sys.stderr,
                )
            return matches[0]
    return None


def parse_input(path):
    """Parse le fichier en un seul passage, structures légères (listes/tuples)."""
    with open(path, "r") as f:
        V, E, R, C, X = map(int, f.readline().split())

        sizes = list(map(int, f.readline().split()))

        endpoint_dc = [0] * E          # latence datacenter par endpoint
        endpoint_caches = [None] * E   # liste de (cache_id, latence) par endpoint

        for e in range(E):
            Dl, K = map(int, f.readline().split())
            endpoint_dc[e] = Dl
            caches = []
            for _ in range(K):
                Lc, Yc = map(int, f.readline().split())
                caches.append((Lc, Yc))
            endpoint_caches[e] = caches

        requests = []  # (video, endpoint, n)
        for _ in range(R):
            Rv, Re, Rn = map(int, f.readline().split())
            requests.append((Rv, Re, Rn))

    return {
        "V": V, "E": E, "R": R, "C": C, "X": X,
        "sizes": sizes,
        "endpoint_dc": endpoint_dc,
        "endpoint_caches": endpoint_caches,
        "requests": requests,
    }


# ------------------------------------------------------------
# Utilitaires d'affichage
# ------------------------------------------------------------

def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def dist_stats(values):
    """Retourne min/max/moyenne/médiane/écart-type, tolère les listes vides."""
    if not values:
        return None
    n = len(values)
    result = {
        "n": n,
        "min": min(values),
        "max": max(values),
        "moyenne": sum(values) / n,
        "mediane": statistics.median(values),
    }
    result["ecart_type"] = statistics.pstdev(values) if n > 1 else 0.0
    return result


def print_dist(label, values):
    d = dist_stats(values)
    if d is None:
        print(f"{label} : aucune donnée")
        return
    print(f"{label} : n={d['n']} min={d['min']} max={d['max']} "
          f"moyenne={d['moyenne']:.2f} mediane={d['mediane']:.2f} "
          f"ecart_type={d['ecart_type']:.2f}")


def print_top_bottom(label, items):
    """items : liste de (id, valeur), déjà triable."""
    if not SHOW_TOP_BOTTOM or not items:
        return
    items_sorted = sorted(items, key=lambda t: t[1], reverse=True)
    top = items_sorted[:TOP_N]
    bottom = items_sorted[-BOTTOM_N:] if BOTTOM_N else []
    print(f"  Top {len(top)} {label} :")
    for i, v in top:
        print(f"    id={i} valeur={v}")
    if bottom:
        print(f"  Bottom {len(bottom)} {label} :")
        for i, v in bottom:
            print(f"    id={i} valeur={v}")


# ------------------------------------------------------------
# Blocs de métriques
# ------------------------------------------------------------

def metrics_structure(data):
    section("1. Structure générale")
    V, E, R, C, X = data["V"], data["E"], data["R"], data["C"], data["X"]
    print(f"V (vidéos)        = {V}")
    print(f"E (endpoints)     = {E}")
    print(f"R (lignes requête)= {R}")
    print(f"C (caches)        = {C}")
    print(f"X (capacité cache)= {X}")

    total_video_size = sum(data["sizes"])
    total_cache_capacity = C * X
    print(f"Volume total des vidéos      = {total_video_size}")
    print(f"Capacité totale des caches   = {total_cache_capacity}")
    if total_video_size > 0:
        ratio = total_cache_capacity / total_video_size
        print(f"Ratio capacité/volume total  = {ratio:.3f} "
              f"(1.0 = on pourrait tout cacher sans contrainte de placement)")

    distinct_videos = len({r[0] for r in data["requests"]})
    print(f"Vidéos distinctes réellement demandées = {distinct_videos} / {V}")


def metrics_videos(data):
    section("2. Tailles des vidéos")
    sizes = data["sizes"]
    print_dist("Tailles de vidéos", sizes)

    X = data["X"]
    fit_alone = sum(1 for s in sizes if s <= X)
    print(f"Vidéos tenant seules dans un cache (taille <= X={X}) : "
          f"{fit_alone} / {len(sizes)}")

    print_top_bottom("vidéos par taille", list(enumerate(sizes)))


def metrics_endpoints(data):
    section("3. Endpoints et connectivité")
    endpoint_dc = data["endpoint_dc"]
    endpoint_caches = data["endpoint_caches"]

    k_values = [len(c) for c in endpoint_caches]
    print_dist("Nombre de caches connectés par endpoint (K)", k_values)

    isolated = sum(1 for k in k_values if k == 0)
    print(f"Endpoints isolés (K=0, uniquement datacenter) : {isolated} / {len(k_values)}")

    print_dist("Latence datacenter (Dl)", endpoint_dc)

    all_yc = [yc for caches in endpoint_caches for (_, yc) in caches]
    print_dist("Latence cache (Yc), tous endpoints confondus", all_yc)

    gains = []
    for e, caches in enumerate(endpoint_caches):
        if caches:
            best_yc = min(yc for (_, yc) in caches)
            gains.append(endpoint_dc[e] - best_yc)
    print_dist("Gain de latence potentiel par endpoint (Dl - min(Yc))", gains)

    print_top_bottom("endpoints par K (nb caches connectés)", list(enumerate(k_values)))


def metrics_requests(data):
    section("4. Requêtes")
    requests = data["requests"]
    R = len(requests)

    if R > LARGE_R_THRESHOLD:
        print(f"[info] R={R} > seuil {LARGE_R_THRESHOLD} : "
              f"certaines stats sont calculées sur un échantillon de "
              f"{SAMPLE_SIZE_FOR_LARGE_R} lignes.")
        import random
        sample = random.sample(requests, SAMPLE_SIZE_FOR_LARGE_R)
    else:
        sample = requests

    rn_values = [r[2] for r in sample]
    print_dist("Nombre de requêtes par ligne (Rn)", rn_values)

    total_rn = sum(r[2] for r in requests)
    print(f"Somme totale des requêtes (poids total) = {total_rn}")

    # Poids par vidéo (sur l'échantillon si trop gros)
    weight_per_video = defaultdict(int)
    for v, e, n in sample:
        weight_per_video[v] += n
    print_top_bottom(
        "vidéos par poids de requêtes (échantillon)" if R > LARGE_R_THRESHOLD
        else "vidéos par poids de requêtes",
        list(weight_per_video.items()),
    )

    weight_per_endpoint = defaultdict(int)
    for v, e, n in sample:
        weight_per_endpoint[e] += n
    print_top_bottom(
        "endpoints par poids de requêtes (échantillon)" if R > LARGE_R_THRESHOLD
        else "endpoints par poids de requêtes",
        list(weight_per_endpoint.items()),
    )


def metrics_cache_graph(data):
    section("5. Graphe cache <-> endpoint")
    endpoint_caches = data["endpoint_caches"]
    C = data["C"]

    cache_degree = defaultdict(int)
    total_edges = 0
    for caches in endpoint_caches:
        for (cache_id, _) in caches:
            cache_degree[cache_id] += 1
            total_edges += 1

    degrees = [cache_degree.get(c, 0) for c in range(C)]
    print_dist("Degré des caches (nb endpoints les voyant)", degrees)

    unused = sum(1 for d in degrees if d == 0)
    print(f"Caches jamais référencés par un endpoint : {unused} / {C}")

    E = data["E"]
    max_possible_edges = C * E
    density = total_edges / max_possible_edges if max_possible_edges else 0
    print(f"Arêtes du graphe bipartite endpoint-cache = {total_edges}")
    print(f"Densité du graphe = {density:.6f}")

    print_top_bottom("caches par degré", list(enumerate(degrees)))


def metrics_theoretical_bound(data):
    section("6. Bornes de score théoriques")
    endpoint_dc = data["endpoint_dc"]
    endpoint_caches = data["endpoint_caches"]
    requests = data["requests"]

    # Meilleure latence atteignable par endpoint si le cache optimal
    # pour cet endpoint contenait la vidéo demandée (borne haute,
    # ignore toute contrainte de capacité/placement).
    best_yc_per_endpoint = [
        min((yc for (_, yc) in caches), default=None)
        for caches in endpoint_caches
    ]

    total_saved_upper = 0
    total_rn = 0
    for v, e, n in requests:
        total_rn += n
        best_yc = best_yc_per_endpoint[e]
        if best_yc is not None:
            gain = endpoint_dc[e] - best_yc
            if gain > 0:
                total_saved_upper += gain * n

    if total_rn > 0:
        avg_saved_upper = total_saved_upper / total_rn
        score_upper = int(avg_saved_upper * 1000)
    else:
        avg_saved_upper = 0
        score_upper = 0

    print(f"Score si rien n'est caché (baseline)            = 0")
    print(f"Gain moyen de latence max théorique par requête = {avg_saved_upper:.4f}")
    print(f"Score upper bound (formule Hash Code, ×1000)    = {score_upper}")
    print("  (borne haute optimiste : ignore la capacité des caches et "
          "le fait qu'une vidéo ne peut être placée que sur un sous-ensemble "
          "de caches à la fois)")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = find_input_file()
        if path is None:
            print(
                "Aucun fichier d'entrée trouvé automatiquement "
                f"(motifs cherchés : {AUTO_DETECT_PATTERNS} dans {AUTO_DETECT_DIR}).\n"
                "Précisez un chemin : python hashcode_metrics.py fichier.in",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[info] Fichier détecté automatiquement : {path}", file=sys.stderr)

    if not os.path.isfile(path):
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        sys.exit(1)

    data = parse_input(path)

    if ENABLE_STRUCTURE:
        metrics_structure(data)
    if ENABLE_VIDEOS:
        metrics_videos(data)
    if ENABLE_ENDPOINTS:
        metrics_endpoints(data)
    if ENABLE_REQUESTS:
        metrics_requests(data)
    if ENABLE_CACHE_GRAPH:
        metrics_cache_graph(data)
    if ENABLE_THEORETICAL_BOUND:
        metrics_theoretical_bound(data)

    print()


if __name__ == "__main__":
    main()