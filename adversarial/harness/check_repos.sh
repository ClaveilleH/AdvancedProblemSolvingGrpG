#!/usr/bin/env bash
# Vérifie qu'aucun clone de repos/ n'a été modifié.
cd "$(dirname "$0")/.." || exit 1
for d in repos/*; do
  s=$(git -C "$d" status --porcelain | wc -l); g=$(git -C "$d" diff | wc -l)
  echo "$d : status=$s lignes, diff=$g lignes $( [ $s -eq 0 ] && [ $g -eq 0 ] && echo OK || echo MODIFIÉ)"
done
