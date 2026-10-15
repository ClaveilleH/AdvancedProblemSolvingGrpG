"""Piège « densité + cache leurre » (famille T1).

Structure (2 caches, 2 ou 3 endpoints, 2 vidéos) :

    vidéo B : taille X (remplit exactement un cache), très rentable au total
    vidéo A : taille sA, petite, densité gain/taille légèrement > celle de B

    endpoint eB : LD_B, relié au cache 0 (latence LD_B - 1, gain 1 ms : leurre)
                         et au cache 1 (latence 1, gain LD_B - 1)
    endpoint eA : LD_A, relié au cache 1 seulement
    endpoint eF : sans cache, requêtes de remplissage (optionnel) qui
                  diluent le score moyen sans que personne ne puisse les servir

Ce que font les algos :
  - gloutons par densité (AUTRE_1 global, AUTRE_2 par cache) : A d'abord dans
    le cache 1, B n'y tient plus, B part dans le leurre (gain 1 ms).
  - AUTRE_3 (tri par valeur, caches dans l'ordre des index) : cache 0 traité
    en premier, B y est placé ; eB est alors marqué « servi » pour B et le
    cache 1 ignore B pour eB.
  - MOI : le glouton par nombre de requêtes place B (nB > nA) dans le cache
    le plus rapide de eB qui a la place, le cache 1.

Usage : python generator/trap_served.py out.in [--X ..] [--LDB ..] [--nB ..]
        [--sA ..] [--fill auto|0|N]
--fill auto : juste assez de requêtes de remplissage pour que le score des
autres soit arrondi à 0.
"""
import argparse


def build(X, LDB, nB, sA, nA, fill):
    gainB = nB * (LDB - 1)                       # valeur de B dans le cache 1
    # densité de A = nA*gA/sA doit dépasser gainB/X : plus petit gA entier qui convient
    gA = gainB * sA // (X * nA) + 1
    LDA = gA + 1                                 # latence cache 1 -> eA = 1
    a = nA * gA
    others_gain = a + nB                         # A dans le cache 1, B dans le leurre
    if fill == "auto":
        # floor(1000*others_gain/N) = 0  <=>  N > 1000*others_gain
        fill = max(0, 1000 * others_gain + 1 - nA - nB)
    fill = int(fill)
    E = 3 if fill else 2
    R = 3 if fill else 2
    lines = [f"2 {E} {R} 2 {X}", f"{X} {sA}",
             f"{LDB} 2", f"0 {LDB - 1}", "1 1",
             f"{LDA} 1", "1 1"]
    if fill:
        lines.append("1 0")
    lines += [f"0 0 {nB}", f"1 1 {nA}"]
    if fill:
        lines.append(f"0 2 {fill}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    INT_MAX = 2**31 - 1
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--X", type=int, default=INT_MAX)
    ap.add_argument("--LDB", type=int, default=INT_MAX)
    ap.add_argument("--nB", type=int, default=2)
    ap.add_argument("--nA", type=int, default=1)
    ap.add_argument("--sA", type=int, default=1)
    ap.add_argument("--fill", default="auto")
    a = ap.parse_args()
    assert a.nB > a.nA, "le glouton de MOI doit voir B avant A"
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.X, a.LDB, a.nB, a.sA, a.nA, a.fill))
