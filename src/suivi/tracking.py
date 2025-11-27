
from typing import Dict, List, Optional
from datetime import datetime
from src.models import Trajet, Commande
import time
import random


class ServiceSuivi:
    """Suit l'avancement des livraisons en temps réel"""
    
    def __init__(self):
        self.trajets_actifs = {}  # {livreur_id: état_trajet}
        self.positions_actuelles = {}  # {livreur_id: (lat, lon)}
        self.historique_positions = {}  # {livreur_id: [(lat, lon, timestamp)]}
        self.etats_commandes = {}  # {commande_id: statut}
    
    def demarrer_suivi_trajet(self, livreur_id: str, trajet: Trajet):
        """
        Démarre le suivi d'un trajet
        
        Args:
            livreur_id: ID du livreur
            trajet: Trajet planifié
        """
        self.trajets_actifs[livreur_id] = {
            'trajet': trajet,
            'statut': 'en_cours',
            'commande_actuelle_index': 0,
            'heure_debut': datetime.now().isoformat(),
            'commandes_livrees': [],
            'commandes_restantes': trajet.commandes.copy()
        }
        
        # Initialiser la position au dépôt
        if trajet.points_gps:
            self.positions_actuelles[livreur_id] = trajet.points_gps[0]
            self.historique_positions[livreur_id] = [
                (trajet.points_gps[0][0], trajet.points_gps[0][1], 
                 datetime.now().isoformat())
            ]
        
        print(f"🚀 Suivi démarré pour {livreur_id}: {len(trajet.commandes)} livraisons")
    
    def mettre_a_jour_position(self, livreur_id: str, 
                               latitude: float, 
                               longitude: float):
        """
        Met à jour la position GPS d'un livreur
        
        Args:
            livreur_id: ID du livreur
            latitude: Latitude actuelle
            longitude: Longitude actuelle
        """
        self.positions_actuelles[livreur_id] = (latitude, longitude)
        
        if livreur_id not in self.historique_positions:
            self.historique_positions[livreur_id] = []
        
        self.historique_positions[livreur_id].append(
            (latitude, longitude, datetime.now().isoformat())
        )
    
    def marquer_livraison_effectuee(self, livreur_id: str, commande_id: str) -> bool:
        """
        Marque une commande comme livrée
        
        Returns:
            True si succès, False sinon
        """
        if livreur_id not in self.trajets_actifs:
            return False
        
        etat = self.trajets_actifs[livreur_id]
        
        if commande_id in etat['commandes_restantes']:
            etat['commandes_restantes'].remove(commande_id)
            etat['commandes_livrees'].append({
                'commande_id': commande_id,
                'heure_livraison': datetime.now().isoformat()
            })
            etat['commande_actuelle_index'] += 1
            
            self.etats_commandes[commande_id] = 'livree'
            
            print(f"✅ Livraison {commande_id} effectuée par {livreur_id}")
            
            # Vérifier si tournée terminée
            if not etat['commandes_restantes']:
                self._terminer_trajet(livreur_id)
            
            return True
        
        return False
    
    def _terminer_trajet(self, livreur_id: str):
        """Termine le suivi d'un trajet"""
        if livreur_id in self.trajets_actifs:
            self.trajets_actifs[livreur_id]['statut'] = 'termine'
            self.trajets_actifs[livreur_id]['heure_fin'] = datetime.now().isoformat()
            print(f"🏁 Tournée terminée pour {livreur_id}")
    
    def obtenir_etat_livreur(self, livreur_id: str) -> Optional[dict]:
        """
        Récupère l'état actuel d'un livreur
        
        Returns:
            Dict avec toutes les infos de suivi ou None
        """
        if livreur_id not in self.trajets_actifs:
            return None
        
        etat = self.trajets_actifs[livreur_id]
        position = self.positions_actuelles.get(livreur_id)
        
        return {
            'livreur_id': livreur_id,
            'statut': etat['statut'],
            'position_actuelle': position,
            'commandes_livrees': len(etat['commandes_livrees']),
            'commandes_restantes': len(etat['commandes_restantes']),
            'progression_pourcent': (len(etat['commandes_livrees']) / 
                                    len(etat['trajet'].commandes) * 100 
                                    if etat['trajet'].commandes else 0),
            'heure_debut': etat['heure_debut'],
            'prochaine_livraison': (etat['commandes_restantes'][0] 
                                   if etat['commandes_restantes'] else None)
        }
    
    def obtenir_vue_ensemble(self) -> dict:
        """
        Vue d'ensemble de tous les livreurs actifs
        
        Returns:
            Statistiques globales
        """
        livreurs_actifs = [lid for lid, e in self.trajets_actifs.items() 
                          if e['statut'] == 'en_cours']
        livreurs_termines = [lid for lid, e in self.trajets_actifs.items() 
                            if e['statut'] == 'termine']
        
        total_livraisons = sum(
            len(e['commandes_livrees']) for e in self.trajets_actifs.values()
        )
        total_a_livrer = sum(
            len(e['commandes_restantes']) for e in self.trajets_actifs.values()
        )
        
        return {
            'livreurs_actifs': len(livreurs_actifs),
            'livreurs_termines': len(livreurs_termines),
            'livraisons_effectuees': total_livraisons,
            'livraisons_restantes': total_a_livrer,
            'taux_completion': (total_livraisons / (total_livraisons + total_a_livrer) * 100
                               if (total_livraisons + total_a_livrer) > 0 else 0),
            'livreurs_en_cours': livreurs_actifs
        }
    
    def simuler_progression(self, livreur_id: str, vitesse_simulation: float = 1.0):
        """
        Simule la progression d'un livreur (pour démo/test)
        
        Args:
            livreur_id: ID du livreur
            vitesse_simulation: Multiplicateur de vitesse (1.0 = temps réel)
        """
        if livreur_id not in self.trajets_actifs:
            print(f"❌ Livreur {livreur_id} non suivi")
            return
        
        etat = self.trajets_actifs[livreur_id]
        trajet = etat['trajet']
        
        print(f"🎬 Simulation de la tournée de {livreur_id}...")
        
        for i, commande_id in enumerate(trajet.commandes):
            if etat['statut'] != 'en_cours':
                break
            
            # Simuler le déplacement
            if i < len(trajet.points_gps) - 1:
                position = trajet.points_gps[i + 1]
                self.mettre_a_jour_position(livreur_id, position[0], position[1])
            
            # Temps de trajet simulé
            temps_attente = random.uniform(2, 5) / vitesse_simulation
            time.sleep(temps_attente)
            
            # Marquer comme livrée
            self.marquer_livraison_effectuee(livreur_id, commande_id)
            
            temps_service = random.uniform(1, 3) / vitesse_simulation
            time.sleep(temps_service)
        
        print(f"✅ Simulation terminée pour {livreur_id}")
    
    def obtenir_historique_positions(self, livreur_id: str, 
                                    limite: int = 100) -> List[tuple]:
        """
        Récupère l'historique des positions d'un livreur
        
        Args:
            livreur_id: ID du livreur
            limite: Nombre maximum de positions à retourner
        
        Returns:
            Liste de (lat, lon, timestamp)
        """
        historique = self.historique_positions.get(livreur_id, [])
        return historique[-limite:]
    
    def calculer_distance_parcourue(self, livreur_id: str) -> float:
        """
        Calcule la distance parcourue par un livreur (approximation)
        
        Returns:
            Distance en km
        """
        from src.utils import DistanceCalculator
        
        historique = self.historique_positions.get(livreur_id, [])
        if len(historique) < 2:
            return 0.0
        
        distance_calc = DistanceCalculator()
        distance_totale = 0.0
        
        for i in range(len(historique) - 1):
            lat1, lon1, _ = historique[i]
            lat2, lon2, _ = historique[i + 1]
            distance_totale += distance_calc.haversine(lat1, lon1, lat2, lon2)
        
        return round(distance_totale, 2)
