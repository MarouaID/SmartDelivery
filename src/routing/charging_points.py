import json
import os

# Chemin vers le fichier JSON
RECHARGE_FILE = os.path.join("data", "recharge_stations.json")


def load_recharge_points():
    """
    Charge la liste des bornes de recharge (JSON).
    Retourne uniquement les coordonnées sous forme [(lat, lon), ...].
    """
    if not os.path.exists(RECHARGE_FILE):
        raise FileNotFoundError(f"⚠ Fichier introuvable : {RECHARGE_FILE}")

    with open(RECHARGE_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Extraire uniquement les coordonnées
    return [(entry["lat"], entry["lon"]) for entry in raw]
