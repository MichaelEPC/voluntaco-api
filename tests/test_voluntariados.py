"""Tests del endpoint de creación de voluntariados (/api/v1/fundaciones/voluntariados)."""

import uuid

from tests.conftest import FakeResult

PREFIX = "/api/v1/fundaciones"


def _payload(**overrides):
    base = {
        "meta_id": 1,
        "tipo_id": 1,
        "nombre": "Apoyo logístico",
        "descripcion": "Ayuda con la logística del evento",
        "modalidad_id": 1,
        "usuario_rol_id": 1,
        "habilidades_ids": [],
    }
    base.update(overrides)
    return base


def test_crear_voluntariado_exitoso(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [
        FakeResult(rows=[(1,)]),  # la meta existe y pertenece (vía proyecto) a la fundación
        FakeResult(),  # insert del voluntariado (el ID se genera como UUID en el servicio)
    ]

    response = client.post(
        f"{PREFIX}/voluntariados/crear",
        json=_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert uuid.UUID(body["voluntariado_id"])  # debe ser un UUID válido


def test_crear_voluntariado_meta_no_pertenece_a_fundacion(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult(rows=[])]  # la meta no existe o no es de esta fundación

    response = client.post(
        f"{PREFIX}/voluntariados/crear",
        json=_payload(meta_id=999),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meta no encontrada o no pertenece a tu fundación."


def test_crear_voluntariado_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.post(
        f"{PREFIX}/voluntariados/crear",
        json=_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_obtener_voluntariado_por_id_exitoso(client, fake_db, fake_storage):
    fake_db._responses = [
        FakeResult(
            rows=[
                (
                    "vol-1",
                    "Apoyo logístico",
                    "Ayuda con la logística del evento",
                    "ABIERTO",
                    "2024-01-01",
                    "Presencial",
                    "Analista",
                    "proyecto-1",
                    "Reforestación Urbana",
                    "proyectos/proyecto-1/2024/01/foto-abc123.jpg",
                    "fundacion-1",
                    "Fundación Verde",
                    "perfiles_fundaciones/fundacion-1/2024/01/foto-xyz789.jpg",
                )
            ]
        )
    ]

    response = client.get(f"{PREFIX}/voluntariados/vol-1")

    assert response.status_code == 200
    assert response.json() == {
        "id": "vol-1",
        "nombre": "Apoyo logístico",
        "descripcion": "Ayuda con la logística del evento",
        "estado": "ABIERTO",
        "fecha_creacion": "2024-01-01",
        "modalidad": "Presencial",
        "rol_buscado": "Analista",
        "proyecto": {
            "id": "proyecto-1",
            "titulo": "Reforestación Urbana",
            "foto_url": "https://fake-r2.test/presigned/proyectos/proyecto-1/2024/01/foto-abc123.jpg",
        },
        "fundacion": {
            "id": "fundacion-1",
            "nombre": "Fundación Verde",
            "foto_url": (
                "https://fake-r2.test/presigned/"
                "perfiles_fundaciones/fundacion-1/2024/01/foto-xyz789.jpg"
            ),
        },
    }


def test_obtener_voluntariado_por_id_no_encontrado(client, fake_db):
    fake_db._responses = [FakeResult(rows=[])]

    response = client.get(f"{PREFIX}/voluntariados/no-existe")

    assert response.status_code == 404
    assert response.json()["detail"] == "Voluntariado no encontrado."
