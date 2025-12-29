from typing import List, Dict, Any, Tuple

from src.models import Commande, Livreur
from src.routing.types import Coord

from src.routing.algorithms.tsp_nearest import nearest_neighbor_route
from src.routing.algorithms.opt_2opt_3opt import two_opt, three_opt, route_distance
from src.routing.algorithms.tsp_genetic import genetic_optimize_advanced, GAConfig

from src.routing.osrm_client import (
    build_osrm_table,
    osrm_route,
    osrm_route_geometry,
    find_nearest_station,
    osrm_distance_to_station,
)

from src.routing.recharge_loader import load_recharge_points


# =========================================================
# Helpers horaires
# =========================================================
def hhmm_to_minutes(h):
    hh, mm = map(int, h.split(":"))
    return hh * 60 + mm


def minutes_to_hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


# =========================================================
# ROUTING OPTIMIZER
# =========================================================
class RoutingOptimizer:

    def generate_route(self, livreur: Livreur, commandes: List[Commande]) -> Dict[str, Any]:

        # -------------------------------------------------
        # 1) Coordonnées
        # -------------------------------------------------
        coords: List[Coord] = [
            (livreur.latitude_depart, livreur.longitude_depart)
        ] + [(c.latitude, c.longitude) for c in commandes]

        # -------------------------------------------------
        # 2) Matrices OSRM
        # -------------------------------------------------
        dist_matrix, time_matrix = build_osrm_table(coords)

        # -------------------------------------------------
        # 3) Heuristiques
        # -------------------------------------------------
        route_nn = nearest_neighbor_route(dist_matrix, start=0)
        route_2opt, _ = two_opt(route_nn, dist_matrix)
        route_3opt, _ = three_opt(route_2opt, dist_matrix)

        # -------------------------------------------------
        # 4) Genetic Algorithm (contraintes)
        # -------------------------------------------------
        cfg = GAConfig(
            population_size=80,
            generations=200,
            mutation_rate=0.2,
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
            stations=load_recharge_points(),
            cfg=cfg,
        )

        ordre_ids = [commandes[i - 1].id for i in route_ga if i != 0]

        (
            dist_osrm,
            time_osrm,
            points_gps,
            livrees,
            reportees,
            end_min
        ) = self._compute_osrm(route_ga, coords, livreur, commandes)

        # -------------------------------------------------
        # 5) Géométrie réelle OSRM
        # -------------------------------------------------
        route_geometry = osrm_route_geometry(points_gps)

        # -------------------------------------------------
        # 6) Résultat final
        # -------------------------------------------------
        return {
            "livreur_id": livreur.id,
            "ordre_livraison": ordre_ids,
            "distance_osrm": dist_osrm,
            "temps_osrm": time_osrm,
            "points_gps": points_gps,
            "route_geometry": route_geometry,
            "livrees_aujourd_hui": livrees,
            "reportees": reportees,
            "heure_debut_tour": livreur.heure_debut,
            "heure_fin_tour": minutes_to_hhmm(end_min),
        }

    # =====================================================
    # OSRM + FIN DE JOURNÉE
    # =====================================================
    def _compute_osrm(
        self,
        route_indices: List[int],
        coords: List[Coord],
        livreur: Livreur,
        commandes: List[Commande],
    ) -> Tuple[float, float, List[Coord], List[str], List[str], int]:

        start_min = hhmm_to_minutes(livreur.heure_debut)
        end_min = hhmm_to_minutes(livreur.heure_fin)

        current_time = start_min
        total_dist = 0.0
        total_time = 0.0

        points_gps: List[Coord] = []
        livrees: List[str] = []
        reportees: List[str] = []

        prev = coords[route_indices[0]]
        points_gps.append(prev)

        for idx in route_indices[1:]:
            cur = coords[idx]
            d, t = osrm_route([prev, cur])

            if current_time + t > end_min:
                if idx != 0:
                    reportees.append(commandes[idx - 1].id)
                break

            total_dist += d
            total_time += t
            current_time += t
            points_gps.append(cur)

            if idx != 0:
                livrees.append(commandes[idx - 1].id)

            prev = cur

        return (
            total_dist,
            total_time,
            points_gps,
            livrees,
            reportees,
            int(current_time),
        )
