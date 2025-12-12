from typing import List, Tuple


def route_distance(route: List[int], dist_matrix: List[List[float]]) -> float:
    return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))



def two_opt(route: List[int], dist_matrix: List[List[float]]) -> Tuple[List[int], float]:
    best = route[:]
    best_dist = route_distance(best, dist_matrix)
    improved = True

    while improved:
        improved = False
        for i in range(1, len(best)-2):
            for j in range(i+1, len(best)-1):
                if j - i == 1:
                    continue
                new_route = best[:]
                new_route[i:j] = reversed(best[i:j])
                new_dist = route_distance(new_route, dist_matrix)

                if new_dist < best_dist - 1e-6:
                    best, best_dist = new_route, new_dist
                    improved = True
    return best, best_dist



def three_opt(route: List[int], dist_matrix: List[List[float]]) -> Tuple[List[int], float]:
    best = route[:]
    best_dist = route_distance(best, dist_matrix)
    n = len(route)
    improved = True

    while improved:
        improved = False
        for i in range(1, n - 4):
            for j in range(i + 2, n - 2):
                for k in range(j + 2, n):

                    A, B, C, D = best[:i], best[i:j], best[j:k], best[k:]

                    candidates = [
                        A + B[::-1] + C + D,
                        A + B + C[::-1] + D,
                        A + B[::-1] + C[::-1] + D,
                        A + C + B + D,
                        A + C[::-1] + B + D,
                        A + C + B[::-1] + D,
                        A + C[::-1] + B[::-1] + D,
                    ]

                    for cand in candidates:
                        new_dist = route_distance(cand, dist_matrix)
                        if new_dist < best_dist - 1e-6:
                            best = cand
                            best_dist = new_dist
                            improved = True
                            break
                if improved:
                    break
            if improved:
                break
    return best, best_dist
