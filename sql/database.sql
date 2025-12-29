-- =========================
--  BASE DE DONNÉES
-- =========================
DROP DATABASE IF EXISTS smart_delivery;
CREATE DATABASE smart_delivery;
USE smart_delivery;

-- =========================
--  TABLE LIVREURS
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
--  TABLE COMMANDES
--  (client_id + livreur_id supporté)
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

    client_id INT,
    statut VARCHAR(20) DEFAULT 'en_attente',

    -- 🆕 colonne affectation livreur
    livreur_id VARCHAR(20) NULL,

    CONSTRAINT fk_commande_livreur
        FOREIGN KEY (livreur_id)
        REFERENCES livreurs(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
--  TABLE USERS
-- =========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    role ENUM('admin','livreur','client') NOT NULL,

    livreur_id VARCHAR(20),
    client_id INT,

    FOREIGN KEY (livreur_id) REFERENCES livreurs(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================
-- HASHAGE AUTOMATIQUE SHA256
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
--  ADMIN PAR DÉFAUT
--  (mot de passe -> adminensa)
-- =========================
INSERT INTO users(email, password_hash, role, livreur_id, client_id)
VALUES(
    'Admin@smartdelivery.com',
    'adminensa',
    'admin',
    NULL,
    NULL
);
CREATE TABLE clients (
    id VARCHAR(20) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    email VARCHAR(120) UNIQUE
);

INSERT INTO livreurs
(id, nom, latitude_depart, longitude_depart,
 capacite_poids, capacite_volume,
 heure_debut, heure_fin,
 vitesse_moyenne, cout_km,
 telephone, email)
VALUES
('LIV1','Ahmed Karim',33.5731,-7.5898,150,2,'08:00','18:00',45,2.5,'0600000001','ahmed@sd.com'),
('LIV2','Sara Ben',34.0209,-6.8416,130,1.8,'08:00','18:00',42,2.6,'0600000002','sara@sd.com'),
('LIV3','Youssef Ali',35.7595,-5.83395,160,2,'08:00','18:00',40,2.7,'0600000003','youssef@sd.com'),
('LIV4','Fatima Zahra',33.8815,-6.8498,140,1.9,'08:00','18:00',43,2.4,'0600000004','fatima@sd.com'),
('LIV5','Omar Said',31.6340,-8.0089,170,2.2,'08:00','18:00',44,2.3,'0600000005','omar@sd.com'),
('LIV6','Hajar Lina',34.6867,-1.9114,150,2,'08:00','18:00',41,2.8,'0600000006','hajar@sd.com'),
('LIV7','Rachid Noor',32.2994,-9.2372,145,1.7,'08:00','18:00',39,2.9,'0600000007','rachid@sd.com'),
('LIV8','Amine Idrissi',34.0132,-6.8326,155,2,'08:00','18:00',46,2.5,'0600000008','amine@sd.com'),
('LIV9','Khadija Rami',35.1680,-2.9335,150,2,'08:00','18:00',43,2.6,'0600000009','khadija@sd.com'),
('LIV10','Walid Taha',33.5951,-7.6188,165,2.3,'08:00','18:00',47,2.4,'0600000010','walid@sd.com');

INSERT INTO clients(id, nom, telephone, email) VALUES
('CL001','Client One','0601111111','client1@sd.com'),
('CL002','Client Two','0602222222','client2@sd.com'),
('CL003','Client Three','0603333333','client3@sd.com'),
('CL004','Client Four','0604444444','client4@sd.com'),
('CL005','Client Five','0605555555','client5@sd.com'),
('CL006','Client Six','0606666666','client6@sd.com'),
('CL007','Client Seven','0607777777','client7@sd.com'),
('CL008','Client Eight','0608888888','client8@sd.com'),
('CL009','Client Nine','0609999999','client9@sd.com'),
('CL010','Client Ten','0610000000','client10@sd.com');

INSERT INTO users(email, password_hash, role, client_id, livreur_id) VALUES
('client1@sd.com','client123','client','CL001',NULL),
('client2@sd.com','client123','client','CL002',NULL),
('client3@sd.com','client123','client','CL003',NULL),
('client4@sd.com','client123','client','CL004',NULL),
('client5@sd.com','client123','client','CL005',NULL),
('client6@sd.com','client123','client','CL006',NULL),
('client7@sd.com','client123','client','CL007',NULL),
('client8@sd.com','client123','client','CL008',NULL),
('client9@sd.com','client123','client','CL009',NULL),
('client10@sd.com','client123','client','CL010',NULL);

INSERT INTO users(email, password_hash, role, livreur_id, client_id) VALUES
('ahmed@sd.com','livreur123','livreur','LIV1',NULL),
('sara@sd.com','livreur123','livreur','LIV2',NULL),
('youssef@sd.com','livreur123','livreur','LIV3',NULL),
('fatima@sd.com','livreur123','livreur','LIV4',NULL),
('omar@sd.com','livreur123','livreur','LIV5',NULL),
('hajar@sd.com','livreur123','livreur','LIV6',NULL),
('rachid@sd.com','livreur123','livreur','LIV7',NULL),
('amine@sd.com','livreur123','livreur','LIV8',NULL),
('khadija@sd.com','livreur123','livreur','LIV9',NULL),
('walid@sd.com','livreur123','livreur','LIV10',NULL);

INSERT INTO commandes
(id, adresse, latitude, longitude, poids, volume,
 fenetre_debut, fenetre_fin, priorite, temps_service,
 client_id, livreur_id, statut)
VALUES
('CMD001','Guéliz, Marrakech',31.6340,-7.9995,5,12,'09:00','11:00',1,10,'CL001',NULL,'en_attente'),
('CMD002','Jemaa el-Fna',31.6236,-7.9930,3,8,'10:00','12:00',2,8,'CL002',NULL,'en_attente'),
('CMD003','Hivernage',31.6178,-8.0101,12,25,'08:30','11:30',3,12,'CL003',NULL,'en_attente'),
('CMD004','Quartier Palmier',31.6422,-7.9922,7,14,'13:00','15:30',1,10,'CL004',NULL,'en_attente'),
('CMD005','Route de Casablanca',31.6610,-7.9810,15,30,'14:00','16:00',2,12,'CL005',NULL,'en_attente'),

('CMD006','Marrakech Plaza',31.6339,-8.0040,4,9,'09:00','10:30',1,7,'CL006',NULL,'en_attente'),
('CMD007','Daoudiat',31.6490,-8.0002,9,19,'11:00','13:00',2,9,'CL007',NULL,'en_attente'),
('CMD008','Bab Doukkala',31.6318,-7.9960,6,13,'10:30','12:30',1,8,'CL008',NULL,'en_attente'),
('CMD009','Sidi Ghanem',31.6568,-8.0483,20,40,'12:00','15:00',3,15,'CL009',NULL,'en_attente'),
('CMD010','Massira 1',31.6005,-8.0362,8,18,'16:00','18:00',1,10,'CL010',NULL,'en_attente'),

('CMD011','Sidi Youssef Ben Ali',31.6074,-7.9730,10,22,'09:00','11:00',2,11,'CL001',NULL,'en_attente'),
('CMD012','Route Ourika',31.5510,-7.9821,5,10,'10:00','12:00',1,7,'CL002',NULL,'en_attente'),
('CMD013','Mellah',31.6195,-7.9822,3,6,'11:00','13:00',2,6,'CL003',NULL,'en_attente'),
('CMD014','Kasbah',31.6142,-7.9892,12,25,'14:00','16:00',3,12,'CL004',NULL,'en_attente'),
('CMD015','Agdal',31.5855,-7.9890,9,18,'15:00','17:30',1,9,'CL005',NULL,'en_attente'),

('CMD016','Menara Mall',31.6112,-8.0177,6,13,'09:00','10:30',1,8,'CL006',NULL,'en_attente'),
('CMD017','Route Targa',31.6480,-8.0510,14,30,'11:00','13:00',2,12,'CL007',NULL,'en_attente'),
('CMD018','Avenue Mohammed VI',31.6078,-8.0043,7,15,'12:00','14:00',1,9,'CL008',NULL,'en_attente'),
('CMD019','Mhamid',31.5841,-8.0399,5,11,'13:30','15:30',2,8,'CL009',NULL,'en_attente'),
('CMD020','Azli',31.5865,-8.0540,3,7,'14:00','16:00',1,6,'CL010',NULL,'en_attente'),

('CMD021','Targa Centre',31.6512,-8.0655,6,14,'08:30','10:30',1,8,'CL001',NULL,'en_attente'),
('CMD022','Al Massira 2',31.6031,-8.0257,8,17,'10:00','12:00',2,9,'CL002',NULL,'en_attente'),
('CMD023','Hivernage Residence',31.6160,-8.0091,10,22,'12:30','14:30',2,12,'CL003',NULL,'en_attente'),
('CMD024','Bab Agnaou',31.6149,-7.9880,4,8,'13:00','15:00',1,7,'CL004',NULL,'en_attente'),
('CMD025','Route Amizmiz',31.5566,-8.0611,15,35,'15:00','17:30',3,14,'CL005',NULL,'en_attente'),

('CMD026','Caméléon Mall',31.6333,-8.0110,9,20,'09:00','11:00',1,10,'CL006',NULL,'en_attente'),
('CMD027','Sidi Abbad',31.6552,-7.9755,7,15,'11:00','13:00',2,10,'CL007',NULL,'en_attente'),
('CMD028','Hay Hassani',31.6432,-7.9621,6,12,'12:30','14:30',1,9,'CL008',NULL,'en_attente'),
('CMD029','Hay Mohammedi',31.6460,-7.9707,5,11,'14:00','16:00',1,8,'CL009',NULL,'en_attente'),
('CMD030','Bab El Khemis',31.6374,-7.9819,4,9,'15:00','17:00',2,7,'CL010',NULL,'en_attente'),

('CMD031','Gueliz Victor Hugo',31.6349,-8.0061,8,18,'09:00','11:00',1,9,'CL001',NULL,'en_attente'),
('CMD032','Semlalia',31.6405,-8.0201,10,23,'10:00','12:00',2,11,'CL002',NULL,'en_attente'),
('CMD033','Inara',31.6120,-7.9650,6,13,'12:00','14:00',1,8,'CL003',NULL,'en_attente'),
('CMD034','Abwab Marrakech',31.6320,-8.0655,12,27,'13:00','15:30',3,13,'CL004',NULL,'en_attente'),
('CMD035','Hay Charaf',31.6038,-7.9672,7,16,'14:30','16:30',2,9,'CL005',NULL,'en_attente'),

('CMD036','M Avenue',31.6108,-8.0112,5,11,'09:30','11:00',1,7,'CL006',NULL,'en_attente'),
('CMD037','Quartier Industriel Sidi Ghanem',31.6577,-8.0500,18,38,'11:00','14:00',3,15,'CL007',NULL,'en_attente'),
('CMD038','Hay Nahda',31.6371,-7.9602,9,19,'13:00','15:00',2,10,'CL008',NULL,'en_attente'),
('CMD039','Hay Mohammadi Extension',31.6498,-7.9666,6,13,'14:00','16:00',1,9,'CL009',NULL,'en_attente'),
('CMD040','Sidi Bel Abbes',31.6509,-7.9855,4,9,'15:00','17:30',1,7,'CL010',NULL,'en_attente');