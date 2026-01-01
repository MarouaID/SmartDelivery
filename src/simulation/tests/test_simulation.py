
import pytest
from src.simulation.simulateur import Simulateur
from src.simulation.generateur_donnees import GenerateurDonnees


def test_generateur_commandes():
    """Test de génération de commandes"""
    generateur = GenerateurDonnees()
    
    commandes = generateur.generer_commandes(10)
    
    assert len(commandes) == 10
    assert all(c.id.startswith('CMD') for c in commandes)
    assert all(1 <= c.priorite <= 3 for c in commandes)


def test_generateur_livreurs():
    """Test de génération de livreurs"""
    generateur = GenerateurDonnees()
    
    livreurs = generateur.generer_livreurs(5)
    
    assert len(livreurs) == 5
    assert all(l.id.startswith('LIV') for l in livreurs)
    assert all(l.capacite_poids > 0 for l in livreurs)


def test_scenario_normal():
    """Test du scénario normal"""
    simulateur = Simulateur()
    
    scenario = simulateur.generer_scenario('normal', nb_livreurs=3, nb_commandes=10)
    
    assert scenario['type_scenario'] == 'normal'
    assert len(scenario['livreurs']) == 3
    assert len(scenario['commandes']) == 10


def test_scenario_pic():
    """Test du scénario de pic"""
    simulateur = Simulateur()
    
    scenario = simulateur.generer_scenario('pic', nb_livreurs=5, nb_commandes=20)
    
    # Le scénario pic génère plus de commandes
    assert len(scenario['commandes']) > 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
