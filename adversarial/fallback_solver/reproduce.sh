#!/usr/bin/env bash
# Preuve de reproductibilité : deux exécutions, sorties comparées octet par octet, puis score.
# Usage : fallback_solver/reproduce.sh [instance]   (défaut : best/instance_repli.in)
cd "$(dirname "$0")/.." || exit 1
INST=${1:-best/instance_repli.in}
OUT=${2:-best/repli_sorties}
mkdir -p "$OUT"
python fallback_solver/solver.py "$INST" "$OUT/solver_run1.out"
python fallback_solver/solver.py "$INST" "$OUT/solver_run2.out"
if cmp -s "$OUT/solver_run1.out" "$OUT/solver_run2.out"; then echo "sorties identiques"; else echo "SORTIES DIFFÉRENTES"; exit 1; fi
echo "score exécution 1 : $(python scorer/score.py "$INST" "$OUT/solver_run1.out")"
echo "score exécution 2 : $(python scorer/score.py "$INST" "$OUT/solver_run2.out")"
echo "borne supérieure (sans capacités) : $(python scorer/upper_bound.py "$INST")"
sha256sum "$OUT/solver_run1.out" "$OUT/solver_run2.out"
