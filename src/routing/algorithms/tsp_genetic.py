# src/routing/algorithms/tsp_genetic.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import random
import math


# =========================
# Helpers temps
# =========================
def hhmm_to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Distance 'vol d’oiseau' en km."""
    R = 6371.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(x))


# =========================
# Réglages GA
# =========================
@dataclass
class GAConfig:
    population_size: int = 25
    generations: int = 120
    elite_ratio: float = 0.10
    mutation_rate: float = 0.15
    tournament_k: int = 3
    # “secouer” un peu pour éviter stagnation
    random_immigrants_ratio: float = 0.04
    seed: Optional[int] = None





# =========================
# Fitness multi-contrainte
# =========================
def _priority_weight(prio: int) -> float:
    # 1 urgent -> pénalité forte
    if prio == 1:
        return 6.0
    if prio == 2:
        return 3.0
    return 1.5


def _nearest_station_detour_minutes(
    current_coord: Tuple[float, float],
    stations: List[Dict[str, Any]],
    speed_kmh: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Retourne (temps_detour_min_estime, station)
    estimation simple : haversine / speed
    """
    best = None
    best_km = float("inf")
    for st in stations:
        st_coord = (st["lat"], st["lon"])
        d = haversine_km(current_coord, st_coord)
        if d < best_km:
            best_km = d
            best = st
    # temps aller vers borne
    time_min = (best_km / max(speed_kmh, 1e-6)) * 60.0
    return time_min, best


def evaluate_route_constraints(
    route: List[int],
    coords: List[Tuple[float, float]],
    commandes: List[Any],
    livreur: Any,
    dist_matrix: List[List[float]],
    time_matrix: List[List[float]],
    stations: List[Dict[str, Any]],
) -> float:
    """
    Fitness à MINIMISER.
    route: [0, i, j, ...] indices dans coords (1..n commandes)
    """

    # ----- paramètres journée -----
    start_min = hhmm_to_minutes(getattr(livreur, "heure_debut", "08:00"))
    end_min = hhmm_to_minutes(getattr(livreur, "heure_fin", "18:00"))

    current_time = float(start_min)

    # ----- batterie -----
    batterie_max = float(getattr(livreur, "batterie_max", 90.0))
    batterie = float(getattr(livreur, "batterie_restante", batterie_max))
    recharge_rate = float(getattr(livreur, "recharge_rate", 1.5))  # 1 min charge => 1.5 min autonomie
    speed_kmh = float(getattr(livreur, "vitesse_moyenne", 30.0))

    # ----- score de base : distance + temps -----
    total_dist = 0.0
    total_time = 0.0

    # ----- pénalités -----
    penalty_late = 0.0
    penalty_overtime = 0.0
    penalty_battery = 0.0

    # mapping idx -> commande (idx 1..n)
    # coords[0] = depot, coords[i] = commande i-1
    def cmd_of_index(idx: int):
        return commandes[idx - 1]

    prev = route[0]  # 0

    for idx in route[1:]:
        # segment OSRM-table
        seg_dist = dist_matrix[prev][idx]
        seg_time = time_matrix[prev][idx]

        # ============ BATTERIE ============
        if seg_time > batterie:
            # option “recharge virtuelle”
            # on estime détour + recharge (sans recalcul OSRM)
            detour_to_station_min, st = _nearest_station_detour_minutes(coords[prev], stations, speed_kmh)

            # si même aller à une borne dépasse la batterie -> pénalité énorme
            if detour_to_station_min > batterie:
                penalty_battery += 5000.0 + 100.0 * (detour_to_station_min - batterie)
                # on “force” recharge quand même
            else:
                # consommer détour vers borne
                total_time += detour_to_station_min
                current_time += detour_to_station_min
                batterie -= detour_to_station_min

            # recharge jusqu’à plein
            manque = batterie_max - batterie
            charge_time = manque / max(recharge_rate, 1e-6)
            total_time += charge_time
            current_time += charge_time
            batterie = batterie_max

            # pénalité légère pour détour (on veut éviter recharges trop fréquentes)
            penalty_battery += 25.0 + 0.5 * charge_time

        # après recharge éventuelle, faire le segment normal
        total_dist += seg_dist
        total_time += seg_time
        current_time += seg_time
        batterie -= seg_time

        # ============ FENÊTRES HORAIRES + SERVICE ============
        if idx != 0:
            c = cmd_of_index(idx)
            w_start = hhmm_to_minutes(getattr(c, "fenetre_debut", "00:00"))
            w_end = hhmm_to_minutes(getattr(c, "fenetre_fin", "23:59"))
            service = float(getattr(c, "temps_service", 0))

            # attendre si trop tôt
            if current_time < w_start:
                wait = (w_start - current_time)
                current_time += wait
                total_time += wait

            # retard si trop tard
            if current_time > w_end:
                late = current_time - w_end
                prio = int(getattr(c, "priorite", 2))
                penalty_late += late * _priority_weight(prio)

            # service time
            current_time += service
            total_time += service

        # ============ FIN DE JOURNÉE ============
        if current_time > end_min:
            # pénalité énorme (on veut que GA évite dépasser)
            overtime = current_time - end_min
            penalty_overtime += 2000.0 + 25.0 * overtime

        prev = idx

    # Score final: distance + (temps) + pénalités
    # (tu peux ajuster les poids)
    score = (
        1.0 * total_dist +
        0.30 * total_time +           # temps important
        1.20 * penalty_late +         # retard pénalisé fort
        1.00 * penalty_battery +      # recharges pénalisées
        1.50 * penalty_overtime       # dépassement journée très pénalisé
    )
    return score


