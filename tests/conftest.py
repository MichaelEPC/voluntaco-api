"""Fixtures compartidas para los tests de la API.

Como la app usa un cliente Turso (libsql) async inyectado vía
`Depends(get_db)`, en tests lo sustituimos por un doble de prueba
(`FakeDBClient`) mediante `app.dependency_overrides`, sin tocar red.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.services.storage.r2_storage import get_storage_service


class FakeResult:
    """Imita la respuesta de libsql_client: expone `.rows`."""

    def __init__(self, rows=None, last_insert_rowid=None):
        self.rows = rows or []
        self.last_insert_rowid = last_insert_rowid


class FakeDBClient:
    """Doble de prueba del cliente Turso: devuelve respuestas predefinidas en orden."""

    def __init__(self, responses=None):
        self._responses = list(responses or [])
        self.executed = []

    async def execute(self, query, params=None):
        self.executed.append((query, params))
        if self._responses:
            return self._responses.pop(0)
        return FakeResult()

    async def batch(self, operations):
        self.executed.append(("BATCH", operations))
        return FakeResult()

    async def close(self):
        pass


class FakeStorageService:
    """Doble de prueba del servicio de almacenamiento R2: no habla con la red."""

    def __init__(self):
        self.archivos_subidos = []
        self.urls_resueltas = []

    def guardar_archivo(self, contenido, carpeta, nombre_base, extension, content_type):
        self.archivos_subidos.append((contenido, carpeta, nombre_base, extension, content_type))
        return f"https://fake-r2.test/{carpeta}/{nombre_base}.{extension}"

    def obtener_url_descarga(self, valor_almacenado, expiracion_segundos=None):
        self.urls_resueltas.append(valor_almacenado)
        if valor_almacenado.startswith(("http://", "https://")):
            return valor_almacenado
        return f"https://fake-r2.test/presigned/{valor_almacenado}"


@pytest.fixture
def fake_db():
    return FakeDBClient()


@pytest.fixture
def fake_storage():
    return FakeStorageService()


@pytest.fixture
def client(fake_db, fake_storage):
    async def override_get_db():
        yield fake_db

    def override_get_storage_service():
        return fake_storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage_service] = override_get_storage_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token_factory():
    def _make(user_id: str = "user-123", role: int = 1, name: str = "Test User"):
        return create_access_token({"sub": user_id, "role": role, "name": name})

    return _make

