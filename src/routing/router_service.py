# src/routing/router_service.py

from typing import Dict, List, Any
from src.models import Commande, Livreur
from src.routing.routing_optimizer import RoutingOptimizer


def compute_routes(affectations: Dict[str, List[Any]]) -> Dict[str, Any]:
    """
    Entrée :
        affectations = { "LIV1": [Commande, Commande, ...], ... }

    Sortie :
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

        # =====================================================
        # 1) LIVREUR (routing-level representation)
        # =====================================================
        # NOTE:
        # - Le livreur réel vient déjà de la DB dans /optimiser
        # - Ici on reconstruit seulement ce qui est nécessaire au routing
        livreur = Livreur(
            id=liv_id,
            nom=f"Livreur_{liv_id}",
            latitude_depart=31.6300,
            longitude_depart=-7.9900,
            capacite_poids=10_000,     # large safety margin
            heure_debut="08:00",
            heure_fin="18:00",
            vitesse_moyenne=40,        # fallback if OSRM unavailable
            cout_km=0.5
        )

        commandes: List[Commande] = []

        # =====================================================
        # 2) NORMALISATION DES COMMANDES
        # =====================================================
        for c in commandes_input:

            if isinstance(c, Commande):
                commandes.append(c)

            elif isinstance(c, dict):
                commandes.append(
                    Commande(
                        id=str(c.get("id")),
                        adresse=c.get("adresse", ""),
                        latitude=float(c.get("latitude", 0)),
                        longitude=float(c.get("longitude", 0)),
                        poids=float(c.get("poids", 1)),
                        priorite=int(c.get("priorite", 2)),
                        client_nom=c.get("client_nom"),
                        client_tel=c.get("client_tel"),
                        statut=c.get("statut", "affectee")
                    )
                )

            else:
                raise TypeError(
                    f"Format de commande inconnu dans routing: {type(c)}"
                )

        # =====================================================
        # 3) AUCUNE COMMANDE → IGNORER
        # =====================================================
        if not commandes:
            routes_result[liv_id] = {"message": "Aucune commande"}
            continue

        # =====================================================
        # 4) DEBUG (clair & lisible)
        # =====================================================
        print("\n=== ROUTING DEBUG ===")
        print("Livreur:", liv_id)
        print("Nb commandes:", len(commandes))
        for c in commandes:
            print(f" - CMD {c.id} | ({c.latitude},{c.longitude}) | {c.poids}kg")
        print("====================")

        # =====================================================
        # 5) ROUTING
        # =====================================================
        route_info = optimizer.generate_route(livreur, commandes)
        routes_result[liv_id] = route_info

    return {
        "success": True,
        "routes": routes_result
    }
