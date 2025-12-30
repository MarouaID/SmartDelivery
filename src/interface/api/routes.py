from flask import Blueprint, jsonify, request, current_app
import traceback
import json
import subprocess
import os
from src.affectation.affectation_manager import AffectationManager
from src.routing.router_service import compute_routes
from src.models import Livreur, Commande
from src.interface.api.app import get_db

# =====================================================
#  API BLUEPRINT
# =====================================================
api_bp = Blueprint("api", __name__, url_prefix="/api")

# =====================================================
#  STOCKAGE EN MÉMOIRE (POUR DASHBOARD + CARTE)
# =====================================================
_LAST_OPTIMISATION = None


# =====================================================
#  STATUS
# =====================================================
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}




@api_bp.get("/livreurs")
def get_livreurs():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM livreurs WHERE disponible = 1")
        livreurs = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({"livreurs": livreurs})
    except Exception:
        traceback.print_exc()
        return jsonify({"livreurs": []})


# =====================================================
#  OPTIMISATION GLOBALE (DB + ROUTING)
# =====================================================
@api_bp.post("/optimiser")
def optimiser():
    global _LAST_OPTIMISATION
    print("DATA REÇUE PAR /optimiser :", request.json)

    try:
        # =====================================================
        # DB
        # =====================================================
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM livreurs WHERE disponible = 1")
        livreurs_db = cursor.fetchall()

        cursor.execute("SELECT * FROM commandes WHERE statut = 'en_attente'")
        commandes_db = cursor.fetchall()
        print("LIVREURS DB:", len(livreurs_db))
        print("COMMANDES DB:", len(commandes_db))

        cursor.close()
        db.close()

        if not livreurs_db or not commandes_db:
            return jsonify({
                "success": False,
                "error": "Pas de données suffisantes"
            }), 400

        # OBJETS LIVREURS
        livreurs = [
            Livreur(
                id=l["id"],
                nom=l["nom"],
                latitude_depart=float(l["latitude_depart"]),
                longitude_depart=float(l["longitude_depart"]),
                capacite_poids=float(l["capacite_poids"]),
                capacite_volume=float(l["capacite_volume"]),
                heure_debut=l["heure_debut"],
                heure_fin=l["heure_fin"],
                vitesse_moyenne=float(l["vitesse_moyenne"]),
                cout_km=float(l["cout_km"]),
                telephone=l.get("telephone"),
                email=l.get("email"),
                disponible=l.get("disponible", 1)
            ) for l in livreurs_db
        ]

        # OBJETS COMMANDES
        commandes = [
            Commande(
                id=c["id"],
                adresse=c["adresse"],
                latitude=float(c["latitude"]),
                longitude=float(c["longitude"]),
                poids=float(c["poids"]),
                volume=float(c["volume"]),
                fenetre_debut=c["fenetre_debut"],
                fenetre_fin=c["fenetre_fin"],
                priorite=int(c["priorite"]),
                temps_service=int(c["temps_service"]),
                client_nom=c.get("client_nom"),
                client_tel=c.get("client_tel"),
                statut=c.get("statut", "en_attente")
            ) for c in commandes_db
        ]

        # =====================================================
        # AFFECTATION
        # =====================================================
        manager = AffectationManager()
        result_aff = manager.affecter_commandes_branch_and_bound(livreurs, commandes)

        affectations = result_aff["affectations"]
        non_affectees = result_aff["non_affectees"]
        score = result_aff["total_cost"]

        # =====================================================
        # UPDATE DB
        # =====================================================
        db = get_db()
        cursor = db.cursor()

        for livreur_id, cmds in affectations.items():
            for cmd in cmds:
                cursor.execute("""
                    UPDATE commandes
                    SET livreur_id = %s,
                        statut = 'affectee'
                    WHERE id = %s
                """, (livreur_id, cmd.id))

        db.commit()
        cursor.close()
        db.close()

        # =====================================================
        # ROUTAGE
        # =====================================================
        print("Calcul des trajets optimisés…")
        trajets = compute_routes(affectations)
        # =====================================================
        # CALCUL DISTANCE / TEMPS / COÛT TOTAL
        # =====================================================
        total_distance_km = 0.0
        total_time_min = 0.0
        total_cost = 0.0

        routes = trajets.get("routes", {})

        for liv_id, route in routes.items():
            if not isinstance(route, dict):
                continue

            # OSRM → meters & seconds
            dist_m = route.get("distance", 0)
            time_s = route.get("duration", 0)

            dist_km = dist_m / 1000.0
            time_min = time_s / 60.0

            total_distance_km += dist_km
            total_time_min += time_min

            # récupérer le vrai livreur
            livreur = next((l for l in livreurs if l.id == liv_id), None)
            if livreur:
                total_cost += dist_km * livreur.cout_km
                    
        # =====================================================
        # SÉRIALISATION
        # =====================================================
        def serial(x):
            if hasattr(x, "to_dict"):
                return x.to_dict()
            return x.__dict__

        affectations_json = {
            lid: [serial(c) for c in cmds]
            for lid, cmds in affectations.items()
        }

        result = {
            "success": True,
            "message": "Optimisation réussie",
            "nb_trajets": len([c for c in affectations.values() if c]),

            "distance_totale_km": round(total_distance_km, 2),
            "temps_total_min": round(total_time_min, 1),
            "cout_total": round(total_cost, 2),

            "affectations": affectations_json,
            "trajets_optimises": trajets,
            "non_affectees": [serial(c) for c in non_affectees],
        }



        # STOCKAGE POUR DASHBOARD + CARTE
        global _LAST_OPTIMISATION
        _LAST_OPTIMISATION = result
        print("\n=== API RESULT DEBUG ===")
        for liv, route in trajets.get("routes", {}).items():
            print("Livreur:", liv)
            print("Keys:", route.keys())
            print("Distance:", route.get("distance_km"))
            print("Cost:", route.get("cost"))
        print("========================\n")
        current_app.config["LAST_RESULT"] = result

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =====================================================
#  API CARTE LEAFLET (ROUTES SEULEMENT)
# =====================================================
@api_bp.get("/trajets")
def get_trajets():
    if not _LAST_OPTIMISATION:
        return jsonify({"trajets": {}})

    trajets = _LAST_OPTIMISATION.get("trajets_optimises", {})
    routes = trajets.get("routes", {})

    return jsonify({
        "trajets": routes
    })


