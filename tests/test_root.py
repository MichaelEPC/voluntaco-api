"""Tests del endpoint raíz."""


def test_read_root(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Welcome to Voluntaco API"
    assert body["version"] == "1.0.0"
