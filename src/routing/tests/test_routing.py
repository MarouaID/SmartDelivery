# src/routing/tests/test_routing.py

from src.routing.osrm_client import build_osrm_table, osrm_route_segment
from src.routing.algorithms.tsp_nearest import nearest_neighbor_route
from src.routing.algorithms.opt_2opt_3opt import two_opt, three_opt, route_distance
from src.models import Commande, Livreur
import numpy as np


def generate_commandes(prefix: str, base_lat: float, base_lon: float):
    """Génère 10 commandes chaotiques autour d’un point."""
    commandes = []
    for i in range(10):
        commandes.append(
            Commande(
                id=f"{prefix}{i+1}",
                adresse=f"Adresse {prefix}{i+1}",
                latitude=base_lat + (i % 5) * np.random.uniform(0.01, 0.04) + i * np.random.uniform(0.0004, 0.0007),
                longitude=base_lon + (i % 3) * np.random.uniform(0.015, 0.035) - i * np.random.uniform(0.0006, 0.0008),
                poids=5,
                volume=0.1,
                fenetre_debut="08:00",
                fenetre_fin="20:00",
                priorite=1,
                temps_service=5
            )
        )
    return commandes


def test_livreur_routing(livreur, commandes):
    """Test complet : NN, 2-OPT, 3-OPT + OSRM time & distance."""

    # --- Coordonnées (livreur + commandes)
    coords = [(livreur.latitude_depart, livreur.longitude_depart)] + \
             [(c.latitude, c.longitude) for c in commandes]

    # --- MATRICES OSRM (distance + durée réelles)
    dist_matrix, time_matrix = build_osrm_table(coords)

    # --- Nearest Neighbor
    route_nn = nearest_neighbor_route(dist_matrix, start=0)
    dist_nn = route_distance(route_nn, dist_matrix)

    # --- 2-OPT
    route_2opt, dist_2 = two_opt(route_nn, dist_matrix)

    # --- 3-OPT
    route_3opt, dist_3 = three_opt(route_2opt, dist_matrix)

    # --- Distance & temps OSRM réels (segment par segment)
    real_distance = 0
    real_duration = 0

    for i in range(len(route_3opt) - 1):
        a = coords[route_3opt[i]]
        b = coords[route_3opt[i + 1]]
        seg_dist, seg_time = osrm_route_segment(a, b)
        real_distance += seg_dist
        real_duration += seg_time

    # --- Affichage
    print("\n============================================")
    print(f"🚚 LIVREUR {livreur.id} - {livreur.nom}")
    print("============================================\n")

    print("📦 Nombre de commandes :", len(commandes))
    print("--------------------------------------------")

    print(f"🔹 Nearest Neighbor   : {round(dist_nn, 3)} km")
    print(f"🔹 Après 2-OPT        : {round(dist_2, 3)} km")
    print(f"🔹 Après 3-OPT        : {round(dist_3, 3)} km")
    print(f"🔹 Distance OSRM réelle : {round(real_distance, 3)} km")
    print("--------------------------------------------")

    estimate = int((dist_3 / livreur.vitesse_moyenne) * 60)
    print(f"⏱ Temps estimé (simple vitesse livreur) : {estimate} min")
    print(f"⏱ Temps OSRM réel                      : {round(real_duration, 2)} min")

    print("--------------------------------------------")
    print("📉 Gain total :", round(dist_nn - dist_3, 3), "km")
    print("--------------------------------------------")
    print("➡ Ordre final 3-OPT :", route_3opt)
    print("============================================\n")


if __name__ == "__main__":
    # ========== 5 livreurs ==========
    livreurs = [
        Livreur("L1", "Livreur_1", 31.6300, -7.9900, 250, 2.0, "08:00", "18:00", 40, 0.5),
        Livreur("L2", "Livreur_2", 31.6280, -7.9870, 250, 2.0, "08:00", "18:00", 40, 0.5),
        Livreur("L3", "Livreur_3", 31.6330, -7.9920, 250, 2.0, "08:00", "18:00", 40, 0.5),
        Livreur("L4", "Livreur_4", 31.6315, -7.9855, 250, 2.0, "08:00", "18:00", 40, 0.5),
        Livreur("L5", "Livreur_5", 31.6295, -7.9935, 250, 2.0, "08:00", "18:00", 40, 0.5),
    ]

    # ========== Test pour chaque livreur ==========
    for livreur in livreurs:
        commandes = generate_commandes(
            prefix=f"{livreur.id}_C",
            base_lat=livreur.latitude_depart,
            base_lon=livreur.longitude_depart
        )
        test_livreur_routing(livreur, commandes)
