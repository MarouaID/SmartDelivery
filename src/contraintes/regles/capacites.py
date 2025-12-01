from typing import List, Tuple
from src.models import Commande, Livreur


class ValidateurCapacites:
    """Valide les contraintes de poids et volume"""
    
    def valider_capacite_totale(self, livreur: Livreur, 
                                commandes: List[Commande]) -> Tuple[bool, str]:
       
        poids_total = sum(c.poids for c in commandes)
        volume_total = sum(c.volume for c in commandes)
        
        erreurs = []
        
        if poids_total > livreur.capacite_poids:
            erreurs.append(
                f"Poids dépassé: {poids_total:.1f} kg > {livreur.capacite_poids} kg"
            )
        
        if volume_total > livreur.capacite_volume:
            erreurs.append(
                f"Volume dépassé: {volume_total:.2f} m³ > {livreur.capacite_volume} m³"
            )
        
        if erreurs:
            return False, f"Livreur {livreur.id}: " + "; ".join(erreurs)
        
        return True, ""
    
    def calculer_utilisation_capacite(self, livreur: Livreur, 
                                     commandes: List[Commande]) -> dict:
        
        poids_total = sum(c.poids for c in commandes)
        volume_total = sum(c.volume for c in commandes)
        
        return {
            'poids_utilise_kg': poids_total,
            'poids_capacite_kg': livreur.capacite_poids,
            'poids_restant_kg': livreur.capacite_poids - poids_total,
            'poids_utilisation_pourcent': (poids_total / livreur.capacite_poids) * 100,
            'volume_utilise_m3': volume_total,
            'volume_capacite_m3': livreur.capacite_volume,
            'volume_restant_m3': livreur.capacite_volume - volume_total,
            'volume_utilisation_pourcent': (volume_total / livreur.capacite_volume) * 100
        }
    
    def valider_commande_individuelle(self, commande: Commande, 
                                     livreur: Livreur) -> Tuple[bool, str]:
        """Vérifie qu'une seule commande peut être transportée"""
        if commande.poids > livreur.capacite_poids:
            return False, (f"Commande {commande.id} trop lourde: "
                          f"{commande.poids} kg > {livreur.capacite_poids} kg")
        
        if commande.volume > livreur.capacite_volume:
            return False, (f"Commande {commande.id} trop volumineuse: "
                          f"{commande.volume} m³ > {livreur.capacite_volume} m³")
        
        return True, ""
    
    def verifier_ajout_commande(self, livreur: Livreur, 
                               commandes_actuelles: List[Commande],
                               nouvelle_commande: Commande) -> Tuple[bool, str]:
        """Vérifie si on peut ajouter une commande à une charge existante"""
        toutes_commandes = commandes_actuelles + [nouvelle_commande]
        return self.valider_capacite_totale(livreur, toutes_commandes)
