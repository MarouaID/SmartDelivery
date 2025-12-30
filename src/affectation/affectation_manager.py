from typing import List, Dict
from src.utils import DistanceCalculator
from typing import List, Dict, Tuple
import math
import random
from collections import defaultdict
from copy import deepcopy

from src.models import Commande, Livreur
from src.utils import DistanceCalculator, TimeUtils
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

    # -------------------------
    # K-MEANS léger (2D: lat/lon)
    # -------------------------
    def _kmeans(self, points: List[Tuple[float, float]], k: int, iters: int = 10):
        if k <= 0 or not points:
            return []

        # init centroids: sample k unique points
        centroids = random.sample(points, min(k, len(points)))
        for _ in range(iters):
            clusters = [[] for _ in range(len(centroids))]
            for p in points:
                # find nearest centroid
                best_i = 0
                best_d = float('inf')
                for i, c in enumerate(centroids):
                    d = self.dist.haversine(p[0], p[1], c[0], c[1])
                    if d < best_d:
                        best_d = d
                        best_i = i
                clusters[best_i].append(p)
            # recompute centroids
            new_centroids = []
            for cl in clusters:
                if not cl:
                    # pick a random point as centroid fallback
                    new_centroids.append(random.choice(points))
                else:
                    lat_mean = sum(p[0] for p in cl) / len(cl)
                    lon_mean = sum(p[1] for p in cl) / len(cl)
                    new_centroids.append((lat_mean, lon_mean))
            centroids = new_centroids
        return centroids

    def clusteriser_commandes(self, commandes: List[Commande], k: int) -> List[List[Commande]]:
        if not self.use_clustering or k <= 1 or len(commandes) <= k:
            return [commandes[:]]
        pts = [(c.latitude, c.longitude) for c in commandes]
        centroids = self._kmeans(pts, k)
        clusters = [[] for _ in centroids]
        for c in commandes:
            best_i = 0
            best_d = float('inf')
            for i, cen in enumerate(centroids):
                d = self.dist.haversine(
                    c.latitude, c.longitude, cen[0], cen[1])
                if d < best_d:
                    best_d = d
                    best_i = i
            clusters[best_i].append(c)
        # remove empty clusters
        clusters = [cl for cl in clusters if cl]
        return clusters

    # -------------------------
    # Coût simple entre livreur (slot) et commande
    # -------------------------
    def _cout_slot_cmd(self, slot_origin: Tuple[float, float], cmd: Commande, scenario: str) -> float:
        d = self.dist.haversine(
            slot_origin[0], slot_origin[1], cmd.latitude, cmd.longitude)
        # penalité priorité (urgent small penalty)
        penalite_priorite = {1: 0.0, 2: 2.0, 3: 5.0}.get(cmd.priorite, 2.0)
        coeff = {"normal": 1.0, "pic": 1.3, "incident": 1.7}.get(scenario, 1.0)
        return d + penalite_priorite * coeff

    # -------------------------
    # création des slots (copies) pour matching
    # -------------------------
    def _create_slots(self, livreurs: List[Livreur], nb_slots_per_livreur: int) -> List[Dict]:
        """
        Retourne une liste de slots, chaque slot est dict:
        { 'livreur': Livreur, 'slot_id': str, 'lat': float, 'lon': float, 'capacite_poids': float, 'capacite_volume': float }
        """
        slots = []
        for l in livreurs:
            for s in range(nb_slots_per_livreur):
                slot = {
                    'livreur': l,
                    'slot_id': f"{l.id}_S{s+1}",
                    'lat': l.latitude_depart,
                    'lon': l.longitude_depart,
                    # capacities on slot = livreur capacities initially (we will check real capacities on assignment)
                    'capacite_poids': l.capacite_poids,
                    'capacite_volume': l.capacite_volume,
                }
                slots.append(slot)
        return slots

    # -------------------------
    # Greedy min-cost matching on slots
    # -------------------------
    def _match_slots_greedy(self, slots: List[Dict], commandes: List[Commande], scenario: str):
        """
        Retourne mapping slot_id -> list(Commande)
        Algorithme:
          - calculer toutes les paires (slot, cmd, cost)
          - trier par cost asc
          - pour chaque paire: si commande non affectée AND slot compat (capacité restante selon livreur current assigned cmds) => assigner
        """
        # prepare mapping for capacities per livreur (we track by livreur.id)
        assigned_cmds_by_livreur = defaultdict(list)
        assigned_slots = defaultdict(list)  # slot_id -> cmds

        # precompute costs
        pairs = []
        for si, slot in enumerate(slots):
            origin = (slot['lat'], slot['lon'])
            for cmd in commandes:
                cost = self._cout_slot_cmd(origin, cmd, scenario)
                pairs.append((cost, si, cmd))

        pairs.sort(key=lambda x: x[0])

        assigned_cmds_ids = set()
        for cost, si, cmd in pairs:
            if cmd.id in assigned_cmds_ids:
                continue
            slot = slots[si]
            livreur = slot['livreur']
            # check capacity if add cmd to this livreur (current assigned + this cmd)
            current_cmds = assigned_cmds_by_livreur[livreur.id]
            ok_cap, _ = self.cap_validator.verifier_ajout_commande(
                livreur, current_cmds, cmd)
            if not ok_cap:
                continue
            # check meteo at cmd location
            ok_meteo, _ = self.meteo_validator.valider_conditions(
                [(cmd.latitude, cmd.longitude)])
            if not ok_meteo:
                continue
            # check livreur availability (use start hour)
            ok_h, _ = self.horaire_validator.valider_disponibilite_livreur(
                livreur, livreur.heure_debut)
            if not ok_h:
                continue
            # assign
            assigned_cmds_by_livreur[livreur.id].append(cmd)
            assigned_slots[slot['slot_id']].append(cmd)
            assigned_cmds_ids.add(cmd.id)

        # build final affectations per livreur (merge slots)
        affectations = {slots[0]['livreur'].id: []} if slots else {}
        # safer init
        for s in slots:
            affectations[s['livreur'].id] = []

        for lid, cmds in assigned_cmds_by_livreur.items():
            affectations[lid] = cmds[:]

        # unassigned commands:
        unassigned = [c for c in commandes if c.id not in assigned_cmds_ids]

        return affectations, unassigned

    # -------------------------
    # fallback greedy assign (simple)
    # -------------------------
    def _fallback_greedy(self, livreurs: List[Livreur], remaining_cmds: List[Commande], current_affect: Dict[str, List[Commande]], scenario: str):
        for cmd in remaining_cmds:
            best_l = None
            best_cost = float('inf')
            for l in livreurs:
                ok, _ = self.cap_validator.verifier_ajout_commande(
                    l, current_affect.get(l.id, []), cmd)
                if not ok:
                    continue
                ok_m, _ = self.meteo_validator.valider_conditions(
                    [(cmd.latitude, cmd.longitude)])
                if not ok_m:
                    continue
                cost = self._cout_slot_cmd(
                    (l.latitude_depart, l.longitude_depart), cmd, scenario)
                if cost < best_cost:
                    best_cost = cost
                    best_l = l
            if best_l:
                current_affect.setdefault(best_l.id, []).append(cmd)
        # recalc remaining
        remain = []
        for c in remaining_cmds:
            found = False
            for cmds in current_affect.values():
                if any(cc.id == c.id for cc in cmds):
                    found = True
                    break
            if not found:
                remain.append(c)
        return current_affect, remain

    # -------------------------
    # distance total approx (sum of origin->first + pairwise)
    # -------------------------
    def _distance_total_estime(self, affectations: Dict[str, List[Commande]], livreurs: List[Livreur]) -> float:
        total = 0.0
        for l in livreurs:
            cmds = affectations.get(l.id, [])
            if not cmds:
                continue
            # depot -> first
            total += self.dist.haversine(l.latitude_depart,
                                         l.longitude_depart, cmds[0].latitude, cmds[0].longitude)
            for i in range(len(cmds) - 1):
                total += self.dist.haversine(
                    cmds[i].latitude, cmds[i].longitude, cmds[i+1].latitude, cmds[i+1].longitude)
        return total

    # -------------------------
    # API publique principale
    # -------------------------
    def affecter_hybrid(self, livreurs: List[Livreur], commandes: List[Commande], scenario: str = "normal") -> Dict:
        """
        Pipeline :
          - clustering (k = min(nb_clusters, ...))
          - pour chaque cluster : créer slots et matcher greedily
          - rassembler affectations
          - fallback greedy pour restes
        """
        if not livreurs or not commandes:
            return {"affectations": {}, "non_affectees": commandes, "total_cost": 0.0, "score_global": 0.0}

        # copies (we will not mutate originals)
        livreurs_copy = deepcopy(livreurs)
        commandes_copy = deepcopy(commandes)

        # choose k clusters: heuristic = min(len(commandes)//8 + 1, len(livreurs))
        nb_clusters = min(max(1, len(commandes_copy) //
                          8 + 1), len(livreurs_copy))
        clusters = self.clusteriser_commandes(
            commandes_copy, nb_clusters) if self.use_clustering else [commandes_copy]

        final_affect = {l.id: [] for l in livreurs_copy}
        leftover = []

        # for each cluster, build slots and match
        for cluster in clusters:
            if not cluster:
                continue
            # decide slots per livreur: ceil(len(cluster)/len(livreurs)) but cap to 6 to avoid explosion
            slots_per_l = max(1, math.ceil(len(cluster) / len(livreurs_copy)))
            slots_per_l = min(slots_per_l, 6)

            slots = self._create_slots(livreurs_copy, slots_per_l)
            cluster_affect, unassigned = self._match_slots_greedy(
                slots, cluster, scenario)

            # merge cluster_affect into final_affect (respect capacities via verifier_ajout_commande)
            for lid, cmds in cluster_affect.items():
                for cmd in cmds:
                    ok, _ = self.cap_validator.verifier_ajout_commande(
                        next(l for l in livreurs_copy if l.id == lid), final_affect[lid], cmd)
                    if ok:
                        final_affect[lid].append(cmd)
                    else:
                        unassigned.append(cmd)

            leftover.extend(unassigned)

        # fallback greedy on leftover
        if leftover:
            final_affect, still_left = self._fallback_greedy(
                livreurs_copy, leftover, final_affect, scenario)
        else:
            still_left = []

        # compute outputs
        total_cost = self._distance_total_estime(final_affect, livreurs_copy)
        # compute score global simple
        # score distance
        score_distance = 1.0 / (1.0 + total_cost)
        total_prior = sum((4 - c.priorite)
                          for cmds in final_affect.values() for c in cmds)
        nb_cmds = sum(len(cmds) for cmds in final_affect.values())
        score_prior = (total_prior / (nb_cmds + 1e-9)) / 3.0
        loads = [len(cmds)
                 for cmds in final_affect.values()] if final_affect else [0]
        score_equilibre = (min(loads) / max(loads)) if max(loads) > 0 else 1.0
        score_global = 0.45 * score_distance + 0.45 * score_prior + 0.1 * score_equilibre

        return {
            "affectations": final_affect,
            "non_affectees": still_left,
            "total_cost": float(round(total_cost, 4)),
            "score_global": float(score_global)
        }

    # backward-compatible name used in project
    def affecter_commandes_branch_and_bound(self, livreurs, commandes, scenario="normal"):
        return self.affecter_hybrid(livreurs, commandes, scenario)


