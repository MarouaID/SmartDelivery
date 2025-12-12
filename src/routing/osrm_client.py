# src/routing/osrm_client.py
import requests
import math

# Adresse du conteneur OSRM
OSRM_URL = "http://localhost:5001"


# =============================================================
# 1) OSRM TABLE : matrice distances + durées
# =============================================================
def build_osrm_table(coords):
    """
    coords = [(lat, lon), (lat, lon), ...]
    Retourne :
      - matrice distances (km)
      - matrice temps (minutes)

    ⚠ Limitation OSRM : maximum ~120 points.
    """
    coord_str = ";".join([f"{lng},{lat}" for lat, lng in coords])
    url = f"{OSRM_URL}/table/v1/driving/{coord_str}?annotations=distance,duration"

    response = requests.get(url)
    data = response.json()

    if data.get("code") != "Ok":
        raise Exception("Erreur OSRM TABLE API : " + str(data))

    # distances en mètres → km
    dist_matrix = [[d / 1000 for d in row] for row in data["distances"]]

    # durées en secondes → minutes
    time_matrix = [[t / 60 for t in row] for row in data["durations"]]

    return dist_matrix, time_matrix


# =============================================================
# 2) OSRM ROUTE : distance & duration réelles d'un trajet
# =============================================================
def osrm_route(coords):
    """
    Calcule la distance réelle OSRM + durée réelle OSRM entre plusieurs points.
    coords = [ (lat, lon), (lat, lon), ... ]
    """
    coord_str = ";".join([f"{lng},{lat}" for lat, lng in coords])
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=false"

    res = requests.get(url).json()

    if res.get("code") != "Ok":
        raise Exception("Erreur OSRM ROUTE API : " + str(res))

    route = res["routes"][0]

    distance_km = route["distance"] / 1000      # mètres → km
    duration_min = route["duration"] / 60       # secondes → minutes

    return distance_km, duration_min


# =============================================================
# 3) HAVERSINE : distance rapide en vol d’oiseau
# =============================================================
def haversine(a, b):
    """
    Distance vol d’oiseau entre deux points lat/lon.
    Utile pour sélectionner les stations proches.
    """
    R = 6371.0  # rayon Terre en km
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    x = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

    return 2 * R * math.asin(math.sqrt(x))


# =============================================================
# 4) Trouver la borne de recharge la plus proche
# =============================================================
def find_nearest_station(current_coord, stations):
    """
    Retourne la borne la plus proche d’un point donné.

    - current_coord = (lat, lon)
    - stations = [ { "id": "...", "lat": 31.62, "lon": -7.99 }, .. ]

    Retour :
      {
        "id": "...",
        "lat": ...,
        "lon": ...,
        "distance_km": <distance à vol d’oiseau>
      }
    """
    best_station = None
    best_dist = float("inf")

    for st in stations:
        st_coord = (st["lat"], st["lon"])
        d = haversine(current_coord, st_coord)

        if d < best_dist:
            best_dist = d
            best_station = st

    if best_station is None:
        raise Exception("Aucune borne trouvée !")

    best_station = dict(best_station)  # copie pour éviter modification globale
    best_station["distance_km"] = best_dist

    return best_station


# =============================================================
# 5) OSRM distance exacte entre un point et une borne
# =============================================================
def osrm_distance_to_station(current_coord, station):
    """
    Retourne :
      - distance OSRM en km
      - durée OSRM en minutes
    """
    coords = [
        current_coord,
        (station["lat"], station["lon"])
    ]

    return osrm_route(coords)
