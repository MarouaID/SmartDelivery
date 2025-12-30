# src/interface/api/routes.py

from flask import Blueprint, jsonify, request
from src.affectation.affectation_manager import AffectationManager  
from src.utils import load_json
from src.models import Commande, Livreur
import traceback

api_bp = Blueprint("api", __name__)

# --------------------------
# ENDPOINT TEST / STATUS
# --------------------------
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}

# --------------------------
# ENDPOINT COMMANDES
# --------------------------
@api_bp.get("/commandes")
def get_commandes():
    commandes = load_json("data/commandes_exemple.json")
    return jsonify(commandes)

# --------------------------
# ENDPOINT LIVREURS
# --------------------------
@api_bp.get("/livreurs")
def get_livreurs():
    livreurs = load_json("data/livreurs_exemple.json")
    return jsonify(livreurs)

# --------------------------
# ENDPOINT OPTIMISATION SCALABLE
# --------------------------
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

            scene = simulateur.generer_scenario(scenario, nb_livreurs, nb_commandes)
            livreurs = scene["livreurs"]
            commandes = scene["commandes"]

        # ---------------------------------------------------
        #   CAS 2 : Affectation directe (livreurs + commandes)
        # ---------------------------------------------------
        else:
            livreurs_data = data.get("livreurs")
            commandes_data = data.get("commandes")

            if not livreurs_data or not commandes_data:
                return jsonify({"success": False, "error": "livreurs and commandes are required"}), 400

            # Convertir JSON → objets Livreur/Commande
            livreurs = [Livreur(**l) for l in livreurs_data]
            commandes = [Commande(**c) for c in commandes_data]

        # ---------------------------------------------------
        #   APPEL AFFECTATION SCALABLE
        # ---------------------------------------------------
        manager = AffectationManager(num_zones=50)  # ajuste num_zones selon taille
        affectations = manager.affectation_scalable(livreurs, commandes)

        # ---------------------------------------------------
        #   JSON SÉRIALISABLE
        # ---------------------------------------------------
        def serial(item):
            if hasattr(item, "to_dict"):
                return item.to_dict()
            if hasattr(item, "__dict__"):
                return item.__dict__
            return str(item)

        affectations_serial = {liv_id: [serial(c) for c in cmds] for liv_id, cmds in affectations.items()}

        # Commandes non affectées
        affectees_ids = {c.id for cmds in affectations.values() for c in cmds}
        non_affectees_serial = [serial(c) for c in commandes if c.id not in affectees_ids]

        # Nombre de trajets
        nb_trajets = sum(1 for cmds in affectations.values() if len(cmds) > 0)

        # Score total (distance)
        total_cost = sum(
            manager.dist.haversine(l.latitude_depart, l.longitude_depart, c.latitude, c.longitude)
            for l in livreurs for c in affectations[l.id]
        )

        return jsonify({
            "success": True,
            "message": "Optimisation réussie",
            "nb_trajets": nb_trajets,
            "score": float(total_cost),
            "affectations": affectations_serial,
            "non_affectees": non_affectees_serial
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
