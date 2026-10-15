"""Piste PGCD : multiplie la capacité X et TOUTES les tailles de vidéos par un même facteur g.

Usage : python generator/scale_pgcd.py entree.in sortie.in --g 1000000

L'instance obtenue est équivalente (mêmes solutions valides, mêmes scores) : seule l'unité de taille
change. Un algo qui divise par le PGCD des tailles (le knapsack de MOI) retrouve sa petite table de
programmation dynamique ; un algo qui fait une DP indexée sur la capacité brute doit remplir une table
g fois plus grande. Les gloutons ne voient aucune différence.
Vérifie que X * g et chaque taille restent <= 2^31 - 1 (lecture en int32 par AUTRE_3 et les juges).
"""
import argparse

INT_MAX = 2**31 - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--g", type=int, default=1_000_000)
    a = ap.parse_args()
    with open(a.src) as f:
        lines = f.read().split("\n")
    head = lines[0].split()
    head[4] = str(int(head[4]) * a.g)
    sizes = [int(x) * a.g for x in lines[1].split()]
    assert int(head[4]) <= INT_MAX and max(sizes) <= INT_MAX, "facteur trop grand pour rester en 32 bits"
    lines[0] = " ".join(head)
    lines[1] = " ".join(map(str, sizes))
    with open(a.dst, "w", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
