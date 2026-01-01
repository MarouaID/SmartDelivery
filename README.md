 #pip install -r requirements.txt

=============================================================================================================
🗺️ Routing & OSRM (Open Source Routing Machine)

Cette partie du projet SmartDelivery utilise OSRM (Open Source Routing Machine) pour calculer :

les distances réelles (km) sur le réseau routier marocain

les temps de trajet réels (minutes)

les matrices de distances/temps utilisées par les algorithmes d’optimisation (NN, 2-OPT, 3-OPT)

OSRM est exécuté exclusivement via Docker, ce qui garantit une installation simple, reproductible et indépendante du système d’exploitation.

⚙️ Pré-requis

Avant de lancer la partie routing :

✅ Docker installé (Windows / Linux / macOS)

✅ Python 3.10+ pour lancer l’API SmartDelivery

❌ Aucune installation locale d’OSRM requise

❌ Aucune compilation manuelle

📦 Données cartographiques utilisées

Le routing est basé sur les données OpenStreetMap du Maroc :

morocco.osm.pbf


📥 Téléchargement (obligatoire une seule fois) :
https://download.geofabrik.de/africa/morocco-latest.osm.pbf

👉 Le fichier doit être placé dans SmartDelivery/osrm/data/morocco-latest.osm.pbf   (apres avoir deposer le fichier installé dans osrm/data le renommé morocco-latest.osm.pbf)

⚠️ Le fichier .osm.pbf n’est pas versionné sur GitHub (trop volumineux).

🐳 Génération des fichiers OSRM avec Docker

//. Installer Docker (si ce n’est pas déjà fait)

Téléchargez Docker Desktop :

👉 https://www.docker.com/products/docker-desktop/

Vérifiez l’installation :

    docker --version

lancé docker desktop puis :
    (là où se trouve morocco.osm.pbf) :

1️⃣ Extraction des données
    docker run -t -v ${PWD}:/data osrm/osrm-backend \
    osrm-extract -p /opt/car.lua /data/morocco.osm.pbf

2️⃣ Partitionnement (algorithme MLD)
    docker run -t -v ${PWD}:/data osrm/osrm-backend \
    osrm-partition /data/morocco.osrm

3️⃣ Personnalisation
    docker run -t -v ${PWD}:/data osrm/osrm-backend \
    osrm-customize /data/morocco.osrm


Ces commandes génèrent automatiquement les fichiers .osrm* nécessaires.

🚀 Lancement du serveur OSRM
    docker run -t -i -p 5001:5000 -v ${PWD}:/data \
    osrm/osrm-backend osrm-routed /data/morocco.osrm


📍 Le serveur OSRM est alors accessible sur :

http://localhost:5001
