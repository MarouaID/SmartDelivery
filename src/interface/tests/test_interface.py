import json
import pytest
from src.interface.api.app import create_app


@pytest.fixture
def client():
    """
    Initialise une application Flask de test.
    """
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# -------------------------------------------
# TEST : /api/status
# -------------------------------------------
def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "OK"
    assert "SmartDelivery API" in data["service"]


# -------------------------------------------
# TEST : /api/commandes
# -------------------------------------------
def test_get_commandes(client):
    response = client.get("/api/commandes")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) or isinstance(data, dict)


# -------------------------------------------
# TEST : /api/livreurs
# -------------------------------------------
def test_get_livreurs(client):
    response = client.get("/api/livreurs")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) or isinstance(data, dict)


# -------------------------------------------
# TEST : /api/affecter
# -------------------------------------------
def test_affecter(client):
    payload = {
        "commandes": [
            {"id": 1, "latitude": 48.85, "longitude": 2.35}
        ],
        "livreurs": [
            {"id": 100, "latitude": 48.86, "longitude": 2.34}
        ]
    }

    response = client.post(
        "/api/affecter",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    data = response.get_json()

    # les assertions varient selon ton AffectationManager
    assert isinstance(data, dict)
    assert "affectations" in data or "resultat" in data


# -------------------------------------------
# TEST : /api/optimiser_route
# -------------------------------------------
def test_optimiser_route(client):
    payload = {
        "points": [
            {"lat": 48.8566, "lon": 2.3522},
            {"lat": 48.8600, "lon": 2.3400},
            {"lat": 48.8700, "lon": 2.3600}
        ]
    }

    response = client.post(
        "/api/optimiser_route",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, dict)
    assert "chemin" in data or "solution" in data

