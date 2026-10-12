"""Lógica de negocio para la gestión de voluntariados de una fundación.

Cadena de propiedad: fundación -> proyecto -> meta -> voluntariado.
Como la tabla `voluntariados` no almacena `fundacion_id` directamente,
toda verificación de pertenencia se hace vía JOIN a través de `metas`
y `proyectos`.
"""

import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


# Extraer Voluntariados de una Fundación específica
async def obtener_voluntariados_por_fundacion(id_fundacion: str, db):
    # Seleccionamos los datos relevantes y hacemos JOIN para traer el nombre de la modalidad y el rol
    query = """
        SELECT
            v.id,
            v.nombre,
            v.descripcion,
            v.estado,
            v.fecha_creacion,
            mod.nombre as modalidad,
            vr.nombre as rol_buscado
        FROM voluntariados v
        JOIN metas mt ON v.meta_id = mt.id
        JOIN proyectos p ON mt.proyecto_id = p.id
        LEFT JOIN modalidades mod ON v.modalidad_id = mod.id
        LEFT JOIN voluntarios_roles vr ON v.usuario_rol_id = vr.id
        WHERE p.fundacion_id = ?
        ORDER BY v.fecha_creacion DESC
    """

    result = await db.execute(query, [id_fundacion])

    # Transformamos las filas en una lista de diccionarios con nombres de columna claros
    voluntariados = [
        {
            "id": row[0],
            "nombre": row[1],
            "descripcion": row[2],
            "estado": row[3],
            "fecha_creacion": row[4],
            "modalidad": row[5],
            "rol_buscado": row[6]
        }
        for row in result.rows
    ]

    return voluntariados


async def _verificar_propiedad_meta(meta_id: int, fundacion_id: str, db):
    """Verifica que la meta exista y pertenezca (vía su proyecto) a la fundación."""
    result = await db.execute(
        """
        SELECT mt.id FROM metas mt
        JOIN proyectos p ON mt.proyecto_id = p.id
        WHERE mt.id = ? AND p.fundacion_id = ?
        """,
        [meta_id, fundacion_id],
    )
    if not result.rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meta no encontrada o no pertenece a tu fundación.",
        )


async def _verificar_propiedad_voluntariado(voluntariado_id: int, fundacion_id: str, db):
    """Verifica que el voluntariado exista y pertenezca a la fundación."""
    result = await db.execute(
        """
        SELECT v.id FROM voluntariados v
        JOIN metas mt ON v.meta_id = mt.id
        JOIN proyectos p ON mt.proyecto_id = p.id
        WHERE v.id = ? AND p.fundacion_id = ?
        """,
        [voluntariado_id, fundacion_id],
    )
    if not result.rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voluntariado no encontrado o no tienes permisos sobre él.",
        )


async def crear_nuevo_voluntariado(fundacion_id: str, datos, db):
    # 0. Verificar que la meta pertenezca a la fundación
    await _verificar_propiedad_meta(datos.meta_id, fundacion_id, db)

    try:
        # 1. Insertar el voluntariado principal
        res = await db.execute(
            """
            INSERT INTO voluntariados (meta_id, tipo_id, nombre, descripcion, modalidad_id, usuario_rol_id, estado)
            VALUES (?, ?, ?, ?, ?, ?, 'ABIERTO')
            """,
            [datos.meta_id, datos.tipo_id, datos.nombre, datos.descripcion, datos.modalidad_id, datos.usuario_rol_id]
        )

        # Obtenemos el ID del voluntariado recién creado
        nuevo_id = res.last_insert_rowid

        # 2. Si hay habilidades, las insertamos en la tabla intermedia
        if datos.habilidades_ids:
            # Preparamos las tuplas para el batch
            operaciones_habilidades = [
                (
                    "INSERT INTO voluntariado_habilidades (voluntariado_id, habilidad_id) VALUES (?, ?)",
                    [nuevo_id, h_id]
                )
                for h_id in datos.habilidades_ids
            ]

            await db.batch(operaciones_habilidades)

        return {
            "status": "success",
            "message": "Convocatoria publicada correctamente.",
            "voluntariado_id": nuevo_id
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error al crear voluntariado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar la convocatoria."
        ) from None


async def eliminar_voluntariado(voluntariado_id: int, fundacion_id: str, db):
    # 1. Verificar que el voluntariado existe y pertenece a la fundación
    await _verificar_propiedad_voluntariado(voluntariado_id, fundacion_id, db)

    try:
        # 2. Eliminar en cascada manualmente (si no tienes ON DELETE CASCADE en SQL)
        # Primero las habilidades asociadas
        await db.execute(
            "DELETE FROM voluntariado_habilidades WHERE voluntariado_id = ?",
            [voluntariado_id]
        )

        # Luego el voluntariado
        await db.execute(
            "DELETE FROM voluntariados WHERE id = ?",
            [voluntariado_id]
        )

        return {"status": "success", "message": "Voluntariado eliminado correctamente."}

    except Exception:
        logger.exception("Error al eliminar voluntariado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar eliminar el registro."
        ) from None


async def modificar_voluntariado(v_id: int, f_id: str, datos, db):
    # 1. Verificar propiedad y existencia
    await _verificar_propiedad_voluntariado(v_id, f_id, db)

    # 2. Construir la query dinámica para los campos básicos
    campos = datos.model_dump(exclude={'habilidades_ids'}, exclude_unset=True)
    if campos:
        set_query = ", ".join([f"{k} = ?" for k in campos.keys()])
        valores = list(campos.values()) + [v_id]
        await db.execute(
            f"UPDATE voluntariados SET {set_query} WHERE id = ?",
            valores
        )

    # 3. Actualizar habilidades (si se enviaron en el body)
    if datos.habilidades_ids is not None:
        # Borramos las anteriores
        await db.execute("DELETE FROM voluntariado_habilidades WHERE voluntariado_id = ?", [v_id])

        # Insertamos las nuevas
        if datos.habilidades_ids:
            batch_habilidades = [
                ("INSERT INTO voluntariado_habilidades (voluntariado_id, habilidad_id) VALUES (?, ?)", [v_id, h_id])
                for h_id in datos.habilidades_ids
            ]
            await db.batch(batch_habilidades)

    return {"message": "Voluntariado actualizado correctamente"}
