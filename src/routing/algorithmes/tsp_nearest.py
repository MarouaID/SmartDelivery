"""
Algorithme du plus proche voisin pour le TSP
Heuristique gloutonne rapide
"""

from typing import List, Tuple


class NearestNeighborTSP:
    """Résout le TSP avec l'heuristique du plus proche voisin"""
    
    def __init__(self, matrice_distances: List[List[float]]):
        """
        Args:
            matrice_distances: Matrice n×n des distances
                              Index 0 = dépôt
        """
        self.matrice = matrice_distances
        self.n = len(matrice_distances) - 1  # Nombre de commandes (sans dépôt)
    
    def resoudre(self) -> Tuple[List[int], float]:
        """
        Résout le TSP et retourne (ordre, distance_totale)
        
        Returns:
            ordre: Liste des indices des commandes dans l'ordre optimal
            distance: Distance totale du trajet
        """
        if self.n == 0:
            return [], 0.0
        
        visite = [False] * (self.n + 1)
        visite[0] = True  # Dépôt déjà visité
        
        ordre = []
        position_actuelle = 0  # On commence au dépôt
        distance_totale = 0.0
        
        # Visiter toutes les commandes
        for _ in range(self.n):
            plus_proche = -1
            distance_min = float('inf')
            
            # Trouver la commande la plus proche non visitée
            for i in range(1, self.n + 1):
                if not visite[i]:
                    distance = self.matrice[position_actuelle][i]
                    if distance < distance_min:
                        distance_min = distance
                        plus_proche = i
            
            if plus_proche != -1:
                ordre.append(plus_proche - 1)  # Convertir en index de commande (0-based)
                visite[plus_proche] = True
                distance_totale += distance_min
                position_actuelle = plus_proche
        
        # Retour au dépôt
        distance_totale += self.matrice[position_actuelle][0]
        
        return ordre, distance_totale
