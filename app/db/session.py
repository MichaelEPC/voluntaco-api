"""Sesión de base de datos (Turso / libsql) inyectada vía dependencias de FastAPI."""

import libsql_client

from app.core.config import settings


async def get_db():
    """Crea un cliente libsql por request y lo cierra al finalizar."""
    client = libsql_client.create_client(
        url=settings.TURSO_DATABASE_URL,
        auth_token=settings.TURSO_AUTH_TOKEN,
    )
    try:
        yield client
    finally:
        await client.close()
