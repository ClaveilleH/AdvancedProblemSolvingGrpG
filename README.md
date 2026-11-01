# Advanced Problem Solving — Hash Code 2017 (Streaming Videos)

Groupe G — Jade, Hugo, Kyllian, Valentin.

Résolution du sujet *Streaming Videos to Cache Servers* : placer des vidéos dans des caches
pour minimiser la latence des requêtes. Le dépôt contient les algorithmes, le harnais de mesure
qui a produit les chiffres de l'oral, les instances et les supports de présentation.

---

## Démarrage rapide

```bash
# Une instance, chaîne complète : gloutons -> knapsack -> recherche locale
python main.py instances/kittens.in
# -> écrit concour/results/kittens.txt

# Mesurer tous les algos sur les 4 instances Google (300 s max par exécution)
python -m bench.run google --timeout 300
# -> écrit bench/data/runs.csv et results/bench/
```

## Dépendances

Python ≥ 3.10, puis :

```bash
pip install pandas numpy matplotlib
# ou, avec uv :
uv pip install pandas numpy matplotlib
```

- `pandas` : requis par `algos/knapsack_slay.py`, donc par `main.py` et tout `bench/`.
- `numpy` : `trap_generate.py`, `metrics/`.
- `matplotlib` : `bench/plots.py`, `metrics/`.

Sous macOS, la commande `python` n'existe pas toujours : utiliser `python3`, ou préfixer
par `uv run` (`uv run python main.py …`).

---

## Arborescence

| Chemin | Rôle |
|---|---|
| `main.py` | Point d'entrée : enchaîne les algos sur une instance et écrit la solution. |
| `utils.py` | Anciens helpers de lecture/écriture (remplacés par `algos/utils.py`). |
| `algos/` | Les algorithmes. |
| `algos/greedy.py`, `greedy2.py`, `greedy3.py` | Les trois gloutons (gain, gain/taille, taille). |
| `algos/knapsack.py` | Sac à dos de référence, sans mise à jour des gains. |
| `algos/knapsack_slay.py` | Sac à dos multi-passes **avec mise à jour** des gains (`KS_maj`). |
| `algos/local_search.py` | Recherche locale, tabou aléatoire (`TS`), tabou trié (`TSS`). |
| `algos/localsearchkyllian.py` | Version d'essai de la recherche locale. |
| `algos/utils.py` | Lecture des instances, écriture des solutions, coût et score. |
| `bench/` | Harnais de mesure : une ligne de CSV par (instance, algo, graine). |
| `bench/run.py` | Lance les algos, gère le timeout et la reprise. |
| `bench/common.py` | Chemins, listes d'instances (Google, promo, jouets), évaluation. |
| `bench/features.py` | Caractéristiques des instances (capacité, caches/endpoint…). |
| `bench/solution_stats.py` | Statistiques sur les solutions produites (doublons, remplissage…). |
| `bench/plots.py` | Génère les figures de l'oral. |
| `bench/data/` | CSV produits : `runs.csv`, `grid.csv`, `features.csv`, `solutions.csv`. |
| `metrics/` | Lecture entrée/sortie et métriques détaillées (slides de Kyllian). |
| `judge/` | Juge officiel (binaires Linux) et source `jugeCorrige.cpp`. |
| `judgeHashCode2017.cpp` | Source du juge, à la racine. |
| `instances/` | Les 33 instances `.in` (4 Google, 24 promo, 5 jouets). |
| `concour/` | Rendus de la compétition : `instances/`, `rendu1/`, `rendu2/`, `results/`. |
| `results/` | Sorties du bench (`results/bench/`), ignorées par git. |
| `trap_generate.py` | Générateur d'instances pièges pour les gloutons. |
| `docs/exel/` | Google Sheet des scores (archive du 10/10) et scraper. |
| `docs/oral/` | Première présentation (`diapo.tex`) et ses figures. |
| `docs/oralFinal/` | Support final (`main.tex`, `assets/`, `ORAL.md`). |
| `plot.py`, `convergence.csv` | Tracé ad hoc d'une courbe de convergence. |
| `PB1/`, `res`, `modele_beamer.zip` | Restes de séance : à ignorer. |