class AffectationManager:

    def __init__(self):
        self.dist = DistanceCalculator()
        self.cap = ValidateurCapacites()
        self.horaires = ValidateurHoraires()
        self.meteo = ValidateurMeteo()

    # --------------------------------------------------------
    # 1) COÛT MULTI-CRITÈRES
    # --------------------------------------------------------
    def cout_multi_criteres(self, livreur, commande, scenario: str) -> float:

        # Distance depuis le dépôt
        dist = self.dist.haversine(
            livreur.latitude_depart,
            livreur.longitude_depart,
            commande.latitude,
            commande.longitude
        )

        # Priorité
        penalite_priorite = {
            1: 0,
            2: 3,
            3: 7
        }[commande.priorite]

        # Poids dans le véhicule
        # (on pénalise les livreurs déjà très remplis)
        ratio_charge = commande.poids / (livreur.capacite_poids + 1)

        # Scénario
        coeff_scenario = {
            "normal": 1.0,
            "pic": 1.5,
            "incident": 1.9
        }.get(scenario, 1.0)

        # Score final pondéré
        return (
            dist * 1.0 +
            penalite_priorite * 1.2 +
            ratio_charge * 5.0
        ) * coeff_scenario

    # --------------------------------------------------------
    # 2) AFFECTATION MULTI-CRITÈRES OPTIMISÉE
    # --------------------------------------------------------
    def affecter_multi_criteres(self, livreurs: List[Livreur],
                                commandes: List[Commande],
                                scenario="normal") -> Dict:

        # On triple trie : priorité → poids → distance
        commandes_triees = sorted(
            commandes,
            key=lambda c: (c.priorite, -c.poids)
        )

        affect = {l.id: [] for l in livreurs}
        non_affectees = []

        for cmd in commandes_triees:

            meilleur_livreur = None
            meilleur_score = float("inf")

            for liv in livreurs:

                # --------- Contraintes ------------
                ok_cap, _ = self.cap.verifier_ajout_commande(
                    liv, affect[liv.id], cmd)
                if not ok_cap:
                    continue

                ok_hor, _ = self.horaires.valider_disponibilite_livreur(
                    liv, liv.heure_debut)
                if not ok_hor:
                    continue

                ok_met, _ = self.meteo.valider_conditions(
                    [(cmd.latitude, cmd.longitude)])
                if not ok_met:
                    continue

                # --------- Score Multi-Critères -----
                score = self.cout_multi_criteres(liv, cmd, scenario)

                if score < meilleur_score:
                    meilleur_score = score
                    meilleur_livreur = liv

            # -------- Affectation -----------
            if meilleur_livreur:
                affect[meilleur_livreur.id].append(cmd)
            else:
                non_affectees.append(cmd)

        # Calcul du coût total final
        total_cost = 0
        for liv in livreurs:
            for cmd in affect[liv.id]:
                total_cost += self.dist.haversine(
                    liv.latitude_depart, liv.longitude_depart,
                    cmd.latitude, cmd.longitude
                )

        return {
            "affectations": affect,
            "non_affectees": non_affectees,
            "total_cost": round(total_cost, 3)
        }

    # Compatibilité avec ancien nom
    def affecter_commandes_branch_and_bound(self, livreurs, commandes, scenario="normal"):
        return self.affecter_multi_criteres(livreurs, commandes, scenario)