from typing import List, Dict, Tuple
import random
from copy import deepcopy

from src.models import Commande, Livreur
from src.utils import DistanceCalculator


class AffectationManager:
    """
    Affectation robuste et explicable.
    Contraintes réelles uniquement : POIDS + DISTANCE + PRIORITÉ.
    """

    def __init__(self, use_clustering: bool = True, random_seed: int = 42):
        self.dist = DistanceCalculator()
        self.use_clustering = use_clustering
        random.seed(random_seed)

    # =====================================================
    # SIMPLE K-MEANS (lat/lon)
    # =====================================================
    def _kmeans(self, points: List[Tuple[float, float]], k: int, iters: int = 10):
        if k <= 0 or not points:
            return []

        centroids = random.sample(points, min(k, len(points)))

        for _ in range(iters):
            clusters = [[] for _ in centroids]

            for p in points:
                idx = min(
                    range(len(centroids)),
                    key=lambda i: self.dist.haversine(
                        p[0], p[1], centroids[i][0], centroids[i][1]
                    )
                )
                clusters[idx].append(p)

            new_centroids = []
            for cl in clusters:
                if not cl:
                    new_centroids.append(random.choice(points))
                else:
                    lat = sum(p[0] for p in cl) / len(cl)
                    lon = sum(p[1] for p in cl) / len(cl)
                    new_centroids.append((lat, lon))

            centroids = new_centroids

        return centroids

    # =====================================================
    # CLUSTER COMMANDES
    # =====================================================
    def clusteriser_commandes(
        self, commandes: List[Commande], k: int
    ) -> List[List[Commande]]:

        if not self.use_clustering or k <= 1 or len(commandes) <= k:
            return [commandes[:]]

        pts = [(c.latitude, c.longitude) for c in commandes]
        centroids = self._kmeans(pts, k)
        clusters = [[] for _ in centroids]

        for c in commandes:
            idx = min(
                range(len(centroids)),
                key=lambda i: self.dist.haversine(
                    c.latitude, c.longitude,
                    centroids[i][0], centroids[i][1]
                )
            )
            clusters[idx].append(c)

        return [cl for cl in clusters if cl]

    # =====================================================
    # CAPACITY CHECK (POIDS UNIQUEMENT)
    # =====================================================
    def _can_add(
        self,
        livreur: Livreur,
        current_cmds: List[Commande],
        cmd: Commande
    ) -> bool:
        total_poids = sum(c.poids for c in current_cmds) + cmd.poids
        return total_poids <= livreur.capacite_poids

    # =====================================================
    # SCORE LIVREUR ↔ COMMANDE
    # =====================================================
    def _score(self, livreur: Livreur, commande: Commande) -> float:
        if not livreur.disponible:
            return -1.0

        # Distance (km)
        d = self.dist.haversine(
            livreur.latitude_depart,
            livreur.longitude_depart,
            commande.latitude,
            commande.longitude
        )

        score_distance = 1.0 / (1.0 + d)

        # Priorité : 1 → 1.0 | 3 → 0.33
        score_priorite = (4 - commande.priorite) / 3.0

        return 0.6 * score_distance + 0.4 * score_priorite

    # =====================================================
    # TSP GREEDY (ORDER DELIVERY)
    # =====================================================
    def _tsp_greedy(
        self,
        livreur: Livreur,
        commandes: List[Commande]
    ) -> List[Commande]:

        if not commandes:
            return []

        remaining = commandes[:]
        ordered = []
        cur_lat, cur_lon = livreur.latitude_depart, livreur.longitude_depart

        while remaining:
            nxt = min(
                remaining,
                key=lambda c: self.dist.haversine(
                    cur_lat, cur_lon,
                    c.latitude, c.longitude
                )
            )
            ordered.append(nxt)
            remaining.remove(nxt)
            cur_lat, cur_lon = nxt.latitude, nxt.longitude

        return ordered

    # =====================================================
    # DISTANCE ESTIMÉE TOTALE
    # =====================================================
    def _distance_total_estime(
        self,
        affectations: Dict[str, List[Commande]],
        livreurs: List[Livreur]
    ) -> float:

        total = 0.0

        for l in livreurs:
            cmds = affectations.get(l.id, [])
            if not cmds:
                continue

            total += self.dist.haversine(
                l.latitude_depart, l.longitude_depart,
                cmds[0].latitude, cmds[0].longitude
            )

            for i in range(len(cmds) - 1):
                total += self.dist.haversine(
                    cmds[i].latitude, cmds[i].longitude,
                    cmds[i + 1].latitude, cmds[i + 1].longitude
                )

        return total

    # =====================================================
    # MAIN AFFECTATION PIPELINE
    # =====================================================
    def affecter_hybrid(
        self,
        livreurs: List[Livreur],
        commandes: List[Commande],
        scenario: str = "normal"
    ) -> Dict:

        if not livreurs or not commandes:
            return {
                "affectations": {},
                "non_affectees": commandes,
                "total_cost": 0.0,
                "score_global": 0.0
            }

        livreurs_c = deepcopy(livreurs)
        commandes_c = deepcopy(commandes)

        k = min(max(1, len(commandes_c) // 20), len(livreurs_c))
        clusters = self.clusteriser_commandes(commandes_c, k)

        affectations: Dict[str, List[Commande]] = {l.id: [] for l in livreurs_c}
        assigned_ids = set()

        # ========= GREEDY ASSIGNMENT =========
        for cluster in clusters:
            for c in cluster:
                best_l = None
                best_score = -1.0

                for l in livreurs_c:
                    if not self._can_add(l, affectations[l.id], c):
                        continue

                    s = self._score(l, c)
                    if s > best_score:
                        best_score = s
                        best_l = l

                if best_l:
                    affectations[best_l.id].append(c)
                    assigned_ids.add(c.id)

        # ========= ORDER ROUTES =========
        for l in livreurs_c:
            affectations[l.id] = self._tsp_greedy(l, affectations[l.id])

        non_affectees = [c for c in commandes_c if c.id not in assigned_ids]
        total_cost = self._distance_total_estime(affectations, livreurs_c)

        return {
            "affectations": affectations,
            "non_affectees": non_affectees,
            "total_cost": round(total_cost, 3),
            "score_global": round(1.0 / (1.0 + total_cost), 6)
        }

    # =====================================================
    # BACKWARD COMPATIBILITY
    # =====================================================
    def affecter_commandes_branch_and_bound(
        self,
        livreurs: List[Livreur],
        commandes: List[Commande],
        scenario: str = "normal"
    ):
        return self.affecter_hybrid(livreurs, commandes, scenario)
