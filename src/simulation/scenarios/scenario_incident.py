
import random
from typing import List
from src.models import Commande, Livreur, Trajet


class ScenarioIncident:
    """Scénario avec incidents perturbateurs"""
    
    def __init__(self):
        self.description = "Journée avec incidents majeurs (météo, pannes, etc.)"
        self.incidents_globaux = []
    
    def generer_commandes(self, generateur, n: int) -> List[Commande]:
        """Commandes normales mais avec risques d'annulation"""
        commandes = generateur.generer_commandes(n, {
            'urgent': 0.15,
            'normal': 0.65,
            'flexible': 0.2
        })
        
        # Simuler quelques annulations
        nb_annulations = int(n * 0.05)  # 5% d'annulations
        for _ in range(nb_annulations):
            if commandes:
                commande_annulee = random.choice(commandes)
                commande_annulee.statut = "annulee"
        
        return commandes
    
    def modifier_livreurs(self, livreurs: List[Livreur]) -> List[Livreur]:
        """Plusieurs livreurs indisponibles à cause d'incidents"""
        
        # 1-2 livreurs totalement indisponibles
        nb_indisponibles = random.randint(1, min(2, len(livreurs) // 3))
        for i in range(nb_indisponibles):
            if i < len(livreurs):
                livreurs[i].disponible = False
                self.incidents_globaux.append({
                    'type': 'livreur_indisponible',
                    'livreur_id': livreurs[i].id,
                    'raison': random.choice(['panne_vehicule', 'maladie', 'accident'])
                })
        
        # Réduire la vitesse de certains à cause de la météo
        for livreur in livreurs[nb_indisponibles:]:
            if random.random() < 0.3:  # 30% affectés
                livreur.vitesse_moyenne *= 0.7  # Réduction de 30%
        
        return livreurs
    
    def simuler_incidents(self, trajet: Trajet) -> List[dict]:
        """Nombreux incidents (40% de chance)"""
        incidents = []
        
        if random.random() < 0.4:
            types_incidents = [
                'panne_vehicule',
                'accident_route',
                'colis_endommage',
                'adresse_incorrecte',
                'client_injoignable'
            ]
            
            nb_incidents = random.randint(1, 2)
            for _ in range(nb_incidents):
                incidents.append({
                    'type': random.choice(types_incidents),
                    'trajet_id': trajet.livreur_id,
                    'description': 'Incident majeur nécessitant intervention',
                    'impact_minutes': random.randint(20, 60)
                })
        
        return incidents
