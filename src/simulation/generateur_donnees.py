import random
from typing import List, Dict
from src.models import Commande, Livreur


class GenerateurDonnees:
    """
    Génère des livreurs et des commandes pour les scénarios de simulation.
    Compatible avec ScenarioNormal, ScenarioPic, ScenarioIncident.
    """

    def __init__(self, config=None):
        """
        Le simulateur appelle : GenerateurDonnees(config)
        Donc l'argument doit être accepté même s’il est None.
        """
        self.config = config or {}

        # Centre géographique pour générer des points (Marrakech)
        self.centre_lat = 31.63
        self.centre_lon = -8.01

    # -----------------------------------------------------
    #                GENERATION DES LIVREURS
    # -----------------------------------------------------
    def generer_livreurs(self, n: int) -> List[Livreur]:
        livreurs = []

        for i in range(n):
            livreur = Livreur(
                id=f"LIV{i+1}",
                nom=f"Livreur {i+1}",
                latitude_depart=self.centre_lat + random.uniform(-0.02, 0.02),
                longitude_depart=self.centre_lon + random.uniform(-0.02, 0.02),
                capacite_poids=random.randint(30, 60),   # kg
                capacite_volume=random.randint(20, 40),  # m³
                heure_debut="08:00",
                heure_fin="18:00",
                vitesse_moyenne=random.uniform(30, 45),  # km/h
                cout_km=random.uniform(0.4, 0.8),
                disponible=True,
                telephone="0600000000",
                email=f"livreur{i+1}@smartdelivery.com"
            )
            livreurs.append(livreur)

        return livreurs

    # -----------------------------------------------------
    #                GENERATION DES COMMANDES
    # -----------------------------------------------------
    def generer_commandes(self, n: int, distribution_priorites: Dict[str, float]) -> List[Commande]:
        """
        Génère n commandes avec une distribution :
        urgent / normal / flexible
        """
        commandes = []

        for i in range(n):

            # --- Déterminer la priorité selon la distribution ---
            r = random.random()
            urgent = distribution_priorites.get('urgent', 0)
            normal = distribution_priorites.get('normal', 0)

            if r < urgent:
                priorite = 1
            elif r < urgent + normal:
                priorite = 2
            else:
                priorite = 3

            commande = Commande(
                id=f"CMD{i+1}",
                adresse=f"Adresse {i+1}",
                latitude=self.centre_lat + random.uniform(-0.03, 0.03),
                longitude=self.centre_lon + random.uniform(-0.03, 0.03),
                poids=random.uniform(2, 12),         # kg
                volume=random.uniform(1, 8),         # m³
                fenetre_debut="09:00",
                fenetre_fin="18:00",
                priorite=priorite,
                temps_service=random.randint(5, 15),
                client_nom="Client X",
                client_tel="0700000000",
                statut="en_attente"
            )

            commandes.append(commande)

        return commandes

    # -----------------------------------------------------
    #        GENERATION D’UNE ZONE DENSE (ScenarioPic)
    # -----------------------------------------------------
    def generer_zone_dense(self, n: int, lat: float, lon: float, rayon_km: float) -> List[Commande]:

        commandes = []

        # Conversion km → degrés (approximation)
        rayon_deg = rayon_km / 111

        for i in range(n):
            commande = Commande(
                id=f"CMD_ZONE{i+1}",
                adresse=f"Zone dense {i+1}",
                latitude=lat + random.uniform(-rayon_deg, rayon_deg),
                longitude=lon + random.uniform(-rayon_deg, rayon_deg),
                poids=random.uniform(3, 10),
                volume=random.uniform(1, 6),
                fenetre_debut="09:00",
                fenetre_fin="17:00",
                priorite=random.choice([1, 2]),  # zone dense = plus urgent
                temps_service=random.randint(5, 10),
                client_nom="Client Y",
                client_tel="0600000000",
                statut="en_attente"
            )
            commandes.append(commande)

        return commandes
