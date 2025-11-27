
import random
from typing import List
from src.models import Commande, Livreur, Trajet


class ScenarioPic:
    """Scénario de haute demande avec contraintes temporelles"""
    
    def __init__(self):
        self.description = "Pic d'activité avec nombreuses commandes urgentes"
    
    def generer_commandes(self, generateur, n: int) -> List[Commande]:
        """
        Génère plus de commandes urgentes et des zones denses
        """
        # 150% du nombre normal
        n_augmente = int(n * 1.5)
        
        # Distribution avec plus d'urgences
        commandes_base = generateur.generer_commandes(n_augmente, {
            'urgent': 0.4,  # 40% urgentes
            'normal': 0.5,
            'flexible': 0.1
        })
        
        # Ajouter une zone très dense
        zone_dense = generateur.generer_zone_dense(
            int(n * 0.3),
            generateur.centre_lat,
            generateur.centre_lon,
            rayon_km=3
        )
        
        return commandes_base + zone_dense
    
    def modifier_livreurs(self, livreurs: List[Livreur]) -> List[Livreur]:
        """Quelques livreurs indisponibles (surchargés)"""
        for livreur in livreurs:
            if random.random() < 0.15:  # 15% indisponibles
                livreur.disponible = False
        return livreurs
    
    def simuler_incidents(self, trajet: Trajet) -> List[dict]:
        """Plus d'incidents en période de pic (25% de chance)"""
        incidents = []
        
        if random.random() < 0.25:
            type_incident = random.choice([
                'retard_circulation',
                'commande_incorrecte',
                'client_absent'
            ])
            
            incidents.append({
                'type': type_incident,
                'trajet_id': trajet.livreur_id,
                'description': f'Incident: {type_incident}',
                'impact_minutes': random.randint(10, 30)
            })
        
        return incidents
