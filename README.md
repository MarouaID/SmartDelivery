 #pip install -r requirements.txt
Optimisation – SmartDelivery

Ce module fait partie du projet SmartDelivery et contient les outils d’optimisation de parcours pour les livreurs, en particulier via un algorithme génétique (GA).

🗂 Structure du dossier
src/
└── optimisation/
    ├── algorithmes/
    │   ├── __init__.py
    │   ├── genetic_algorithm.py   # Algorithme génétique pour optimisation TSP
    │   ├── utils.py               # Fonctions utilitaires (matrices de distance mock)
    │   └── aid.py                 # Fonctions d’aide pour afficher les résultats
    └── tests/
        └── test_optimisation.py  # Exemple de test pour l’algorithme génétique

⚙️ Description des fichiers
genetic_algorithm.py

Contient la classe GeneticOptimizer qui implémente un algorithme génétique simplifié.

Fonctions principales :

init_population() : initialise la population de solutions aléatoires

fitness(individual) : calcule la distance totale d’un parcours

select_parents() : sélectionne les meilleurs individus pour la reproduction

crossover(parent1, parent2) : combine deux parcours pour créer un enfant

mutate(individual) : mutation aléatoire pour diversifier la population

run() : exécute l’algorithme sur plusieurs générations et retourne le meilleur parcours

utils.py

Fournit des fonctions utilitaires pour le développement et les tests.

Exemple : generate_mock_distance_matrix(n_points) crée une matrice de distances fictive pour tester l’algorithme sans OSRM/Docker.

aid.py

Fonctions d’aide pour afficher et analyser les résultats.

Exemple : print_route_summary(route, dist_matrix) affiche le parcours et la distance totale.

__init__.py

Permet d’importer facilement les fonctions et classes depuis le package optimisation.

tests/test_optimisation.py

Contient un exemple d’utilisation du GA avec matrice fictive.

Permet de tester et visualiser le parcours et la distance totale.

🛠 Utilisation

Activer l’environnement virtuel :

.venv\Scripts\Activate.ps1   # Windows PowerShell


Installer les dépendances si nécessaire :

pip install -r requirements.txt


Lancer le test :

python -m src.optimisation.tests.test_optimisation


Importer le GA dans d’autres modules :

from src.optimisation.algorithmes.genetic_algorithm import GeneticOptimizer
from src.optimisation.algorithmes.utils import generate_mock_distance_matrix
from src.optimisation.algorithmes.aid import print_route_summary

⚡ Notes importantes

Actuellement, le GA utilise une matrice de distances fictives pour les tests.

Plus tard, il sera intégré aux résultats du routing réel avec OSRM (Docker).

Le dossier est prêt pour étendre les fonctionnalités :

différents types de mutation/crossover

contraintes batterie et bornes de recharge

intégration avec l’algorithme d’optimisation global de SmartDelivery
