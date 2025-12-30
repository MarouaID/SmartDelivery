#Affectation
from typing import List, Dict
import numpy as np
from sklearn.cluster import KMeans
from src.models import Commande, Livreur
from src.utils import DistanceCalculator


class AffectationManager:

    def __init__(self, num_zones: int = 50):
        self.dist = DistanceCalculator()
        self.num_zones = num_zones

    # =========================
    # SCORE [0 – 1]
    # =========================
    def score(self, livreur: Livreur, commande: Commande) -> float:
        if not livreur.disponible:
            return 0
        if commande.poids > livreur.capacite_poids:
            return 0
        if commande.volume > livreur.capacite_volume:
            return 0

        d = self.dist.haversine(
            livreur.latitude_depart,
            livreur.longitude_depart,
            commande.latitude,
            commande.longitude
        )
        score_distance = 1 / (1 + d)
        score_priorite = (4 - commande.priorite) / 3
        return 0.6 * score_distance + 0.4 * score_priorite

    # =========================
    # OPTIMISATION TSP GREEDY
    # =========================
    def optimize_tour_greedy(self, livreur: Livreur, commandes: List[Commande]) -> List[Commande]:
        tour = []
        remaining = commandes.copy()
        cur_lat = livreur.latitude_depart
        cur_lon = livreur.longitude_depart

        while remaining:
            next_c = min(
                remaining,
                key=lambda c: self.dist.haversine(cur_lat, cur_lon, c.latitude, c.longitude)
            )
            tour.append(next_c)
            remaining.remove(next_c)
            cur_lat, cur_lon = next_c.latitude, next_c.longitude

        return tour

    # =========================
    # CLUSTERING DES COMMANDES
    # =========================
    def cluster_commandes(self, commandes: List[Commande]):
        if len(commandes) <= self.num_zones:
            # Chaque commande devient sa propre zone
            return {i: [c] for i, c in enumerate(commandes)}

        coords = np.array([(c.latitude, c.longitude) for c in commandes])
        kmeans = KMeans(n_clusters=self.num_zones, random_state=42, n_init=10).fit(coords)
        zones = {i: [] for i in range(self.num_zones)}
        for idx, label in enumerate(kmeans.labels_):
            zones[label].append(commandes[idx])
        return zones

    # =========================
    # PIPELINE SCALABLE
    # =========================
    def affectation_scalable(self, livreurs: List[Livreur], commandes: List[Commande]) -> Dict[str, List[Commande]]:
        affectations = {l.id: [] for l in livreurs}

        # Cluster des commandes
        zones = self.cluster_commandes(commandes)

        # Affectation greedy par zone
        for zone_cmds in zones.values():
            for c in zone_cmds:
                # Choisir le meilleur livreur disponible
                best_l = max(
                    [l for l in livreurs if l.disponible
                     and l.capacite_poids >= c.poids
                     and l.capacite_volume >= c.volume],
                    key=lambda l: self.score(l, c),
                    default=None
                )
                if best_l:
                    affectations[best_l.id].append(c)

        # Optimisation TSP locale pour chaque livreur
        for l in livreurs:
            affectations[l.id] = self.optimize_tour_greedy(l, affectations[l.id])

        return affectations