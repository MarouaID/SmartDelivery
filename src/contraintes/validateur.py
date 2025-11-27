"""
Validateur principal de toutes les contraintes
Responsable: Personne 5
"""

from typing import List, Dict, Tuple
from src.models import Commande, Livreur, Trajet
from src.utils import TimeUtils
from src.contraintes.regles.horaires import ValidateurHoraires
from src.contraintes.regles.capacites import ValidateurCapacites
from src.contraintes.regles.meteo import ValidateurMeteo


class ValidateurContraintes:
    """Validateur central de toutes les contraintes du système"""
    
    def __init__(self, config: dict = None):
        """
        Args:
            config: Configuration des contraintes
        """
        self.config = config or {}
        self.validateur_horaires = ValidateurHoraires()
        self.validateur_capacites = ValidateurCapacites()
        self.validateur_meteo = ValidateurMeteo()
        
        self.violations = []
        self.avertissements = []
    
    def valider_affectation(self, livreur: Livreur, 
                           commandes: List[Commande]) -> Tuple[bool, List[str]]:
        """
        Valide qu'un livreur peut prendre en charge des commandes
        
        Returns:
            (est_valide, liste_erreurs)
        """
        erreurs = []
        
        # 1. Vérifier les capacités
        capacite_ok, msg_capacite = self.validateur_capacites.valider_capacite_totale(
            livreur, commandes
        )
        if not capacite_ok:
            erreurs.append(msg_capacite)
        
        # 2. Vérifier la disponibilité
        if not livreur.disponible:
            erreurs.append(f"Livreur {livreur.id} non disponible")
        
        # 3. Vérifier le nombre maximum de commandes
        max_commandes = self.config.get('max_commandes_par_livreur', 20)
        if len(commandes) > max_commandes:
            erreurs.append(f"Trop de commandes: {len(commandes)} > {max_commandes}")
        
        return len(erreurs) == 0, erreurs
    
    def valider_trajet(self, trajet: Trajet, livreur: Livreur, 
                      commandes: List[Commande]) -> Tuple[bool, List[str]]:
        """
        Valide un trajet complet avec toutes les contraintes
        
        Returns:
            (est_valide, liste_erreurs)
        """
        erreurs = []
        
        # 1. Contraintes de capacité
        capacite_ok, msg = self.validateur_capacites.valider_capacite_totale(
            livreur, commandes
        )
        if not capacite_ok:
            erreurs.append(msg)
        
        # 2. Contraintes horaires
        horaires_ok, msgs_horaires = self.validateur_horaires.valider_trajet_complet(
            trajet, livreur, commandes
        )
        if not horaires_ok:
            erreurs.extend(msgs_horaires)
        
        # 3. Contrainte de durée de travail
        duree_max = self.config.get('duree_travail_max_minutes', 600)
        if trajet.temps_total > duree_max:
            erreurs.append(
                f"Durée de travail dépassée: {trajet.temps_total} min > {duree_max} min"
            )
        
        # 4. Contraintes météo (optionnel)
        if self.config.get('verifier_meteo', False):
            meteo_ok, msg_meteo = self.validateur_meteo.valider_conditions(
                trajet.points_gps
            )
            if not meteo_ok:
                self.avertissements.append(msg_meteo)
        
        return len(erreurs) == 0, erreurs
    
    def valider_solution_complete(self, trajets: Dict[str, Trajet],
                                  livreurs: List[Livreur],
                                  commandes: List[Commande]) -> Dict:
        """
        Valide une solution complète du système
        
        Returns:
            Dict avec le statut de validation et les détails
        """
        self.violations = []
        self.avertissements = []
        
        trajets_valides = {}
        trajets_invalides = {}
        
        # Créer un mapping des commandes par ID
        commandes_dict = {c.id: c for c in commandes}
        livreurs_dict = {l.id: l for l in livreurs}
        
        for livreur_id, trajet in trajets.items():
            if livreur_id not in livreurs_dict:
                self.violations.append(f"Livreur {livreur_id} introuvable")
                continue
            
            livreur = livreurs_dict[livreur_id]
            commandes_trajet = [commandes_dict[cid] for cid in trajet.commandes 
                               if cid in commandes_dict]
            
            est_valide, erreurs = self.valider_trajet(trajet, livreur, commandes_trajet)
            
            if est_valide:
                trajets_valides[livreur_id] = trajet
            else:
                trajets_invalides[livreur_id] = {
                    'trajet': trajet,
                    'erreurs': erreurs
                }
                self.violations.extend([f"[{livreur_id}] {e}" for e in erreurs])
        
        # Vérifier que toutes les commandes sont affectées une seule fois
        commandes_affectees = set()
        for trajet in trajets.values():
            for cmd_id in trajet.commandes:
                if cmd_id in commandes_affectees:
                    self.violations.append(f"Commande {cmd_id} affectée plusieurs fois")
                commandes_affectees.add(cmd_id)
        
        commandes_manquantes = set(c.id for c in commandes) - commandes_affectees
        if commandes_manquantes:
            self.avertissements.append(
                f"{len(commandes_manquantes)} commandes non affectées: {commandes_manquantes}"
            )
        
        est_valide_global = len(self.violations) == 0
        
        return {
            'valide': est_valide_global,
            'trajets_valides': trajets_valides,
            'trajets_invalides': trajets_invalides,
            'nombre_violations': len(self.violations),
            'violations': self.violations,
            'nombre_avertissements': len(self.avertissements),
            'avertissements': self.avertissements,
            'taux_reussite': len(trajets_valides) / len(trajets) if trajets else 0
        }
    
    def obtenir_rapport(self) -> str:
        """Génère un rapport textuel de validation"""
        rapport = []
        rapport.append("=" * 60)
        rapport.append("RAPPORT DE VALIDATION DES CONTRAINTES")
        rapport.append("=" * 60)
        
        if not self.violations and not self.avertissements:
            rapport.append("✅ Toutes les contraintes sont respectées")
        else:
            if self.violations:
                rapport.append(f"\n❌ {len(self.violations)} VIOLATIONS CRITIQUES:")
                for v in self.violations:
                    rapport.append(f"   • {v}")
            
            if self.avertissements:
                rapport.append(f"\n⚠️  {len(self.avertissements)} AVERTISSEMENTS:")
                for a in self.avertissements:
                    rapport.append(f"   • {a}")
        
        rapport.append("=" * 60)
        return "\n".join(rapport)