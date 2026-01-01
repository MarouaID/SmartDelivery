import random
from typing import List, Dict
from datetime import datetime
from src.models import Commande, Livreur, Trajet
from src.simulation.generateur_donnees import GenerateurDonnees
from src.simulation.scenarios.scenario_normal import ScenarioNormal
from src.simulation.scenarios.scenario_pic import ScenarioPic
from src.simulation.scenarios.scenario_incident import ScenarioIncident


class Simulateur:
    """Simule différents scénarios de livraison"""
    
    def __init__(self, config: dict = None):
        """
        Args:
            config: Configuration de la simulation
        """
        self.config = config or {}
        self.generateur = GenerateurDonnees(config)
        self.historique_simulations = []
        self.scenarios_disponibles = {
            'normal': ScenarioNormal(),
            'pic': ScenarioPic(),
            'incident': ScenarioIncident()
        }
    
    def generer_scenario(self, type_scenario: str = 'normal',
                        nb_livreurs: int = 5,
                        nb_commandes: int = 20) -> Dict:
        """
        Génère un scénario de simulation
        
        Args:
            type_scenario: 'normal', 'pic', 'incident'
            nb_livreurs: Nombre de livreurs
            nb_commandes: Nombre de commandes
        
        Returns:
            Dict contenant livreurs et commandes
        """
        if type_scenario not in self.scenarios_disponibles:
            raise ValueError(f"Scénario inconnu: {type_scenario}")
        
        scenario = self.scenarios_disponibles[type_scenario]
        
        # Générer les données selon le scénario
        livreurs = self.generateur.generer_livreurs(nb_livreurs)
        commandes = scenario.generer_commandes(self.generateur, nb_commandes)
        
        # Appliquer les modifications spécifiques au scénario
        livreurs = scenario.modifier_livreurs(livreurs)
        
        return {
            'type_scenario': type_scenario,
            'livreurs': livreurs,
            'commandes': commandes,
            'timestamp': datetime.now().isoformat(),
            'description': scenario.description
        }
    
    def simuler_execution(self, trajets: Dict[str, Trajet],
                         type_scenario: str = 'normal') -> Dict:
        """
        Simule l'exécution des trajets avec des événements aléatoires
        
        Args:
            trajets: Trajets planifiés
            type_scenario: Type de scénario pour les incidents
        
        Returns:
            Dict avec les résultats de simulation
        """
        scenario = self.scenarios_disponibles.get(type_scenario, ScenarioNormal())
        
        resultats = {
            'trajets_planifies': len(trajets),
            'trajets_termines': 0,
            'trajets_en_retard': 0,
            'incidents': [],
            'temps_execution_simule': 0
        }
        
        for livreur_id, trajet in trajets.items():
            # Simuler l'exécution du trajet
            incidents_trajet = scenario.simuler_incidents(trajet)
            
            if incidents_trajet:
                resultats['incidents'].extend(incidents_trajet)
                resultats['trajets_en_retard'] += 1
            else:
                resultats['trajets_termines'] += 1
            
            # Temps d'exécution avec aléa
            temps_reel = trajet.temps_total * random.uniform(0.9, 1.2)
            resultats['temps_execution_simule'] += temps_reel
        
        resultats['taux_reussite'] = (
            resultats['trajets_termines'] / resultats['trajets_planifies']
            if resultats['trajets_planifies'] > 0 else 0
        )
        
        self.historique_simulations.append({
            'timestamp': datetime.now().isoformat(),
            'scenario': type_scenario,
            'resultats': resultats
        })
        
        return resultats
    
    def comparer_scenarios(self, scenarios: List[str],
                          nb_livreurs: int = 5,
                          nb_commandes: int = 20,
                          repetitions: int = 10) -> Dict:
        """
        Compare plusieurs scénarios sur plusieurs exécutions
        
        Args:
            scenarios: Liste des types de scénarios à comparer
            nb_livreurs: Nombre de livreurs
            nb_commandes: Nombre de commandes
            repetitions: Nombre de simulations par scénario
        
        Returns:
            Statistiques comparatives
        """
        comparaison = {scenario: [] for scenario in scenarios}
        
        for scenario in scenarios:
            print(f"📊 Simulation du scénario '{scenario}'...")
            
            for i in range(repetitions):
                # Générer données
                donnees = self.generer_scenario(scenario, nb_livreurs, nb_commandes)
                
                # Ici, on simule juste la génération
                # Dans le système complet, on lancerait l'optimisation
                comparaison[scenario].append({
                    'iteration': i + 1,
                    'nb_commandes': len(donnees['commandes']),
                    'nb_livreurs': len(donnees['livreurs'])
                })
        
        return comparaison
    
    def generer_rapport_simulation(self) -> str:
        """Génère un rapport textuel des simulations"""
        rapport = []
        rapport.append("=" * 60)
        rapport.append("RAPPORT DE SIMULATION")
        rapport.append("=" * 60)
        rapport.append(f"Nombre de simulations: {len(self.historique_simulations)}")
        
        if self.historique_simulations:
            rapport.append("\nDernières simulations:")
            for sim in self.historique_simulations[-5:]:
                rapport.append(f"\n📅 {sim['timestamp']}")
                rapport.append(f"   Scénario: {sim['scenario']}")
                if 'resultats' in sim:
                    res = sim['resultats']
                    rapport.append(f"   Taux de réussite: {res.get('taux_reussite', 0)*100:.1f}%")
                    rapport.append(f"   Incidents: {len(res.get('incidents', []))}")
        
        rapport.append("=" * 60)
        return "\n".join(rapport)
