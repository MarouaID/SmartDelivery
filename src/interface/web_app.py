from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import json
from datetime import datetime
from typing import Dict

# Créer l'application Flask
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'smart-delivery-secret-key-2024'
app.config['JSON_AS_ASCII'] = False


class WebApp:
    """Gestionnaire de l'application web"""
    
    def __init__(self):
        self.systeme_principal = None  # Sera défini lors de l'initialisation
        self.cache_donnees = {}
    
    def initialiser(self, systeme_principal):
        """
        Initialise l'app avec le système principal
        
        Args:
            systeme_principal: Instance de SmartDeliverySystem
        """
        self.systeme_principal = systeme_principal
        print("✅ Application web initialisée")
    
    def demarrer(self, host='0.0.0.0', port=5000, debug=True):
        """Démarre le serveur web"""
        print(f"\n🌐 Serveur web démarrant sur http://{host}:{port}")
        print(f"   Dashboard: http://{host}:{port}/")
        print(f"   API: http://{host}:{port}/api/")
        app.run(host=host, port=port, debug=debug)


# Instance globale
web_app = WebApp()


# ============================================================================
# ROUTES WEB (Pages HTML)
# ============================================================================

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')


@app.route('/carte')
def carte():
    """Carte interactive des livraisons"""
    return render_template('carte.html')


@app.route('/livreurs')
def livreurs():
    """Liste des livreurs"""
    return render_template('livreurs.html')


@app.route('/commandes')
def commandes():
    """Liste des commandes"""
    return render_template('commandes.html')


@app.route('/suivi')
def suivi_temps_reel():
    """Suivi en temps réel"""
    return render_template('suivi.html')


# ============================================================================
# API REST
# ============================================================================

@app.route('/api/status', methods=['GET'])
def api_status():
    """Status de l'API"""
    return jsonify({
        'status': 'online',
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'service': 'Smart Delivery API'
    })


@app.route('/api/statistiques', methods=['GET'])
def api_statistiques():
    """Statistiques globales"""
    if not web_app.systeme_principal:
        return jsonify({'error': 'Système non initialisé'}), 500
    
    # Récupérer les stats depuis le cache ou calculer
    stats = web_app.cache_donnees.get('statistiques', {
        'livreurs_total': 0,
        'commandes_total': 0,
        'trajets_actifs': 0,
        'distance_totale_km': 0,
        'cout_total_euro': 0
    })
    
    return jsonify(stats)


@app.route('/api/livreurs', methods=['GET'])
def api_livreurs():
    """Liste des livreurs"""
    livreurs = web_app.cache_donnees.get('livreurs', [])
    return jsonify({
        'count': len(livreurs),
        'livreurs': [l.to_dict() if hasattr(l, 'to_dict') else l for l in livreurs]
    })


@app.route('/api/livreurs/<livreur_id>', methods=['GET'])
def api_livreur_detail(livreur_id):
    """Détails d'un livreur"""
    livreurs = web_app.cache_donnees.get('livreurs', [])
    
    for livreur in livreurs:
        if livreur.id == livreur_id:
            return jsonify(livreur.to_dict() if hasattr(livreur, 'to_dict') else livreur)
    
    return jsonify({'error': 'Livreur non trouvé'}), 404


@app.route('/api/commandes', methods=['GET'])
def api_commandes():
    """Liste des commandes"""
    commandes = web_app.cache_donnees.get('commandes', [])
    
    # Filtres optionnels
    statut = request.args.get('statut')
    priorite = request.args.get('priorite', type=int)
    
    if statut:
        commandes = [c for c in commandes if c.statut == statut]
    if priorite:
        commandes = [c for c in commandes if c.priorite == priorite]
    
    return jsonify({
        'count': len(commandes),
        'commandes': [c.to_dict() if hasattr(c, 'to_dict') else c for c in commandes]
    })


@app.route('/api/commandes/<commande_id>', methods=['GET'])
def api_commande_detail(commande_id):
    """Détails d'une commande"""
    commandes = web_app.cache_donnees.get('commandes', [])
    
    for commande in commandes:
        if commande.id == commande_id:
            return jsonify(commande.to_dict() if hasattr(commande, 'to_dict') else commande)
    
    return jsonify({'error': 'Commande non trouvée'}), 404


@app.route('/api/trajets', methods=['GET'])
def api_trajets():
    """Liste des trajets"""
    trajets = web_app.cache_donnees.get('trajets', {})
    
    return jsonify({
        'count': len(trajets),
        'trajets': {
            lid: (t.to_dict() if hasattr(t, 'to_dict') else t)
            for lid, t in trajets.items()
        }
    })


