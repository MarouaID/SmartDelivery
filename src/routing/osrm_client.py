# src/routing/osrm_client.py
import requests
import math

# Adresse du serveur OSRM (Docker)
OSRM_URL = "http://localhost:5001"


# =============================================================
# OSRM TABLE : matrice distances + durées
# =============================================================
def build_osrm_table(coords):
    """
    coords = [(lat, lon), ...]
    Retourne :
      - dist_matrix (km)
      - time_matrix (minutes)
    """
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"{OSRM_URL}/table/v1/driving/{coord_str}?annotations=distance,duration"

    res = requests.get(url).json()
    if res.get("code") != "Ok":
        raise Exception("Erreur OSRM TABLE")

    dist_matrix = [[d / 1000 for d in row] for row in res["distances"]]
    time_matrix = [[t / 60 for t in row] for row in res["durations"]]

    return dist_matrix, time_matrix


# =============================================================
# OSRM ROUTE : distance + durée
# =============================================================
def osrm_route(coords):
    """
    coords = [(lat, lon), (lat, lon)]
    """
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=false"

    res = requests.get(url).json()
    if res.get("code") != "Ok":
        raise Exception("Erreur OSRM ROUTE")

    r = res["routes"][0]
    return r["distance"] / 1000, r["duration"] / 60


# =============================================================
# OSRM ROUTE GEOMETRY (IMPORTANT POUR LA CARTE)
# =============================================================
def osrm_route_geometry(coords):
    """
    Retourne la géométrie réelle OSRM (GeoJSON)
    [[lon, lat], ...]
    """
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=full&geometries=geojson"

    res = requests.get(url).json()
    if res.get("code") != "Ok":
        raise Exception("Erreur OSRM GEOMETRY")

    return res["routes"][0]["geometry"]["coordinates"]


# =============================================================
# HAVERSINE (vol d’oiseau)
# =============================================================
def haversine(a, b):
    R = 6371.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    x = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(x))


# =============================================================
# BORNE LA PLUS PROCHE
# =============================================================
def find_nearest_station(current_coord, stations):
    best = None
    best_dist = float("inf")

    for st in stations:
        d = haversine(current_coord, (st["lat"], st["lon"]))
        if d < best_dist:
            best = st
            best_dist = d

    best = dict(best)
    best["distance_km"] = best_dist
    return best


# =============================================================
# DISTANCE OSRM VERS BORNE
# =============================================================
def osrm_distance_to_station(current_coord, station):
    return osrm_route([
        current_coord,
        (station["lat"], station["lon"])
    ])
