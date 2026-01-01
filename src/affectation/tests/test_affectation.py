import pytest
from src.models import Commande, Livreur
from src.affectation.affectation_manager import AffectationManager


def test_calculer_score_affectation():
    """Test du calcul de score"""
    manager = AffectationManager()
    
    livreur = Livreur(
        id="L1", nom="Jean", latitude_depart=48.8566, longitude_depart=2.3522,
        capacite_poids=100, capacite_volume=2.0,
        heure_debut="08:00", heure_fin="18:00",
        vitesse_moyenne=30, cout_km=0.5
    )
    
    commande = Commande(
        id="C1", adresse="Paris", latitude=48.8600, longitude=2.3500,
        poids=10, volume=0.1, fenetre_debut="09:00", fenetre_fin="12:00",
        priorite=1, temps_service=10
    )
    
    score = manager.calculer_score_affectation(livreur, commande)
    
    assert 0 <= score <= 1
    assert score > 0  # Devrait être possible


def test_affectation_glouton():
    """Test de l'algorithme glouton"""
    manager = AffectationManager()
    
    livreurs = [
        Livreur("L1", "Jean", 48.8566, 2.3522, 100, 2.0, "08:00", "18:00", 30, 0.5),
        Livreur("L2", "Marie", 48.8500, 2.3400, 150, 3.0, "08:00", "18:00", 30, 0.5)
    ]
    
    commandes = [
        Commande("C1", "Paris 1", 48.8600, 2.3500, 10, 0.1, "09:00", "12:00", 1, 10),
        Commande("C2", "Paris 2", 48.8550, 2.3450, 20, 0.2, "10:00", "14:00", 2, 15)
    ]
    
    affectations = manager.affecter_commandes_glouton(livreurs, commandes)
    
    assert len(affectations) == 2
    total_affecte = sum(len(cmds) for cmds in affectations.values())
    assert total_affecte == 2  # Toutes les commandes doivent être affectées


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