# =====================================================
#  API RÉSULTAT COMPLET POUR DASHBOARD
# =====================================================
@api_bp.get("/resultat")
def get_last_result():
    if not _LAST_OPTIMISATION:
        return jsonify({
            "success": False,
            "message": "Aucune optimisation encore réalisée"
        })

    return jsonify(_LAST_OPTIMISATION)




@api_bp.get("/livreur/trajet")
def get_trajet_livreur():
    from flask import session

    if "livreur" not in session:
        return jsonify({"success": False}), 401

    liv_id = session["livreur"]["id"]

    if not _LAST_OPTIMISATION:
        return jsonify({"success": False, "message": "Aucune optimisation"})

    routes = _LAST_OPTIMISATION["trajets_optimises"]["routes"]
    trajet = routes.get(liv_id)

    if not trajet:
        return jsonify({"success": False, "message": "Aucun trajet"})

    return jsonify({
        "success": True,
        "trajet": trajet
    })





@api_bp.route("/sumo/replay/<livreur_id>", methods=["POST"])
def replay_sumo(livreur_id):
    result = current_app.config.get("LAST_RESULT")
    if not result:
        return jsonify({"error": "Aucune optimisation"}), 400

    route = result["trajets_optimises"]["routes"].get(livreur_id)
    if not route:
        return jsonify({"error": "Livreur inconnu"}), 404

    sumo_dir = os.path.join(os.getcwd(), "sumo")
    os.makedirs(sumo_dir, exist_ok=True)

    routes_file = os.path.join(sumo_dir, "routes.rou.xml")

    # simple mapping: every delivery = move A → B → C
    with open(routes_file, "w") as f:
        f.write(f"""<routes>
    <vType id="truck" accel="1.0" decel="4.5" maxSpeed="13" length="7" color="1,0,0"/>
    <vehicle id="{livreur_id}" type="truck" depart="0">
        <route edges="A_B"/>
    </vehicle>
</routes>
""")

    subprocess.Popen([
        "python",
        os.path.join(sumo_dir, "run_sumo.py")
    ])

    return jsonify({"success": True})
