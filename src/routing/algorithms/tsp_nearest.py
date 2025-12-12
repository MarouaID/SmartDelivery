import math
from typing import List
from src.routing.types import Coord


def haversine(a: Coord, b: Coord) -> float:
    R = 6371.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    x = (math.sin(dlat / 2)**2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2)
    return 2 * R * math.asin(math.sqrt(x))


def build_distance_matrix(points: List[Coord]) -> List[List[float]]:
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(points[i], points[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def nearest_neighbor_route(dist_matrix: List[List[float]], start: int = 0) -> List[int]:
    n = len(dist_matrix)
    visited = {start}
    route = [start]

    while len(route) < n:
        last = route[-1]
        best_next = None
        best_dist = float("inf")

        for j in range(n):
            if j not in visited:
                d = dist_matrix[last][j]
                if d < best_dist:
                    best_dist = d
                    best_next = j

        route.append(best_next)
        visited.add(best_next)

    return route
