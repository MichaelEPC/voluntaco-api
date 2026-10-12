"""Tests del endpoint de creación de voluntariados (/api/v1/fundaciones/voluntariados)."""

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
        FakeResult(last_insert_rowid=9),  # insert del voluntariado
    ]

    response = client.post(
        f"{PREFIX}/voluntariados/crear",
        json=_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["voluntariado_id"] == 9


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