---

## Lancer les fichiers clés

Toutes les commandes se lancent **depuis la racine du dépôt**.

### Résoudre une instance — `main.py`

```bash
python main.py instances/me_at_the_zoo.in     # une instance au chemin donné
python main.py                                # instance par défaut (instance01.txt)
python main.py all                            # toutes les instances de concour/instances
```

La solution est écrite dans `concour/results/<nom>.txt`, au format du concours
(une ligne par cache : `id_cache video1 video2 …`).

### Mesurer les algorithmes — `bench/run.py`

C'est ce qui a produit les chiffres de l'oral. Chaque exécution tourne dans son propre
processus ; au bout du timeout, l'algo est interrompu et l'état courant est évalué.

```bash
python -m bench.run all                              # 33 instances, 8 algos
python -m bench.run google --timeout 300             # les 4 instances Google
python -m bench.run kittens big --algos Greedy KS_maj
python -m bench.run kittens --grid                   # étude du voisinage des tabous
python -m bench.run kittens --seeds 10 --workers 4   # 10 graines, 4 processus
python -m bench.run all --force                      # repart de zéro
```

Le bench **reprend là où il s'est arrêté** : une ligne déjà présente dans `runs.csv`
n'est pas relancée. Sorties : `bench/data/runs.csv` et `results/bench/<instance>__<algo>.out`.

### Caractéristiques et statistiques

```bash
python -m bench.features all                 # -> bench/data/features.csv
python -m bench.solution_stats all           # -> bench/data/solutions.csv
```

`features.csv` donne par instance le ratio capacité/volume, les caches par endpoint, etc.
`solution_stats.csv` donne le remplissage des caches, les doublons, la part servie par cache.

### Régénérer les figures de l'oral

```bash
python -m bench.plots        # lit bench/data/*.csv, écrit dans docs/oral/figures/
```

Les figures utilisées par le support final sont copiées dans `docs/oralFinal/assets/`.

### Vérifier une solution avec le juge

```bash
./judge/judgeHashCode2017 instances/kittens.in results/bench/kittens__KS_maj.out
# affiche « Score = ... »
```

Les binaires fournis sont des exécutables **Linux**. Sur macOS, recompiler d'abord :

```bash
g++ -O2 judge/jugeCorrige.cpp -o judge/jugeCorrige
```

### Compiler les slides

```bash
cd docs/oralFinal
make          # compile main.pdf avec latexmk (ou pdflatex en secours)
make view     # ouvre le PDF
make clean    # supprime les fichiers temporaires
```

Le dossier `docs/oralFinal/` est autonome : il contient ses propres figures dans `assets/`,
donc il peut être importé tel quel dans Overleaf. Le minutage et la répartition par
orateur sont dans `docs/oralFinal/ORAL.md`.

### Générer des instances pièges

```bash
python trap_generate.py mon_piege --caches 200 --density 0.45
# -> instances/generated/mon_piege.in
```

Ces instances sont construites pour faire chuter un glouton gain/taille : utiles pour
montrer qu'un glouton seul ne suffit pas.

---

## Conventions

- Les scripts de `bench/` lisent les instances dans `instances/` et écrivent dans `bench/data/`.
  `main.py`, lui, lit le chemin qu'on lui donne et écrit dans `concour/results/`.
- `bench/data/runs.csv` : une ligne par (instance, algo, graine), avec le statut
  `ok` / `timeout` et le score obtenu.
- `results/` et les fichiers `.out` ne sont pas versionnés : ce sont des sorties de calcul.
- Les scores de référence (VBS par groupe) viennent de `docs/exel/backup_10_10_26/`,
  pas du bench.
