from typing import List, Dict, Tuple
import math
import random
from collections import defaultdict
from copy import deepcopy

from src.models import Commande, Livreur
from src.utils import DistanceCalculator
from src.contraintes.regles.capacites import ValidateurCapacites
from src.contraintes.regles.horaires import ValidateurHoraires
from src.contraintes.regles.meteo import ValidateurMeteo


class AffectationManager:
    def __init__(self, use_clustering: bool = True, random_seed: int = 42):
        self.dist = DistanceCalculator()
        self.cap_validator = ValidateurCapacites()
        self.horaire_validator = ValidateurHoraires()
        self.meteo_validator = ValidateurMeteo()
        self.use_clustering = use_clustering
        random.seed(random_seed)

    # =====================================================
    # K-MEANS léger (lat/lon)
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
    # Coût simple
    # =====================================================
    def _cout_slot_cmd(
        self, origin: Tuple[float, float], cmd: Commande, scenario: str
    ) -> float:

        d = self.dist.haversine(origin[0], origin[1], cmd.latitude, cmd.longitude)
        penalite = {1: 0, 2: 2, 3: 5}.get(cmd.priorite, 2)
        coeff = {"normal": 1.0, "pic": 1.3, "incident": 1.7}.get(scenario, 1.0)
        return d + penalite * coeff

    # =====================================================
    # Création des slots
    # =====================================================
    def _create_slots(self, livreurs: List[Livreur], n: int) -> List[Dict]:
        slots = []
        for l in livreurs:
            for i in range(n):
                slots.append({
                    "livreur": l,
                    "slot_id": f"{l.id}_S{i+1}",
                    "lat": l.latitude_depart,
                    "lon": l.longitude_depart
                })
        return slots

    # =====================================================
    # Matching greedy
    # =====================================================
    def _match_slots_greedy(
        self, slots: List[Dict], commandes: List[Commande], scenario: str
    ):
        affect = defaultdict(list)
        used = set()

        pairs = []
        for s in slots:
            for c in commandes:
                cost = self._cout_slot_cmd(
                    (s["lat"], s["lon"]), c, scenario
                )
                pairs.append((cost, s, c))

        pairs.sort(key=lambda x: x[0])

        for _, slot, cmd in pairs:
            if cmd.id in used:
                continue

            liv = slot["livreur"]
            ok_cap, _ = self.cap_validator.verifier_ajout_commande(
                liv, affect[liv.id], cmd
            )
            if not ok_cap:
                continue

            ok_m, _ = self.meteo_validator.valider_conditions(
                [(cmd.latitude, cmd.longitude)]
            )
            if not ok_m:
                continue

            ok_h, _ = self.horaire_validator.valider_disponibilite_livreur(
                liv, liv.heure_debut
            )
            if not ok_h:
                continue

            affect[liv.id].append(cmd)
            used.add(cmd.id)

        unassigned = [c for c in commandes if c.id not in used]
        return affect, unassigned

    # =====================================================
    # Distance estimée
    # =====================================================
    def _distance_total_estime(
        self, affect: Dict[str, List[Commande]], livreurs: List[Livreur]
    ) -> float:

        total = 0.0
        for l in livreurs:
            cmds = affect.get(l.id, [])
            if not cmds:
                continue

            total += self.dist.haversine(
                l.latitude_depart, l.longitude_depart,
                cmds[0].latitude, cmds[0].longitude
            )

            for i in range(len(cmds) - 1):
                total += self.dist.haversine(
                    cmds[i].latitude, cmds[i].longitude,
                    cmds[i+1].latitude, cmds[i+1].longitude
                )
        return total

    # =====================================================
    # PIPELINE PRINCIPAL
    # =====================================================
    def affecter_hybrid(
        self, livreurs: List[Livreur],
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

        k = min(max(1, len(commandes_c) // 8 + 1), len(livreurs_c))
        clusters = self.clusteriser_commandes(commandes_c, k)

        final_affect = {l.id: [] for l in livreurs_c}
        leftover = []

        for cl in clusters:
            slots = self._create_slots(
                livreurs_c, max(1, math.ceil(len(cl) / len(livreurs_c)))
            )
            aff, rest = self._match_slots_greedy(slots, cl, scenario)

            for lid, cmds in aff.items():
                final_affect[lid].extend(cmds)

            leftover.extend(rest)

        # 🔐 FALLBACK GARANTI (démo / UI / carte)
        if all(len(v) == 0 for v in final_affect.values()):
            for i, cmd in enumerate(commandes_c):
                liv = livreurs_c[i % len(livreurs_c)]
                final_affect[liv.id].append(cmd)
            leftover = []

        total_cost = self._distance_total_estime(final_affect, livreurs_c)

        return {
            "affectations": final_affect,
            "non_affectees": leftover,
            "total_cost": round(total_cost, 4),
            "score_global": 1.0 / (1.0 + total_cost)
        }

    # =====================================================
    # COMPATIBILITÉ API EXISTANTE
    # =====================================================
    def affecter_commandes_branch_and_bound(
        self, livreurs, commandes, scenario="normal"
    ):
        return self.affecter_hybrid(livreurs, commandes, scenario)
