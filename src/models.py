from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


# ============================================================
#                         COMMANDE
# ============================================================

@dataclass
class Commande:
    """Commande simplifiée (poids + position + priorité)."""

    id: str
    adresse: str
    latitude: float
    longitude: float
    poids: float                 # kg
    priorite: int                # 1 urgent, 2 normal, 3 flexible

    client_nom: Optional[str] = None
    client_tel: Optional[str] = None
    statut: str = "en_attente"   # en_attente, affectee, livree

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"Commande({self.id}, poids={self.poids}, prio={self.priorite})"


# ============================================================
#                         LIVREUR
# ============================================================

@dataclass
class Livreur:
    """Livreur avec capacité poids uniquement."""

    id: str
    nom: str

    latitude_depart: float
    longitude_depart: float

    capacite_poids: float        # kg MAX (THIS IS THE ONLY CONSTRAINT)

    heure_debut: str             # HH:MM
    heure_fin: str               # HH:MM

    vitesse_moyenne: float       # km/h
    cout_km: float               # cost per km

    disponible: bool = True
    telephone: Optional[str] = None
    email: Optional[str] = None

    # Electric / future extensions (safe defaults)
    batterie_max: float = 90.0
    batterie_restante: float = 90.0
    recharge_rate: float = 1.5

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"Livreur({self.id}, cap={self.capacite_poids}kg)"


# ============================================================
#                          TRAJET
# ============================================================

@dataclass
class Trajet:
    livreur_id: str
    commandes: List[str]
    ordre_livraison: List[str]

    distance_totale: float       # km
    temps_total: float           # minutes
    cout_total: float            # €

    points_gps: List[Tuple[float, float]] = field(default_factory=list)
    statut: str = "planifie"

    def to_dict(self):
        return asdict(self)


# ============================================================
#                        NOTIFICATION
# ============================================================

@dataclass
class Notification:
    id: str
    timestamp: str
    type: str
    message: str
    destinataire_id: str
    lu: bool = False

    def to_dict(self):
        return asdict(self)
