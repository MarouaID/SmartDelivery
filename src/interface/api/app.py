import os
from flask import Flask, render_template
from .routes import api_bp

def create_app():
    template_folder = os.path.join(os.path.dirname(__file__), '../web/templates')
    static_folder = os.path.join(os.path.dirname(__file__), '../web/static')
    
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # Enregistrement du blueprint API
    app.register_blueprint(api_bp, url_prefix="/api")

    # Routes HTML
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/carte')
    def carte():
        return render_template('carte.html')
    
    @app.route("/livreurs")
    def livreurs():
        return render_template("livreurs.html")

    @app.route("/commandes")
    def commandes():
        return render_template("commandes.html")

    @app.route("/suivi")
    def suivi():
        return render_template("suivi.html")

    return app
