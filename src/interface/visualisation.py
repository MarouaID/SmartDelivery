"""
Génération de visualisations et rapports
Responsable: Personne 4
"""

import json
from typing import List, Dict
from datetime import datetime
from src.models import Commande, Livreur, Trajet


class Visualisation:
    """Génère des rapports et visualisations des données"""
    
    def __init__(self):
        self.couleurs_priorite = {
            1: '#FF4444',  # Rouge - Urgent
            2: '#FFA500',  # Orange - Normal
            3: '#4CAF50'   # Vert - Flexible
        }
    
    def generer_rapport_json(self, trajets: Dict[str, Trajet],
                            livreurs: List[Livreur],
                            commandes: List[Commande],
                            metriques: dict = None) -> str:
        """
        Génère un rapport JSON complet
        
        Returns:
            JSON string formaté
        """
        rapport = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'type': 'rapport_livraisons'
            },
            'statistiques_globales': {
                'nb_livreurs': len(livreurs),
                'nb_livreurs_actifs': sum(1 for l in livreurs if l.disponible),
                'nb_commandes': len(commandes),
                'nb_commandes_assignees': sum(len(t.commandes) for t in trajets.values()),
                'distance_totale_km': round(sum(t.distance_totale for t in trajets.values()), 2),
                'temps_total_minutes': sum(t.temps_total for t in trajets.values()),
                'cout_total_euro': round(sum(t.cout_total for t in trajets.values()), 2)
            },
            'livreurs': [self._serialiser_livreur(l) for l in livreurs],
            'commandes': [self._serialiser_commande(c) for c in commandes],
            'trajets': {lid: self._serialiser_trajet(t) for lid, t in trajets.items()},
            'metriques_optimisation': metriques or {}
        }
        
        return json.dumps(rapport, indent=2, ensure_ascii=False)
    
    def _serialiser_livreur(self, livreur: Livreur) -> dict:
        """Convertit un livreur en dict"""
        return {
            'id': livreur.id,
            'nom': livreur.nom,
            'position_depart': {
                'latitude': livreur.latitude_depart,
                'longitude': livreur.longitude_depart
            },
            'capacites': {
                'poids_kg': livreur.capacite_poids,
                'volume_m3': livreur.capacite_volume
            },
            'horaires': {
                'debut': livreur.heure_debut,
                'fin': livreur.heure_fin
            },
            'disponible': livreur.disponible,
            'contact': {
                'telephone': livreur.telephone,
                'email': livreur.email
            }
        }
    
    def _serialiser_commande(self, commande: Commande) -> dict:
        """Convertit une commande en dict"""
        return {
            'id': commande.id,
            'adresse': commande.adresse,
            'position': {
                'latitude': commande.latitude,
                'longitude': commande.longitude
            },
            'details': {
                'poids_kg': commande.poids,
                'volume_m3': commande.volume,
                'temps_service_min': commande.temps_service
            },
            'fenetre_horaire': {
                'debut': commande.fenetre_debut,
                'fin': commande.fenetre_fin
            },
            'priorite': commande.priorite,
            'statut': commande.statut
        }
    
    def _serialiser_trajet(self, trajet: Trajet) -> dict:
        """Convertit un trajet en dict"""
        return {
            'livreur_id': trajet.livreur_id,
            'commandes': trajet.commandes,
            'ordre': trajet.ordre_livraison,
            'metriques': {
                'distance_km': trajet.distance_totale,
                'temps_minutes': trajet.temps_total,
                'cout_euro': trajet.cout_total
            },
            'horaires': {
                'depart': trajet.heure_depart,
                'retour_estime': trajet.heure_retour_estimee
            },
            'points_gps': trajet.points_gps,
            'statut': trajet.statut
        }
    
    def afficher_resume_console(self, trajets: Dict[str, Trajet]):
        """Affiche un résumé formaté dans la console"""
        print("\n" + "="*70)
        print(" "*20 + "📦 SMART DELIVERY")
        print(" "*15 + "Résumé des Livraisons Optimisées")
        print("="*70)
        
        if not trajets:
            print("\n⚠️  Aucun trajet planifié")
            print("="*70 + "\n")
            return
        
        # Statistiques globales
        distance_totale = sum(t.distance_totale for t in trajets.values())
        temps_total = sum(t.temps_total for t in trajets.values())
        cout_total = sum(t.cout_total for t in trajets.values())
        nb_commandes = sum(len(t.commandes) for t in trajets.values())
        
        print(f"\n📊 STATISTIQUES GLOBALES")
        print(f"   Livreurs actifs      : {len(trajets)}")
        print(f"   Commandes totales    : {nb_commandes}")
        print(f"   Distance totale      : {distance_totale:.2f} km")
        print(f"   Temps total estimé   : {temps_total // 60}h {temps_total % 60}min")
        print(f"   Coût total           : {cout_total:.2f} €")
        
        print(f"\n{'─'*70}")
        print(f"\n🚚 DÉTAILS PAR LIVREUR")
        print(f"{'─'*70}")
        
        for livreur_id, trajet in sorted(trajets.items()):
            print(f"\n📍 {livreur_id}")
            print(f"   └─ Commandes        : {len(trajet.commandes)}")
            print(f"   └─ Distance         : {trajet.distance_totale:.2f} km")
            print(f"   └─ Durée estimée    : {trajet.temps_total} min")
            print(f"   └─ Coût             : {trajet.cout_total:.2f} €")
            print(f"   └─ Départ           : {trajet.heure_depart}")
            print(f"   └─ Retour estimé    : {trajet.heure_retour_estimee}")
            
            if trajet.commandes:
                print(f"   └─ Ordre livraison  : {' → '.join(trajet.commandes[:5])}", end="")
                if len(trajet.commandes) > 5:
                    print(f" ... (+{len(trajet.commandes)-5})")
                else:
                    print()
        
        print(f"\n{'='*70}\n")
    
    def generer_html_carte(self, trajets: Dict[str, Trajet],
                          commandes: List[Commande],
                          livreurs: List[Livreur]) -> str:
        """
        Génère le HTML d'une carte interactive avec Leaflet
        
        Returns:
            Code HTML complet
        """
        # Calculer le centre de la carte
        if commandes:
            centre_lat = sum(c.latitude for c in commandes) / len(commandes)
            centre_lon = sum(c.longitude for c in commandes) / len(commandes)
        else:
            centre_lat, centre_lon = 48.8566, 2.3522
        
        # Préparer les données pour JavaScript
        commandes_json = json.dumps([{
            'id': c.id,
            'lat': c.latitude,
            'lon': c.longitude,
            'adresse': c.adresse,
            'priorite': c.priorite
        } for c in commandes])
        
        livreurs_json = json.dumps([{
            'id': l.id,
            'nom': l.nom,
            'lat': l.latitude_depart,
            'lon': l.longitude_depart
        } for l in livreurs])
        
        trajets_json = json.dumps({
            lid: {
                'livreur_id': t.livreur_id,
                'points': t.points_gps,
                'commandes': t.commandes
            } for lid, t in trajets.items()
        })
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Smart Delivery - Carte des Livraisons</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        .legend-item {{
            margin: 5px 0;
            display: flex;
            align-items: center;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>📦 Smart Delivery</h3>
        <p><strong>Livreurs:</strong> <span id="nb-livreurs">{len(livreurs)}</span></p>
        <p><strong>Commandes:</strong> <span id="nb-commandes">{len(commandes)}</span></p>
        <p><strong>Distance totale:</strong> <span id="distance-totale">
            {sum(t.distance_totale for t in trajets.values()):.2f} km
        </span></p>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #FF4444;"></div>
            <span>Urgent</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FFA500;"></div>
            <span>Normal</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #4CAF50;"></div>
            <span>Flexible</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #2196F3; border-radius: 50%;"></div>
            <span>Dépôt</span>
        </div>
    </div>

    <script>
        // Initialiser la carte
        var map = L.map('map').setView([{centre_lat}, {centre_lon}], 12);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Données
        var commandes = {commandes_json};
        var livreurs = {livreurs_json};
        var trajets = {trajets_json};
        
        // Couleurs par priorité
        var couleursPriorite = {{
            1: '#FF4444',
            2: '#FFA500',
            3: '#4CAF50'
        }};
        
        // Afficher les commandes
        commandes.forEach(function(cmd) {{
            var couleur = couleursPriorite[cmd.priorite];
            L.circleMarker([cmd.lat, cmd.lon], {{
                radius: 8,
                fillColor: couleur,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }}).bindPopup(
                '<b>' + cmd.id + '</b><br>' +
                cmd.adresse + '<br>' +
                'Priorité: ' + cmd.priorite
            ).addTo(map);
        }});
        
        // Afficher les dépôts
        livreurs.forEach(function(liv) {{
            L.circleMarker([liv.lat, liv.lon], {{
                radius: 10,
                fillColor: '#2196F3',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }}).bindPopup(
                '<b>🏢 ' + liv.nom + '</b><br>' +
                'Dépôt: ' + liv.id
            ).addTo(map);
        }});
        
        // Afficher les trajets
        var couleursTrajets = ['#E91E63', '#9C27B0', '#3F51B5', '#00BCD4', '#4CAF50', '#FF9800'];
        var idx = 0;
        
        for (var livreur_id in trajets) {{
            var trajet = trajets[livreur_id];
            if (trajet.points && trajet.points.length > 0) {{
                var couleur = couleursTrajets[idx % couleursTrajets.length];
                
                L.polyline(trajet.points, {{
                    color: couleur,
                    weight: 3,
                    opacity: 0.7,
                    dashArray: '5, 10'
                }}).bindPopup('<b>' + livreur_id + '</b><br>' + 
                             trajet.commandes.length + ' livraisons').addTo(map);
                
                idx++;
            }}
        }}
    </script>
</body>
</html>
"""
        return html
    
    def sauvegarder_carte_html(self, trajets: Dict[str, Trajet],
                               commandes: List[Commande],
                               livreurs: List[Livreur],
                               filepath: str = "carte_livraisons.html"):
        """Sauvegarde la carte HTML dans un fichier"""
        html = self.generer_html_carte(trajets, commandes, livreurs)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"🗺️  Carte sauvegardée: {filepath}")
    
    def generer_tableau_excel(self, trajets: Dict[str, Trajet],
                             commandes: List[Commande],
                             filepath: str = "rapport_livraisons.csv"):
        """
        Génère un fichier CSV pour Excel
        """
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow([
                'Livreur ID', 'Commande ID', 'Adresse', 'Priorité',
                'Fenêtre Début', 'Fenêtre Fin', 'Poids (kg)', 'Volume (m³)',
                'Position dans trajet'
            ])
            
            # Données
            for livreur_id, trajet in trajets.items():
                for idx, cmd_id in enumerate(trajet.commandes):
                    cmd = next((c for c in commandes if c.id == cmd_id), None)
                    if cmd:
                        writer.writerow([
                            livreur_id,
                            cmd.id,
                            cmd.adresse,
                            cmd.priorite,
                            cmd.fenetre_debut,
                            cmd.fenetre_fin,
                            cmd.poids,
                            cmd.volume,
                            idx + 1
                        ])
        
        print(f"📊 Tableau CSV sauvegardé: {filepath}")