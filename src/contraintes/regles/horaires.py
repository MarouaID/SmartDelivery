
from typing import List, Tuple
from datetime import datetime, timedelta
from src.models import Commande, Livreur, Trajet
from src.utils import TimeUtils, DistanceCalculator


class ValidateurHoraires:
    """Valide toutes les contraintes horaires"""
    
    def __init__(self):
        self.distance_calc = DistanceCalculator()
    
    def valider_fenetre_horaire(self, commande: Commande, 
                                heure_arrivee: str) -> Tuple[bool, str]:
        """
        Vérifie si l'heure d'arrivée respecte la fenêtre de livraison
        
        Returns:
            (est_valide, message)
        """
        try:
            arrivee = TimeUtils.parse_time(heure_arrivee)
            debut = TimeUtils.parse_time(commande.fenetre_debut)
            fin = TimeUtils.parse_time(commande.fenetre_fin)
            
            if debut <= arrivee <= fin:
                return True, ""
            else:
                return False, (f"Commande {commande.id}: arrivée {heure_arrivee} "
                             f"hors fenêtre [{commande.fenetre_debut}-{commande.fenetre_fin}]")
        except Exception as e:
            return False, f"Erreur de validation horaire: {str(e)}"
    
    def calculer_heure_arrivee(self, heure_depart: str, 
                              distance_km: float, 
                              vitesse_kmh: float) -> str:
        """Calcule l'heure d'arrivée estimée"""
        temps_trajet_min = self.distance_calc.calculer_temps_trajet(
            distance_km, vitesse_kmh
        )
        return TimeUtils.add_minutes(heure_depart, temps_trajet_min)
    
    def valider_trajet_complet(self, trajet: Trajet, 
                              livreur: Livreur, 
                              commandes: List[Commande]) -> Tuple[bool, List[str]]:
        
        erreurs = []
        
        # Vérifier que le livreur commence dans sa plage horaire
        try:
            heure_debut_livreur = TimeUtils.parse_time(livreur.heure_debut)
            heure_fin_livreur = TimeUtils.parse_time(livreur.heure_fin)
        except:
            erreurs.append(f"Horaires livreur {livreur.id} invalides")
            return False, erreurs
        
        # Simuler le trajet
        heure_actuelle = livreur.heure_debut
        position_lat = livreur.latitude_depart
        position_lon = livreur.longitude_depart
        
        # Parcourir les commandes dans l'ordre
        commandes_dict = {c.id: c for c in commandes}
        
        for idx in trajet.ordre_livraison:
            if idx >= len(trajet.commandes):
                erreurs.append(f"Index {idx} hors limites")
                continue
            
            cmd_id = trajet.commandes[idx]
            if cmd_id not in commandes_dict:
                erreurs.append(f"Commande {cmd_id} introuvable")
                continue
            
            commande = commandes_dict[cmd_id]
            
            # Calculer distance et temps jusqu'à cette commande
            distance = self.distance_calc.haversine(
                position_lat, position_lon,
                commande.latitude, commande.longitude
            )
            
            temps_trajet = self.distance_calc.calculer_temps_trajet(
                distance, livreur.vitesse_moyenne
            )
            
            # Heure d'arrivée
            heure_arrivee = TimeUtils.add_minutes(heure_actuelle, temps_trajet)
            
            # Valider la fenêtre
            fenetre_ok, msg = self.valider_fenetre_horaire(commande, heure_arrivee)
            if not fenetre_ok:
                erreurs.append(msg)
            
            # Mettre à jour pour la prochaine commande
            heure_actuelle = TimeUtils.add_minutes(
                heure_arrivee, commande.temps_service
            )
            position_lat = commande.latitude
            position_lon = commande.longitude
        
        # Vérifier l'heure de retour
        try:
            heure_retour = TimeUtils.parse_time(trajet.heure_retour_estimee)
            if heure_retour > heure_fin_livreur:
                erreurs.append(
                    f"Retour tardif: {trajet.heure_retour_estimee} > {livreur.heure_fin}"
                )
        except:
            erreurs.append("Heure de retour invalide")
        
        return len(erreurs) == 0, erreurs
    
    def valider_disponibilite_livreur(self, livreur: Livreur, 
                                      heure_demandee: str) -> Tuple[bool, str]:
        """Vérifie qu'un livreur est disponible à une heure donnée"""
        try:
            heure = TimeUtils.parse_time(heure_demandee)
            debut = TimeUtils.parse_time(livreur.heure_debut)
            fin = TimeUtils.parse_time(livreur.heure_fin)
            
            if debut <= heure <= fin:
                return True, ""
            else:
                return False, (f"Livreur {livreur.id} non disponible à {heure_demandee} "
                             f"(plage: {livreur.heure_debut}-{livreur.heure_fin})")
        except Exception as e:
            return False, f"Erreur validation disponibilité: {str(e)}"