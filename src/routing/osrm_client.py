# src/routing/osrm_client.py
import requests
import math
from typing import List, Tuple, Dict, Any, Optional

# Adresse du serveur OSRM (Docker)
OSRM_URL = "http://localhost:5001"
_TIMEOUT = 15  # seconds

Coord = Tuple[float, float]  # (lat, lon)


# =============================================================
# INTERNAL HELPERS
# =============================================================
def _to_osrm_coord_str(coords: List[Coord]) -> str:
    # OSRM expects "lon,lat;lon,lat;..."
    return ";".join([f"{lon},{lat}" for (lat, lon) in coords])


def _check_osrm(res: Dict[str, Any], label: str):
    if not isinstance(res, dict):
        raise Exception(f"Erreur OSRM {label}: réponse invalide")
    if res.get("code") != "Ok":
        msg = res.get("message") or res.get("code") or "Unknown"
        raise Exception(f"Erreur OSRM {label}: {msg}")


def _get(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=_TIMEOUT)
    return r.json()


# =============================================================
# OSRM TABLE : matrice distances + durées
# =============================================================
def build_osrm_table(coords: List[Coord]):
    """
    coords = [(lat, lon), ...]
    Retourne :
      - dist_matrix (km)
      - time_matrix (minutes)
    """
    if not coords or len(coords) < 2:
        return [[0.0]], [[0.0]]

    coord_str = _to_osrm_coord_str(coords)
    url = f"{OSRM_URL}/table/v1/driving/{coord_str}?annotations=distance,duration"

    res = _get(url)
    _check_osrm(res, "TABLE")

    dist_matrix = [[(d or 0.0) / 1000 for d in row] for row in res["distances"]]
    time_matrix = [[(t or 0.0) / 60 for t in row] for row in res["durations"]]

    return dist_matrix, time_matrix


# =============================================================
# OSRM ROUTE : distance + durée (2 points)
# =============================================================
def osrm_route(coords: List[Coord]):
    """
    coords = [(lat, lon), (lat, lon)]
    Retourne (distance_km, duration_min)
    """
    if not coords or len(coords) < 2:
        return 0.0, 0.0

    coord_str = _to_osrm_coord_str(coords[:2])
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=false"

    res = _get(url)
    _check_osrm(res, "ROUTE")

    r = res["routes"][0]
    return (r["distance"] / 1000.0), (r["duration"] / 60.0)


# =============================================================
# OSRM ROUTE GEOMETRY (IMPORTANT POUR LA CARTE)
# =============================================================
def osrm_route_geometry(coords: List[Coord]):
    """
    Retourne la géométrie réelle OSRM (GeoJSON)
    [[lon, lat], ...]
    """
    if not coords or len(coords) < 2:
        return []

    coord_str = _to_osrm_coord_str(coords)
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=full&geometries=geojson"

    res = _get(url)
    _check_osrm(res, "GEOMETRY")

    return res["routes"][0]["geometry"]["coordinates"]


# =============================================================
# ✅ NEW: OSRM FULL ROUTE (N points) -> dist + time + geometry
# =============================================================
def osrm_route_full(coords: List[Coord], include_geometry: bool = True):
    """
    Multi-waypoint OSRM route:
      - coords: [(lat,lon), (lat,lon), ...] length >= 2
    Returns:
      {
        "distance_km": float,
        "duration_min": float,
        "geometry": [[lon,lat], ...]  (if include_geometry)
      }
    """
    if not coords or len(coords) < 2:
        return {"distance_km": 0.0, "duration_min": 0.0, "geometry": []}

    coord_str = _to_osrm_coord_str(coords)
    if include_geometry:
        url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    else:
        url = f"{OSRM_URL}/route/v1/driving/{coord_str}?overview=false"

    res = _get(url)
    _check_osrm(res, "ROUTE_FULL")

    r = res["routes"][0]
    out = {
        "distance_km": r["distance"] / 1000.0,
        "duration_min": r["duration"] / 60.0,
        "geometry": []
    }
    if include_geometry:
        out["geometry"] = r["geometry"]["coordinates"]
    return out


# =============================================================
# HAVERSINE (vol d’oiseau)
# =============================================================
def haversine(a: Coord, b: Coord) -> float:
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
def find_nearest_station(current_coord: Coord, stations: List[Dict[str, Any]]):
    best = None
    best_dist = float("inf")

    for st in stations:
        d = haversine(current_coord, (st["lat"], st["lon"]))
        if d < best_dist:
            best = st
            best_dist = d

    if best is None:
        return None

    best = dict(best)
    best["distance_km"] = best_dist
    return best


# =============================================================
# DISTANCE OSRM VERS BORNE
# =============================================================
def osrm_distance_to_station(current_coord: Coord, station: Dict[str, Any]):
    return osrm_route([
        current_coord,
        (station["lat"], station["lon"])
    ])
