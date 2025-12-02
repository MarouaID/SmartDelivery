# src/interface/api/routes.py

from flask import Blueprint, jsonify, request
from src.affectation.affectation_manager import AffectationManager
from src.utils import load_json
import traceback

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------
#     ENDPOINT TEST / STATUS
# ---------------------------------------------------
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}


# ---------------------------------------------------
#     ENDPOINT COMMANDES
# ---------------------------------------------------
@api_bp.get("/commandes")
def get_commandes():
    commandes = load_json("data/commandes_exemple.json")
    return jsonify(commandes)


# ---------------------------------------------------
#     ENDPOINT LIVREURS
# ---------------------------------------------------
@api_bp.get("/livreurs")
def get_livreurs():
    livreurs = load_json("data/livreurs_exemple.json")
    return jsonify(livreurs)


# ---------------------------------------------------
#     ENDPOINT OPTIMISATION (BRANCH & BOUND)
# ---------------------------------------------------
@api_bp.post("/optimiser")
def optimiser():
    """
    Endpoint d'optimisation :
    - Peut recevoir {scenario, nb_livreurs, nb_commandes}
    - OU {livreurs, commandes}
    """

    data = request.json or {}
    print("🔍 DATA REÇUE PAR /optimiser :", data)

    try:
        # ---------------------------------------------------
        #   CAS 1 : Simulation (scenario)
        # ---------------------------------------------------
        if "scenario" in data:
            from src.simulation.simulateur import Simulateur

            simulateur = Simulateur()
            scenario = data.get("scenario", "normal")
            nb_livreurs = int(data.get("nb_livreurs", 5))
            nb_commandes = int(data.get("nb_commandes", 20))

            # génération automatique livreurs + commandes
            scene = simulateur.generer_scenario(
                scenario, nb_livreurs, nb_commandes)
            livreurs = scene["livreurs"]
            commandes = scene["commandes"]

        # ---------------------------------------------------
        #   CAS 2 : Affectation directe (livreurs + commandes)
        # ---------------------------------------------------
        else:
            livreurs = data.get("livreurs")
            commandes = data.get("commandes")

        if not livreurs or not commandes:
            return jsonify({"success": False, "error": "livreurs and commandes are required"}), 400

        # ---------------------------------------------------
        #   DEBUG
        # ---------------------------------------------------
        print("\n=== DEBUG LIVREURS ===")
        for l in livreurs:
            print(type(l), l)

        print("\n=== DEBUG COMMANDES ===")
        for c in commandes:
            print(type(c), c)

        # ---------------------------------------------------
        #   APPEL BRANCH & BOUND
        # ---------------------------------------------------
        manager = AffectationManager()
        resultat = manager.affecter_commandes_branch_and_bound(
            livreurs, commandes)

        affectations = resultat["affectations"]
        non_affectees = resultat["non_affectees"]
        total_cost = resultat["total_cost"]

        # ---------------------------------------------------
        #   JSON SÉRIALISABLE
        # ---------------------------------------------------
        def serial(item):
            """Transforme un objet Livreur/Commande en dict sérialisable"""
            if hasattr(item, "to_dict"):
                return item.to_dict()
            if hasattr(item, "__dict__"):
                return item.__dict__
            return str(item)

        # commandes affectées → dict
        affectations_serial = {
            liv_id: [serial(cmd) for cmd in cmds]
            for liv_id, cmds in affectations.items()
        }

        # commandes non affectées → dict
        non_affectees_serial = [serial(c) for c in non_affectees]

        # ---------------------------------------------------
        #   NOMBRE DE TRAJETS
        # ---------------------------------------------------
        nb_trajets = sum(1 for cmds in affectations.values() if len(cmds) > 0)

        # ---------------------------------------------------
        #   RÉPONSE FINALE
        # ---------------------------------------------------
        return jsonify({
            "success": True,
            "message": "Optimisation réussie",
            "nb_trajets": nb_trajets,
            "score": float(total_cost) if total_cost is not None else None,
            "affectations": affectations_serial,
            "non_affectees": non_affectees_serial
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
