# src/affectation/branch_and_bound_allocator.py

import math
import numpy as np


class BranchAndBoundAllocator:

    def __init__(self, cost_matrix: np.ndarray):
        self.cost = np.array(cost_matrix, dtype=float)
        self.cost = np.nan_to_num(
            self.cost, nan=9999.0, posinf=9999.0, neginf=9999.0)

        # nombre d'entités à assigner (ici = nb commandes)
        self.n_rows = self.cost.shape[0]
        self.n_cols = self.cost.shape[1]   # nombre de slots disponibles

        self.best_cost = math.inf
        self.best_assignment = [-1] * self.n_rows

        self.used = [False] * self.n_cols

        # row_min pour bound: prend la valeur minimale de chaque ligne (commande)
        # si une ligne est entièrement 9999, min sera 9999 et poussera le LB haut
        if self.n_rows > 0:
            self.row_min = np.min(self.cost, axis=1)
        else:
            self.row_min = np.array([])

    def lower_bound(self, level):
        """Somme minimale des lignes restantes (index level..end)."""
        if level >= self.n_rows:
            return 0.0
        return float(np.sum(self.row_min[level:]))

    def solve(self):
        assignment = [-1] * self.n_rows
        self._branch(0, assignment, 0.0)
        return self.best_assignment, float(self.best_cost) if self.best_cost != math.inf else None

    def _branch(self, row, assignment, current_cost):
        # si on a assigné toutes les lignes
        if row == self.n_rows:
            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_assignment = assignment.copy()
            return

        # bound
        lb = current_cost + self.lower_bound(row)
        if lb >= self.best_cost:
            return

        # parcours des colonnes triées par coût croissant pour cette ligne
        for col in np.argsort(self.cost[row]):
            if self.used[col]:
                continue

            new_cost = current_cost + self.cost[row][col]
            if new_cost >= self.best_cost:
                continue

            # assign
            self.used[col] = True
            assignment[row] = int(col)

            # recursif
            self._branch(row + 1, assignment, new_cost)

            # backtrack
            self.used[col] = False
            assignment[row] = -1
