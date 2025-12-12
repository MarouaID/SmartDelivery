from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


# ============================================================
#                         COMMANDE
# ============================================================

@dataclass
class Commande:
    """Représente une commande à livrer."""
    id: str
    adresse: str
    latitude: float
    longitude: float
    poids: float                # kg
    volume: float               # m³

    fenetre_debut: str          # HH:MM
    fenetre_fin: str            # HH:MM
    priorite: int               # 1 urgent, 2 normal, 3 flexible
    temps_service: int          # minutes

    client_nom: Optional[str] = None
    client_tel: Optional[str] = None

    statut: str = "en_attente"  # en_attente, assignee, en_cours, livree

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"Commande({self.id}, priorite={self.priorite})"


# ============================================================
#                         LIVREUR
# ============================================================

@dataclass
class Livreur:
    """Représente un livreur + son autonomie électrique."""
    
    # Identité
    id: str
    nom: str

    # Départ
    latitude_depart: float
    longitude_depart: float

    # Capacités véhicule
    capacite_poids: float
    capacite_volume: float

    # Horaires
    heure_debut: str
    heure_fin: str

    # Performance
    vitesse_moyenne: float      # km/h
    cout_km: float              # €/km

    # Options / contact
    disponible: bool = True
    telephone: Optional[str] = None
    email: Optional[str] = None

    # Batterie électrique (pour extension “points recharge”)
    batterie_max: float = 90.0          # 90 minutes d’autonomie
    batterie_restante: float = 90.0     # commence pleine
    recharge_rate: float = 1.5          # 1 min branchée → 1.5 min récupérées

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"Livreur({self.id}, {self.nom})"


# ============================================================
#                          TRAJET
# ============================================================

@dataclass
class Trajet:
    """Résultat d'un routing pour un livreur."""

    livreur_id: str
    commandes: List[str]               # IDs affectées
    ordre_livraison: List[str]         # IDs dans l'ordre optimisé

    # Distances calculées par NN/2opt/3opt
    distance_totale: float             # km
    temps_total: int                   # minutes
    cout_total: float                  # €

    # Distances réelles OSRM
    distance_osrm: float = 0.0         # km
    temps_osrm: float = 0.0            # minutes

    heure_depart: str = ""
    heure_retour_estimee: str = ""

    points_gps: List[Tuple[float, float]] = field(default_factory=list)
    statut: str = "planifie"           # planifie, en_cours, termine

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"Trajet({self.livreur_id}, {len(self.commandes)} commandes)"


# ============================================================
#                        NOTIFICATION
# ============================================================

@dataclass
class Notification:
    """Notification envoyée par le système."""
    id: str
    timestamp: str
    type: str                # affectation, depart, livraison, incident, recharge
    message: str
    destinataire_id: str
    lu: bool = False

    def to_dict(self):
        return asdict(self)
