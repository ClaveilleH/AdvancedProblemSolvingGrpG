"""Piège ciblé AUTRE_1 : déclencher son « fast-fill » et sa limite de 70 endpoints par cache.

AUTRE_1 bascule vers `_solve_large` si C > 20 et si la somme, sur les LIGNES de
requêtes (doublons compris), du nombre de caches de l'endpoint dépasse 8·10⁶.
Le fast-fill ne garde alors, pour chaque cache, que les 70 endpoints qui ont le
plus de requêtes (volume), sans regarder le gain de latence.

Construction (fichier de ~110 Ko) :
  - C = 1000 caches de capacité X = taille d'une vidéo (une vidéo par cache) ;
  - endpoint 0 relié aux 1000 caches, 8001 lignes de requêtes identiques
    (vidéo 0, 1 requête chacune) : Σ K = 8 001 000 > 8·10⁶, le fast-fill est activé ;
  - 70 endpoints « lourds » reliés au cache 0, gain 1 ms, beaucoup de requêtes
    pour la vidéo H ;
  - 1 endpoint « léger » relié au cache 0, gain énorme, peu de requêtes pour
    la vidéo B. Il est 71e en volume : le fast-fill ne le voit jamais.

Usage : python generator/trap_fastfill.py out.in
"""
import sys

INT_MAX = 2**31 - 1


def build():
    C, X = 1000, 1
    V = 3                              # 0 = vidéo de déclenchement, 1 = H, 2 = B
    heavy = 70
    E = 1 + heavy + 1
    lines_req = []
    eps = [f"2 {C}"] + [f"{c} 1" for c in range(C)]                 # endpoint 0
    for _ in range(heavy):                                          # endpoints 1..70
        eps += ["2 1", "0 1"]
    eps += [f"{INT_MAX} 1", "0 1"]                                  # endpoint 71 (léger)
    lines_req += ["0 0 1"] * 8001
    lines_req += [f"1 {1 + i} 1000" for i in range(heavy)]
    lines_req += [f"2 {E - 1} 10"]
    head = [f"{V} {E} {len(lines_req)} {C} {X}", " ".join(["1"] * V)]
    return "\n".join(head + eps + lines_req) + "\n"


if __name__ == "__main__":
    with open(sys.argv[1], "w", newline="\n") as f:
        f.write(build())
