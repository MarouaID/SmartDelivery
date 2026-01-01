# ============================================================
#  Gestion avancée de la batterie : insertion de bornes
# ============================================================

from typing import List, Tuple
from src.routing.osrm_client import osrm_route


# Durée maximale d'autonomie (en minutes)
BATTERY_LIMIT_MIN = 90


def find_best_recharge_point(current_coord, next_coord, charge_points):
    """
    Trouver la borne de recharge la plus proche d’un segment.
    """
    best_point = None
    best_dist = float("inf")

    for p in charge_points:
        dist, _ = osrm_route([current_coord, p])
        if dist < best_dist:
            best_dist = dist
            best_point = p
    
    return best_point


def simulate_battery_and_insert_stops(coords: List[Tuple[float, float]],
                                      charge_points: List[Tuple[float, float]]):
    """
    Simule le trajet segment par segment.
    Insère des bornes si la durée cumulée dépasse BATTERY_LIMIT_MIN.
    Retourne :
      - new_coords : la liste des points (avec bornes insérées)
      - stops : liste des recharges effectuées (coordonnées)
    """

    new_coords = [coords[0]]
    recharge_stops = []

    battery_time = 0  # en minutes

    for i in range(1, len(coords)):
        A = new_coords[-1]
        B = coords[i]

        # Durée réelle du segment A → B
        dist, duration = osrm_route([A, B])

        # Regarder si batterie OK
        if battery_time + duration > BATTERY_LIMIT_MIN:

            # On doit insérer une borne AVANT B
            best_stop = find_best_recharge_point(A, B, charge_points)

            if best_stop is None:
                raise Exception("Aucune borne de recharge disponible !")

            # Ajouter borne
            new_coords.append(best_stop)
            recharge_stops.append(best_stop)

            # Batterie remise à 0 après recharge
            battery_time = 0

            # Recalculer A → B après recharge
            dist, duration = osrm_route([best_stop, B])

        # Ajouter B normal
        new_coords.append(B)

        # Mettre à jour batterie
        battery_time += duration

    return new_coords, recharge_stops
