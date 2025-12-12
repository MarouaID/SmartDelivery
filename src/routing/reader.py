# src/routing/reader.py

from src.models import Livreur, Commande

def parse_affectations(json_affectations: dict):
    livreurs = []
    commandes_map = {}

    for livreur_id, cmds in json_affectations.items():
        
        # Création d'un livreur générique (personne 1 ne fournit pas encore ses données)
        livreur = Livreur(
            id=livreur_id,
            nom=livreur_id,
            latitude_depart=31.63,
            longitude_depart=-7.99,
            capacite_poids=500,
            capacite_volume=3.0,
            heure_debut="08:00",
            heure_fin="18:00",
            vitesse_moyenne=40,
            cout_km=0.5
        )

        livreurs.append(livreur)

        # Conversion des commandes
        commandes_objs = []
        for c in cmds:
            commandes_objs.append(
                Commande(
                    id=c["id"],
                    adresse=c["adresse"],
                    latitude=c["latitude"],
                    longitude=c["longitude"],
                    poids=c["poids"],
                    volume=c["volume"],
                    fenetre_debut=c["fenetre_debut"],
                    fenetre_fin=c["fenetre_fin"],
                    priorite=c["priorite"],
                    temps_service=c["temps_service"]
                )
            )

        commandes_map[livreur_id] = commandes_objs

    return livreurs, commandes_map
