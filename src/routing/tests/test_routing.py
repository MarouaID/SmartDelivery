"""
Tests unitaires pour le module de routing
"""

import pytest
from src.models import Commande, Livreur
from src.routing.routing_optimizer import RoutingOptimizer


def test_optimiser_trajet_simple():
    """Test d'optimisation avec 3 commandes"""
    optimizer = RoutingOptimizer(algorithme="nearest_neighbor")
    
    livreur = Livreur(
        id="L1", nom="Jean", latitude_depart=48.8566, longitude_depart=2.3522,
        capacite_poids=100, capacite_volume=2.0,
        heure_debut="08:00", heure_fin="18:00",
        vitesse_moyenne=30, cout_km=0.5
    )
    
    commandes = [
        Commande("C1", "Paris 1", 48.8600, 2.3500, 10, 0.1, "09:00", "12:00", 1, 10),
        Commande("C2", "Paris 2", 48.8550, 2.3450, 15, 0.2, "10:00", "14:00", 2, 15),
        Commande("C3", "Paris 3", 48.8580, 2.3480, 12, 0.15, "11:00", "15:00", 2, 12)
    ]
    
    trajet = optimizer.optimiser_trajet(livreur, commandes)
    
    assert trajet.livreur_id == "L1"
    assert len(trajet.commandes) == 3
    assert trajet.distance_totale > 0
    assert trajet.temps_total > 0
    assert len(trajet.points_gps) == 5  # Dépôt + 3 commandes + retour


def test_algorithme_genetique():
    """Test avec l'algorithme génétique"""
    optimizer = RoutingOptimizer(algorithme="genetic")
    
    livreur = Livreur("L1", "Jean", 48.8566, 2.3522, 100, 2.0, "08:00", "18:00", 30, 0.5)
    commandes = [
        Commande("C1", "A", 48.86, 2.35, 10, 0.1, "09:00", "12:00", 1, 10),
        Commande("C2", "B", 48.85, 2.34, 10, 0.1, "09:00", "12:00", 1, 10)
    ]
    
    trajet = optimizer.optimiser_trajet(livreur, commandes)
    
    assert trajet is not None
    assert len(trajet.commandes) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
