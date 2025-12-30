DROP DATABASE IF EXISTS smart_delivery;
CREATE DATABASE smart_delivery;
USE smart_delivery;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS commandes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS livreurs;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- LIVREURS
-- =========================
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

-- =========================
-- CLIENTS
-- =========================
CREATE TABLE clients (
    id VARCHAR(20) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    email VARCHAR(120) UNIQUE
);

-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','livreur','client') NOT NULL,
    livreur_id VARCHAR(20),
    client_id VARCHAR(20),
    FOREIGN KEY (livreur_id) REFERENCES livreurs(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
-- COMMANDES
-- =========================
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
    client_id VARCHAR(20) NOT NULL,
    livreur_id VARCHAR(20),
    statut VARCHAR(20) DEFAULT 'en_attente',
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (livreur_id) REFERENCES livreurs(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
-- PASSWORD HASH TRIGGERS
-- =========================
DELIMITER $$

CREATE TRIGGER hash_password_before_insert
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    SET NEW.password_hash = SHA2(NEW.password_hash, 256);
END$$

CREATE TRIGGER hash_password_before_update
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    IF NEW.password_hash <> OLD.password_hash THEN
        SET NEW.password_hash = SHA2(NEW.password_hash, 256);
    END IF;
END$$

DELIMITER ;

-- =========================
-- DATA INSERTION
-- =========================

INSERT INTO livreurs VALUES
('LIV1','Ahmed Karim',33.5731,-7.5898,150,2,'08:00','18:00',45,2.5,1,'0600000001','ahmed@sd.com',90,90,1.5),
('LIV2','Sara Ben',34.0209,-6.8416,130,1.8,'08:00','18:00',42,2.6,1,'0600000002','sara@sd.com',90,90,1.5),
('LIV3','Youssef Ali',35.7595,-5.83395,160,2,'08:00','18:00',40,2.7,1,'0600000003','youssef@sd.com',90,90,1.5),
('LIV4','Fatima Zahra',33.8815,-6.8498,140,1.9,'08:00','18:00',43,2.4,1,'0600000004','fatima@sd.com',90,90,1.5);

INSERT INTO clients VALUES
('CL001','Client One','0601111111','client1@sd.com'),
('CL002','Client Two','0602222222','client2@sd.com'),
('CL003','Client Three','0603333333','client3@sd.com'),
('CL004','Client Four','0604444444','client4@sd.com');

-- ADMIN (password = adminensa)
INSERT INTO users(email,password_hash,role,client_id,livreur_id)
VALUES ('admin@smartdelivery.com','adminensa','admin',NULL,NULL);

INSERT INTO users(email,password_hash,role,client_id,livreur_id) VALUES
('client1@sd.com','client123','client','CL001',NULL),
('client2@sd.com','client123','client','CL002',NULL),
('client3@sd.com','client123','client','CL003',NULL),
('client4@sd.com','client123','client','CL004',NULL),
('ahmed@sd.com','livreur123','livreur',NULL,'LIV1'),
('sara@sd.com','livreur123','livreur',NULL,'LIV2'),
('youssef@sd.com','livreur123','livreur',NULL,'LIV3'),
('fatima@sd.com','livreur123','livreur',NULL,'LIV4');

INSERT INTO commandes VALUES
('CMD004998112345671891011234','Daoudiat',31.6490,-8.0002,6,9,'09:00','11:00',1,8,'CL001',NULL,'en_attente'),
('CMD005118923456789301212345','Sidi Ghanem',31.6568,-8.0483,18,30,'08:00','12:00',3,15,'CL002',NULL,'en_attente'),
('CMD005229834567892012331456','Agdal',31.5855,-7.9890,9,14,'10:00','13:00',2,9,'CL003',NULL,'en_attente'),
('CMD005337745678901241434567','Mhamid',31.5841,-8.0399,14,22,'11:00','15:00',2,11,'CL004',NULL,'en_attente'),
('CMD005446656789012534515678','Semlalia',31.6405,-8.0201,8,12,'09:30','12:30',1,7,'CL001',NULL,'en_attente'),

('CMD0055555678901234561789','Bab Doukkala',31.6318,-7.9960,5,8,'10:00','12:00',1,6,'CL002',NULL,'en_attente'),
('CMD0056644789012345671890','Azli',31.5865,-8.0540,16,26,'13:00','17:00',3,14,'CL003',NULL,'en_attente'),
('CMD0057733890123456781901','Route de Casablanca',31.6610,-7.9810,20,35,'08:00','11:30',3,16,'CL004',NULL,'en_attente'),
('CMD0058822901234567819012','Victor Hugo',31.6349,-8.0061,7,11,'09:00','11:00',1,7,'CL001',NULL,'en_attente'),
('CMD0059911012345678901123','Menara',31.6112,-8.0177,10,18,'14:00','17:00',2,10,'CL002',NULL,'en_attente'),

('CMD0061000123456789011234','Kasbah',31.6142,-7.9892,12,21,'08:30','11:30',2,12,'CL003',NULL,'en_attente'),
('CMD0062199234567890121345','Mellah',31.6195,-7.9822,4,6,'10:00','12:00',1,5,'CL004',NULL,'en_attente'),
('CMD0063288345678901231456','Targa',31.6480,-8.0510,17,28,'13:00','16:30',3,15,'CL001',NULL,'en_attente'),
('CMD0064377456789012341567','Hay Hassani',31.6432,-7.9621,6,10,'09:00','11:00',1,6,'CL002',NULL,'en_attente'),
('CMD0065466567890123451678','Bab El Khemis',31.6374,-7.9819,9,14,'15:00','18:00',2,9,'CL003',NULL,'en_attente'),

('CMD0066555678901234561789','Sidi Abbad',31.6552,-7.9755,13,23,'10:00','14:00',2,12,'CL004',NULL,'en_attente'),
('CMD0067644789012345671890','Hay Mohammedi',31.6460,-7.9707,8,13,'11:00','14:00',1,8,'CL001',NULL,'en_attente'),
('CMD0068733890123456718901','Inara',31.6120,-7.9650,6,9,'12:00','15:00',1,7,'CL002',NULL,'en_attente'),
('CMD0069822901234567819012','M Avenue',31.6108,-8.0112,5,8,'09:30','11:30',1,6,'CL003',NULL,'en_attente'),
('CMD00709110123456789110123','Quartier Industriel',31.6577,-8.0500,22,40,'08:00','13:00',3,18,'CL004',NULL,'en_attente');
