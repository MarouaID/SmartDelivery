import os
import random
import string
import hashlib
import mysql.connector
from datetime import timedelta
from flask import Flask, render_template, jsonify, request, session, redirect


# ================= DATABASE ================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Alaa2021",
        database="smart_delivery"
    )


# ================= APP FACTORY =================
def create_app():
    template_folder = os.path.join(os.path.dirname(__file__), '../web/templates')
    static_folder = os.path.join(os.path.dirname(__file__), '../web/static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.secret_key = "smartdelivery_secret_key"

    # ================= NO CACHE =================
    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # ================= HTML ROUTES =================
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

    # ================= AUTH =================
    @app.route("/login")
    def page_login():
        return render_template("login.html")

    @app.route("/login", methods=["POST"])
    def login_action():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False}), 401

        # DB already hashes passwords via trigger
        if hashlib.sha256(password.encode()).hexdigest() != user["password_hash"]:
            return jsonify({"success": False}), 401

        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["email"] = user["email"]

        if user["livreur_id"]:
            cursor.execute("SELECT * FROM livreurs WHERE id=%s", (user["livreur_id"],))
            livreur = cursor.fetchone()

            if livreur:
                # convert TIME / timedelta to string
                for k, v in livreur.items():
                    if isinstance(v, timedelta):
                        sec = int(v.total_seconds())
                        h = sec // 3600
                        m = (sec % 3600) // 60
                        livreur[k] = f"{h:02d}:{m:02d}"

                session["livreur"] = livreur


        if user["client_id"]:
            cursor.execute("SELECT * FROM clients WHERE id=%s", (user["client_id"],))
            session["client"] = cursor.fetchone()

        cursor.close()
        db.close()

        return jsonify({"success": True, "role": user["role"]})

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")
    




    # ================= CLIENT DASHBOARD =================
    @app.route("/clientDashboard")
    def client_dashboard():
        if "client" not in session:
            return redirect("/login")
        return render_template("clientDashboard.html")


    # ================= LIVREUR DASHBOARD =================
    @app.route("/livreurDashboard")
    def livreur_dashboard():
        if "livreur" not in session:
            return redirect("/login")
        return render_template("livreurDashboard.html")

    # =========================================================
    # ===== COMMANDES POUR LIVREUR (DASHBOARD LIVREUR) =========
    # =========================================================
    @app.route("/api/livreur/commandes")
    def commandes_livreur():

        if "livreur" not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401

        liv_id = session["livreur"]["id"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                c.id,
                c.adresse,
                c.poids,
                c.priorite,
                c.statut,
                cl.telephone AS client_tel
            FROM commandes c
            LEFT JOIN clients cl ON c.client_id = cl.id
            WHERE c.livreur_id = %s
        """, (liv_id,))

        commandes = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "commandes": commandes
        })

    # =========================================================
    # ======================= LIVREURS ========================
    # =========================================================
    @app.route("/api/livreurs", methods=["GET"])
    def get_livreurs():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM livreurs")
        rows = cursor.fetchall()

        # TIME → string (JSON safe)
        for l in rows:
            for k in ("heure_debut", "heure_fin"):
                if isinstance(l.get(k), timedelta):
                    sec = int(l[k].total_seconds())
                    h = sec // 3600
                    m = (sec % 3600) // 60
                    l[k] = f"{h:02d}:{m:02d}"

        cursor.close()
        db.close()
        return jsonify(rows)

    @app.route("/api/livreurs", methods=["POST"])
    def add_livreur():
        data = request.json

        cap_map = {
            "SCOOTER": 30,
            "VAN": 300,
            "TRUCK": 3000
        }

        capacite = cap_map.get(data["type_vehicule"], 0)
        raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO livreurs (
                id, nom, latitude_depart, longitude_depart,
                type_vehicule, capacite_poids,
                heure_debut, heure_fin,
                vitesse_moyenne, cout_km,
                telephone, email, disponible
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
        """, (
            data["id"],
            data["nom"],
            data["latitude_depart"],
            data["longitude_depart"],
            data["type_vehicule"],   # ✅ REQUIRED
            capacite,                # 30 / 300 / 3000
            data["heure_debut"],
            data["heure_fin"],
            data["vitesse_moyenne"],
            data["cout_km"],
            data["telephone"],
            data["email"]
        ))


        cursor.execute("""
            INSERT INTO users (email, password_hash, role, livreur_id)
            VALUES (%s,%s,'livreur',%s)
        """, (
            data["email"],
            raw_password,
            data["id"]
        ))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "login_email": data["email"],
            "password": raw_password
        })

    @app.route("/api/livreurs/<id>", methods=["DELETE"])
    def delete_livreur(id):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE commandes
            SET livreur_id = NULL, statut='en_attente'
            WHERE livreur_id=%s
        """, (id,))

        cursor.execute("DELETE FROM users WHERE livreur_id=%s", (id,))
        cursor.execute("DELETE FROM livreurs WHERE id=%s", (id,))

        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})
    
    # =========================================================
    # ======================= COMMANDES =======================
    # =========================================================
    @app.route("/api/commandes", methods=["GET"])
    def get_commandes():
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.*, cl.nom AS client_nom
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
        cursor = db.cursor(dictionary=True)

        try:
            client_id = data.get("client_id")
            client_created = False
            generated_password = None

            # =====================================================
            # 1️⃣ CLIENT HANDLING
            # =====================================================
            if client_id:
                cursor.execute("SELECT id FROM clients WHERE id=%s", (client_id,))
                if not cursor.fetchone():
                    return jsonify({"success": False, "error": "Client introuvable"}), 400

            else:
                # ---- create NEW client ----
                client_id = "CL" + ''.join(random.choices(string.digits, k=4))

                cursor.execute("""
                    INSERT INTO clients (id, nom, telephone, email)
                    VALUES (%s,%s,%s,%s)
                """, (
                    client_id,
                    data["client_nom"],
                    data.get("client_tel"),
                    data["client_email"]
                ))

                # ---- generate password ----
                generated_password = ''.join(
                    random.choices(string.ascii_letters + string.digits, k=10)
                )

                # ---- create user (trigger hashes password) ----
                cursor.execute("""
                    INSERT INTO users (email, password_hash, role, client_id)
                    VALUES (%s,%s,'client',%s)
                """, (
                    data["client_email"],
                    generated_password,
                    client_id
                ))

                client_created = True

            # =====================================================
            # 2️⃣ COMMANDE INSERT
            # =====================================================
            cursor.execute("""
                INSERT INTO commandes
                (id, adresse, latitude, longitude, poids, priorite, client_id, statut)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'en_attente')
            """, (
                data["id"],
                data["adresse"],
                data["latitude"],
                data["longitude"],
                data["poids"],
                data["priorite"],
                client_id
            ))

            db.commit()

            # =====================================================
            # 3️⃣ RESPONSE
            # =====================================================
            response = {"success": True}

            if client_created:
                response.update({
                    "client_created": True,
                    "client_id": client_id,
                    "client_email": data["client_email"],
                    "password": generated_password  # ⚠️ shown ONCE
                })

            return jsonify(response)

        except Exception as e:
            db.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

        finally:
            cursor.close()
            db.close()


    # =========================================================
    # =============== COMMANDES DU CLIENT =====================
    # =========================================================
    @app.route("/api/client/commandes")
    def commandes_client():

        if "client" not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401

        client_id = session["client"]["id"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, adresse, poids, priorite, statut
            FROM commandes
            WHERE client_id = %s
            ORDER BY id DESC
        """, (client_id,))

        commandes = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "commandes": commandes
        })


    # =========================================================
    # ===== CHANGER STATUT COMMANDE (LIVREUR) ==================
    # =========================================================
    @app.route("/api/commandes/<id>/status", methods=["PUT"])
    def changer_statut_commande(id):

        if "livreur" not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401

        data = request.json
        statut = data.get("statut")

        if statut not in ("livree", "reportee"):
            return jsonify({"success": False, "error": "Statut invalide"}), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE commandes
            SET statut = %s
            WHERE id = %s
            AND livreur_id = %s
        """, (statut, id, session["livreur"]["id"]))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({"success": True})



    @app.route("/livreur/map")
    def livreur_map():
        if "livreur" not in session:
            return redirect("/login")
        return render_template("livreurMap.html")


    @app.route("/api/commandes/<id>", methods=["DELETE"])
    def delete_commande(id):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DELETE FROM commandes WHERE id=%s", (id,))
        db.commit()

        cursor.close()
        db.close()

        return jsonify({"success": True})

    # ================= BLUEPRINT =================
    from src.interface.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


