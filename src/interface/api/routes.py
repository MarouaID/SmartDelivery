from flask import Blueprint, jsonify, current_app
import traceback
import subprocess
import os
from datetime import timedelta
from src.routing.osrm_client import osrm_route_geometry
from src.routing.osrm_client import osrm_route_geometry
from src.affectation.affectation_manager import AffectationManager
from src.routing.router_service import compute_routes
from src.models import Livreur, Commande
from src.interface.api.app import get_db


# =====================================================
#  API BLUEPRINT
#  NOTE: NO url_prefix HERE (app.py already uses /api)
# =====================================================
api_bp = Blueprint("api", __name__)

# =====================================================
#  STOCKAGE EN MÉMOIRE (DASHBOARD + CARTE)
# =====================================================
_LAST_OPTIMISATION = None


# =====================================================
#  SMALL HELPERS
# =====================================================
def time_to_str(x):
    """Convert MySQL TIME (often returned as timedelta) to 'HH:MM' string."""
    if isinstance(x, timedelta):
        sec = int(x.total_seconds())
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h:02d}:{m:02d}"
    if x is None:
        return None
    s = str(x)
    return s[:5] if len(s) >= 5 else s


def safe_float(x, default=0.0):
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def safe_int(x, default=0):
    try:
        if x is None:
            return int(default)
        return int(x)
    except Exception:
        return int(default)


