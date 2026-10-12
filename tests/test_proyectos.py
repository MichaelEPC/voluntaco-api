"""Tests del endpoint de creación de proyectos (/api/v1/fundaciones/proyectos)."""

import uuid
from datetime import UTC, datetime, timedelta

from tests.conftest import FakeResult

PREFIX = "/api/v1/fundaciones"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_listar_proyectos_exitoso(client, fake_db, fake_storage, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [
        FakeResult(
            rows=[
                (
                    1,
                    "Reforestación Urbana",
                    "Plantar árboles",
                    "proyectos/1/2024/01/foto-abc123.jpg",  # key cruda (bucket privado)
                    "ACTIVO",
                    "2024-01-01",
                ),
            ]
        )
    ]

    response = client.get(
        f"{PREFIX}/proyectos",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "id": 1,
            "nombre": "Reforestación Urbana",
            "descripcion": "Plantar árboles",
            "foto_url": "https://fake-r2.test/presigned/proyectos/1/2024/01/foto-abc123.jpg",
            "estado": "ACTIVO",
            "fecha_creacion": "2024-01-01",
        }
    ]
    # No se expone la foto de encabezado en el listado, solo la principal
    assert "foto_cabeza_url" not in body[0]
    assert fake_storage.urls_resueltas == ["proyectos/1/2024/01/foto-abc123.jpg"]


