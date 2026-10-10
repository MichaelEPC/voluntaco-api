"""Tests de los endpoints de autenticación (/api/v1/auth)."""

from tests.conftest import FakeResult

PREFIX = "/api/v1/auth"


def test_iniciar_sesion_email_demasiado_largo(client):
    email_largo = f"{'a' * 70}@test.com"  # formato válido, pero > 72 caracteres
    response = client.post(
        f"{PREFIX}/iniciar-sesion",
        json={"email": email_largo, "password": "secret123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "El correo electrónico debe tener entre 1 y 72 caracteres."


def test_iniciar_sesion_credenciales_invalidas(client, fake_db):
    fake_db._responses = [FakeResult(rows=[])]  # usuario no encontrado

    response = client.post(
        f"{PREFIX}/iniciar-sesion",
        json={"email": "user@test.com", "password": "secret123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El email no se encuentra registrado."


def test_registro_voluntario_documento_invalido(client):
    response = client.post(
        f"{PREFIX}/registro-voluntario",
        json={
            "documento_identidad": "12345678901",  # 11 caracteres, excede el máximo de 10
            "nombre_completo": "Ana Pérez",
            "email": "ana@test.com",
            "password": "secret123",
            "telefono": "3001234567",
            "rol_id": 1,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "El documento de identidad debe tener entre 1 y 10 caracteres."


def test_registro_voluntario_email_duplicado(client, fake_db):
    fake_db._responses = [FakeResult(rows=[("existing-id",)])]  # el email ya existe

    response = client.post(
        f"{PREFIX}/registro-voluntario",
        json={
            "documento_identidad": "123456789",
            "nombre_completo": "Ana Pérez",
            "email": "ana@test.com",
            "password": "secret123",
            "telefono": "3001234567",
            "rol_id": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El email ya se encuentra registrado."


def test_registro_voluntario_exitoso(client, fake_db):
    fake_db._responses = [FakeResult(rows=[]), FakeResult(rows=[])]  # email y cédula libres

    response = client.post(
        f"{PREFIX}/registro-voluntario",
        json={
            "documento_identidad": "123456789",
            "nombre_completo": "Ana Pérez",
            "email": "ana@test.com",
            "password": "secret123",
            "telefono": "3001234567",
            "rol_id": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "usuario_id" in body
