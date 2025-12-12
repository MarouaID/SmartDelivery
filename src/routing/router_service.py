# src/routing/router_service.py

from typing import Dict, List, Any
from src.models import Commande, Livreur
from src.routing.routing_optimizer import RoutingOptimizer


def compute_routes(affectations: Dict[str, List[Any]]) -> Dict[str, Any]:
    """
    Prend :
        affectations = { "LIV1": [commande1, commande2], ... }

    Retourne :
        {
            "success": True,
            "routes": {
                "LIV1": { routing complet },
                "LIV2": { routing complet }
            }
        }
    """

    optimizer = RoutingOptimizer()
    routes_result = {}

    for liv_id, commandes_input in affectations.items():

        # ---------------------------
        # 1) Création du livreur
        # ---------------------------
        # (On n’a pas toutes les infos provenant du front, donc valeurs par défaut)
        livreur = Livreur(
            id=liv_id,
            nom=f"Livreur_{liv_id}",
            latitude_depart=31.6300,
            longitude_depart=-7.9900,
            capacite_poids=500,
            capacite_volume=3.0,
            heure_debut="08:00",
            heure_fin="18:00",
            vitesse_moyenne=40,     # utilisé si OSRM down
            cout_km=0.5,
        )

        commandes: List[Commande] = []

        # ---------------------------
        # 2) Conversion commande
        # ---------------------------
        for c in commandes_input:

            if isinstance(c, Commande):
                commandes.append(c)

            elif isinstance(c, dict):
                commandes.append(
                    Commande(
                        id=c.get("id"),
                        adresse=c.get("adresse", ""),
                        latitude=c.get("latitude"),
                        longitude=c.get("longitude"),
                        poids=c.get("poids", 1),
                        volume=c.get("volume", 0.1),
                        fenetre_debut=c.get("fenetre_debut", "08:00"),
                        fenetre_fin=c.get("fenetre_fin", "20:00"),
                        priorite=c.get("priorite", 2),
                        temps_service=c.get("temps_service", 5),
                        client_nom=c.get("client_nom"),
                        client_tel=c.get("client_tel"),
                    )
                )

            else:
                raise TypeError(f"Format de commande inconnu : {type(c)}")

        # ---------------------------
        # 3) Aucune commande = ignorer
        # ---------------------------
        if not commandes:
            routes_result[liv_id] = {"message": "Aucune commande"}
            continue

        # ---------------------------
        # 4) Calcul routing complet
        # ---------------------------
        route_info = optimizer.generate_route(livreur, commandes)
        routes_result[liv_id] = route_info

    return {
        "success": True,
        "routes": routes_result
    }
