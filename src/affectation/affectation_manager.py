"""
Gestion de l'affectation des commandes aux livreurs
Algorithmes: Glouton, Hongrois
Responsable: Personne 1
"""

from typing import List, Dict, Tuple
from src.models import Commande, Livreur
from src.utils import DistanceCalculator
import numpy as np


class AffectationManager:
    """Gère l'affectation optimale des commandes aux livreurs"""
    
    def __init__(self):
        self.distance_calc = DistanceCalculator()
        self.affectations = {}
        self.capacites_restantes = {}
        self.scores_affectation = {}
    
    def calculer_score_affectation(self, livreur: Livreur, commande: Commande) -> float:
        """
        Calcule un score d'affectation [0, 1] basé sur:
        - Distance livreur-commande (40%)
        - Priorité de la commande (30%)
        - Capacité disponible du livreur (30%)
        
        Plus le score est élevé, meilleure est l'affectation
        """
        # Score de distance (inverse)
        distance = self.distance_calc.haversine(
            livreur.latitude_depart, livreur.longitude_depart,
            commande.latitude, commande.longitude
        )
        score_distance = 1 / (1 + distance)
        
        # Score de priorité (urgent = meilleur)
        score_priorite = (4 - commande.priorite) / 3
        
        # Score de capacité (vérifier qu'on peut livrer)
        cap_restante = self.capacites_restantes.get(livreur.id, {
            'poids': livreur.capacite_poids,
            'volume': livreur.capacite_volume
        })
        
        if cap_restante['poids'] < commande.poids or cap_restante['volume'] < commande.volume:
            return 0.0  # Impossible
        
        score_capacite = min(
            cap_restante['poids'] / commande.poids,
            cap_restante['volume'] / commande.volume
        )
        
        # Score global pondéré
        score_final = (0.4 * score_distance + 
                      0.3 * score_priorite + 
                      0.3 * min(score_capacite, 1.0))
        
        return score_final
    
    def _initialiser_capacites(self, livreurs: List[Livreur]):
        """Initialise les capacités restantes pour chaque livreur"""
        self.capacites_restantes = {
            l.id: {
                'poids': l.capacite_poids,
                'volume': l.capacite_volume
            }
            for l in livreurs
        }
    
    def affecter_commandes_glouton(self, livreurs: List[Livreur], 
                                   commandes: List[Commande]) -> Dict[str, List[Commande]]:
        """
        Algorithme glouton d'affectation:
        1. Trier les commandes par priorité
        2. Pour chaque commande, choisir le meilleur livreur disponible
        3. Affecter et mettre à jour les capacités
        
        Retourne: Dict[livreur_id] -> List[Commande]
        """
        self._initialiser_capacites(livreurs)
        self.affectations = {l.id: [] for l in livreurs}
        self.scores_affectation = {}
        
        # Trier par priorité (1=urgent avant 3=flexible)
        commandes_triees = sorted(commandes, key=lambda c: c.priorite)
        
        for commande in commandes_triees:
            meilleur_livreur = None
            meilleur_score = -1
            
            for livreur in livreurs:
                if not livreur.disponible:
                    continue
                
                score = self.calculer_score_affectation(livreur, commande)
                
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_livreur = livreur
            
            # Affecter si un livreur valide trouvé
            if meilleur_livreur and meilleur_score > 0:
                self.affectations[meilleur_livreur.id].append(commande)
                self.scores_affectation[commande.id] = meilleur_score
                
                # Réduire les capacités
                self.capacites_restantes[meilleur_livreur.id]['poids'] -= commande.poids
                self.capacites_restantes[meilleur_livreur.id]['volume'] -= commande.volume
                
                commande.statut = "assignee"
            else:
                print(f"⚠️ Impossible d'affecter la commande {commande.id}")
        
        return self.affectations
    
    def creer_matrice_couts(self, livreurs: List[Livreur], 
                           commandes: List[Commande]) -> np.ndarray:
        """
        Crée une matrice de coûts pour l'algorithme hongrois
        matrice[i][j] = coût d'affecter commande j au livreur i
        """
        n_livreurs = len(livreurs)
        n_commandes = len(commandes)
        
        # Matrice carrée (compléter avec des valeurs infinies si besoin)
        taille = max(n_livreurs, n_commandes)
        matrice = np.full((taille, taille), 1e6)  # Valeur très élevée
        
        for i, livreur in enumerate(livreurs):
            for j, commande in enumerate(commandes):
                score = self.calculer_score_affectation(livreur, commande)
                # Convertir score [0,1] en coût (inverser)
                matrice[i][j] = 1 - score if score > 0 else 1e6
        
        return matrice
    
    def obtenir_statistiques(self) -> dict:
        """Retourne les statistiques d'affectation"""
        total_commandes_affectees = sum(len(cmds) for cmds in self.affectations.values())
        
        stats = {
            'total_commandes_affectees': total_commandes_affectees,
            'livreurs_utilises': sum(1 for cmds in self.affectations.values() if len(cmds) > 0),
            'score_moyen': np.mean(list(self.scores_affectation.values())) if self.scores_affectation else 0,
            'repartition': {
                livreur_id: len(cmds) 
                for livreur_id, cmds in self.affectations.items()
            }
        }
        
        return stats
    
    def __repr__(self):
        return f"AffectationManager(affectations={len(self.affectations)})"
