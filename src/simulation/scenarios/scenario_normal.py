
import random
from typing import List
from src.models import Commande, Livreur, Trajet


class ScenarioNormal:
    """Scénario standard sans incidents majeurs"""
    
    def __init__(self):
        self.description = "Journée normale avec charge équilibrée"
    
    def generer_commandes(self, generateur, n: int) -> List[Commande]:
        """Génère des commandes avec distribution normale"""
        return generateur.generer_commandes(n, {
            'urgent': 0.1,
            'normal': 0.7,
            'flexible': 0.2
        })
    
    def modifier_livreurs(self, livreurs: List[Livreur]) -> List[Livreur]:
        """Tous les livreurs disponibles en scénario normal"""
        for livreur in livreurs:
            livreur.disponible = True
        return livreurs
    
    def simuler_incidents(self, trajet: Trajet) -> List[dict]:
        """Très peu d'incidents en scénario normal (5% de chance)"""
        incidents = []
        
        if random.random() < 0.05:
            incidents.append({
                'type': 'retard_mineur',
                'trajet_id': trajet.livreur_id,
                'description': 'Léger retard de circulation',
                'impact_minutes': random.randint(5, 15)
            })
        
        return incidents
