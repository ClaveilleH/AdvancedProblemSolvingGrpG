"""Instance principale, famille T2 : densité + débordement d'AUTRE_3, sans leurre.

Un seul cache de capacité X = 2³¹-1.
  vidéo 0 = A (taille 1), vidéo 1 = B (taille X)
  eB : LD = 2³¹-1, cache 0 à latence 1 ; kB lignes « B, eB, 2³¹-1 »
       -> chez AUTRE_3 (lignes non fusionnées, accumulateur long long), la valeur
          de B déborde dès kB = 3 et devient négative : B passe en dernier ;
       -> chez MOI (requêtes fusionnées), B est la requête la plus demandée :
          `greedy` la place d'abord, dans le seul cache.
  eA : LD = 2³¹-1, cache 0 à latence 1, 3 requêtes pour A
  eA2: LD = 2, cache 0 à latence 1, 1 requête pour A
       -> valeur de A = 3(2³¹-2) + 1 = (valeur de B)/X + 1 : densité de A
          juste au-dessus de celle de B, donc les gloutons par densité
          (AUTRE_1, AUTRE_2) prennent A et B ne tient plus.
  eF : sans cache, requêtes de remplissage (lignes de 2³¹-1 au plus) pour que
       le gain des autres (valeur de A) × 1000 soit < nombre total de requêtes.

Score de MOI ≈ 1000 × valeur(B) / N ≈ X ≈ 2,1e9 ; score des autres = 0.

Usage : python generator/trap_overflow_main.py out.in [--kB 3] [--fill auto|0]
"""
import argparse

INT_MAX = 2**31 - 1


def build(kB, fill):
    X = INT_MAX
    gB = INT_MAX - 1
    VB = kB * INT_MAX * gB
    a_target = VB // X + 1                      # plus petite valeur entière de A de densité > B
    gA = INT_MAX - 1
    nA, rest = divmod(a_target, gA)             # nA requêtes à gain gA, + reste via eA2
    reqs = [f"1 0 {INT_MAX}"] * kB + [f"0 1 {nA}"]
    eps = [f"{INT_MAX} 1", "0 1", f"{INT_MAX} 1", "0 1"]
    E = 2
    if rest:
        eps += [f"{rest + 1} 1", "0 1"]         # gain = rest, 1 requête
        reqs.append(f"0 {E} 1")
        E += 1
    a = nA * gA + rest
    if fill == "auto":
        n_now = kB * INT_MAX + nA + (1 if rest else 0)
        need = max(0, 1000 * a + 1 - n_now)     # floor(1000*a/N) = 0  <=>  N > 1000*a
        eps += ["2 0"]
        lines = []
        while need > 0:
            k = min(need, INT_MAX)
            lines.append(f"0 {E} {k}")
            need -= k
        reqs += lines
        E += 1
    head = [f"2 {E} {len(reqs)} 1 {X}", f"1 {X}"]
    return "\n".join(head + eps + reqs) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--kB", type=int, default=3)
    ap.add_argument("--fill", default="auto")
    a = ap.parse_args()
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.kB, a.fill))
