from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Commande:
    """Représente une commande à livrer"""
    id: str
    adresse: str
    latitude: float
    longitude: float
    poids: float  # kg
    volume: float  # m³
    fenetre_debut: str  # Format "HH:MM"
    fenetre_fin: str  # Format "HH:MM"
    priorite: int  # 1=urgent, 2=normal, 3=flexible
    temps_service: int  # minutes pour décharger
    client_nom: Optional[str] = None
    client_tel: Optional[str] = None
    statut: str = "en_attente"  # en_attente, assignee, en_cours, livree
    
    def to_dict(self):
        return asdict(self)
    
    def __repr__(self):
        return f"Commande({self.id}, priorite={self.priorite})"


@dataclass
class Livreur:
    """Représente un livreur avec ses capacités"""
    id: str
    nom: str
    latitude_depart: float
    longitude_depart: float
    capacite_poids: float  # kg
    capacite_volume: float  # m³
    heure_debut: str  # Format "HH:MM"
    heure_fin: str  # Format "HH:MM"
    vitesse_moyenne: float  # km/h
    cout_km: float  # €/km
    disponible: bool = True
    telephone: Optional[str] = None
    email: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    def __repr__(self):
        return f"Livreur({self.id}, {self.nom})"


@dataclass
class Trajet:
    """Résultat d'optimisation pour un livreur"""
    livreur_id: str
    commandes: List[str]  # Liste des IDs de commandes
    ordre_livraison: List[int]  # Indices d'ordre
    distance_totale: float  # km
    temps_total: int  # minutes
    cout_total: float  # €
    heure_depart: str
    heure_retour_estimee: str
    points_gps: List[tuple] = field(default_factory=list)
    statut: str = "planifie"  # planifie, en_cours, termine
    
    def to_dict(self):
        return asdict(self)
    
    def __repr__(self):
        return f"Trajet({self.livreur_id}, {len(self.commandes)} commandes)"


@dataclass
class Notification:
    """Notification système"""
    id: str
    timestamp: str
    type: str  # affectation, depart, livraison, incident
    message: str
    destinataire_id: str
    lu: bool = False
    
    def to_dict(self):
        return asdict(self)
