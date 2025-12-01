# src/interface/api/routes.py

from flask import Blueprint, jsonify, request
import json
from src.affectation.affectation_manager import AffectationManager
from src.routing.routing_optimizer import RoutingOptimizer
from src.utils import load_json

api_bp = Blueprint("api", __name__)


# ----------------------------
# ===  API STATUS / HEALTH ===
# ----------------------------
@api_bp.get("/status")
def status():
    return {"status": "OK", "service": "SmartDelivery API"}


# ----------------------------
# ===  COMMANDES / LIVREURS ===
# ----------------------------
@api_bp.get("/commandes")
def get_commandes():
    commandes = load_json("data/commandes_exemple.json")
    return jsonify(commandes)


@api_bp.get("/livreurs")
def get_livreurs():
    livreurs = load_json("data/livreurs_exemple.json")
    return jsonify(livreurs)


# ----------------------------
# ===  AFFECTATION (CORE) ===
# ----------------------------
@api_bp.post("/affecter")
def affecter():
    payload = request.json

    commandes = payload.get("commandes")
    livreurs = payload.get("livreurs")

    if not commandes or not livreurs:
        return {"error": "commandes and livreurs are required"}, 400

    manager = AffectationManager()
    resultat = manager.affecter_commandes(commandes, livreurs)

    return jsonify(resultat)


# ----------------------------
# ===  OPTIMISATION ROUTING ===
# ----------------------------
@api_bp.post("/optimiser_route")
def optimiser_route():
    data = request.json
    points = data.get("points")

    if not points:
        return {"error": "points are required"}, 400

    optimizer = RoutingOptimizer()
    solution = optimizer.optimiser(points)

    return jsonify(solution)

