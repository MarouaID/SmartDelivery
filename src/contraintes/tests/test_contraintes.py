
import pytest
from src.models import Commande, Livreur, Trajet
from src.contraintes.validateur import ValidateurContraintes
from src.contraintes.regles.horaires import ValidateurHoraires
from src.contraintes.regles.capacites import ValidateurCapacites


def test_validation_capacite():
    """Test de validation de capacité"""
    validateur = ValidateurCapacites()
    
    livreur = Livreur(
        "L1", "Jean", 48.8566, 2.3522, 100, 2.0, 
        "08:00", "18:00", 30, 0.5
    )
    
    commandes = [
        Commande("C1", "A", 48.86, 2.35, 50, 0.5, "09:00", "12:00", 1, 10),
        Commande("C2", "B", 48.85, 2.34, 60, 0.6, "10:00", "14:00", 2, 15)
    ]
    
    # Devrait dépasser la capacité
    est_valide, msg = validateur.valider_capacite_totale(livreur, commandes)
    assert not est_valide
    assert "Poids dépassé" in msg


def test_validation_fenetre_horaire():
    """Test de validation des fenêtres horaires"""
    validateur = ValidateurHoraires()
    
    commande = Commande(
        "C1", "Paris", 48.86, 2.35, 10, 0.1, 
        "09:00", "12:00", 1, 10
    )
    
    # Dans la fenêtre
    valide, _ = validateur.valider_fenetre_horaire(commande, "10:30")
    assert valide
    
    # Hors fenêtre
    valide, msg = validateur.valider_fenetre_horaire(commande, "13:00")
    assert not valide
    assert "hors fenêtre" in msg


def test_validation_solution_complete():
    """Test de validation d'une solution complète"""
    validateur = ValidateurContraintes()
    
    livreurs = [
        Livreur("L1", "Jean", 48.8566, 2.3522, 100, 2.0, "08:00", "18:00", 30, 0.5)
    ]
    
    commandes = [
        Commande("C1", "A", 48.86, 2.35, 10, 0.1, "09:00", "12:00", 1, 10)
    ]
    
    trajets = {
        "L1": Trajet(
            livreur_id="L1",
            commandes=["C1"],
            ordre_livraison=[0],
            distance_totale=5.0,
            temps_total=30,
            cout_total=2.5,
            heure_depart="08:00",
            heure_retour_estimee="09:00"
        )
    }
    
    resultat = validateur.valider_solution_complete(trajets, livreurs, commandes)
    
    assert 'valide' in resultat
    assert 'trajets_valides' in resultat


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
