# src/routing/routing_optimizer.py

from typing import List, Dict, Any, Tuple

from src.models import Commande, Livreur
from src.routing.types import Coord

# Heuristiques classiques
from src.routing.algorithms.tsp_nearest import nearest_neighbor_route
from src.routing.algorithms.opt_2opt_3opt import (
    two_opt,
    three_opt,
    route_distance,
)

# Genetic Algorithm avancé (avec contraintes)
from src.routing.algorithms.tsp_genetic import (
    genetic_optimize_advanced,
    GAConfig,
)

# OSRM + recharge
from src.routing.osrm_client import (
    build_osrm_table,
    osrm_route,
    find_nearest_station,
    osrm_distance_to_station,
)

from src.routing.recharge_loader import load_recharge_points


# =========================================================
#  Helpers horaires
# =========================================================
def hhmm_to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def minutes_to_hhmm(total_min: int) -> str:
    total_min = int(total_min)
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"


# =========================================================
#  ROUTING OPTIMIZER
# =========================================================
class RoutingOptimizer:
    """
    Pipeline complet :
    NN → 2-OPT → 3-OPT → GA avancé (contraintes métier)
    Puis calcul OSRM réel avec batterie + recharge + fin de journée
    """

    # =====================================================
    #  FONCTION PRINCIPALE
    # =====================================================
    def generate_route(self, livreur: Livreur, commandes: List[Commande]) -> Dict[str, Any]:

        # -------------------------------------------------
        # 1) Coordonnées (dépôt + commandes)
        # -------------------------------------------------
        coords: List[Coord] = [
            (livreur.latitude_depart, livreur.longitude_depart)
        ] + [(c.latitude, c.longitude) for c in commandes]

        # -------------------------------------------------
        # 2) Matrices OSRM TABLE
        # -------------------------------------------------
        dist_matrix, time_matrix = build_osrm_table(coords)

        # -------------------------------------------------
        # 3) NN
        # -------------------------------------------------
        route_nn = nearest_neighbor_route(dist_matrix, start=0)
        dist_nn = route_distance(route_nn, dist_matrix)

        # -------------------------------------------------
        # 4) 2-OPT
        # -------------------------------------------------
        route_2opt, dist_2opt = two_opt(route_nn, dist_matrix)

        # -------------------------------------------------
        # 5) 3-OPT
        # -------------------------------------------------
        route_3opt, dist_3opt = three_opt(route_2opt, dist_matrix)

        # -------------------------------------------------
        # 6) GENETIC ALGORITHM AVANCÉ (contraintes)
        # -------------------------------------------------
        stations = load_recharge_points()

        cfg = GAConfig(
            population_size=80,
            generations=250,
            mutation_rate=0.20,
            elite_ratio=0.12,
            tournament_k=4,
            random_immigrants_ratio=0.08,
            seed=None,
        )

        route_ga = genetic_optimize_advanced(
            seed_route=route_3opt,
            coords=coords,
            commandes=commandes,
            livreur=livreur,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            stations=stations,
            cfg=cfg,
        )

        dist_ga = route_distance(route_ga, dist_matrix)

        # -------------------------------------------------
        # 7) Ordre final des commandes (GA)
        # -------------------------------------------------
        ordre_ids = [
            commandes[i - 1].id for i in route_ga if i != 0
        ]

        # -------------------------------------------------
        # 8) OSRM réel + batterie + recharge + fin journée
        # -------------------------------------------------
        (
            distance_osrm,
            temps_osrm,
            points_gps,
            recharge_events,
            livrees_today,
            reportees,
            end_time_min,
        ) = self._compute_osrm_with_recharge_and_day_limit(
            livreur=livreur,
            coords=coords,
            route_indices=route_ga,
            commandes=commandes,
        )

        # -------------------------------------------------
        # 9) JSON final
        # -------------------------------------------------
        return {
            "livreur_id": livreur.id,

            # Commandes
            "commandes": [c.id for c in commandes],
            "ordre_livraison": ordre_ids,

            # Distances heuristiques
            "distance_initial": dist_nn,
            "distance_2opt": dist_2opt,
            "distance_3opt": dist_3opt,

            # Genetic
            "distance_genetic": dist_ga,
            "gain_total": dist_nn - dist_ga,

            # OSRM réel
            "distance_osrm": distance_osrm,
            "temps_osrm": temps_osrm,

            # Coût
            "cout": distance_osrm * livreur.cout_km,
            "temps_estime": int(temps_osrm),

            # Trajet réel
            "points_gps": points_gps,

            # Recharge
            "recharges": recharge_events,

            # Fin de journée
            "livrees_aujourd_hui": livrees_today,
            "reportees": reportees,
            "heure_debut_tour": livreur.heure_debut,
            "heure_fin_tour": minutes_to_hhmm(end_time_min),
        }

    # =====================================================
    #  OSRM + RECHARGE + FIN DE JOURNÉE
    # =====================================================
    def _compute_osrm_with_recharge_and_day_limit(
        self,
        livreur: Livreur,
        coords: List[Coord],
        route_indices: List[int],
        commandes: List[Commande],
    ) -> Tuple[
        float,
        float,
        List[Coord],
        List[Dict[str, Any]],
        List[str],
        List[str],
        int,
    ]:

        # Horaires
        start_min = hhmm_to_minutes(livreur.heure_debut)
        end_min = hhmm_to_minutes(livreur.heure_fin)
        current_time = float(start_min)

        # Batterie
        batterie_max = getattr(livreur, "batterie_max", 90.0)
        batterie = getattr(livreur, "batterie_restante", batterie_max)
        recharge_rate = getattr(livreur, "recharge_rate", 1.5)

        stations = load_recharge_points()

        index_to_commande = {i + 1: commandes[i] for i in range(len(commandes))}

        total_distance = 0.0
        total_time = 0.0

        points_gps: List[Coord] = []
        recharge_events: List[Dict[str, Any]] = []

        livrees_today: List[str] = []
        reportees: List[str] = []

        prev_coord = coords[route_indices[0]]
        points_gps.append(prev_coord)

        for pos in range(1, len(route_indices)):
            idx = route_indices[pos]
            current_coord = coords[idx]
            is_cmd = idx != 0

            seg_dist, seg_time = osrm_route([prev_coord, current_coord])

            # Recharge si nécessaire
            if seg_time > batterie:
                station = find_nearest_station(prev_coord, stations)
                detour_dist, detour_time = osrm_distance_to_station(prev_coord, station)

                total_distance += detour_dist
                total_time += detour_time
                current_time += detour_time
                batterie -= detour_time

                recharge_time = (batterie_max - batterie) / recharge_rate
                total_time += recharge_time
                current_time += recharge_time
                batterie = batterie_max

                station_coord = (station["lat"], station["lon"])
                points_gps.append(station_coord)

                recharge_events.append({
                    "station_id": station["id"],
                    "station_nom": station.get("nom"),
                    "lat": station["lat"],
                    "lon": station["lon"],
                    "temps_recharge_min": recharge_time,
                })

                prev_coord = station_coord
                seg_dist, seg_time = osrm_route([prev_coord, current_coord])

            # Fin de journée
            if current_time + seg_time > end_min:
                for j in route_indices[pos:]:
                    if j != 0:
                        reportees.append(index_to_commande[j].id)
                break

            # Segment normal
            total_distance += seg_dist
            total_time += seg_time
            current_time += seg_time
            batterie -= seg_time

            points_gps.append(current_coord)

            if is_cmd:
                livrees_today.append(index_to_commande[idx].id)

            prev_coord = current_coord

        livreur.batterie_restante = batterie

        return (
            total_distance,
            total_time,
            points_gps,
            recharge_events,
            livrees_today,
            reportees,
            int(current_time),
        )
