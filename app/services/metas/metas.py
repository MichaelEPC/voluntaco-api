"""Lógica de negocio para la gestión de metas (necesidades) de un proyecto."""

import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


async def _verificar_propiedad_proyecto(proyecto_id: str, fundacion_id: str, db) -> None:
    """Verifica que el proyecto exista y pertenezca a la fundación autenticada."""
    check = await db.execute(
        "SELECT id FROM proyectos WHERE id = ? AND fundacion_id = ?",
        [proyecto_id, fundacion_id],
    )
    if not check.rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado o no pertenece a tu fundación.",
        )


async def crear_nueva_meta(proyecto_id: str, fundacion_id: str, datos, db):
    """Crea una nueva meta dentro de un proyecto perteneciente a la fundación autenticada."""
    await _verificar_propiedad_proyecto(proyecto_id, fundacion_id, db)

    try:
        res = await db.execute(
            """
            INSERT INTO metas (proyecto_id, titulo, descripcion, estado)
            VALUES (?, ?, ?, 'PENDIENTE')
            """,
            [proyecto_id, datos.titulo, datos.descripcion],
        )

        return {
            "status": "success",
            "message": "Meta creada correctamente.",
            "meta_id": res.last_insert_rowid,
        }

    except Exception:
        logger.exception("Error al crear meta")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar la meta.",
        ) from None


async def obtener_metas_por_proyecto(proyecto_id: str, fundacion_id: str, db):
    """Obtiene todas las metas de un proyecto perteneciente a la fundación autenticada."""
    await _verificar_propiedad_proyecto(proyecto_id, fundacion_id, db)

    query = """
        SELECT id, titulo, descripcion, estado, fecha_creacion
        FROM metas
        WHERE proyecto_id = ?
        ORDER BY fecha_creacion DESC
    """

    result = await db.execute(query, [proyecto_id])

    return [
        {
            "id": row[0],
            "titulo": row[1],
            "descripcion": row[2],
            "estado": row[3],
            "fecha_creacion": row[4],
        }
        for row in result.rows
    ]
