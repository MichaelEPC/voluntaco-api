"""Tests del endpoint de creación de metas (/api/v1/fundaciones/proyectos/{id}/metas)."""

from tests.conftest import FakeResult

PREFIX = "/api/v1/fundaciones"


def test_crear_meta_exitoso(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [
        FakeResult(rows=[(1,)]),  # el proyecto existe y pertenece a la fundación
        FakeResult(last_insert_rowid=7),  # insert de la meta
    ]

    response = client.post(
        f"{PREFIX}/proyectos/1/metas/crear",
        json={"titulo": "Recolectar 500 árboles", "descripcion": "Meta de reforestación"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["meta_id"] == 7


def test_crear_meta_proyecto_no_pertenece_a_fundacion(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult(rows=[])]  # el proyecto no existe o no es de esta fundación

    response = client.post(
        f"{PREFIX}/proyectos/999/metas/crear",
        json={"titulo": "Meta inválida"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Proyecto no encontrado o no pertenece a tu fundación."


def test_crear_meta_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.post(
        f"{PREFIX}/proyectos/1/metas/crear",
        json={"titulo": "Meta cualquiera"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_crear_meta_sin_token(client):
    response = client.post(
        f"{PREFIX}/proyectos/1/metas/crear",
        json={"titulo": "Meta cualquiera"},
    )

    assert response.status_code == 401


def test_obtener_metas_exitoso(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [
        FakeResult(rows=[(1,)]),  # el proyecto existe y pertenece a la fundación
        FakeResult(
            rows=[
                (7, "Recolectar 500 árboles", "Meta de reforestación", "PENDIENTE", "2024-01-01"),
                (8, "Capacitar voluntarios", None, "COMPLETADA", "2024-01-02"),
            ]
        ),
    ]

    response = client.get(
        f"{PREFIX}/proyectos/1/metas",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 7,
            "titulo": "Recolectar 500 árboles",
            "descripcion": "Meta de reforestación",
            "estado": "PENDIENTE",
            "fecha_creacion": "2024-01-01",
        },
        {
            "id": 8,
            "titulo": "Capacitar voluntarios",
            "descripcion": None,
            "estado": "COMPLETADA",
            "fecha_creacion": "2024-01-02",
        },
    ]


def test_obtener_metas_proyecto_sin_metas(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [
        FakeResult(rows=[(1,)]),  # el proyecto existe y pertenece a la fundación
        FakeResult(rows=[]),  # sin metas todavía
    ]

    response = client.get(
        f"{PREFIX}/proyectos/1/metas",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_obtener_metas_proyecto_no_pertenece_a_fundacion(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult(rows=[])]  # el proyecto no existe o no es de esta fundación

    response = client.get(
        f"{PREFIX}/proyectos/999/metas",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Proyecto no encontrado o no pertenece a tu fundación."


def test_obtener_metas_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.get(
        f"{PREFIX}/proyectos/1/metas",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_obtener_metas_sin_token(client):
    response = client.get(f"{PREFIX}/proyectos/1/metas")

    assert response.status_code == 401
