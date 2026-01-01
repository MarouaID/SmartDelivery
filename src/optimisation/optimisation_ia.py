"""
Optimisation globale du système de livraison
Utilise des métaheuristiques pour améliorer la solution
Responsable: Personne 3
"""

from typing import Dict, List, Tuple
import numpy as np
from src.models import Trajet, Livreur, Commande
from src.optimisation.algorithmes.genetic_algorithm import AlgorithmeGenetique
from src.optimisation.algorithmes.simulated_annealing import RecuitSimule


class OptimisationIA:
    """Optimisation globale avec algorithmes évolutionnaires"""
    
    def __init__(self, methode: str = "genetic"):
        """
        Args:
            methode: "genetic" ou "annealing"
        """
        self.methode = methode
        self.meilleure_solution = None
        self.historique_scores = []
        self.iterations_executees = 0
    
    def evaluer_solution(self, trajets: Dict[str, Trajet]) -> float:
        """
        Évalue la qualité d'une solution globale
        
        Critères à minimiser:
        - Distance totale (poids: 10)
        - Temps total (poids: 0.5)
        - Coût total (poids: 5)
        - Déséquilibre entre livreurs (poids: 2)
        
        Returns:
            Score (plus bas = meilleur)
        """
        if not trajets:
            return float('inf')
        
        # Métriques de base
        distance_totale = sum(t.distance_totale for t in trajets.values())
        temps_total = sum(t.temps_total for t in trajets.values())
        cout_total = sum(t.cout_total for t in trajets.values())
        
        # Calcul du déséquilibre (écart-type des temps)
        temps_par_livreur = [t.temps_total for t in trajets.values()]
        if len(temps_par_livreur) > 1:
            ecart_type_temps = np.std(temps_par_livreur)
        else:
            ecart_type_temps = 0
        
        # Pénalité pour les trajets trop longs (>8h)
        penalite_duree = sum(max(0, t.temps_total - 480) * 10 for t in trajets.values())
        
        # Score composite
        score = (
            distance_totale * 10 +
            temps_total * 0.5 +
            cout_total * 5 +
            ecart_type_temps * 2 +
            penalite_duree
        )
        
        return score
    
    def calculer_metriques_detaillees(self, trajets: Dict[str, Trajet]) -> dict:
        """Calcule des métriques détaillées pour analyse"""
        if not trajets:
            return {}
        
        distances = [t.distance_totale for t in trajets.values()]
        temps = [t.temps_total for t in trajets.values()]
        couts = [t.cout_total for t in trajets.values()]
        nb_commandes = [len(t.commandes) for t in trajets.values()]
        
        return {
            'score_global': self.evaluer_solution(trajets),
            'distance_totale_km': sum(distances),
            'distance_moyenne_km': np.mean(distances),
            'distance_max_km': max(distances) if distances else 0,
            'temps_total_min': sum(temps),
            'temps_moyen_min': np.mean(temps),
            'temps_max_min': max(temps) if temps else 0,
            'ecart_type_temps': np.std(temps) if len(temps) > 1 else 0,
            'cout_total_euro': sum(couts),
            'nb_commandes_total': sum(nb_commandes),
            'equilibrage_charge': np.std(nb_commandes) if len(nb_commandes) > 1 else 0
        }
    
    def optimiser_solution(self, trajets_initiaux: Dict[str, Trajet],
                          livreurs: List[Livreur],
                          commandes: List[Commande],
                          iterations: int = 100) -> Dict:
        """
        Améliore la solution initiale avec des métaheuristiques
        
        Args:
            trajets_initiaux: Solution de départ
            livreurs: Liste des livreurs
            commandes: Liste des commandes
            iterations: Nombre d'itérations
        
        Returns:
            Dict contenant la solution optimisée et les statistiques
        """
        score_initial = self.evaluer_solution(trajets_initiaux)
        self.historique_scores = [score_initial]
        
        print(f"🎯 Score initial: {score_initial:.2f}")
        
        # Choisir l'algorithme
        if self.methode == "genetic":
            optimiseur = AlgorithmeGenetique(
                trajets_initiaux, livreurs, commandes,
                population_size=50, generations=iterations
            )
        elif self.methode == "annealing":
            optimiseur = RecuitSimule(
                trajets_initiaux, livreurs, commandes,
                iterations=iterations
            )
        else:
            raise ValueError(f"Méthode inconnue: {self.methode}")
        
        # Optimisation
        trajets_optimises, scores = optimiseur.optimiser()
        self.historique_scores.extend(scores)
        self.iterations_executees = iterations
        
        score_final = self.evaluer_solution(trajets_optimises)
        amelioration = ((score_initial - score_final) / score_initial) * 100
        
        print(f"✅ Score final: {score_final:.2f}")
        print(f"📈 Amélioration: {amelioration:.1f}%")
        
        self.meilleure_solution = trajets_optimises
        
        return {
            'trajets_optimises': trajets_optimises,
            'score_initial': score_initial,
            'score_final': score_final,
            'amelioration_pourcent': amelioration,
            'iterations': iterations,
            'methode': self.methode,
            'metriques': self.calculer_metriques_detaillees(trajets_optimises),
            'historique_scores': self.historique_scores
        }
    
    def comparer_solutions(self, solution1: Dict[str, Trajet],
                          solution2: Dict[str, Trajet]) -> dict:
        """Compare deux solutions"""
        score1 = self.evaluer_solution(solution1)
        score2 = self.evaluer_solution(solution2)
        
        return {
            'solution1_score': score1,
            'solution2_score': score2,
            'meilleure': 'solution1' if score1 < score2 else 'solution2',
            'difference': abs(score1 - score2),
            'amelioration_pourcent': ((score1 - score2) / score1) * 100 if score1 > 0 else 0
        }
