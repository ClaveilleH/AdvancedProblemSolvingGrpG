"""Piège d'affectation agrandi et bruité (famille PB), pensé contre les recherches locales.

P paires de caches. Pour la paire p :
  cache partagé  S_p (index p)      : relié à e0_p (latence 1..5) et e1_p (latence 1..5)
  cache secours  B_p (index P + p)  : relié à e0_p (latence L1, élevée) et à un endpoint parasite n_p
  e0_p : k_p vidéos de taille s_p, un peu PLUS rentables que celles de e1_p dans S_p
  e1_p : k_p autres vidéos de taille s_p ; S_p est son seul cache
  n_p  : quelques vidéos parasites peu rentables, qui remplissent B_p dans la solution piégée
X = k_p * s_p pour toutes les paires (S_p tient exactement un endpoint).

Solution piégée (gloutons, ordre des index, sac à dos exact cache par cache) : e0 dans S_p,
parasites dans B_p, e1 servi par le datacenter. Optimum : e1 dans S_p, e0 dans B_p.

Pour qu'une recherche locale passe de l'un à l'autre, chaque échange demande plusieurs mouvements
perdants (retirer un parasite, retirer une vidéo de e0 de S_p : perte n0 * (L1 - L0)) avant le gain,
et il faut le refaire pour toutes les vidéos de toutes les paires.

Ce qui permet à MOI de trouver l'optimum SANS recherche locale : son knapsack (knapsack_slay)
traite les caches par valeur totale décroissante. Un endpoint « fantôme » relié à tous les B_p
demande des vidéos fantômes trop grosses pour tenir dans un cache : elles gonflent la valeur totale
des B_p (qui passent donc avant les S_p), sans que personne ne puisse jamais les placer. Le knapsack
remplit B_p avec e0 en premier ; la valeur de e0 dans S_p chute, et S_p reçoit e1.

Toutes les valeurs restent dans les bornes de l'énoncé (LD <= 4000, Lc <= 500, Rn <= 10000,
tailles <= 1000) et en 32 bits. Seed fixée : même seed = même fichier.

Usage : python generator/trap_affectation_bruit.py out.in [--P 30] [--X 60] [--L1 150 300] [--seed 1]
"""
import argparse
import random


