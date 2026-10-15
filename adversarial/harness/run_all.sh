#!/usr/bin/env bash
# Lance les 4 algos disponibles (moi, autre1..3 ; autre4 introuvable) sur une instance.
# Usage : harness/run_all.sh <instance.in> [--timeout S] [--keep DIR]
cd "$(dirname "$0")/.." || exit 1
exec python harness/run_all.py "$@"
