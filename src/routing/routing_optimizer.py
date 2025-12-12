# src/routing/routing_optimizer.py

from typing import List, Dict, Any, Tuple

from src.models import Commande, Livreur
from src.routing.types import Coord

# Algorithmes heuristiques
from src.routing.algorithms.tsp_nearest import nearest_neighbor_route
from src.routing.algorithms.opt_2opt_3opt import (
    two_opt,
    three_opt,
    route_distance,
)

# OSRM + fonctions autour des bornes
from src.routing.osrm_client import (
    build_osrm_table,
    osrm_route,
    find_nearest_station,
    osrm_distance_to_station,
)

# Chargement des bornes de recharge
from src.routing.recharge_loader import load_recharge_points


# =========================================================
#  Helpers horaires
# =========================================================

def hhmm_to_minutes(hhmm: str) -> int:
    """
    "08:30" -> 510 minutes
    """
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def minutes_to_hhmm(total_min: int) -> str:
    """
    510 -> "08:30"
    """
    total_min = int(total_min)
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"


class RoutingOptimizer:
    """
    Optimiseur de tournée pour un livreur :
    - NN → 2-OPT → 3-OPT sur matrice OSRM (table)
    - OSRM /route pour la distance + durée réelles
    - Gestion de la batterie + insertion de bornes de recharge
    - Gestion de la fin de journée (heure_fin) → commandes reportées
    """

    # =========================================================
    #  FONCTION PRINCIPALE
    # =========================================================
    def generate_route(self, livreur: Livreur, commandes: List[Commande]) -> Dict[str, Any]:
        """
        Génère un trajet optimisé pour un livreur :
        - Heuristique : NN → 2-OPT → 3-OPT
        - OSRM : distance & durée réelles
        - Recharge : si batterie insuffisante
        - Temps de travail limité : commandes reportées au lendemain
        """

        # 1) Coordonnées : dépôt + commandes
        coords: List[Coord] = [
            (livreur.latitude_depart, livreur.longitude_depart)
        ] + [
            (c.latitude, c.longitude) for c in commandes
        ]

        # 2) Matrices OSRM TABLE (distance + durée entre tous les points)
        dist_matrix, time_matrix = build_osrm_table(coords)

        # 3) Nearest Neighbor (solution initiale)
        route_nn = nearest_neighbor_route(dist_matrix, start=0)
        dist_nn = route_distance(route_nn, dist_matrix)

        # 4) 2-OPT
        route_2opt, dist_2opt = two_opt(route_nn, dist_matrix)

        # 5) 3-OPT
        route_3opt, dist_3opt = three_opt(route_2opt, dist_matrix)

        # 6) Conversion indices → IDs (0 = dépôt → on ignore)
        ordre_ids = [
            commandes[i - 1].id for i in route_3opt if i != 0
        ]

        # 7) Calcul OSRM réel + recharges + coupure à la fin de journée
        (
            distance_osrm,
            temps_osrm,
            points_with_stations,
            recharge_events,
            livrees_today,
            reportees,
            end_time_min,
        ) = self._compute_osrm_with_recharge_and_day_limit(
            livreur=livreur,
            coords=coords,
            route_indices=route_3opt,
            commandes=commandes,
        )

        # 8) Construction de la réponse JSON finale
        result: Dict[str, Any] = {
            "livreur_id": livreur.id,
            "commandes": [c.id for c in commandes],

            # Ordre optimal global (calcul heuristique, sans couper la journée)
            "ordre_livraison": ordre_ids,

            # Distances heuristiques (sur la matrice OSRM table)
            "distance_initial": dist_nn,
            "distance_2opt": dist_2opt,
            "distance_3opt": dist_3opt,
            "gain_total": dist_nn - dist_3opt,

            # Valeurs réelles OSRM (avec détours + recharges + coupure jour)
            "distance_osrm": distance_osrm,
            "temps_osrm": temps_osrm,

            # Coût réel basé sur distance OSRM
            "cout": distance_osrm * livreur.cout_km,
            "temps_estime": int(temps_osrm),

            # Trajet complet (dépôt + commandes livrées + bornes)
            "points_gps": points_with_stations,

            # Détails des recharges
            "recharges": recharge_events,

            # Gestion de fin de journée
            "livrees_aujourd_hui": livrees_today,
            "reportees": reportees,
            "heure_debut_tour": getattr(livreur, "heure_debut", "08:00"),
            "heure_fin_tour": minutes_to_hhmm(end_time_min),
        }

        return result

    # =========================================================
    #  FONCTION INTERNE : OSRM + RECHARGE + LIMITE JOURNÉE
    # =========================================================
    def _compute_osrm_with_recharge_and_day_limit(
        self,
        livreur: Livreur,
        coords: List[Coord],
        route_indices: List[int],
        commandes: List[Commande],
    ) -> Tuple[
        float,                  # distance totale OSRM (km)
        float,                  # temps total OSRM (min)
        List[Coord],            # points GPS (avec bornes)
        List[Dict[str, Any]],   # événements de recharge
        List[str],              # commandes livrées aujourd'hui
        List[str],              # commandes reportées
        int                     # heure de fin (en minutes depuis 00:00)
    ]:
        """
        Parcourt l'itinéraire final (route_indices appliqué à coords) :
        - additionne distances & temps via OSRM
        - insère des bornes de recharge si batterie insuffisante
        - s'arrête lorsque l'horaire de travail du livreur est dépassé
        - renvoie :
            * distance totale,
            * temps total,
            * liste des points GPS (dépôt + commandes + bornes),
            * liste des événements de recharge,
            * liste des IDs de commandes livrées,
            * liste des IDs de commandes reportées,
            * heure de fin de tournée (en minutes).
        """

        # -----------  PARAMÈTRES JOURNÉE (horaire de travail) -----------
        heure_debut = getattr(livreur, "heure_debut", "08:00")
        heure_fin = getattr(livreur, "heure_fin", "18:00")

        start_min = hhmm_to_minutes(heure_debut)
        end_min = hhmm_to_minutes(heure_fin)

        current_time_min = start_min

        # -----------  PARAMÈTRES BATTERIE -----------
        batterie_max = getattr(livreur, "batterie_max", 90.0)          # minutes
        batterie = getattr(livreur, "batterie_restante", batterie_max) # minutes
        recharge_rate = getattr(livreur, "recharge_rate", 1.5)         # 1 min branché = 1.5 min récupéré

        # -----------  BORNES DISPONIBLES -----------
        stations = load_recharge_points()

        # -----------  MAPPING index → commande -----------
        index_to_commande: Dict[int, Commande] = {
            i + 1: commandes[i] for i in range(len(commandes))
        }

        total_distance = 0.0
        total_time = 0.0

        points_with_stations: List[Coord] = []
        recharge_events: List[Dict[str, Any]] = []

        livrees_today: List[str] = []
        reportees: List[str] = []

        # Point de départ
        prev_idx = route_indices[0]   # normalement 0 (dépôt)
        prev_coord = coords[prev_idx]
        points_with_stations.append(prev_coord)

        # Parcours de l’itinéraire
        for idx in route_indices[1:]:
            current_coord = coords[idx]
            is_commande = (idx != 0)

            # --------------------------
            # Segment dépôt/borne → point suivant
            # --------------------------
            seg_dist, seg_time = osrm_route([prev_coord, current_coord])

            # Cas extrême : un segment plus long que l'autonomie max
            if seg_time > batterie_max:
                # On signale, mais on essaye quand même (sinon il faudra traiter autrement)
                print(f"[⚠] Segment > batterie_max ({seg_time:.1f} min) pour {livreur.id}")

            # ========================
            # 1) Vérifier la batterie
            # ========================
            if seg_time > batterie:
                # 1) Chercher borne la plus proche du point actuel (prev_coord)
                station = find_nearest_station(prev_coord, stations)

                # 2) Distance & temps pour aller jusqu'à la borne
                detour_dist, detour_time = osrm_distance_to_station(prev_coord, station)

                # 3) Consommer ce trajet vers la borne
                total_distance += detour_dist
                total_time += detour_time
                current_time_min += detour_time
                batterie -= detour_time

                # 4) Temps de recharge nécessaire pour revenir à batterie_max
                manque_autonomie = batterie_max - batterie
                temps_recharge = manque_autonomie / recharge_rate

                total_time += temps_recharge
                current_time_min += temps_recharge
                batterie = batterie_max  # batterie pleine

                # 5) Ajouter la borne aux points GPS
                station_coord: Coord = (station["lat"], station["lon"])
                points_with_stations.append(station_coord)

                # 6) Enregistrer l'événement de recharge
                recharge_events.append({
                    "station_id": station["id"],
                    "station_nom": station.get("nom"),
                    "lat": station["lat"],
                    "lon": station["lon"],
                    "distance_detour_km": detour_dist,
                    "duree_detour_min": detour_time,
                    "temps_recharge_min": temps_recharge,
                    "heure_arrivee": minutes_to_hhmm(current_time_min - temps_recharge),
                    "heure_depart": minutes_to_hhmm(current_time_min),
                })

                # 7) Nouveau point de départ = borne
                prev_coord = station_coord

                # 8) Recalcule du segment borne → point suivant
                seg_dist, seg_time = osrm_route([prev_coord, current_coord])

            # ========================
            # 2) Vérifier l'horaire de fin de journée
            # ========================
            # Si on dépasse l'horaire de travail en ajoutant ce segment -> on arrête ici
            if current_time_min + seg_time > end_min:
                # Toutes les commandes restantes à partir de ce point sont reportées
                # y compris celle-ci (si c'est une commande)
                remaining_ids: List[str] = []

                # idx courant
                if is_commande and idx in index_to_commande:
                    remaining_ids.append(index_to_commande[idx].id)

                # le reste de la route
                for next_idx in route_indices[route_indices.index(idx) + 1:]:
                    if next_idx != 0 and next_idx in index_to_commande:
                        remaining_ids.append(index_to_commande[next_idx].id)

                # On les ajoute dans "reportees"
                reportees.extend(remaining_ids)
                # Fin du parcours
                break

            # ========================
            # 3) On peut faire le segment normalement
            # ========================
            total_distance += seg_dist
            total_time += seg_time
            current_time_min += seg_time
            batterie -= seg_time

            # Ajout du point dans la polyline finale
            points_with_stations.append(current_coord)

            # Si c'est une commande → marquer comme livrée aujourd'hui
            if is_commande and idx in index_to_commande:
                livrees_today.append(index_to_commande[idx].id)

            prev_coord = current_coord

        # Mise à jour éventuelle de la batterie dans l'objet livreur
        try:
            livreur.batterie_restante = batterie
        except Exception:
            pass

        # Heure réelle de fin de tournée (peut être < heure_fin si journée pas remplie)
        end_time_min_effective = current_time_min

        return (
            total_distance,
            total_time,
            points_with_stations,
            recharge_events,
            livrees_today,
            reportees,
            end_time_min_effective,
        )