# =========================
# Opérateurs GA (TSP)
# =========================
def _make_individual_from_seed(seed_route: List[int]) -> List[int]:
    # route = [0, ...] ; on permute tout sauf 0
    genes = seed_route[1:]
    random.shuffle(genes)
    return [0] + genes


def _ordered_crossover(p1: List[int], p2: List[int]) -> List[int]:
    """
    OX crossover TSP (en gardant 0 au début).
    """
    a = p1[1:]
    b = p2[1:]
    n = len(a)
    if n <= 2:
        return p1[:]

    i, j = sorted(random.sample(range(n), 2))
    child = [None] * n
    child[i:j] = a[i:j]

    fill = [x for x in b if x not in child[i:j]]
    ptr = 0
    for k in range(n):
        if child[k] is None:
            child[k] = fill[ptr]
            ptr += 1

    return [0] + child


def _mutate_swap(route: List[int]) -> List[int]:
    r = route[:]
    if len(r) <= 3:
        return r
    i, j = random.sample(range(1, len(r)), 2)
    r[i], r[j] = r[j], r[i]
    return r


def _mutate_reverse(route: List[int]) -> List[int]:
    r = route[:]
    if len(r) <= 4:
        return r
    i, j = sorted(random.sample(range(1, len(r)), 2))
    r[i:j] = reversed(r[i:j])
    return r


def _tournament_select(pop: List[List[int]], scores: List[float], k: int) -> List[int]:
    idxs = random.sample(range(len(pop)), k)
    best = min(idxs, key=lambda t: scores[t])
    return pop[best]


# =========================
# API PRINCIPALE
# =========================
def genetic_optimize_advanced(
    seed_route: List[int],
    coords: List[Tuple[float, float]],
    commandes: List[Any],
    livreur: Any,
    dist_matrix: List[List[float]],
    time_matrix: List[List[float]],
    stations: List[Dict[str, Any]],
    cfg: Optional[GAConfig] = None,
) -> List[int]:
    """
    Retourne une route améliorée (TSP) au format [0, ...].
    seed_route: sortie de 3-opt (liste d'indices coords)
    """

    cfg = cfg or GAConfig()
    if cfg.seed is not None:
        random.seed(cfg.seed)

    # sécurité : route commence par 0
    if not seed_route or seed_route[0] != 0:
        # on force 0 en tête si nécessaire
        seed_route = [0] + [x for x in seed_route if x != 0]

    n = len(seed_route) - 1
    if n <= 2:
        return seed_route[:]

    # ---- init population ----
    population: List[List[int]] = []
    population.append(seed_route[:])  # garder seed tel quel
    while len(population) < cfg.population_size:
        population.append(_make_individual_from_seed(seed_route))

    def score_of(ind: List[int]) -> float:
        return evaluate_route_constraints(
            route=ind,
            coords=coords,
            commandes=commandes,
            livreur=livreur,
            dist_matrix=dist_matrix,
            time_matrix=time_matrix,
            stations=stations,
        )

    # ---- évolution ----
    elite_count = max(1, int(cfg.elite_ratio * cfg.population_size))

    best = population[0]
    best_score = score_of(best)

    for _gen in range(cfg.generations):
        scores = [score_of(ind) for ind in population]

        # update best
        gen_best_idx = min(range(len(population)), key=lambda i: scores[i])
        if scores[gen_best_idx] < best_score:
            best_score = scores[gen_best_idx]
            best = population[gen_best_idx][:]

        # elites
        elite_idxs = sorted(range(len(population)), key=lambda i: scores[i])[:elite_count]
        new_pop = [population[i][:] for i in elite_idxs]

        # immigrants aléatoires
        immigrants = int(cfg.random_immigrants_ratio * cfg.population_size)
        for _ in range(immigrants):
            new_pop.append(_make_individual_from_seed(seed_route))

        # reproduction
        while len(new_pop) < cfg.population_size:
            p1 = _tournament_select(population, scores, cfg.tournament_k)
            p2 = _tournament_select(population, scores, cfg.tournament_k)

            child = _ordered_crossover(p1, p2)

            # mutation
            if random.random() < cfg.mutation_rate:
                if random.random() < 0.5:
                    child = _mutate_swap(child)
                else:
                    child = _mutate_reverse(child)

            new_pop.append(child)

        population = new_pop

    return best