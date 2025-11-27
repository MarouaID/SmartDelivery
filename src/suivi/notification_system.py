
from typing import List, Dict, Optional
from datetime import datetime
from src.models import Notification
import json


class SystemeNotification:
    """Gère l'envoi et le stockage des notifications"""
    
    def __init__(self):
        self.notifications = []
        self.compteur_notifications = 0
        self.abonnes = {}  # {utilisateur_id: [callbacks]}
    
    def creer_notification(self, type_notif: str, 
                          message: str, 
                          destinataire_id: str,
                          priorite: str = "normale") -> Notification:
        """
        Crée une nouvelle notification
        
        Args:
            type_notif: 'affectation', 'depart', 'livraison', 'incident', 'retard'
            message: Contenu du message
            destinataire_id: ID du livreur ou responsable
            priorite: 'basse', 'normale', 'haute', 'critique'
        
        Returns:
            Notification créée
        """
        self.compteur_notifications += 1
        
        notification = Notification(
            id=f"NOTIF{self.compteur_notifications:06d}",
            timestamp=datetime.now().isoformat(),
            type=type_notif,
            message=message,
            destinataire_id=destinataire_id,
            lu=False
        )
        
        self.notifications.append(notification)
        
        # Afficher selon priorité
        emoji = self._get_emoji_priorite(priorite)
        print(f"{emoji} [{type_notif.upper()}] {destinataire_id}: {message}")
        
        # Notifier les abonnés
        self._notifier_abonnes(destinataire_id, notification)
        
        return notification
    
    def _get_emoji_priorite(self, priorite: str) -> str:
        """Retourne l'emoji selon la priorité"""
        emojis = {
            'basse': '💬',
            'normale': '📢',
            'haute': '⚠️',
            'critique': '🚨'
        }
        return emojis.get(priorite, '📢')
    
    def notifier_affectation(self, livreur_id: str, 
                            nb_commandes: int, 
                            commandes_ids: List[str]):
        """Notifie un livreur de son affectation"""
        message = (f"Vous avez {nb_commandes} commande(s) assignée(s): "
                  f"{', '.join(commandes_ids[:3])}"
                  f"{' ...' if len(commandes_ids) > 3 else ''}")
        
        self.creer_notification('affectation', message, livreur_id, 'normale')
    
    def notifier_depart(self, livreur_id: str, heure_depart: str):
        """Notifie le départ d'un livreur"""
        message = f"Départ prévu à {heure_depart}"
        self.creer_notification('depart', message, livreur_id, 'normale')
    
    def notifier_livraison_effectuee(self, livreur_id: str, 
                                     commande_id: str,
                                     heure_livraison: str):
        """Notifie qu'une livraison est effectuée"""
        message = f"Livraison {commande_id} effectuée à {heure_livraison}"
        self.creer_notification('livraison', message, livreur_id, 'basse')
    
    def notifier_retard(self, livreur_id: str, 
                       commande_id: str, 
                       retard_minutes: int):
        """Notifie un retard"""
        priorite = 'haute' if retard_minutes > 30 else 'normale'
        message = f"Retard de {retard_minutes} min pour commande {commande_id}"
        self.creer_notification('retard', message, livreur_id, priorite)
    
    def notifier_incident(self, livreur_id: str, 
                         type_incident: str, 
                         description: str):
        """Notifie un incident"""
        message = f"Incident {type_incident}: {description}"
        self.creer_notification('incident', message, livreur_id, 'critique')
    
    def notifier_fin_tournee(self, livreur_id: str, 
                            nb_livraisons: int,
                            heure_retour: str):
        """Notifie la fin de tournée"""
        message = (f"Tournée terminée: {nb_livraisons} livraisons effectuées. "
                  f"Retour à {heure_retour}")
        self.creer_notification('fin_tournee', message, livreur_id, 'normale')
    
    def obtenir_notifications_utilisateur(self, utilisateur_id: str, 
                                         non_lues_seulement: bool = False) -> List[Notification]:
        """
        Récupère les notifications d'un utilisateur
        
        Args:
            utilisateur_id: ID du livreur ou responsable
            non_lues_seulement: Si True, retourne uniquement les non lues
        
        Returns:
            Liste de notifications
        """
        notifs = [n for n in self.notifications 
                 if n.destinataire_id == utilisateur_id]
        
        if non_lues_seulement:
            notifs = [n for n in notifs if not n.lu]
        
        return sorted(notifs, key=lambda n: n.timestamp, reverse=True)
    
    def marquer_comme_lue(self, notification_id: str) -> bool:
        """Marque une notification comme lue"""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.lu = True
                return True
        return False
    
    def marquer_toutes_lues(self, utilisateur_id: str):
        """Marque toutes les notifications d'un utilisateur comme lues"""
        for notif in self.notifications:
            if notif.destinataire_id == utilisateur_id:
                notif.lu = True
    
    def abonner(self, utilisateur_id: str, callback):
        """
        Abonne un utilisateur aux notifications en temps réel
        
        Args:
            utilisateur_id: ID de l'utilisateur
            callback: Fonction à appeler lors d'une nouvelle notification
        """
        if utilisateur_id not in self.abonnes:
            self.abonnes[utilisateur_id] = []
        self.abonnes[utilisateur_id].append(callback)
    
    def _notifier_abonnes(self, utilisateur_id: str, notification: Notification):
        """Notifie les callbacks abonnés"""
        if utilisateur_id in self.abonnes:
            for callback in self.abonnes[utilisateur_id]:
                try:
                    callback(notification)
                except Exception as e:
                    print(f"Erreur callback notification: {e}")
    
    def obtenir_statistiques(self) -> dict:
        """Retourne les statistiques des notifications"""
        stats_par_type = {}
        for notif in self.notifications:
            stats_par_type[notif.type] = stats_par_type.get(notif.type, 0) + 1
        
        nb_non_lues = sum(1 for n in self.notifications if not n.lu)
        
        return {
            'total_notifications': len(self.notifications),
            'non_lues': nb_non_lues,
            'taux_lecture': (len(self.notifications) - nb_non_lues) / len(self.notifications) * 100 
                           if self.notifications else 0,
            'par_type': stats_par_type,
            'utilisateurs_actifs': len(set(n.destinataire_id for n in self.notifications))
        }
    
    def exporter_historique(self, filepath: str = "notifications_log.json"):
        """Exporte l'historique des notifications en JSON"""
        data = [n.to_dict() for n in self.notifications]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Historique exporté vers {filepath}")
