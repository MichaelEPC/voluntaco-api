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


@pytest.fixture
def fake_db():
    return FakeDBClient()


@pytest.fixture
def client(fake_db):
    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token_factory():
    def _make(user_id: str = "user-123", role: int = 1, name: str = "Test User"):
        return create_access_token({"sub": user_id, "role": role, "name": name})

    return _make
