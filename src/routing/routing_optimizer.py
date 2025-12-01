"""
Optimisation des trajets de livraison
Résout le problème du voyageur de commerce (TSP)
Responsable: Personne 2
"""

from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from src.models import Commande, Livreur, Trajet
from src.utils import DistanceCalculator, TimeUtils
from src.routing.algorithmes.tsp_nearest import NearestNeighborTSP
from src.routing.algorithmes.tsp_genetic import GeneticTSP


class RoutingOptimizer:
    """Optimise l'ordre des livraisons pour minimiser distance/temps"""
    
    def __init__(self, algorithme: str = "nearest_neighbor"):
        """
        Args:
            algorithme: "nearest_neighbor" ou "genetic"
        """
        self.distance_calc = DistanceCalculator()
        self.algorithme = algorithme
        self.trajets_optimises = {}
        
    def calculer_matrice_distances(self, livreur: Livreur, 
                                   commandes: List[Commande]) -> List[List[float]]:
        """
        Calcule la matrice de distances incluant le dépôt
        matrice[0] = dépôt du livreur
        matrice[i+1] = commande i
        """
        n = len(commandes)
        matrice = [[0.0] * (n + 1) for _ in range(n + 1)]
        
        positions = [(livreur.latitude_depart, livreur.longitude_depart)]
        positions.extend([(c.latitude, c.longitude) for c in commandes])
        
        for i in range(n + 1):
            for j in range(n + 1):
                if i != j:
                    matrice[i][j] = self.distance_calc.haversine(
                        positions[i][0], positions[i][1],
                        positions[j][0], positions[j][1]
                    )
        
        return matrice
    
    def optimiser_trajet(self, livreur: Livreur, 
                        commandes: List[Commande]) -> Trajet:
        """
        Optimise le trajet pour un livreur donné
        Retourne un objet Trajet avec l'ordre optimal
        """
        if not commandes:
            return self._creer_trajet_vide(livreur)
        
        # Calculer la matrice de distances
        matrice_distances = self.calculer_matrice_distances(livreur, commandes)
        
        # Choisir l'algorithme
        if self.algorithme == "nearest_neighbor":
            solver = NearestNeighborTSP(matrice_distances)
        elif self.algorithme == "genetic":
            solver = GeneticTSP(matrice_distances)
        else:
            raise ValueError(f"Algorithme inconnu: {self.algorithme}")
        
        # Résoudre le TSP
        ordre_optimal, distance_totale = solver.resoudre()
        
        # Calculer le temps total
        temps_trajet = self.distance_calc.calculer_temps_trajet(
            distance_totale, livreur.vitesse_moyenne
        )
        temps_service = sum(commandes[i].temps_service for i in ordre_optimal)
        temps_total = temps_trajet + temps_service
        
        # Calculer le coût
        cout_total = distance_totale * livreur.cout_km
        
        # Heure de retour estimée
        heure_depart_dt = TimeUtils.parse_time(livreur.heure_debut)
        heure_retour_dt = heure_depart_dt + timedelta(minutes=temps_total)
        heure_retour = TimeUtils.format_time(heure_retour_dt)
        
        # Créer les points GPS du trajet
        points_gps = [(livreur.latitude_depart, livreur.longitude_depart)]
        for i in ordre_optimal:
            points_gps.append((commandes[i].latitude, commandes[i].longitude))
        points_gps.append((livreur.latitude_depart, livreur.longitude_depart))
        
        # Créer l'objet Trajet
        trajet = Trajet(
            livreur_id=livreur.id,
            commandes=[commandes[i].id for i in ordre_optimal],
            ordre_livraison=ordre_optimal,
            distance_totale=round(distance_totale, 2),
            temps_total=int(temps_total),
            cout_total=round(cout_total, 2),
            heure_depart=livreur.heure_debut,
            heure_retour_estimee=heure_retour,
            points_gps=points_gps
        )
        
        return trajet
    
    def optimiser_tous_trajets(self, livreurs: List[Livreur], 
                              affectations: Dict[str, List[Commande]]) -> Dict[str, Trajet]:
        """
        Optimise les trajets pour tous les livreurs
        
        Args:
            livreurs: Liste des livreurs
            affectations: Dict[livreur_id] -> List[Commande]
        
        Returns:
            Dict[livreur_id] -> Trajet optimisé
        """
        self.trajets_optimises = {}
        
        for livreur in livreurs:
            commandes = affectations.get(livreur.id, [])
            if commandes:
                trajet = self.optimiser_trajet(livreur, commandes)
                self.trajets_optimises[livreur.id] = trajet
        
        return self.trajets_optimises
    
    def _creer_trajet_vide(self, livreur: Livreur) -> Trajet:
        """Crée un trajet vide pour un livreur sans commandes"""
        return Trajet(
            livreur_id=livreur.id,
            commandes=[],
            ordre_livraison=[],
            distance_totale=0.0,
            temps_total=0,
            cout_total=0.0,
            heure_depart=livreur.heure_debut,
            heure_retour_estimee=livreur.heure_debut,
            points_gps=[]
        )
    
    def obtenir_statistiques(self) -> dict:
        """Retourne les statistiques des trajets optimisés"""
        if not self.trajets_optimises:
            return {}
        
        distances = [t.distance_totale for t in self.trajets_optimises.values()]
        temps = [t.temps_total for t in self.trajets_optimises.values()]
        couts = [t.cout_total for t in self.trajets_optimises.values()]
        
        return {
            'nombre_trajets': len(self.trajets_optimises),
            'distance_totale_km': sum(distances),
            'distance_moyenne_km': sum(distances) / len(distances),
            'temps_total_min': sum(temps),
            'temps_moyen_min': sum(temps) / len(temps),
            'cout_total_euro': sum(couts),
            'algorithme_utilise': self.algorithme
        }
