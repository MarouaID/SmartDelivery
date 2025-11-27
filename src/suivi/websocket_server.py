import json
from typing import Dict, Set, Optional
from datetime import datetime


class WebSocketServer:
    """
    Serveur WebSocket simplifié pour les notifications temps réel
    Note: En production, utiliser flask-socketio ou similaire
    """
    
    def __init__(self, port: int = 5001):
        self.port = port
        self.clients_connectes = {}  # {client_id: infos}
        self.canaux_abonnement = {}  # {canal: set(client_ids)}
        self.messages_en_attente = {}  # {client_id: [messages]}
        self.actif = False
    
    def demarrer(self):
        """Démarre le serveur WebSocket"""
        self.actif = True
        print(f"🌐 Serveur WebSocket démarré sur le port {self.port}")
        print("   (Simulation - en production utiliser flask-socketio)")
    
    def arreter(self):
        """Arrête le serveur"""
        self.actif = False
        print("🛑 Serveur WebSocket arrêté")
    
    def connecter_client(self, client_id: str, role: str = "livreur"):
        """
        Enregistre un nouveau client
        
        Args:
            client_id: ID unique du client
            role: 'livreur', 'responsable', 'client'
        """
        self.clients_connectes[client_id] = {
            'id': client_id,
            'role': role,
            'connexion_timestamp': datetime.now().isoformat(),
            'actif': True
        }
        self.messages_en_attente[client_id] = []
        
        print(f"🔌 Client connecté: {client_id} (rôle: {role})")
    
    def deconnecter_client(self, client_id: str):
        """Déconnecte un client"""
        if client_id in self.clients_connectes:
            self.clients_connectes[client_id]['actif'] = False
            print(f"🔌 Client déconnecté: {client_id}")
    
    def abonner_canal(self, client_id: str, canal: str):
        """
        Abonne un client à un canal
        
        Args:
            client_id: ID du client
            canal: Nom du canal ('livraisons', 'notifications', 'incidents', etc.)
        """
        if canal not in self.canaux_abonnement:
            self.canaux_abonnement[canal] = set()
        
        self.canaux_abonnement[canal].add(client_id)
        print(f"📡 {client_id} abonné au canal '{canal}'")
    
    def desabonner_canal(self, client_id: str, canal: str):
        """Désabonne un client d'un canal"""
        if canal in self.canaux_abonnement:
            self.canaux_abonnement[canal].discard(client_id)
    
    def diffuser(self, canal: str, message: dict):
        """
        Diffuse un message à tous les abonnés d'un canal
        
        Args:
            canal: Nom du canal
            message: Contenu du message (sera converti en JSON)
        """
        if canal not in self.canaux_abonnement:
            return
        
        message_json = {
            'canal': canal,
            'timestamp': datetime.now().isoformat(),
            'data': message
        }
        
        for client_id in self.canaux_abonnement[canal]:
            if client_id in self.clients_connectes and self.clients_connectes[client_id]['actif']:
                self.messages_en_attente[client_id].append(message_json)
        
        print(f"📤 Message diffusé sur '{canal}' à {len(self.canaux_abonnement[canal])} clients")
    
    def envoyer_message(self, client_id: str, message: dict):
        """
        Envoie un message à un client spécifique
        
        Args:
            client_id: ID du destinataire
            message: Contenu du message
        """
        if client_id not in self.messages_en_attente:
            self.messages_en_attente[client_id] = []
        
        message_json = {
            'type': 'direct',
            'timestamp': datetime.now().isoformat(),
            'data': message
        }
        
        self.messages_en_attente[client_id].append(message_json)
        print(f"📨 Message envoyé à {client_id}")
    
    def recuperer_messages(self, client_id: str) -> list:
        """
        Récupère les messages en attente pour un client
        
        Returns:
            Liste des messages
        """
        if client_id not in self.messages_en_attente:
            return []
        
        messages = self.messages_en_attente[client_id].copy()
        self.messages_en_attente[client_id] = []
        
        return messages
    
    def diffuser_mise_a_jour_position(self, livreur_id: str, 
                                     latitude: float, 
                                     longitude: float):
        """Diffuse une mise à jour de position"""
        self.diffuser('positions', {
            'type': 'position_update',
            'livreur_id': livreur_id,
            'latitude': latitude,
            'longitude': longitude
        })
    
    def diffuser_livraison_effectuee(self, livreur_id: str, 
                                    commande_id: str):
        """Diffuse une livraison effectuée"""
        self.diffuser('livraisons', {
            'type': 'livraison_effectuee',
            'livreur_id': livreur_id,
            'commande_id': commande_id
        })
    
    def diffuser_incident(self, livreur_id: str, 
                         type_incident: str, 
                         description: str):
        """Diffuse un incident"""
        self.diffuser('incidents', {
            'type': 'incident',
            'livreur_id': livreur_id,
            'type_incident': type_incident,
            'description': description,
            'priorite': 'haute'
        })
    
    def obtenir_statistiques(self) -> dict:
        """Statistiques du serveur WebSocket"""
        clients_actifs = sum(1 for c in self.clients_connectes.values() if c['actif'])
        
        return {
            'actif': self.actif,
            'port': self.port,
            'clients_total': len(self.clients_connectes),
            'clients_actifs': clients_actifs,
            'canaux': list(self.canaux_abonnement.keys()),
            'messages_en_attente': sum(len(m) for m in self.messages_en_attente.values())
        }