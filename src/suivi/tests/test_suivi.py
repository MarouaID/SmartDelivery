import pytest
from src.suivi.notification_system import SystemeNotification
from src.suivi.tracking import ServiceSuivi
from src.suivi.websocket_server import WebSocketServer
from src.models import Trajet


def test_creation_notification():
    """Test de création de notification"""
    systeme = SystemeNotification()
    
    notif = systeme.creer_notification(
        'affectation',
        'Test message',
        'LIV001',
        'normale'
    )
    
    assert notif.type == 'affectation'
    assert notif.destinataire_id == 'LIV001'
    assert not notif.lu


def test_suivi_trajet():
    """Test de suivi de trajet"""
    service = ServiceSuivi()
    
    trajet = Trajet(
        livreur_id='LIV001',
        commandes=['CMD001', 'CMD002'],
        ordre_livraison=[0, 1],
        distance_totale=10.0,
        temps_total=60,
        cout_total=5.0,
        heure_depart='08:00',
        heure_retour_estimee='09:00',
        points_gps=[(48.85, 2.35), (48.86, 2.36), (48.87, 2.37)]
    )
    
    service.demarrer_suivi_trajet('LIV001', trajet)
    
    assert 'LIV001' in service.trajets_actifs
    assert service.trajets_actifs['LIV001']['statut'] == 'en_cours'


def test_websocket_connexion():
    """Test de connexion WebSocket"""
    serveur = WebSocketServer(port=5001)
    serveur.demarrer()
    
    serveur.connecter_client('client1', 'livreur')
    serveur.abonner_canal('client1', 'livraisons')
    
    serveur.diffuser('livraisons', {'test': 'message'})
    
    messages = serveur.recuperer_messages('client1')
    assert len(messages) == 1
    
    serveur.arreter()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
