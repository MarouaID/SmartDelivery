import os
from flask import Flask, render_template, jsonify, request
import mysql.connector


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smart_delivery"
    )


def create_app():
    template_folder = os.path.join(os.path.dirname(__file__), '../web/templates')
    static_folder = os.path.join(os.path.dirname(__file__), '../web/static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # ===================== ROUTES HTML =====================
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/carte")
    def carte():
        return render_template("carte.html")

    @app.route("/livreurs")
    def page_livreurs():
        return render_template("livreurs.html")
    
    @app.route("/commandes")
    def page_commandes():
        return render_template("commandes.html")


    # ===================== API LIVREURS =====================

    @app.route("/api/livreurs", methods=["GET"])
    def get_livreurs():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM livreurs")
        livreurs = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(livreurs)

    @app.route("/api/livreurs", methods=["POST"])
    def add_livreur():
        data = request.json
        db = get_db()
        cursor = db.cursor()

        sql = """
        INSERT INTO livreurs
        (id, nom, latitude_depart, longitude_depart,
         capacite_poids, capacite_volume,
         heure_debut, heure_fin,
         vitesse_moyenne, cout_km,
         telephone, email)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data["id"], data["nom"],
            data["latitude_depart"], data["longitude_depart"],
            data["capacite_poids"], data["capacite_volume"],
            data["heure_debut"], data["heure_fin"],
            data["vitesse_moyenne"], data["cout_km"],
            data["telephone"], data["email"]
        )

        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True})

    @app.route("/api/livreurs/<id>", methods=["DELETE"])
    def delete_livreur(id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM livreurs WHERE id=%s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})

    @app.route("/api/livreurs/<id>", methods=["PUT"])
    def update_livreur(id):
        data = request.json
        db = get_db()
        cursor = db.cursor()

        sql = """
        UPDATE livreurs SET
            nom=%s,
            capacite_poids=%s,
            capacite_volume=%s,
            heure_debut=%s,
            heure_fin=%s,
            vitesse_moyenne=%s,
            cout_km=%s,
            telephone=%s,
            email=%s,
            disponible=%s
        WHERE id = %s
        """

        values = (
            data["nom"], data["capacite_poids"], data["capacite_volume"],
            data["heure_debut"], data["heure_fin"],
            data["vitesse_moyenne"], data["cout_km"],
            data["telephone"], data["email"],
            data["disponible"],
            id
        )

        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True})
    
    @app.route("/api/commandes", methods=["GET"])
    def get_commandes():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM commandes")
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(rows)


    @app.route("/api/commandes", methods=["POST"])
    def add_commande():
        data = request.json
        db = get_db()
        cursor = db.cursor()

        sql = """
        INSERT INTO commandes
        (id, adresse, latitude, longitude, poids, volume,
        fenetre_debut, fenetre_fin, priorite, temps_service,
        client_nom, client_tel, statut)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data["id"], data["adresse"],
            data["latitude"], data["longitude"],
            data["poids"], data["volume"],
            data["fenetre_debut"], data["fenetre_fin"],
            data["priorite"], data["temps_service"],
            data["client_nom"], data["client_tel"],
            data["statut"]
        )

        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True})


    @app.route("/api/commandes/<id>", methods=["DELETE"])
    def delete_commande(id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM commandes WHERE id=%s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})


    @app.route("/api/commandes/<id>", methods=["PUT"])
    def update_commande(id):
        data = request.json
        db = get_db()
        cursor = db.cursor()

        sql = """
        UPDATE commandes SET
            adresse=%s, latitude=%s, longitude=%s,
            poids=%s, volume=%s,
            fenetre_debut=%s, fenetre_fin=%s,
            priorite=%s, temps_service=%s,
            client_nom=%s, client_tel=%s,
            statut=%s
        WHERE id=%s
        """

        values = (
            data["adresse"], data["latitude"], data["longitude"],
            data["poids"], data["volume"],
            data["fenetre_debut"], data["fenetre_fin"],
            data["priorite"], data["temps_service"],
            data["client_nom"], data["client_tel"],
            data["statut"],
            id
        )

        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})



    return app
