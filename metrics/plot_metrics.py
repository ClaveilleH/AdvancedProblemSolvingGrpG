"""Statistiques de sortie"""

from statistics import mean

from metrics.mesure_metrics import Problem


class OutputStats:
    """Calcule les statistiques d'une solution (placement) pour un problème donné.

    placement : {id_cache: set(id_videos)}, tel que renvoyé par read_output().
    Tous les calculs sont faits une seule fois à la construction.
    """

    def __init__(self, problem: Problem, placement: dict):
        self.problem = problem
        self.placement = placement
        self._compute()

    # ------------------------------------------------------------------ calcul
    def _compute(self) -> None:
        p = self.problem
        sizes = p.video_sizes

        # --- Passe sur les requêtes : gains, borne sup., requêtes par cache
        self.total_requests = sum(n for _, _, n in p.requests)
        total_gain = 0            # gain réel (ms x requêtes)
        upper_gain = 0            # gain max théorique (ms x requêtes)
        self.requests_per_cache = {c: 0 for c in range(p.n_caches)}
        self.requests_from_cache = 0
        self.requests_from_dc = 0

        for video, ep_id, n in p.requests:
            ep = p.endpoints[ep_id]

            # Borne supérieure : meilleur cache connecté, capacité ignorée
            if ep.caches:
                best_possible = min(ep.caches.values())
                upper_gain += n * max(0, ep.dc_latency - best_possible)

            # Gain réel : meilleur cache connecté contenant la vidéo
            best_lat, best_cache = ep.dc_latency, None
            for c, lat in ep.caches.items():
                if lat < best_lat and video in self.placement.get(c, ()):
                    best_lat, best_cache = lat, c

            if best_cache is None:
                self.requests_from_dc += n
            else:
                self.requests_from_cache += n
                self.requests_per_cache[best_cache] += n
                total_gain += n * (ep.dc_latency - best_lat)

        tr = self.total_requests or 1  # évite la division par zéro
        self.score = (1000 * total_gain) // tr
        self.upper_bound = (1000 * upper_gain) // tr
        self.avg_gain_ms = total_gain / tr
        self.avg_gain_ms_served = (
            total_gain / self.requests_from_cache if self.requests_from_cache else 0.0)

        # --- Remplissage des caches
        self.used_size_per_cache = {
            c: sum(sizes[v] for v in self.placement.get(c, ()))
            for c in range(p.n_caches)
        }
        self.fill_rate_per_cache = {
            c: s / p.cache_capacity for c, s in self.used_size_per_cache.items()
        }
        self.unused_caches = [
            c for c in range(p.n_caches) if not self.placement.get(c)
        ]
        self.total_used_size = sum(self.used_size_per_cache.values())

        # --- Duplication
        total_copies = sum(len(v) for v in self.placement.values())
        distinct = len(set().union(*self.placement.values())) if self.placement else 0
        self.total_copies = total_copies
        self.distinct_videos = distinct
        self.duplication_rate = 1 - distinct / total_copies if total_copies else 0.0
        self.avg_copies_per_video = total_copies / distinct if distinct else 0.0

    # ------------------------------------------------------- statistiques dérivées
    @property
    def score_ratio(self) -> float:
        """Score / borne supérieure (entre 0 et 1)."""
        return self.score / self.upper_bound if self.upper_bound else 0.0

    @property
    def avg_requests_per_cache(self) -> float:
        """Moyenne sur tous les caches (utilisés ou non)."""
        return mean(self.requests_per_cache.values()) if self.requests_per_cache else 0.0

    @property
    def avg_requests_per_used_cache(self) -> float:
        """Moyenne sur les caches utilisés uniquement."""
        used = [n for c, n in self.requests_per_cache.items()
                if c not in set(self.unused_caches)]
        return mean(used) if used else 0.0

    @property
    def avg_fill_rate(self) -> float:
        rates = self.fill_rate_per_cache.values()
        return mean(rates) if rates else 0.0

    @property
    def cache_request_share(self) -> float:
        """Part des requêtes servies par un cache."""
        return self.requests_from_cache / self.total_requests if self.total_requests else 0.0

    @property
    def dc_request_share(self) -> float:
        return 1 - self.cache_request_share if self.total_requests else 0.0

    # ------------------------------------------------------------------ sortie
    def to_dict(self) -> dict:
        """Toutes les statistiques dans un dictionnaire (utile pour CSV/JSON)."""
        return {
            "score": self.score,
            "upper_bound": self.upper_bound,
            "score_ratio": self.score_ratio,
            "avg_requests_per_cache": self.avg_requests_per_cache,
            "avg_requests_per_used_cache": self.avg_requests_per_used_cache,
            "fill_rate_per_cache": self.fill_rate_per_cache,
            "avg_fill_rate": self.avg_fill_rate,
            "unused_caches": self.unused_caches,
            "n_unused_caches": len(self.unused_caches),
            "total_used_size": self.total_used_size,
            "total_capacity": self.problem.n_caches * self.problem.cache_capacity,
            "requests_from_cache": self.requests_from_cache,
            "requests_from_dc": self.requests_from_dc,
            "cache_request_share": self.cache_request_share,
            "dc_request_share": self.dc_request_share,
            "duplication_rate": self.duplication_rate,
            "avg_copies_per_video": self.avg_copies_per_video,
            "distinct_videos_placed": self.distinct_videos,
            "avg_gain_ms": self.avg_gain_ms,
            "avg_gain_ms_per_served_request": self.avg_gain_ms_served,
        }

    def report(self) -> str:
        """Résumé lisible (le détail par cache est volontairement omis)."""
        p = self.problem
        capacity = p.n_caches * p.cache_capacity
        lines = [
            f"Score                         : {self.score:,}",
            f"Borne supérieure théorique    : {self.upper_bound:,}"
            f"  ({self.score_ratio:.1%} atteint)",
            f"Gain moyen / requête          : {self.avg_gain_ms:.2f} ms"
            f"  ({self.avg_gain_ms_served:.2f} ms par requête servie par un cache)",
            f"Requêtes servies par cache    : {self.requests_from_cache:,}"
            f"  ({self.cache_request_share:.1%})",
            f"Requêtes servies par datacenter: {self.requests_from_dc:,}"
            f"  ({self.dc_request_share:.1%})",
            f"Requêtes moyennes / cache     : {self.avg_requests_per_cache:,.1f}"
            f"  ({self.avg_requests_per_used_cache:,.1f} sur les caches utilisés)",
            f"Remplissage moyen des caches  : {self.avg_fill_rate:.1%}",
            f"Caches inutilisés             : {len(self.unused_caches)} / {p.n_caches}",
            f"Taille totale utilisée        : {self.total_used_size:,} Mo / {capacity:,} Mo",
            f"Taux de duplication           : {self.duplication_rate:.1%}"
            f"  ({self.avg_copies_per_video:.2f} copies par vidéo placée)",
        ]
        return "\n".join(lines)
