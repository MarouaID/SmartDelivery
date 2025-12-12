# src/interface/api/routes.py

from flask import Blueprint, jsonify, request
from src.affectation.affectation_manager import AffectationManager
from src.routing.router_service import compute_routes
from src.utils import load_json
from src.models import Livreur,Commande
import traceback

api_bp = Blueprint("api", __name__)


@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}


@api_bp.get("/commandes")
def get_commandes():
    return jsonify(load_json("data/commandes_exemple.json"))


@api_bp.get("/livreurs")
def get_livreurs():
    return jsonify(load_json("data/livreurs_exemple.json"))


@api_bp.post("/optimiser")
def optimiser():
    print("📥 DATA REÇUE PAR /optimiser :", request.json)

    try:
        data = request.json or {}

        # =====================================================
        # 1) RÉCUPÉRATION DES DONNÉES
        # =====================================================
        if "scenario" in data:
            from src.simulation.simulateur import Simulateur
            sim = Simulateur()
            scene = sim.generer_scenario(
                data.get("scenario", "normal"),
                int(data.get("nb_livreurs", 5)),
                int(data.get("nb_commandes", 20)),
            )
            livreurs = scene["livreurs"]
            commandes = scene["commandes"]

        else:
            livreurs_raw = data.get("livreurs")
            commandes_raw = data.get("commandes")

            if not livreurs_raw or not commandes_raw:
                return jsonify({"success": False, "error": "livreurs & commandes manquants"}), 400
            
        if isinstance(livreurs[0], dict):
            livreurs = [Livreur(**l) for l in livreurs]

        if isinstance(commandes[0], dict):
            commandes = [Commande(**c) for c in commandes]

            from src.models import Livreur, Commande
            livreurs = [Livreur(**l) for l in livreurs_raw]
            commandes = [Commande(**c) for c in commandes_raw]

        # =====================================================
        # 2) AFFECTATION BRANCH & BOUND
        # =====================================================
        manager = AffectationManager()
        result_aff = manager.affecter_commandes(livreurs, commandes)

        affectations = result_aff["affectations"]
        non_affectees = result_aff["non_affectees"]
        total_cost = 2

        # =====================================================
        # 3) ROUTING
        # =====================================================
        print("🛣 Calcul des trajets optimisés…")
        trajets = compute_routes(affectations)

        # =====================================================
        # 4) SÉRIALISATION (pour JSON propre)
        # =====================================================
        def serial(x):
            if hasattr(x, "to_dict"):
                return x.to_dict()
            return x.__dict__ if hasattr(x, "__dict__") else str(x)

        affectations_json = {
            lid: [serial(c) for c in cmds]
            for lid, cmds in affectations.items()
        }

        return jsonify({
            "success": True,
            "message": "Optimisation réussie",
            "nb_trajets": len([c for c in affectations.values() if c]),
            "score": float(total_cost) if total_cost else None,

            # AFFECTATION
            "affectations": affectations_json,

            # ROUTING
            "trajets_optimises": trajets,

            # COMMANDES NON AFFECTÉES
            "non_affectees": [serial(c) for c in non_affectees]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
