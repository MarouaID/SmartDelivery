# src/routing/recharge_loader.py

import json
import os


def load_recharge_points():
    """
    Charge la liste des bornes de recharge depuis :
      data/recharge_stations.json

    Retourne une liste de dict :
      [
        {
            "id": "R001",
            "nom": "...",
            "lat": 31.62,
            "lon": -7.99,
            "type": "Rapide",
            "puissance_kW": 50,
            "operateur": "Marjane"
        },
        ...
      ]
    """

    path = os.path.join("data", "recharge_stations.json")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"❌ Fichier des bornes introuvable : {path}"
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            stations = json.load(f)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"❌ Erreur JSON dans recharge_stations.json : {e}"
        )

    # Vérification minimale
    if not isinstance(stations, list):
        raise ValueError("❌ Le fichier recharge_stations.json doit contenir une LISTE.")

    for st in stations:
        if "lat" not in st or "lon" not in st:
            raise ValueError(f"❌ Station mal formée : {st}")

    return stations