def build(P, X, L1min, L1max, seed, noise_per_cache=6):
    rng = random.Random(seed)
    divisors = [d for d in range(1, X + 1) if X % d == 0 and 3 <= X // d <= 12 and d <= 1000]
    sizes, reqs, eps = [], [], []
    C = 2 * P

    def vid(size):
        sizes.append(size)
        return len(sizes) - 1

    ghost_links = []
    shared_total_max = 0
    for p in range(P):
        s = rng.choice(divisors)
        k = X // s
        S, B = p, P + p
        L0a, L0b = rng.randint(1, 5), rng.randint(1, 5)
        L1 = rng.randint(L1min, L1max)
        LD0 = rng.randint(3850, 4000)
        LD1 = rng.randint(3700, 3800)
        e0 = len(eps); eps.append((LD0, [(S, L0a), (B, L1)]))
        e1 = len(eps); eps.append((LD1, [(S, L0b)]))
        LDn = rng.randint(800, 1200)
        en = len(eps); eps.append((LDn, [(B, rng.randint(300, 500))]))
        tot = 0
        for _ in range(k):
            n0 = rng.randint(9400, 10000)
            reqs.append((vid(s), e0, n0)); tot += n0 * (LD0 - L0a)
        for _ in range(k):
            n1 = rng.randint(8800, 9300)
            reqs.append((vid(s), e1, n1)); tot += n1 * (LD1 - L0b)
        for _ in range(noise_per_cache):
            # parasite : taille quelconque <= X, valeur <= 2000 * 900 = 1,8e6, bien moins qu'une vidéo de e0
            reqs.append((vid(rng.randint(1, X)), en, rng.randint(200, 2000)))
        shared_total_max = max(shared_total_max, tot)
        ghost_links.append((B, rng.randint(1, 500)))
    # endpoint fantôme : relié à tous les B_p ; vidéos fantômes de taille > X (jamais plaçables)
    LDg = 4000
    g = len(eps); eps.append((LDg, ghost_links))
    per_ghost = 10000 * (LDg - max(l for _, l in ghost_links))
    n_ghost = shared_total_max // per_ghost + 2
    for _ in range(n_ghost):
        reqs.append((vid(min(1000, X + 1 + rng.randint(0, 1000 - X - 1))), g, 10000))
    # ordre des requêtes mélangé (bruit), ordre des endpoints conservé
    rng.shuffle(reqs)
    lines = [f"{len(sizes)} {len(eps)} {len(reqs)} {C} {X}", " ".join(map(str, sizes))]
    for ld, links in eps:
        lines.append(f"{ld} {len(links)}")
        lines += [f"{c} {l}" for c, l in links]
    lines += [f"{v} {e} {n}" for v, e, n in reqs]
    return "\n".join(lines) + "\n"


def build_big(P, X, L1min, L1max, seed, n_e0=10, noise_per_cache=6, witness=0, ghosts=True, dense=False):
    """Variante « grosse vidéo » : dans chaque paire, e0 n'a qu'UNE vidéo, de taille X.

    Le côté e0 est porté par n_e0 endpoints (reliés à S_p et B_p) qui demandent tous cette vidéo.
    e1 a k petites vidéos qui remplissent S_p. La grosse vidéo vaut un peu plus que toutes les vidéos
    de e1 réunies dans S_p (piège pour gloutons, tri par valeur et sac à dos exact par cache).
    Pour passer à l'optimum, une recherche locale doit sortir la grosse vidéo de S_p : une seule étape
    qui coûte (L1 - L0) / (LD - L0), soit ~12 % de la valeur du cache, avant tout gain.
    """
    rng = random.Random(seed)
    divisors = [d for d in range(1, X + 1) if X % d == 0 and 4 <= X // d <= 12]
    sizes, reqs, eps = [], [], []
    C = 2 * P

    def vid(size):
        sizes.append(size)
        return len(sizes) - 1

    ghost_links = []
    shared_total_max = 0
    for p in range(P):
        s = rng.choice(divisors)
        k = X // s
        S, B = p, P + p
        L1 = rng.randint(L1min, L1max)
        LD1 = rng.randint(3700, 3800)
        L0b = rng.randint(1, 5)
        e1 = len(eps); eps.append((LD1, [(S, L0b)]))
        F = 0
        for _ in range(k):
            n1 = rng.randint(8800, 9300)
            reqs.append((vid(s), e1, n1)); F += n1 * (LD1 - L0b)
        big = vid(X)
        E = 0
        Eb = 0                       # valeur de la grosse vidéo si elle est dans B_p
        e0s = []
        for _ in range(n_e0):
            LD0 = rng.randint(3850, 4000)
            L0a = rng.randint(1, 5)
            e0 = len(eps); eps.append((LD0, [(S, L0a), (B, L1)])); e0s.append((e0, LD0, L0a))
        # requêtes de la grosse vidéo réparties sur les endpoints e0, de sorte que E > F de 3 à 8 %
        target = int(F * rng.uniform(1.03, 1.08))
        while E <= target:
            for e0, LD0, L0a in e0s:
                n0 = rng.randint(1000, 3000)
                reqs.append((big, e0, n0)); E += n0 * (LD0 - L0a); Eb += n0 * (LD0 - L1)
                if E > target:
                    break
        LDn = rng.randint(800, 1200)
        Ln = rng.randint(300, 500)
        en = len(eps); eps.append((LDn, [(B, Ln)]))
        if not dense:
            for _ in range(noise_per_cache):
                reqs.append((vid(rng.randint(1, X)), en, rng.randint(200, 2000)))
        else:
            # parasites DENSES : densité (valeur / taille) entre 1,15 et 1,6 fois celle de la grosse vidéo
            # dans B_p, tailles 1 ou 2. Un glouton qui remplit B_p par densité les prend d'abord, et la grosse
            # vidéo (taille X) ne tient plus. Leur valeur totale reste petite devant celle de la grosse
            # vidéo : un sac à dos EXACT préfère la grosse vidéo.
            d_big = Eb / X
            gn = LDn - Ln
            budget = int(0.45 * X)
            for _ in range(noise_per_cache):
                u = rng.uniform(1.15, 1.6)
                smax = max(1, min(budget, int(10000 * gn / (u * d_big))))
                if budget <= 0 or smax < 1:
                    break
                sz = rng.randint(1, min(2, smax))
                n = -(-int(u * d_big * sz) // gn)
                assert n <= 10000 and n * gn > d_big * sz
                reqs.append((vid(sz), en, n)); budget -= sz
        shared_total_max = max(shared_total_max, E + F)
        ghost_links.append((B, rng.randint(1, 500)))
        # endpoints « témoins » : reliés à B_p seulement, 1 requête pour la grosse vidéo. Ils ne changent
        # presque rien aux gains, mais B_p compte alors plus d'endpoints demandeurs de la grosse vidéo que
        # S_p : greedy2 de MOI (cache relié au plus grand nombre d'endpoints demandeurs) l'y range.
        for _ in range(witness):
            LDw = rng.randint(1000, 4000)
            w = len(eps); eps.append((LDw, [(B, rng.randint(1, LDw - 1))]))
            reqs.append((big, w, 1))
    if ghosts:
        LDg = 4000
        g = len(eps); eps.append((LDg, ghost_links))
        per_ghost = 10000 * (LDg - max(l for _, l in ghost_links))
        for _ in range(shared_total_max // per_ghost + 2):
            reqs.append((vid(min(1000, X + 1 + rng.randint(0, 1000 - X - 1))), g, 10000))
    rng.shuffle(reqs)
    lines = [f"{len(sizes)} {len(eps)} {len(reqs)} {C} {X}", " ".join(map(str, sizes))]
    for ld, links in eps:
        lines.append(f"{ld} {len(links)}")
        lines += [f"{c} {l}" for c, l in links]
    lines += [f"{v} {e} {n}" for v, e, n in reqs]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--P", type=int, default=30)
    ap.add_argument("--X", type=int, default=60)
    ap.add_argument("--L1", type=int, nargs=2, default=[150, 300])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--big", action="store_true", help="variante grosse vidéo (barrière plus haute)")
    ap.add_argument("--noise", type=int, default=6, help="vidéos parasites par cache de secours")
    ap.add_argument("--witness", type=int, default=0, help="endpoints témoins par paire (route greedy2)")
    ap.add_argument("--no-ghosts", action="store_true", help="sans vidéos fantômes (route knapsack)")
    ap.add_argument("--dense", action="store_true", help="parasites denses : il faut un sac à dos EXACT dans B_p")
    a = ap.parse_args()
    assert a.X < 1000, "il faut X < 1000 pour que les vidéos fantômes (taille <= 1000) ne tiennent pas"
    with open(a.out, "w", newline="\n") as f:
        if a.big:
            f.write(build_big(a.P, a.X, a.L1[0], a.L1[1], a.seed, noise_per_cache=a.noise,
                              witness=a.witness, ghosts=not a.no_ghosts, dense=a.dense))
        else:
            f.write(build(a.P, a.X, a.L1[0], a.L1[1], a.seed, noise_per_cache=a.noise))
