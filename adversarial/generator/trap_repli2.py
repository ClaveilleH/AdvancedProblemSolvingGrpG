"""Piège « tout le monde, moi compris », sans cache leurre (famille R2).

Différence avec R1 : AUTRE_3 n'est plus piégé par un cache leurre mais par un
DÉBORDEMENT de son accumulateur `long long`. AUTRE_3 ne fusionne pas les lignes
de requêtes identiques ; la valeur de B dans le cache est
    Σ_lignes (LD - Lc) * Rn = kB * (2³¹-2) * (2³¹-1) > 2⁶³ - 1  dès kB = 3 lignes,
elle devient négative et B est triée en dernier. Les autres valeurs restent
petites. Sans leurre, B n'apporte plus rien du tout aux algos piégés.

Un seul cache (index 0), capacité X = 2³¹-1 :
  vidéo 0 = B (taille X), vidéo 1 = J (taille 1), vidéos 2.. = A_i (taille 1)
  endpoint 0 (eB) : LD = 2³¹-1, cache 0 à latence 1 ; demande J (1 fois) puis B
                    (kB lignes de 2³¹-1 requêtes)
  endpoint 1 (eA) : LD = 2, cache 0 à latence 1 ; demande A_1 (kA lignes de
                    2³¹-1 requêtes : après fusion, plus demandée que B) et
                    A_2..A_m (1 requête chacune, valeur négligeable)

Usage : python generator/trap_repli2.py out.in [--m 4] [--kB 3] [--kA 4] [--small 1]
"""
import argparse

INT_MAX = 2**31 - 1


def autre3_value_of_B(kB):
    """Valeur de B calculée par AUTRE_3 : somme en long long (64 bits signés, modulo 2^64)."""
    v = (kB * (INT_MAX - 1) * INT_MAX) % 2**64
    return v - 2**64 if v >= 2**63 else v


def build(m, kB, kA, small):
    X = INT_MAX
    V = m + 2
    sizes = [X, 1] + [1] * m
    assert autre3_value_of_B(kB) < 0, "kB doit faire déborder la somme vers un négatif (kB ≡ 3 mod 4)"
    reqs = ["1 0 1"] + [f"0 0 {INT_MAX}"] * kB
    if kA == 0:
        # A_1 : kB lignes pleines + 1 requête, juste plus demandée que B après fusion,
        # et valeur kB*(2³¹-1)+1 juste au-dessus de valeur(B)/X = kB*(2³¹-2)
        reqs += [f"2 1 {INT_MAX}"] * kB + ["2 1 1"]
    else:
        reqs += [f"2 1 {INT_MAX}"] * kA
    reqs += [f"{2 + i} 1 {small}" for i in range(1, m)]
    lines = [f"{V} 2 {len(reqs)} 1 {X}", " ".join(map(str, sizes)),
             f"{INT_MAX} 1", "0 1",
             "2 1", "0 1"] + reqs
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--kB", type=int, default=3)
    ap.add_argument("--kA", type=int, default=4)
    ap.add_argument("--small", type=int, default=1)
    a = ap.parse_args()
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.m, a.kB, a.kA, a.small))
