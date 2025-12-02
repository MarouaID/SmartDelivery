# src/affectation/affectation_manager.py

from typing import List, Dict
import numpy as np
from src.models import Commande, Livreur
from src.utils import DistanceCalculator
from src.affectation.branch_and_bound_allocator import BranchAndBoundAllocator


class AffectationManager:

    def __init__(self):
        self.dist = DistanceCalculator()

    # -------------------------------
    # SCORE [0 – 1]
    # -------------------------------
    def score(self, livreur: Livreur, commande: Commande) -> float:

        if not livreur.disponible:
            return 0

        if commande.poids > livreur.capacite_poids or commande.volume > livreur.capacite_volume:
            return 0

        d = self.dist.haversine(
            livreur.latitude_depart, livreur.longitude_depart,
            commande.latitude, commande.longitude
        )

        score_distance = 1 / (1 + d)
        score_priorite = (4 - commande.priorite) / 3

        return 0.6 * score_distance + 0.4 * score_priorite

    # -------------------------------
    # MATRICE DE COÛT
    # -------------------------------
    def create_cost_matrix(self, livreurs: List[Livreur], commandes: List[Commande]):

        L = len(livreurs)
        C = len(commandes)

        nb_cols = max(L, C) + 3  # ≈ plus stable

        matrix = np.full((L, nb_cols), 9999.0)

        for i, l in enumerate(livreurs):
            for j, c in enumerate(commandes):

                s = self.score(l, c)

                if s > 0:
                    matrix[i][j] = 1 - s  # coût faible si bon score

            # Colonnes fictives
            for j in range(C, nb_cols):
                matrix[i][j] = 1.2

        return matrix

    # -------------------------------
    # BRANCH & BOUND
    # -------------------------------
    def affecter_commandes_branch_and_bound(self, livreurs, commandes):

        cost_matrix = self.create_cost_matrix(livreurs, commandes)

        allocator = BranchAndBoundAllocator(cost_matrix)
        assignment, total_cost = allocator.solve()

        affectations = {l.id: [] for l in livreurs}
        used = set()

        for i_liv, col in enumerate(assignment):

            if col < len(commandes):
                affectations[livreurs[i_liv].id].append(commandes[col])
                used.add(col)

        # commandes non assignées
        non_affectees = [c for k, c in enumerate(commandes) if k not in used]

        return {
            "affectations": affectations,
            "non_affectees": non_affectees,
            "total_cost": total_cost
        }
