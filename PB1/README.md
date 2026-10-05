# Hash Code 2017 - Streaming Videos

Ce projet propose des heuristiques d'optimisation (glouton, recherche locale tabou) pour résoudre le problème de cache vidéo du Google Hash Code 2017, ainsi que des outils de métriques et de visualisation.

## Structure du projet

- `main.py` : script principal exécutant l'approche gloutonne suivie de la recherche locale (recherche tabou).
- `greedy.py` : implémentation de l'algorithme glouton de base.
- `local_search.py` : implémentation de la recherche locale (recherche tabou).
- `mesure_metrics.py` : analyse des données d'entrée et validation/évaluation d'une solution avec génération de graphiques.
- `plot_metrics.py` : calcul des métriques et statistiques d'une solution.
- `show_metrics.py` : fonctions de tracé matplotlib pour les instances et les résultats.
- `instances/` : fichiers d'instances au format `.in`.
- `results/` : résultats obtenus (`.out`), statistiques et graphiques exportés.

## Utilisation

### Résolution du problème

Pour exécuter l'algorithme sur une instance :

```bash
python main.py [chemin/vers/fichier.in]
```

Si aucun argument n'est fourni, le script utilise par défaut `instances/test.in`.

### Métriques et visualisation

Le script `mesure_metrics.py` permet d'analyser une instance et, optionnellement, d'évaluer une solution et d'enregistrer les graphiques associés.

Commande de base :

```bash
python mesure_metrics.py -i [fichier.in] -o [fichier.out] -s [chemin_sauvegarde]
```

Remarque : seul le paramètre `-i` est obligatoire.

Options disponibles :
- `-i, --input [fichier.in]` : chemin du fichier d'entrée (obligatoire).
- `-o, --output [fichier.out]` : chemin du fichier de solution pour calculer le score et vérifier les contraintes (optionnel).
- `-s, --save [chemin_sauvegarde]` : préfixe pour sauvegarder les figures générées (par exemple `results/stats/mon_test`), produisant `[chemin_sauvegarde]_input.png` et/ou `[chemin_sauvegarde]_output.png` (optionnel).
- `-w, --which [input|output|both]` : type de graphiques à sauvegarder avec `-s` (défaut : `both`).
- `--plots` / `--no-plots` : active ou désactive l'affichage interactif des graphiques (défaut : affichage actif).

Exemples d'utilisation :

- Analyser uniquement une instance d'entrée :
```bash
python mesure_metrics.py -i instances/me_at_the_zoo.in
```

- Analyser une instance et sa solution en sauvegardant les graphiques sans bloquer l'affichage :
```bash
python mesure_metrics.py -i instances/me_at_the_zoo.in -o results/me_at_the_zoo.out -s results/stats/me_at_the_zoo --no-plots
```
