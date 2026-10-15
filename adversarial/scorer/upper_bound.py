"""Borne supérieure simple du score : chaque requête servie par le cache le plus
rapide de son endpoint, en ignorant les capacités.

Usage : python scorer/upper_bound.py instance.in
"""
import sys

from score import read_instance


def upper_bound(inst):
    saved = total = 0
    for v, e, n in inst["reqs"]:
        lat = [lc for c, lc in inst["links"][e].items() if inst["sizes"][v] <= inst["X"]]
        best = min([inst["ld"][e]] + lat)
        saved += n * (inst["ld"][e] - best)
        total += n
    return saved * 1000 // total if total else 0


if __name__ == "__main__":
    print(upper_bound(read_instance(sys.argv[1])))
