 #pip install -r requirements.txt

===========================================================================================================================================================================
🚚 OSRM – Moteur de calcul d’itinéraires utilisé dans SmartDelivery

SmartDelivery utilise OSRM (Open Source Routing Machine) pour calculer :

les distances réelles sur route,

les durées de trajet précises,

les matrices distance/temps entre plusieurs points,

les itinéraires optimisés pour les livreurs.

OSRM fournit une cartographie routière extrêmement rapide, bien plus précise qu’une distance “à vol d’oiseau” ou qu’une estimation heuristique.
Dans ce projet, il est utilisé pour générer des distances et durées qui alimentent les algorithmes d’optimisation (NN, 2-OPT, 3-OPT, Branch & Bound, gestion de batterie, bornes de recharge, etc.).
=================================================
🛠 Installation (Docker uniquement)

Aucune installation locale de OSRM n’est nécessaire : Docker suffit.

1. Installer Docker Desktop

Téléchargement : https://www.docker.com/products/docker-desktop/

Assurez-vous ensuite que Docker fonctionne correctement :

docker --version
==============================================================
Le dossier :

/osrm_data/

contient déjà :

le fichier cartographique morocco-latest.osm.pbf

tous les fichiers .osrm générés (.osrm, .osrm.cells, .osrm.names, .osrm.partition, etc.)

➡️ Vous n’avez donc pas besoin d’exécuter :
osrm-extract, osrm-partition, osrm-customize

Toute la préparation a déjà été faite.

=================================================================

***** Aprés lancement de Docker Desktop *****

🚀 Démarrer OSRM en 1 commande

Placez-vous à la racine du projet et lancez simplement :

docker run -d -p 5001:5000 \
    -v $(pwd)/osrm_data:/data \
    osrm/osrm-backend osrm-routed /data/morocco-latest.osrm


OSRM sera accessible sur :

http://localhost:5001

