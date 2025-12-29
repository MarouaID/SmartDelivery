from flask import Blueprint, jsonify, request
import traceback

from src.affectation.affectation_manager import AffectationManager
from src.routing.router_service import compute_routes
from src.models import Livreur, Commande
from src.utils import load_json
from src.interface.api.app import get_db

# =====================================================
#  API BLUEPRINT
# =====================================================
api_bp = Blueprint("api", __name__, url_prefix="/api")

# =====================================================
#  STOCKAGE EN MÉMOIRE (POUR LEAFLET)
# =====================================================
_LAST_OPTIMISATION = None


# =====================================================
#  STATUS
# =====================================================
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}


# =====================================================
#  DONNÉES (fallback JSON)
# =====================================================
@api_bp.get("/commandes")
def get_commandes():
    return jsonify({
        "commandes": load_json("data/commandes_exemple.json")
    })


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
    print("📥 DATA REÇUE PAR /optimiser :", request.json)

    try:
        # =====================================================
        # 1️⃣ LECTURE DB
        # =====================================================
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM livreurs WHERE disponible = 1")
        livreurs_db = cursor.fetchall()

        cursor.execute("SELECT * FROM commandes WHERE statut = 'en_attente'")
        commandes_db = cursor.fetchall()

        cursor.close()
        db.close()

        if not livreurs_db or not commandes_db:
            return jsonify({
                "success": False,
                "error": "Pas de données suffisantes"
            }), 400

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
        # 2️⃣ AFFECTATION (BRANCH & BOUND)
        # =====================================================
        manager = AffectationManager()
        result_aff = manager.affecter_commandes(
            livreurs, commandes
        )

        affectations = result_aff["affectations"]
        non_affectees = result_aff["non_affectees"]
        score = result_aff.get("total_cost", 0)

        # =====================================================
        # 3️⃣ UPDATE DB (livreur_id)
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
        # 4️⃣ ROUTING (OSRM + GA)
        # =====================================================
        print("🛣 Calcul des trajets optimisés…")
        trajets = compute_routes(affectations)

        # =====================================================
        # 5️⃣ SÉRIALISATION
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
            "score": float(score),

            "affectations": affectations_json,
            "trajets_optimises": trajets,
            "non_affectees": [serial(c) for c in non_affectees],
        }

        # =====================================================
        # 6️⃣ STOCKAGE POUR LEAFLET
        # =====================================================
        _LAST_OPTIMISATION = result

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =====================================================
#  API CARTE LEAFLET
# =====================================================
@api_bp.get("/trajets")
def get_trajets():
    """
    Retourne uniquement les trajets OSRM
    pour l'affichage Leaflet
    """
    if not _LAST_OPTIMISATION:
        return jsonify({"trajets": {}})

    trajets = _LAST_OPTIMISATION.get("trajets_optimises", {})
    routes = trajets.get("routes", {})

    return jsonify({
        "trajets": routes
    })
