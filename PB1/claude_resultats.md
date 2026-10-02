# Hash Code 2017 (Streaming Videos) — résultats et approche du solveur `claude_*`

Fichiers concernés : `claude_solver.py` (les algos) et `claude_main.py` (le lanceur).

## 1. Résultats

Scores obtenus avec `python claude_main.py all`, tous confirmés par le juge
(`judge/judgeHashCode2017.cpp`) sur les fichiers `results/<instance>_claude.out`.

| Instance | Glouton seul | Glouton + sac à dos | Temps glouton | Temps sac à dos |
|---|---:|---:|---:|---:|
| `me_at_the_zoo` | 507 906 | **512 115** | < 0,01 s | 0,01 s |
| `trending_today` | 499 966 | **499 966** | 5,8 s | 2,1 s |
| `videos_worth_spreading` | 608 277 | **610 574** | 0,3 s | 2,6 s |
| `kittens` | 1 021 680 | **1 024 517** | 2,4 s | 14,8 s |
| **Total (4 instances officielles)** | 2 637 829 | **2 647 172** | | |

`test.in` (l'exemple de l'énoncé) donne 562 500 ; il n'est pas compté dans le total.

L'ensemble tourne en environ 30 secondes, lecture des fichiers comprise.

### Comparaison

- **Classement 2017** (`results_doc/hashcode_2017.csv`) : 2 647 172 se place entre le 3e
  (2 649 544) et le 4e (2 646 990). Le premier est à 2 651 999, soit 0,18 % au-dessus.
  La comparaison est indicative : les équipes avaient quelques heures, en conditions de concours.
- **Algos existants du dépôt**, sur les deux instances où je les ai mesurés :

| Instance | `greedy` | `claude_solve` |
|---|---:|---:|
| `me_at_the_zoo` | 471 938 | 512 115 |
| `videos_worth_spreading` | 484 419 | 610 574 |

### Lecture des résultats

- Le glouton fait l'essentiel du travail : le sac à dos ajoute entre 0 et 0,8 % selon l'instance.
- Sur `trending_today`, le sac à dos améliore le coût (de 76 000) mais pas assez pour changer
  le score entier : le glouton est déjà quasiment au maximum.
- Le résultat est un optimum local : la recherche s'arrête quand plus aucun cache, pris seul,
  ne peut être amélioré. Aller plus loin demanderait de modifier plusieurs caches à la fois.

## 2. Approche

### 2.1 Reformulation

Pour une requête (vidéo `v`, endpoint `e`, `n` demandes), on note `gain(c, e) = latence
datacenter de e − latence de e vers le cache c` (0 si `e` n'est pas relié à `c`).
Le temps gagné par la requête est `n × max gain(c, e)` sur les caches `c` qui contiennent `v`.
Le score est la somme de ces temps gagnés, × 1000, divisée par le nombre total de demandes.

Conséquence importante : **ajouter une vidéo dans un cache ne rapporte que ce qui dépasse
ce que les autres caches rapportent déjà**. Le gain d'un couple (cache, vidéo) dépend donc de
l'état courant et ne peut que diminuer au fil des ajouts.

### 2.2 Pré-calcul (`build_index`)

Fait une seule fois par instance, à partir du dictionnaire `data` de `main.py` :

- `sav[c][e]` : matrice caches × endpoints des gains de latence (500 × 1000 pour `kittens`) ;
- requêtes fusionnées par couple (vidéo, endpoint) et triées par vidéo, avec un tableau
  d'indices donnant la tranche de chaque vidéo (même idée que `adj_list`) ;
- les requêtes qui ne peuvent rien rapporter sont ignorées (vidéo plus grande qu'un cache,
  endpoint sans cache).

Tout est en tableaux numpy : le gain de **toutes** les vidéos pour un cache donné se calcule
en une passe vectorisée sur les requêtes, sans stocker les ~70 millions de triplets
(cache, vidéo, requête) de `kittens`.

### 2.3 Étape 1 — glouton par densité (`claude_greedy`)

1. Calculer, pour chaque couple (cache, vidéo) possible, la densité
   `gain courant / taille de la vidéo`.
2. Placer le couple de meilleure densité.
3. Mettre à jour : seuls les gains **de cette vidéo** changent (dans tous les caches), et
   les vidéos devenues trop grosses pour le cache rempli sont exclues.
4. Recommencer tant qu'un couple a un gain positif.

Diviser par la taille est ce qui fait la différence avec un glouton « par nombre de
requêtes » : la capacité est la ressource rare, on mesure donc le gain par Mo occupé.

Pour aller vite, on garde le meilleur couple de chaque cache. Comme les gains ne font que
baisser, une valeur périmée reste une borne supérieure : on ne recalcule la ligne d'un cache
que lorsqu'il arrive en tête.

### 2.4 Étape 2 — sac à dos cache par cache (`claude_knapsack`)

Pour un cache `c`, les autres caches étant fixés :

1. vider `c` ;
2. calculer le gain de chaque vidéo si on la mettait dans `c` ;
3. ces gains sont indépendants entre vidéos, donc le meilleur remplissage de `c` est
   exactement un **sac à dos 0/1** (poids = taille, valeur = gain, capacité = taille du cache),
   résolu par programmation dynamique ;
4. garder le nouveau contenu s'il est strictement meilleur, sinon remettre l'ancien.

On parcourt tous les caches dans un ordre aléatoire (graine fixe, résultat reproductible) et
on recommence jusqu'à ce qu'une passe complète n'apporte rien. L'ancien contenu étant
toujours une solution possible du sac à dos, **le score ne peut jamais baisser**.

Pour limiter le temps, le sac à dos ne considère que les vidéos les plus denses, jusqu'à une
taille cumulée de `window = 4` fois la capacité, plus l'ancien contenu du cache.
`window=None` prend toutes les vidéos (plus lent, non testé).

Convergence observée : 2 passes sur `me_at_the_zoo` et `trending_today`, 7 sur
`videos_worth_spreading` et `kittens`.

## 3. Utilisation et compatibilité

```
python claude_main.py                       # instances/test.in
python claude_main.py instances/kittens.in
python claude_main.py all
```

Les trois algos ont la signature des algos existants, `algo(data, caches, caches_sizes)` :
ils partent de l'état reçu, modifient `caches` et `caches_sizes` en place, et acceptent des
`list` comme des `set`. Ils se branchent donc directement dans `main.py` :

```python
from claude_solver import claude_solve, claude_knapsack

run("Claude", claude_solve, starts[""], list, data, base_cost, results)
run("ClaudeKnapsack (g)", claude_knapsack, starts["g"], set, data, base_cost, results)
```

`claude_knapsack` peut ainsi servir à améliorer la solution de n'importe quel autre algo.

Deux points à connaître :

- `caches_sizes` est recalculé à partir du contenu des caches, il n'est pas lu en entrée ;
- `claude_main.py` calcule coût et score avec `claude_cost` / `claude_score` (numpy), car
  `utils.compute_cost` est lent sur `kittens`. Les valeurs sont identiques à celles de
  `utils.py` sur les instances où je les ai comparées (`test`, `me_at_the_zoo`,
  `videos_worth_spreading`).
