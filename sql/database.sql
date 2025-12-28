CREATE DATABASE smart_delivery;

USE smart_delivery;

CREATE TABLE livreurs (
    id VARCHAR(20) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,

    latitude_depart DOUBLE,
    longitude_depart DOUBLE,

    capacite_poids DOUBLE,
    capacite_volume DOUBLE,

    heure_debut VARCHAR(10),
    heure_fin VARCHAR(10),

    vitesse_moyenne DOUBLE,
    cout_km DOUBLE,

    disponible BOOLEAN DEFAULT TRUE,
    telephone VARCHAR(20),
    email VARCHAR(120),

    batterie_max DOUBLE DEFAULT 90,
    batterie_restante DOUBLE DEFAULT 90,
    recharge_rate DOUBLE DEFAULT 1.5
);


CREATE TABLE commandes (
    id VARCHAR(50) PRIMARY KEY,
    adresse VARCHAR(255),
    latitude DOUBLE,
    longitude DOUBLE,
    poids DOUBLE,
    volume DOUBLE,
    fenetre_debut VARCHAR(10),
    fenetre_fin VARCHAR(10),
    priorite INT,
    temps_service INT,
    client_nom VARCHAR(100),
    client_tel VARCHAR(30),
    statut VARCHAR(20) DEFAULT 'en_attente'
);
