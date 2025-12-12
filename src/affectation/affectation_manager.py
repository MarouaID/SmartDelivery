from typing import List, Dict
import math
import random
from src.models import Commande, Livreur
from src.utils import DistanceCalculator
from src.affectation.branch_and_bound_allocator import BranchAndBoundAllocator


# ---------------------------------------------------------
# Distance Haversine simple
# ---------------------------------------------------------
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1))*math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# ---------------------------------------------------------
#   K-MEANS ultra simple pour structurer les zones
# ---------------------------------------------------------
def cluster_kmeans_simple(commandes, k=6, iterations=6):

    pts = [(c.latitude, c.longitude) for c in commandes]

    # init aléatoire des centres
    centroids = random.sample(pts, k)

    for _ in range(iterations):
        clusters = [[] for _ in range(k)]

        # Répartition des points
        for c in commandes:
            dists = [distance(c.latitude, c.longitude, cen[0], cen[1]) for cen in centroids]
            idx = dists.index(min(dists))
            clusters[idx].append(c)

        # Recalcul des centres
        new_centroids = []
        for cl in clusters:
            if not cl:
                new_centroids.append(random.choice(pts))
            else:
                lat = sum(c.latitude for c in cl) / len(cl)
                lon = sum(c.longitude for c in cl) / len(cl)
                new_centroids.append((lat, lon))

        centroids = new_centroids

    return clusters, centroids


def selectionner_commandes_eloignees(commandes, n):

    clusters, centroids = cluster_kmeans_simple(commandes, k=n)

    seeds = []
    for i, cl in enumerate(clusters):
        if not cl:
            continue
        cen_lat, cen_lon = centroids[i]
        seed = min(cl, key=lambda c: distance(c.latitude, c.longitude, cen_lat, cen_lon))
        seeds.append(seed)

    
    while len(seeds) < n:
        seeds.append(random.choice(commandes))

    return seeds[:n]


# ---------------------------------------------------------
#   Branch & Bound initial (inchangé sauf poids)
# ---------------------------------------------------------
def branch_and_bound_initial(seeds, livreurs, depot_lat=33.573110, depot_lon=-7.589843):

    cost_matrix = []
    for liv in livreurs:
        row = []
        for cmd in seeds:

            if cmd.poids > liv.capacite_poids or cmd.volume > liv.capacite_volume:
                row.append(99999999)
                continue

            d = distance(depot_lat, depot_lon, cmd.latitude, cmd.longitude)
            cout = d * cmd.priorite
            row.append(cout)

        cost_matrix.append(row)

    allocator = BranchAndBoundAllocator(cost_matrix)
    assignment, _ = allocator.solve()

    affectation = {}
    for i_liv, col in enumerate(assignment):
        if col < len(seeds):
            affectation[livreurs[i_liv].id] = seeds[col]

    return affectation




# -------------------------------
# CONSTRUIRE RESULTAT
# -------------------------------
def construire_resultat(livreurs, commandes):
    resultat = {liv.id: [] for liv in livreurs}
    non_affectees = []

    for cmd in commandes:
        if cmd.statut == "assignee" and hasattr(cmd, "livreur_id"):
            resultat[cmd.livreur_id].append(cmd)
        else:
            non_affectees.append(cmd)

    resume = {
        "affectations": resultat,
        "non_affectees": non_affectees,
        "nb_commandes_affectees": sum(len(v) for v in resultat.values()),
        "nb_commandes_non_affectees": len(non_affectees)
    }

    return resume

# =========================================================
#               AFFECTATION PAR ZONES AMÉLIORÉE
# =========================================================

class AffectationManager:

    def __init__(self):
        self.dist = DistanceCalculator()

    def affecter_commandes(self, livreurs, commandes, DISTANCE_ZONE=1.2):

        # ----------------------------
        # RESET des positions / zones
        # ----------------------------
        for liv in livreurs:
            liv.position = (liv.latitude_depart, liv.longitude_depart)
            liv.zone = None

        # Capacités restantes par livreur
        capacite_restante = {
            liv.id: {
                "poids": liv.capacite_poids,
                "volume": liv.capacite_volume
            }
            for liv in livreurs
        }

        # 1) Commandes encore à traiter
        commandes_restantes = [c for c in commandes if c.statut == "en_attente"]
        commandes_restantes.sort(key=lambda c: c.priorite)

        # 2) Seeds améliorés
        seeds = selectionner_commandes_eloignees(commandes_restantes, len(livreurs))
        assignation_initiale = branch_and_bound_initial(seeds, livreurs)

        # 3) Création des zones + MAJ capacité après seed
        zones = {}
        for liv in livreurs:
            if liv.id in assignation_initiale:
                seed = assignation_initiale[liv.id]

                # On vérifie que le seed rentre dans la capacité restante
                if (seed.poids <= capacite_restante[liv.id]["poids"] and
                        seed.volume <= capacite_restante[liv.id]["volume"]):

                    liv.position = (seed.latitude, seed.longitude)
                    liv.zone = liv.id

                    seed.zone = liv.id
                    seed.statut = "assignee"
                    seed.livreur_id = liv.id

                    # On débite la capacité du livreur
                    capacite_restante[liv.id]["poids"] -= seed.poids
                    capacite_restante[liv.id]["volume"] -= seed.volume

                    zones[liv.id] = [seed]
                else:
                    # seed incompatible en capacité → pas de zone pour ce livreur
                    liv.zone = None

        # 4) Classification des autres commandes dans les zones
        for cmd in commandes_restantes:
            if cmd.statut == "assignee":
                continue

            best_zone = None
            best_dist = 9999

            for liv_id, seeds_zone in zones.items():
                s = seeds_zone[0]
                d = distance(cmd.latitude, cmd.longitude, s.latitude, s.longitude)
                if d < DISTANCE_ZONE and d < best_dist:
                    best_zone = liv_id
                    best_dist = d

            cmd.zone = best_zone  # peut être None → visible par tous

        # 5) Affectation progressive AVEC capacité restante
        while True:
            mouvement = False

            for liv in livreurs:

                cap = capacite_restante[liv.id]

                # Si plus de capacité → ce livreur ne prend plus rien
                if cap["poids"] <= 0 or cap["volume"] <= 0:
                    continue

                visibles = [
                    c for c in commandes_restantes
                    if c.statut == "en_attente"
                    and c.poids <= cap["poids"]
                    and c.volume <= cap["volume"]
                    and (c.zone is None or c.zone == liv.zone)
                ]

                if not visibles:
                    continue

                # Choix de la commande : distance + priorité
                cmd = min(
                    visibles,
                    key=lambda c: 0.7 * distance(
                        liv.position[0], liv.position[1],
                        c.latitude, c.longitude
                    ) + 0.3 * c.priorite
                )

                # Affectation
                cmd.statut = "assignee"
                cmd.livreur_id = liv.id
                liv.position = (cmd.latitude, cmd.longitude)

                # Débit de la capacité restante
                capacite_restante[liv.id]["poids"] -= cmd.poids
                capacite_restante[liv.id]["volume"] -= cmd.volume

                mouvement = True

            if not mouvement:
                break

        return construire_resultat(livreurs, commandes)



