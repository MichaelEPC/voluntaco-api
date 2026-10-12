"""Tests del endpoint de creación de proyectos (/api/v1/fundaciones/proyectos)."""

from tests.conftest import FakeResult

PREFIX = "/api/v1/fundaciones"


def test_crear_proyecto_exitoso(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [FakeResult(last_insert_rowid=42)]

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        json={"nombre": "Reforestación Urbana", "descripcion": "Plantar árboles", "foto_url": None},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["proyecto_id"] == 42


def test_crear_proyecto_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        json={"nombre": "Reforestación Urbana"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Solo las fundaciones pueden realizar esta acción."


def test_crear_proyecto_sin_token(client):
    response = client.post(
        f"{PREFIX}/proyectos/crear",
        json={"nombre": "Reforestación Urbana"},
    )

    assert response.status_code == 401


def test_crear_proyecto_nombre_vacio(client, auth_token_factory):
    token = auth_token_factory(role=2)

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        json={"nombre": ""},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422  # validación de Pydantic (min_length=1)