@app.route('/api/trajets/<livreur_id>', methods=['GET'])
def api_trajet_detail(livreur_id):
    """Détails du trajet d'un livreur"""
    trajets = web_app.cache_donnees.get('trajets', {})
    
    if livreur_id in trajets:
        trajet = trajets[livreur_id]
        return jsonify(trajet.to_dict() if hasattr(trajet, 'to_dict') else trajet)
    
    return jsonify({'error': 'Trajet non trouvé'}), 404


@app.route('/api/optimiser', methods=['POST'])
def api_optimiser():
    """
    Lance une optimisation
    Body: {"nb_livreurs": 5, "nb_commandes": 20, "scenario": "normal"}
    """
    data = request.json
    
    if not web_app.systeme_principal:
        return jsonify({'error': 'Système non initialisé'}), 500
    
    try:
        nb_livreurs = data.get('nb_livreurs', 5)
        nb_commandes = data.get('nb_commandes', 20)
        scenario = data.get('scenario', 'normal')
        
        # Générer le scénario
        donnees = web_app.systeme_principal.simulateur.generer_scenario(
            scenario, nb_livreurs, nb_commandes
        )
        
        livreurs = donnees['livreurs']
        commandes = donnees['commandes']
        
        # Optimiser
        resultats = web_app.systeme_principal.executer_optimisation_complete(
            livreurs, commandes
        )
        
        # Mettre en cache
        web_app.cache_donnees['livreurs'] = livreurs
        web_app.cache_donnees['commandes'] = commandes
        web_app.cache_donnees['trajets'] = resultats['trajets']
        web_app.cache_donnees['statistiques'] = {
            'livreurs_total': len(livreurs),
            'commandes_total': len(commandes),
            'trajets_actifs': len(resultats['trajets']),
            'distance_totale_km': sum(t.distance_totale for t in resultats['trajets'].values()),
            'cout_total_euro': sum(t.cout_total for t in resultats['trajets'].values())
        }
        
        return jsonify({
            'success': True,
            'message': 'Optimisation réussie',
            'score': resultats.get('score_optimisation', 0),
            'nb_trajets': len(resultats['trajets'])
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/suivi/positions', methods=['GET'])
def api_positions_temps_reel():
    """Positions en temps réel de tous les livreurs"""
    if not web_app.systeme_principal:
        return jsonify({'error': 'Système non initialisé'}), 500
    
    service_suivi = web_app.systeme_principal.notificateur
    
    # Dans un vrai système, on récupérerait les positions du service de suivi
    positions = []
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'positions': positions
    })


@app.route('/api/notifications', methods=['GET'])
def api_notifications():
    """Liste des notifications"""
    utilisateur_id = request.args.get('utilisateur_id')
    
    if not utilisateur_id:
        return jsonify({'error': 'utilisateur_id requis'}), 400
    
    if not web_app.systeme_principal:
        return jsonify({'notifications': []})
    
    notifs = web_app.systeme_principal.notificateur.obtenir_notifications_utilisateur(
        utilisateur_id, non_lues_seulement=False
    )
    
    return jsonify({
        'count': len(notifs),
        'notifications': [n.to_dict() if hasattr(n, 'to_dict') else n for n in notifs]
    })


@app.route('/api/export/json', methods=['GET'])
def api_export_json():
    """Exporte les données en JSON"""
    trajets = web_app.cache_donnees.get('trajets', {})
    livreurs = web_app.cache_donnees.get('livreurs', [])
    commandes = web_app.cache_donnees.get('commandes', [])
    
    if not web_app.systeme_principal:
        return jsonify({'error': 'Pas de données à exporter'}), 400
    
    visualisation = web_app.systeme_principal.interface
    rapport = visualisation.generer_rapport_json(trajets, livreurs, commandes)
    
    return jsonify(json.loads(rapport))


@app.route('/api/export/csv', methods=['GET'])
def api_export_csv():
    """Exporte les données en CSV"""
    trajets = web_app.cache_donnees.get('trajets', {})
    commandes = web_app.cache_donnees.get('commandes', [])
    
    if not web_app.systeme_principal:
        return jsonify({'error': 'Pas de données à exporter'}), 400
    
    filepath = 'data/resultats/export_livraisons.csv'
    visualisation = web_app.systeme_principal.interface
    visualisation.generer_tableau_excel(trajets, commandes, filepath)
    
    return send_file(filepath, as_attachment=True)


# ============================================================================
# Gestion des erreurs
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route non trouvée'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur serveur interne'}), 500


if __name__ == '__main__':
    # Pour tester l'app seule
    app.run(debug=True, port=5000)