livreurs = [
    Livreur(id="L1", nom="Ahmed", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=120, capacite_volume=1.2, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=40, cout_km=0.5),

    Livreur(id="L2", nom="Mounir", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=150, capacite_volume=1.5, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=45, cout_km=0.55),

    Livreur(id="L3", nom="Sara", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=100, capacite_volume=1.0, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=38, cout_km=0.52),

    Livreur(id="L4", nom="Youssef", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=130, capacite_volume=1.3, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=42, cout_km=0.48),

    Livreur(id="L5", nom="Imane", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=110, capacite_volume=1.1, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=37, cout_km=0.50),

    Livreur(id="L6", nom="Rachid", latitude_depart=33.573110, longitude_depart=-7.589843,
            capacite_poids=140, capacite_volume=1.4, heure_debut="08:00", heure_fin="18:00",
            vitesse_moyenne=43, cout_km=0.53)
    ]

import random
from src.models import Commande

# Centres des zones
ZONES = {
    "Z1": (33.5862, -7.6316),   # Maarif
    "Z2": (33.6064, -7.5308),   # Ain Sebaa
    "Z3": (33.5820, -7.7020),   # Ain Diab
    "Z4": (33.5323, -7.6535),   # Sidi Maarouf
    "Z5": (33.4487, -7.6543),   # Bouskoura
    "Z6": (33.6579, -7.4721),   # Zenata
}

# Taille des clusters (non égale)
REPARTITION = {
    "Z1": 14,
    "Z2": 8,
    "Z3": 5,
    "Z4": 9,
    "Z5": 6,
    "Z6": 8
}


def generer_commandes_cluster():
    commandes = []
    id_counter = 1

    for zone, nb_cmds in REPARTITION.items():
        lat_centre, lon_centre = ZONES[zone]

        for _ in range(nb_cmds):
            # Variation locale dans un rayon max 0.8 km
            delta_lat = random.uniform(-0.007, 0.007)
            delta_lon = random.uniform(-0.007, 0.007)

            lat = lat_centre + delta_lat
            lon = lon_centre + delta_lon

            commandes.append(
                Commande(
                    id=f"C{id_counter}",
                    adresse=f"Adresse {zone}-{id_counter}",
                    latitude=lat,
                    longitude=lon,
                    poids=random.randint(5, 35),
                    volume=random.uniform(0.03, 0.20),
                    fenetre_debut="08:00",
                    fenetre_fin="18:00",
                    priorite=random.choice([1, 2, 3]),
                    temps_service=random.randint(5, 12)
                )
            )
            id_counter += 1

    return commandes

commandes = generer_commandes_cluster()

if __name__ == "__main__":
    
    manager = AffectationManager()

    print("\n========================")
    print("  ⚙️  AFFECTATION KANNEX")
    print("========================\n")

    print("📦 Nombre de livreurs :", len(livreurs))
    print("📦 Nombre de commandes :", len(commandes))

    # Lancer l'affectation AVEC ZONES
    resultat = manager.affecter_commandes(livreurs, commandes, DISTANCE_ZONE=2)

    print("\n=================================")
    print("  ✅ RÉSULTAT FINAL D'AFFECTATION")
    print("=================================\n")

    for liv in livreurs:
        cmds = resultat["affectations"][liv.id]
        print(f"\n🛵 Livreur {liv.id} ({liv.nom}) a {len(cmds)} commandes :")
        for c in cmds:
            print(f"   - {c.id} | zone={getattr(c, 'zone', None)} | "
                  f"lat={c.latitude:.4f}, lon={c.longitude:.4f}, prio={c.priorite}")

    print("\n📦 Commandes non affectées :", len(resultat["non_affectees"]))
    if resultat["non_affectees"]:
        print("   →", [c.id for c in resultat["non_affectees"]])