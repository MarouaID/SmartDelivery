"""
Algorithme génétique pour le TSP
Plus lent mais meilleure qualité de solution
"""

import random
from typing import List, Tuple


class GeneticTSP:
    """Résout le TSP avec un algorithme génétique"""
    
    def __init__(self, matrice_distances: List[List[float]], 
                 population_size: int = 100,
                 generations: int = 200,
                 mutation_rate: float = 0.02):
        self.matrice = matrice_distances
        self.n = len(matrice_distances) - 1
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
    
    def calculer_distance_trajet(self, ordre: List[int]) -> float:
        """Calcule la distance totale d'un trajet"""
        if not ordre:
            return 0.0
        
        distance = self.matrice[0][ordre[0] + 1]  # Dépôt vers première commande
        
        for i in range(len(ordre) - 1):
            distance += self.matrice[ordre[i] + 1][ordre[i + 1] + 1]
        
        distance += self.matrice[ordre[-1] + 1][0]  # Dernière commande vers dépôt
        
        return distance
    
    def generer_population_initiale(self) -> List[List[int]]:
        """Génère une population initiale aléatoire"""
        population = []
        ordre_base = list(range(self.n))
        
        for _ in range(self.population_size):
            individu = ordre_base.copy()
            random.shuffle(individu)
            population.append(individu)
        
        return population
    
    def selection(self, population: List[List[int]], fitnesses: List[float]) -> List[int]:
        """Sélection par tournoi"""
        taille_tournoi = 5
        tournoi = random.sample(list(zip(population, fitnesses)), taille_tournoi)
        gagnant = min(tournoi, key=lambda x: x[1])
        return gagnant[0]
    
    def croisement(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Croisement PMX (Partially Mapped Crossover)"""
        if self.n <= 1:
            return parent1.copy()
        
        point1 = random.randint(0, self.n - 1)
        point2 = random.randint(point1, self.n)
        
        enfant = [-1] * self.n
        enfant[point1:point2] = parent1[point1:point2]
        
        position = point2
        for gene in parent2[point2:] + parent2[:point2]:
            if gene not in enfant:
                if position >= self.n:
                    position = 0
                enfant[position] = gene
                position += 1
        
        return enfant
    
    def mutation(self, individu: List[int]) -> List[int]:
        """Mutation par échange de deux gènes"""
        if random.random() < self.mutation_rate and self.n > 1:
            i, j = random.sample(range(self.n), 2)
            individu[i], individu[j] = individu[j], individu[i]
        return individu
    
    def resoudre(self) -> Tuple[List[int], float]:
        """
        Résout le TSP avec l'algorithme génétique
        
        Returns:
            ordre: Liste des indices des commandes
            distance: Distance totale
        """
        if self.n == 0:
            return [], 0.0
        
        if self.n == 1:
            return [0], self.matrice[0][1] + self.matrice[1][0]
        
        # Initialisation
        population = self.generer_population_initiale()
        meilleur_individu = None
        meilleure_distance = float('inf')
        
        # Évolution
        for generation in range(self.generations):
            # Évaluation
            fitnesses = [self.calculer_distance_trajet(ind) for ind in population]
            
            # Garder le meilleur
            idx_meilleur = fitnesses.index(min(fitnesses))
            if fitnesses[idx_meilleur] < meilleure_distance:
                meilleure_distance = fitnesses[idx_meilleur]
                meilleur_individu = population[idx_meilleur].copy()
            
            # Nouvelle génération
            nouvelle_population = [meilleur_individu]  # Élitisme
            
            while len(nouvelle_population) < self.population_size:
                parent1 = self.selection(population, fitnesses)
                parent2 = self.selection(population, fitnesses)
                
                enfant = self.croisement(parent1, parent2)
                enfant = self.mutation(enfant)
                
                nouvelle_population.append(enfant)
            
            population = nouvelle_population
        
        return meilleur_individu, meilleure_distance
