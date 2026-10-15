"""Piège « tout le monde, moi compris » (famille R1), pour l'objectif de repli.

Même idée que T1 (B remplit un cache, de petites vidéos plus denses le bloquent,
un cache leurre attire B), avec trois ajouts pour piéger aussi MOI :

  - m vidéos A_i (taille 1) demandées PLUS souvent que B (nA > nB) :
    le glouton `greedy` de MOI (tri par nombre de requêtes) les place
    avant B, et `greedy2` (tri par popularité) aussi ;
  - une vidéo J (taille 1) demandée une fois par eB, listée avant B :
    `greedy3` ne pose qu'une vidéo par endpoint et par cache, il pose J ;
  - tailles premières entre elles (1 et X) et valeurs énormes : les deux
    tables de DP de `knapsack_slay` dépassent LIMIT, il se rabat sur le
    glouton par densité ;
  - m > 7 petites vidéos : la recherche tabou (liste de 7 mouvements) ne peut
    pas vider le cache pour faire entrer B.

Usage : python generator/trap_repli.py out.in [--m 20] [--nB 1000000]
"""
import argparse

INT_MAX = 2**31 - 1


def build(m, nB, X=INT_MAX, LDB=INT_MAX):
    nA = nB + 1                  # A_i plus demandées que B
    gA = 1                       # densité de A_i = nA > densité de B ~ nB
    LDA = gA + 1
    V = m + 2                    # vidéos 0 = B, 1 = J, 2.. = A_i
    sizes = [X, 1] + [1] * m
    lines = [f"{V} 2 {m + 2} 2 {X}", " ".join(map(str, sizes)),
             f"{LDB} 2", f"0 {LDB - 1}", "1 1",
             f"{LDA} 1", "1 1",
             "1 0 1",            # J d'abord (ordre vu par greedy3)
             f"0 0 {nB}"]
    lines += [f"{2 + i} 1 {nA}" for i in range(m)]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--m", type=int, default=20)
    ap.add_argument("--nB", type=int, default=1_000_000)
    ap.add_argument("--LDB", type=int, default=INT_MAX, help="latence datacenter de eB (gain de B = LDB - 1)")
    a = ap.parse_args()
    with open(a.out, "w", newline="\n") as f:
        f.write(build(a.m, a.nB, LDB=a.LDB))
