"""Configuración centralizada de logging para toda la aplicación."""

import logging

from app.core.config import settings


def configure_logging() -> None:
    """Configura el logging raíz una sola vez, al iniciar la aplicación."""
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # Librerías de terceros suelen ser muy verbosas en nivel INFO/DEBUG;
    # las dejamos en WARNING para no inundar los logs de la aplicación.
    logging.getLogger("passlib").setLevel(logging.WARNING)