def serial(obj):
    """Serialize model object safely."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return obj


# =====================================================
#  STATUS
# =====================================================
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}


# =====================================================
#  LIVREURS DISPONIBLES (JSON safe)
# =====================================================
@api_bp.get("/livreurs_disponibles")
def get_livreurs_disponibles():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM livreurs WHERE disponible = 1")
        livreurs = cursor.fetchall()
        cursor.close()
        db.close()

        for l in livreurs:
            l["heure_debut"] = time_to_str(l.get("heure_debut"))
            l["heure_fin"] = time_to_str(l.get("heure_fin"))

        return jsonify({"livreurs": livreurs})

    except Exception:
        traceback.print_exc()
        return jsonify({"livreurs": []})


# =====================================================
#  OPTIMISATION GLOBALE (MATCHES NEW MODELS)
# =====================================================
@api_bp.post("/optimiser")
def optimiser():
    global _LAST_OPTIMISATION
    print("=== /optimiser CALLED ===")

    try:
        # =================================================
        # DB – READ
        # =================================================
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM livreurs WHERE disponible = 1")
        livreurs_db = cursor.fetchall()

        cursor.execute("""
            SELECT c.*, cl.nom AS client_nom, cl.telephone AS client_tel
            FROM commandes c
            LEFT JOIN clients cl ON c.client_id = cl.id
            WHERE c.statut = 'en_attente'
        """)
        commandes_db = cursor.fetchall()

        cursor.execute("SELECT DATABASE() AS dbname")
        print("CONNECTED_DB =", cursor.fetchone())

        cursor.close()
        db.close()

        print("LIVREURS DB =", len(livreurs_db))
        print("COMMANDES DB =", len(commandes_db))

        if not livreurs_db or not commandes_db:
            return jsonify({
                "success": False,
                "error": "Pas de données suffisantes (livreurs dispo ou commandes en attente manquants)"
            }), 400

        # =================================================
        # OBJETS LIVREURS (NEW)
        # =================================================
        livreurs = []
        for l in livreurs_db:
            livreurs.append(
                Livreur(
                    id=str(l.get("id", "")).strip(),
                    nom=l.get("nom", ""),

                    latitude_depart=safe_float(l.get("latitude_depart"), 0),
                    longitude_depart=safe_float(l.get("longitude_depart"), 0),

                    capacite_poids=safe_float(l.get("capacite_poids"), 0),

                    heure_debut=time_to_str(l.get("heure_debut")) or "00:00",
                    heure_fin=time_to_str(l.get("heure_fin")) or "23:59",

                    vitesse_moyenne=safe_float(l.get("vitesse_moyenne"), 40),
                    cout_km=safe_float(l.get("cout_km"), 1.0),

                    telephone=l.get("telephone"),
                    email=l.get("email"),
                    disponible=bool(l.get("disponible", 1))
                )
            )

        # =================================================
        # OBJETS COMMANDES (NEW)
        # =================================================
        commandes = []
        for c in commandes_db:
            commandes.append(
                Commande(
                    id=str(c.get("id", "")).strip(),
                    adresse=c.get("adresse", ""),
                    latitude=safe_float(c.get("latitude"), 0),
                    longitude=safe_float(c.get("longitude"), 0),
                    poids=safe_float(c.get("poids"), 0),
                    priorite=safe_int(c.get("priorite"), 1),
                    client_nom=c.get("client_nom"),
                    client_tel=c.get("client_tel"),
                    statut=c.get("statut", "en_attente")
                )
            )

        # =================================================
        # AFFECTATION
        # =================================================
        manager = AffectationManager()
        result_aff = manager.affecter_commandes_branch_and_bound(livreurs, commandes)

        affectations = result_aff.get("affectations", {})
        non_affectees = result_aff.get("non_affectees", [])

        print("AFFECTATIONS_SIZES =", {k: len(v) for k, v in affectations.items()})
        print("NON_AFFECTEES =", len(non_affectees))

        # =================================================
        # UPDATE DB (assign livreur_id + statut)
        # =================================================
        db = get_db()
        cursor = db.cursor()

        updated_rows = 0
        sample_updates = []

        for livreur_id, cmds in affectations.items():
            for cmd in cmds:
                cursor.execute("""
                    UPDATE commandes
                    SET livreur_id = %s,
                        statut = 'affectee'
                    WHERE id = %s
                """, (livreur_id, cmd.id))

                updated_rows += cursor.rowcount
                if len(sample_updates) < 10:
                    sample_updates.append((livreur_id, cmd.id, cursor.rowcount))

        db.commit()
        cursor.close()
        db.close()

        print("UPDATED_ROWS_TOTAL =", updated_rows)
        print("SAMPLE_UPDATES =", sample_updates)

        if updated_rows == 0:
            return jsonify({
                "success": False,
                "error": "Aucune ligne mise à jour (0 rowcount). Vérifie IDs commandes/livreurs.",
                "debug": {
                    "affectations_sizes": {k: len(v) for k, v in affectations.items()},
                    "sample_updates": sample_updates
                }
            }), 500

        # =================================================
        # ROUTAGE
        # =================================================
        print("Calcul des trajets…")
        trajets = compute_routes(affectations)

        # =================================================
        # METRICS
        # =================================================
        total_distance_km = 0.0
        total_time_min = 0.0
        total_cost = 0.0

        routes = trajets.get("routes", {})

        for liv_id, route in routes.items():
            if not isinstance(route, dict):
                continue

            dist_km = float(route.get("distance_km", 0) or 0)
            time_min = float(route.get("duree_min", 0) or 0)


            total_distance_km += dist_km
            total_time_min += time_min

            liv = next((l for l in livreurs if l.id == liv_id), None)
            if liv:
                total_cost += dist_km * float(getattr(liv, "cout_km", 0) or 0)

        # =================================================
        # FINAL RESULT
        # =================================================
        result = {
            "success": True,
            "message": "Optimisation réussie",
            "nb_trajets": len([v for v in affectations.values() if v]),
            "distance_totale_km": round(total_distance_km, 2),
            "temps_total_min": round(total_time_min, 1),
            "cout_total": round(total_cost, 2),
            "affectations": {
                lid: [serial(c) for c in cmds]
                for lid, cmds in affectations.items()
            },
            "trajets_optimises": trajets,
            "non_affectees": [serial(c) for c in non_affectees],
        }

        _LAST_OPTIMISATION = result
        current_app.config["LAST_RESULT"] = result

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
#  TRAJETS (CARTE)
# =====================================================



DEPOT = (31.63, -7.99) 


@api_bp.get("/trajets")
def get_trajets():
    res = current_app.config.get("LAST_RESULT")
    if not res:
        return jsonify({"trajets": {}})

    routes = res["trajets_optimises"]["routes"]

    # Build lookup: commande_id -> (lat, lon)
    cmd_coords = {}
    for cmds in res.get("affectations", {}).values():
        for c in cmds:
            cmd_coords[str(c["id"])] = (
                float(c["latitude"]),
                float(c["longitude"])
            )

    # ---- APPLY OSRM TO *ALL* ALGORITHMS ----
    for liv_id, trajet in routes.items():
        meta = trajet.get("meta_solutions", {})
        if not meta:
            continue

        for algo, sol in meta.items():
            ordre = sol.get("ordre_ids")
            if not ordre:
                continue

            # Build OSRM waypoints: DEPOT → commandes
            points = [DEPOT]
            for cid in ordre:
                if str(cid) in cmd_coords:
                    points.append(cmd_coords[str(cid)])

            if len(points) < 2:
                continue

            try:
                sol["route_geometry"] = osrm_route_geometry(points)
            except Exception as e:
                print(f"[OSRM ERROR] {liv_id} / {algo} →", e)
                sol["route_geometry"] = None

    return jsonify({"trajets": routes})

# =====================================================
#  RESULTAT COMPLET
# =====================================================
@api_bp.get("/resultat")
def get_last_result():
    if not _LAST_OPTIMISATION:
        return jsonify({
            "success": False,
            "message": "Aucune optimisation encore réalisée"
        })
    return jsonify(_LAST_OPTIMISATION)


# =====================================================
#  TRAJET LIVREUR CONNECTÉ
# =====================================================
@api_bp.get("/livreur/trajet")
def get_trajet_livreur():
    from flask import session

    if "livreur" not in session:
        return jsonify({"success": False}), 401

    liv_id = session["livreur"]["id"]

    if not _LAST_OPTIMISATION:
        return jsonify({"success": False})

    trajet = _LAST_OPTIMISATION["trajets_optimises"].get("routes", {}).get(liv_id)
    if not trajet:
        return jsonify({"success": False})

    return jsonify({"success": True, "trajet": trajet})


# =====================================================
#  SUMO REPLAY (kept as-is)
# =====================================================
@api_bp.post("/sumo/replay/<livreur_id>")
def replay_sumo(livreur_id):
    result = current_app.config.get("LAST_RESULT")
    if not result:
        return jsonify({"error": "Aucune optimisation"}), 400

    route = result["trajets_optimises"].get("routes", {}).get(livreur_id)
    if not route:
        return jsonify({"error": "Livreur inconnu"}), 404

    sumo_dir = os.path.join(os.getcwd(), "sumo")
    os.makedirs(sumo_dir, exist_ok=True)

    with open(os.path.join(sumo_dir, "routes.rou.xml"), "w") as f:
        f.write(f"""<routes>
    <vType id="truck" accel="1.0" decel="4.5" maxSpeed="13" length="7"/>
    <vehicle id="{livreur_id}" type="truck" depart="0">
        <route edges="A_B"/>
    </vehicle>
</routes>
""")

    subprocess.Popen(["python", os.path.join(sumo_dir, "run_sumo.py")])
    return jsonify({"success": True})
