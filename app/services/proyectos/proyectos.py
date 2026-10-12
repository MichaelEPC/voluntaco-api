"""Lógica de negocio para la gestión de proyectos de una fundación."""

import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


async def crear_nuevo_proyecto(fundacion_id: str, datos, db):
    """Crea un nuevo proyecto perteneciente a la fundación autenticada."""
    try:
        res = await db.execute(
            """
            INSERT INTO proyectos (fundacion_id, nombre, descripcion, foto_url, estado)
            VALUES (?, ?, ?, ?, 'ACTIVO')
            """,
            [fundacion_id, datos.nombre, datos.descripcion, datos.foto_url],
        )

        nuevo_id = res.last_insert_rowid

        return {
            "status": "success",
            "message": "Proyecto creado correctamente.",
            "proyecto_id": nuevo_id,
        }

    except Exception:
        logger.exception("Error al crear proyecto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar el proyecto.",
        ) from None
