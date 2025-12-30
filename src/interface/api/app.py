import os
from flask import Flask, render_template, jsonify, request, session, redirect
import mysql.connector
import random, string, hashlib


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Alaa2021",
        database="smart_delivery"
    )


def create_app():
    template_folder = os.path.join(os.path.dirname(__file__), '../web/templates')
    static_folder = os.path.join(os.path.dirname(__file__), '../web/static')


    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # SESSION KEY
    app.secret_key = "smartdelivery_secret_key"

    # ===================== DISABLE CACHE =====================
    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


    # ===================== ROUTES HTML =====================
    @app.route("/")
    def index():
        return render_template("index.html")
        return render_template("index.html")

    @app.route("/dashboard")
    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")
        return render_template("dashboard.html")

    @app.route("/carte")
    @app.route("/carte")
    def carte():
        return render_template("carte.html")

    @app.route("/livreurs")
    def page_livreurs():
        return render_template("livreurs.html")

    @app.route("/commandes")
    def page_commandes():
        return render_template("commandes.html")


    # ===================== LOGIN PAGE =====================
    @app.route("/login")
    def page_login():
        return render_template("login.html")


    # ===================== LOGIN ACTION =====================
    @app.route("/login", methods=["POST"])
    def login_action():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "error": "Champs requis"}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            db.close()
            return jsonify({"success": False, "error": "Utilisateur introuvable"}), 401

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash != user["password_hash"]:
            cursor.close()
            db.close()
            return jsonify({"success": False, "error": "Mot de passe incorrect"}), 401

        # ================= SESSION =================
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["email"] = user["email"]

        # LIVREUR
        if user["role"] == "livreur" and user["livreur_id"]:
            c2 = db.cursor(dictionary=True)
            c2.execute("SELECT * FROM livreurs WHERE id=%s", (user["livreur_id"],))
            session["livreur"] = c2.fetchone()

        # CLIENT
        if user["role"] == "client" and user["client_id"]:
            c3 = db.cursor(dictionary=True)
            c3.execute("SELECT * FROM clients WHERE id=%s", (user["client_id"],))
            session["client"] = c3.fetchone()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "role": user["role"]
        })


    # ===================== LOGOUT =====================
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")


    # ===================== ROLE PAGES =====================
    @app.route("/livreurDashboard")
    def livreur_dashboard():
        if "livreur" not in session:
            return redirect("/login")
        return render_template("livreurDashboard.html")

    @app.route("/clientDashboard")
    def client_dashboard():
        if "client" not in session:
            return redirect("/login")
        return render_template("clientDashboard.html")


    # =========================================================
    # ===================== LIVREURS ==========================
    # =========================================================
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
        generated_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        try:
            db = get_db()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO livreurs
                (id, nom, latitude_depart, longitude_depart,
                 capacite_poids, capacite_volume,
                 heure_debut, heure_fin,
                 vitesse_moyenne, cout_km,
                 telephone, email)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["id"], data["nom"],
                data["latitude_depart"], data["longitude_depart"],
                data["capacite_poids"], data["capacite_volume"],
                data["heure_debut"], data["heure_fin"],
                data["vitesse_moyenne"], data["cout_km"],
                data["telephone"], data["email"]
            ))

            cursor.execute("""
                INSERT INTO users (email, password_hash, role, livreur_id, client_id)
                VALUES (%s,%s,'livreur',%s,NULL)
            """, (
                data["email"],
                generated_password,
                data["id"]
            ))

            db.commit()
            cursor.close()
            db.close()

            return jsonify({
                "success": True,
                "message": "Livreur créé + compte utilisateur généré",
                "login_email": data["email"],
                "password": generated_password
            })

        except Exception as e:
            try: db.rollback()
            except: pass
            return jsonify({"success": False, "error": str(e)}), 500


    # =========================================================
    # ===================== COMMANDES =========================
    # =========================================================
    @app.route("/api/commandes", methods=["GET"])
    def get_commandes():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.*, cl.nom AS client_nom, cl.telephone AS client_tel
            FROM commandes c
            LEFT JOIN clients cl ON c.client_id = cl.id
        """)

        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(rows)



    @app.route("/api/commandes", methods=["POST"])
    def add_commande():
        data = request.json
        db = get_db()
        cursor = db.cursor()

        client_id = data.get("client_id")
        raw_password = None
        client_email = data.get("client_email")

        if client_id:
            cursor.execute("SELECT id FROM clients WHERE id=%s", (client_id,))
            if not cursor.fetchone():
                db.rollback()
                cursor.close()
                db.close()
                return jsonify({"success": False, "error": "Client inexistant"}), 400
        else:
            client_id = "CL" + ''.join(random.choices(string.digits, k=5))
            cursor.execute("""
                INSERT INTO clients(id, nom, telephone, email)
                VALUES (%s,%s,%s,%s)
            """, (
                client_id,
                data.get("client_nom"),
                data.get("client_tel"),
                client_email
            ))

            raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            cursor.execute("""
                INSERT INTO users(email, password_hash, role, client_id, livreur_id)
                VALUES (%s,%s,'client',%s,NULL)
            """, (
                client_email,
                raw_password,
                client_id
            ))

        cursor.execute("""
            INSERT INTO commandes
            (id, adresse, latitude, longitude,
             poids, volume,
             fenetre_debut, fenetre_fin,
             priorite, temps_service,
             client_id, livreur_id, statut)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
        """, (
            data["id"], data["adresse"],
            data["latitude"], data["longitude"],
            data["poids"], data["volume"],
            data["fenetre_debut"], data["fenetre_fin"],
            data["priorite"], data["temps_service"],
            client_id,
            data.get("statut", "en_attente")
        ))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Commande créée",
            "client_created": raw_password is not None,
            "client_id": client_id,
            "client_email": client_email,
            "password": raw_password
        })


    # ========= DELETE =========
    @app.route("/api/commandes/<id>", methods=["DELETE"])
    def delete_commande(id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM commandes WHERE id=%s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})


    # ========= UPDATE =========
    @app.route("/api/commandes/<id>", methods=["PUT"])
    def update_commande(id):
        data = request.json
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
        UPDATE commandes SET
            adresse=%s, latitude=%s, longitude=%s,
            poids=%s, volume=%s,
            fenetre_debut=%s, fenetre_fin=%s,
            priorite=%s, temps_service=%s,
            client_id=%s,
            statut=%s,
            livreur_id=%s
        WHERE id=%s
        """, (
            data["adresse"], data["latitude"], data["longitude"],
            data["poids"], data["volume"],
            data["fenetre_debut"], data["fenetre_fin"],
            data["priorite"], data["temps_service"],
            data["client_id"],
            data["statut"],
            data.get("livreur_id"),
            id
        ))

        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})


    # =========================================================
    # ===== COMMANDES POUR LIVREUR AVEC CONTACT CLIENT ========
    # =========================================================
    @app.route("/api/livreur/commandes")
    def commandes_livreur():

        if "livreur" not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401

        liv_id = session["livreur"]["id"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, adresse, poids, priorite, statut, client_id
            FROM commandes
            WHERE livreur_id = %s
        """, (liv_id,))
        commandes = cursor.fetchall()

        for cmd in commandes:
            cursor.execute("SELECT telephone FROM clients WHERE id=%s", (cmd["client_id"],))
            row = cursor.fetchone()
            cmd["client_tel"] = row["telephone"] if row else "_"

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "commandes": commandes
        })


    @app.route("/api/client/commandes")
    def commandes_client():
        if "client" not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401

        client_id = session["client"]["id"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM commandes WHERE client_id=%s", (client_id,))
        commandes = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({"success": True, "commandes": commandes})

    # ========= CHANGER STATUT =========
    @app.route("/api/commandes/<id>/status", methods=["PUT"])
    def changer_statut(id):
        data = request.json
        statut = data.get("statut")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE commandes SET statut=%s WHERE id=%s", (statut, id))
        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True})
    
    @app.route("/livreur/map")
    def livreur_map():
        if "livreur" not in session:
            return redirect("/login")
        return render_template("livreurMap.html")


    from src.interface.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    return app