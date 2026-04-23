# Sudoku & Jeux de Plateau (PyQt6)

Application desktop en Python avec interface Qt6.

Le projet propose un menu principal qui permet de lancer 2 jeux:

1. Sudoku 9x9 (3 niveaux)
2. Jeu de dames (Joueur vs Joueur et Joueur vs Ordinateur)

## Menu principal

Depuis le menu, vous pouvez:

1. Ouvrir le Sudoku
2. Ouvrir le jeu de dames
3. Quitter l'application

Les fenêtres de jeux peuvent rester ouvertes pendant que le menu principal reste disponible.

## Jeu 1: Sudoku

Fonctionnalités principales:

1. Grille classique 9x9
2. Génération automatique de puzzles
3. 3 niveaux de difficulté:
	- Facile
	- Moyen
	- Difficile
4. Détection immédiate des erreurs
5. Système d'indice:
	- Affiche la bonne valeur d'une case
	- Indice automatique lors d'une erreur
6. Navigation au clavier et via boutons numériques

## Jeu 2: Jeu de dames

Fonctionnalités principales:

1. Plateau 8x8
2. Mode Joueur vs Joueur (local)
3. Mode Joueur vs Ordinateur
4. IA avec 3 niveaux (Facile, Moyen, Difficile)
5. Règles gérées:
	- Captures obligatoires
	- Prises multiples (chaînées)
	- Promotion en dame
	- Fin de partie (plus de coups ou plus de pièces)

## Stack technique

1. Python
2. PyQt6
3. Gestion d'environnement et dépendances avec uv

## Installation

Prérequis:

1. Python 3.13+
2. uv installé

Commandes:

```powershell
uv sync
```

ou (si vous recréez le projet):

```powershell
uv add pyqt6
```

## Lancer l'application

```powershell
uv run main.py
```

## Arborescence utile

1. `main.py`: point d'entrée
2. `sudoku/menu.py`: menu principal
3. `sudoku/ui.py`: interface et logique Sudoku
4. `sudoku/generator.py`: génération des grilles Sudoku
5. `sudoku/checkers.py`: interface + logique jeu de dames + IA