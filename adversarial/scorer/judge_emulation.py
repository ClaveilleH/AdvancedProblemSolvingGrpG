"""Émulation, au bit près, des deux juges C++ du dépôt MOI (judge/), qui plantent sous Windows.

Usage : python scorer/judge_emulation.py instance.in sortie.out

- judgeHashCode2017.cpp (juge d'origine) : `int totalRequest` ; chaque terme
  `requests[i].nb*(dataLatency - minLatency)` est un produit int*int (32 bits signés, débordement
  modulo 2^32) ajouté à un `long long score` ; affiche score*1000/totalRequest (long long / int).
- jugeCorrige.cpp : même chose, mais terme et totalRequest en long long (64 bits).
La division C++ tronque vers 0 (pas vers -∞).

Le calcul exact (entiers Python, sans débordement) est donné à côté pour comparaison.
Hypothèse : la sortie a déjà été validée (scorer/score.py) ; on ne réémule pas la validation.
"""
import sys

from score import read_instance, read_solution


def wrap(x, bits):
    x %= 1 << bits
    return x - (1 << bits) if x >= 1 << (bits - 1) else x


def cdiv(a, b):
    """Division entière C/C++ (troncature vers 0)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def judges(inst, caches):
    s32 = s64 = exact = 0
    tot32 = tot64 = tot = 0
    over32 = False
    for v, e, n in inst["reqs"]:
        ld = inst["ld"][e]
        best = ld
        for c, lc in inst["links"][e].items():
            if lc < best and v in caches.get(c, ()):
                best = lc
        term = n * (ld - best)
        exact += term
        tot += n
        over32 |= not -2**31 <= term < 2**31
        s32 = wrap(s32 + wrap(term, 32), 64)      # int*int puis ajout au long long
        tot32 = wrap(tot32 + n, 32)
        s64 = wrap(s64 + term, 64)
        tot64 = wrap(tot64 + n, 64)
    res = {"exact": exact * 1000 // tot if tot else 0}
    res["judgeHashCode2017 (int32)"] = cdiv(wrap(s32 * 1000, 64), tot32) if tot32 else "division par 0"
    res["jugeCorrige (int64)"] = cdiv(wrap(s64 * 1000, 64), tot64) if tot64 else "division par 0"
    res["débordement int32 ?"] = over32 or not tot < 2**31
    res["débordement int64 ?"] = not exact * 1000 < 2**63
    return res


if __name__ == "__main__":
    inst = read_instance(sys.argv[1])
    caches, err = read_solution(sys.argv[2], inst)
    if err:
        print("INVALIDE :", err)
    else:
        for k, v in judges(inst, caches).items():
            print(f"{k:28s} {v}")