def test_listar_proyectos_sin_foto_no_consulta_almacenamiento(
    client, fake_db, fake_storage, auth_token_factory
):
    token = auth_token_factory(role=2)
    fake_db._responses = [
        FakeResult(
            rows=[(2, "Proyecto sin imagen", None, None, "ACTIVO", "2024-02-01")]
        )
    ]

    response = client.get(
        f"{PREFIX}/proyectos",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["foto_url"] is None
    assert fake_storage.urls_resueltas == []


def test_listar_proyectos_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.get(
        f"{PREFIX}/proyectos",
        headers=_auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Solo las fundaciones pueden realizar esta acción."


def test_listar_proyectos_sin_token(client):
    response = client.get(f"{PREFIX}/proyectos")

    assert response.status_code == 401


def test_obtener_proyecto_individual_resuelve_imagenes_desde_almacenamiento(
    client, fake_db, fake_storage, auth_token_factory
):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [
        FakeResult(
            rows=[
                (
                    "proyecto-1",
                    "Reforestación Urbana",
                    "Plantar árboles",
                    "proyectos/proyecto-1/2024/01/foto-abc123.jpg",  # key cruda (bucket privado)
                    "proyectos/proyecto-1/2024/01/foto-cabeza-def456.jpg",
                    "ACTIVO",
                    "2024-01-01",
                ),
            ]
        )
    ]

    response = client.post(
        f"{PREFIX}/proyectos/proyecto-1",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["foto_url"] == "https://fake-r2.test/presigned/proyectos/proyecto-1/2024/01/foto-abc123.jpg"
    assert (
        body["foto_cabeza_url"]
        == "https://fake-r2.test/presigned/proyectos/proyecto-1/2024/01/foto-cabeza-def456.jpg"
    )
    # Se consultó al almacenamiento por ambas keys guardadas en BD
    assert set(fake_storage.urls_resueltas) == {
        "proyectos/proyecto-1/2024/01/foto-abc123.jpg",
        "proyectos/proyecto-1/2024/01/foto-cabeza-def456.jpg",
    }


def test_obtener_proyecto_individual_sin_imagenes(
    client, fake_db, fake_storage, auth_token_factory
):
    token = auth_token_factory(role=2)
    fake_db._responses = [
        FakeResult(
            rows=[("proyecto-1", "Reforestación Urbana", None, None, None, "ACTIVO", "2024-01-01")]
        )
    ]

    response = client.post(
        f"{PREFIX}/proyectos/proyecto-1",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["foto_url"] is None
    assert body["foto_cabeza_url"] is None
    assert fake_storage.urls_resueltas == []  # No se consulta el almacenamiento sin imágenes


def test_obtener_proyecto_individual_no_encontrado(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult(rows=[])]

    response = client.post(
        f"{PREFIX}/proyectos/no-existe",
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert response.json() is None


def test_crear_proyecto_exitoso_sin_imagenes(client, fake_db, fake_storage, auth_token_factory):
    token = auth_token_factory(role=2)  # role=2 => fundación
    fake_db._responses = [FakeResult()]

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana", "descripcion": "Plantar árboles"},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    # El ID ahora es un UUID (texto) generado en el backend, no un entero autoincremental
    assert uuid.UUID(body["proyecto_id"])
    assert fake_storage.archivos_subidos == []  # No se envió ninguna imagen


def test_crear_proyecto_usa_fecha_creacion_enviada_por_frontend(
    client, fake_db, auth_token_factory
):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult()]

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana", "fecha_creacion": "2023-05-10T08:30:00"},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    _, params = fake_db.executed[0]
    assert params[-1] == "2023-05-10T08:30:00+00:00"  # Normalizada a UTC-aware


def test_crear_proyecto_sin_fecha_usa_fecha_actual_del_servidor(
    client, fake_db, auth_token_factory
):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult()]

    antes = datetime.now(UTC)
    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana"},
        headers=_auth_header(token),
    )
    despues = datetime.now(UTC)

    assert response.status_code == 200
    _, params = fake_db.executed[0]
    fecha_guardada = datetime.fromisoformat(params[-1])
    assert antes <= fecha_guardada <= despues


def test_crear_proyecto_fecha_creacion_futura_es_invalida(client, auth_token_factory):
    token = auth_token_factory(role=2)
    fecha_futura = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana", "fecha_creacion": fecha_futura},
        headers=_auth_header(token),
    )

    assert response.status_code == 422


def test_crear_proyecto_exitoso_con_imagenes(client, fake_db, fake_storage, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult()]

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana", "descripcion": "Plantar árboles"},
        files={
            "foto": ("foto.jpg", b"contenido-foto", "image/jpeg"),
            "foto_cabeza": ("cabeza.png", b"contenido-cabeza", "image/png"),
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert uuid.UUID(body["proyecto_id"])
    # Ambas imágenes se subieron al almacenamiento en la nube
    assert len(fake_storage.archivos_subidos) == 2
    carpetas = {subida[1] for subida in fake_storage.archivos_subidos}
    assert carpetas == {f"proyectos/{body['proyecto_id']}"}
    # La inserción recibe las URLs devueltas por el storage, no el contenido binario
    _, params = fake_db.executed[0]
    assert params[4].startswith("https://fake-r2.test/")  # foto_url
    assert params[5].startswith("https://fake-r2.test/")  # foto_cabeza_url


def test_crear_proyecto_imagen_tipo_no_soportado(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult()]

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana"},
        files={"foto": ("foto.gif", b"contenido", "image/gif")},
        headers=_auth_header(token),
    )

    assert response.status_code == 415
    assert "no soportado" in response.json()["detail"]


def test_crear_proyecto_imagen_excede_tamano_maximo(client, fake_db, auth_token_factory):
    token = auth_token_factory(role=2)
    fake_db._responses = [FakeResult()]

    contenido_grande = b"0" * (5 * 1024 * 1024 + 1)  # 1 byte más que el límite (5 MB)

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana"},
        files={"foto": ("foto.jpg", contenido_grande, "image/jpeg")},
        headers=_auth_header(token),
    )

    assert response.status_code == 413


def test_crear_proyecto_requiere_rol_fundacion(client, auth_token_factory):
    token = auth_token_factory(role=1)  # role=1 => voluntario

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana"},
        headers=_auth_header(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Solo las fundaciones pueden realizar esta acción."


def test_crear_proyecto_sin_token(client):
    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": "Reforestación Urbana"},
    )

    assert response.status_code == 401


def test_crear_proyecto_nombre_vacio(client, auth_token_factory):
    token = auth_token_factory(role=2)

    response = client.post(
        f"{PREFIX}/proyectos/crear",
        data={"nombre": ""},
        headers=_auth_header(token),
    )

    assert response.status_code == 422  # validación de Pydantic (min_length=1)
