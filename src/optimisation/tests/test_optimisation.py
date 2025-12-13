
# src/optimisation/tests/test_genetic.py
from src.optimisation.algorithmes import GeneticOptimizer
from src.optimisation.algorithmes.utils import generate_mock_distance_matrix
from src.optimisation.algorithmes.aid import print_route_summary

# Générer une matrice fictive de 6 points
dist_matrix = generate_mock_distance_matrix(6)

# Créer l'algorithme génétique
ga = GeneticOptimizer(dist_matrix, pop_size=15, generations=30)
best_route, best_score = ga.run()

# Afficher le résultat
print_route_summary(best_route, dist_matrix)
print("Meilleur score (distance totale) :", best_score)
