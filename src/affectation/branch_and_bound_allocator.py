# src/affectation/branch_and_bound_allocator.py

import math
import numpy as np


class BranchAndBoundAllocator:
    """
    Branch & Bound pour résoudre l'affectation.
    Fonctionne avec matrices rectangulaires (livreurs ≠ commandes).
    Retourne un array assignment[i] = colonne affectée au livreur i.
    """

    def __init__(self, cost_matrix: np.ndarray):
        self.cost = np.array(cost_matrix, dtype=float)

        # Nettoyage pour éviter NaN/inf
        self.cost = np.nan_to_num(
            self.cost, nan=9999.0, posinf=9999.0, neginf=9999.0)

        self.n_rows = self.cost.shape[0]  # nombre de livreurs
        self.n_cols = self.cost.shape[1]  # commandes + colonnes fictives

        self.best_cost = math.inf
        self.best_assignment = [-1] * self.n_rows

        # Colonnes déjà utilisées
        self.used = [False] * self.n_cols

        # borne inférieure par ligne
        self.row_min = np.min(self.cost, axis=1)

    # -------------------------------
    # Borne inférieure
    # -------------------------------
    def lower_bound(self, level):
        if level >= self.n_rows:
            return 0
        return float(np.sum(self.row_min[level:]))

    # -------------------------------
    # Solveur principal
    # -------------------------------
    def solve(self):
        assignment = [-1] * self.n_rows
        self._branch(0, assignment, 0.0)
        return self.best_assignment, float(self.best_cost)

    # -------------------------------
    # Fonction récursive
    # -------------------------------
    def _branch(self, row, assignment, current_cost):

        # Toutes les lignes affectées = solution complète
        if row == self.n_rows:
            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_assignment = assignment.copy()
            return

        # Borne inférieure
        lb = current_cost + self.lower_bound(row)
        if lb >= self.best_cost:
            return  # pruning

        # Explorer les colonnes par coût croissant
        for col in np.argsort(self.cost[row]):

            if self.used[col]:
                continue

            new_cost = current_cost + self.cost[row][col]
            if new_cost >= self.best_cost:
                continue

            # choix
            self.used[col] = True
            assignment[row] = col

            self._branch(row + 1, assignment, new_cost)

            # backtrack
            self.used[col] = False
