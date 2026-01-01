from typing import List, Dict, Any, Tuple

from src.models import Commande, Livreur
from src.routing.types import Coord

from src.routing.algorithms.tsp_nearest import nearest_neighbor_route
from src.routing.algorithms.opt_2opt_3opt import two_opt, three_opt
from src.routing.algorithms.tsp_genetic import genetic_optimize_advanced, GAConfig

from src.routing.osrm_client import (
    build_osrm_table,
    osrm_route_full,   
)

# =========================================================
# Helpers horaires
# =========================================================
def hhmm_to_minutes(h: str) -> int:
    hh, mm = map(int, h.split(":"))
    return hh * 60 + mm


def minutes_to_hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


# =========================================================
# ROUTING OPTIMIZER
# =========================================================
class RoutingOptimizer:
    """
    Routing pur (APRÈS affectation) :
    - ordre des livraisons
    - distance
    - durée
    - coût

     aucune contrainte capacité ici
    """

    def generate_route(
        self,
        livreur: Livreur,
        commandes: List[Commande]
    ) -> Dict[str, Any]:

        print("\n>>> generate_route()")
        print("Livreur:", livreur.id)
        print("Nb commandes:", len(commandes))

        # -------------------------------------------------
        # 1) DEPOT UNIQUE + commandes
        # -------------------------------------------------
        coords: List[Coord] = [
            (livreur.latitude_depart, livreur.longitude_depart)
        ] + [(c.latitude, c.longitude) for c in commandes]

        # -------------------------------------------------
        # 2) OSRM table (rapide, heuristiques)
        # -------------------------------------------------
        dist_matrix, time_matrix = build_osrm_table(coords)

        # -------------------------------------------------
        # 3) Heuristiques (ORDRE UNIQUEMENT)
        # -------------------------------------------------
        route_nn = nearest_neighbor_route(dist_matrix, start=0)
        route_2opt, _ = two_opt(route_nn, dist_matrix)
        route_3opt, _ = three_opt(route_2opt, dist_matrix)

        # -------------------------------------------------
        # 4) Genetic Algorithm
        # -------------------------------------------------
        cfg = GAConfig(
            population_size=60,
            generations=150,
            mutation_rate=0.15,
            elite_ratio=0.1,
            tournament_k=4,
            random_immigrants_ratio=0.1,
        )

        route_ga = genetic_optimize_advanced(
            seed_route=route_3opt,
            coords=coords,
            commandes=commandes,
            livreur=livreur,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            stations=[],
            cfg=cfg,
        )

        # -------------------------------------------------
        # 5) ORDRES POUR TOUS LES ALGOS
        # -------------------------------------------------
        solutions: Dict[str, List[int]] = {
            "nearest": route_nn,
            "2opt": route_2opt,
            "3opt": route_3opt,
            "genetic": route_ga,
        }

        # -------------------------------------------------
        # 6) OSRM COMPLET POUR CHAQUE ALGORITHME (CORRECT)
        # -------------------------------------------------
        meta_solutions: Dict[str, Any] = {}

        for algo, route_idx in solutions.items():

            ordered_coords = [coords[i] for i in route_idx]

            osrm = osrm_route_full(ordered_coords)

            cost = osrm["distance_km"] * float(getattr(livreur, "cout_km", 0.0) or 0.0)

            # distance estimée via table (comparaison)
            dist_est = sum(
                dist_matrix[route_idx[i]][route_idx[i + 1]]
                for i in range(len(route_idx) - 1)
            )

            meta_solutions[algo] = {
                "algo": algo,
                "distance_estimee": round(dist_est, 2),
                "distance_km": round(osrm["distance_km"], 2),
                "duree_min": int(osrm["duration_min"]),
                "cost": round(cost, 2),
                "route_geometry": osrm["geometry"],  
                "ordre_ids": [
                    commandes[i - 1].id for i in route_idx if i != 0
                ],
            }

        # -------------------------------------------------
        # 7) GA = solution principale (compatibilité)
        # -------------------------------------------------
        chosen = meta_solutions["genetic"]

        print("Chosen algo: genetic")
        print("Distance km:", chosen["distance_km"])
        print("Durée min:", chosen["duree_min"])
        print("Coût:", chosen["cost"])
        print("<<< generate_route()\n")

        # -------------------------------------------------
        # 8) FORMAT FINAL
        # -------------------------------------------------
        return {
            "livreur_id": livreur.id,

            # anciens champs (dashboard existant)
            "ordre_livraison": chosen["ordre_ids"],
            "distance_km": chosen["distance_km"],
            "duree_min": chosen["duree_min"],
            "cost": chosen["cost"],
            "route_geometry": chosen["route_geometry"],

            # NOUVEAU : toutes les solutions
            "meta_solutions": meta_solutions,
        }
