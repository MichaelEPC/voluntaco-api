"""Lógica de negocio para la gestión de voluntariados de una fundación.

Cadena de propiedad: fundación -> proyecto -> meta -> voluntariado.
Como la tabla `voluntariados` no almacena `fundacion_id` directamente,
toda verificación de pertenencia se hace vía JOIN a través de `metas`
y `proyectos`.
"""

import logging
import uuid

from fastapi import HTTPException, status

from app.services.storage.r2_storage import CloudStorageError, CloudStorageService

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

async def obtener_voluntariados_por_metas(id_meta: str, db):
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
        LEFT JOIN modalidades mod ON v.modalidad_id = mod.id
        LEFT JOIN voluntarios_roles vr ON v.usuario_rol_id = vr.id
        WHERE v.meta_id = ?
        ORDER BY v.fecha_creacion DESC
    """

    result = await db.execute(query, [id_meta])

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


async def obtener_voluntariado_por_id(voluntariado_id: str, db, storage: CloudStorageService):
    """Obtiene el detalle completo de un voluntariado por su ID.

    Además de los datos propios del voluntariado, incluye la información de
    la fundación (vía su perfil en `perfiles_fundaciones`) y del proyecto al
    que pertenece (a través de su meta), con las fotos ya resueltas a URLs
    accesibles desde el navegador.
    """
    query = """
        SELECT
            v.id,
            v.nombre,
            v.descripcion,
            v.estado,
            v.fecha_creacion,
            mod.nombre as modalidad,
            vr.nombre as rol_buscado,
            p.id as proyecto_id,
            p.nombre as proyecto_nombre,
            p.foto_url as proyecto_foto_url,
            pf.usuario_id as fundacion_id,
            pf.nombre_legal as fundacion_nombre,
            pf.foto_perfil_url as fundacion_foto_url
        FROM voluntariados v
        JOIN metas mt ON v.meta_id = mt.id
        JOIN proyectos p ON mt.proyecto_id = p.id
        JOIN perfiles_fundaciones pf ON p.fundacion_id = pf.usuario_id
        LEFT JOIN modalidades mod ON v.modalidad_id = mod.id
        LEFT JOIN voluntarios_roles vr ON v.usuario_rol_id = vr.id
        WHERE v.id = ?
    """

    result = await db.execute(query, [voluntariado_id])
    if not result.rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voluntariado no encontrado.",
        )

    row = result.rows[0]
    return {
        "id": row[0],
        "nombre": row[1],
        "descripcion": row[2],
        "estado": row[3],
        "fecha_creacion": row[4],
        "modalidad": row[5],
        "rol_buscado": row[6],
        "proyecto": {
            "id": row[7],
            "titulo": row[8],
            "foto_url": _resolver_imagen(row[9], storage),
        },
        "fundacion": {
            "id": row[10],
            "nombre": row[11],
            "foto_url": _resolver_imagen(row[12], storage),
        },
    }


def _resolver_imagen(valor: str | None, storage: CloudStorageService) -> str | None:
    """Convierte la key/URL guardada en BD a una URL accesible desde el navegador.

    Si la imagen no existe (`valor` es `None`) o el almacenamiento falla al
    resolverla, se devuelve `None` en vez de romper toda la respuesta.
    """
    if not valor:
        return None

    try:
        return storage.obtener_url_descarga(valor)
    except CloudStorageError:
        logger.warning("No fue posible resolver una URL de imagen ('%s')", valor, exc_info=True)
        return None


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


async def _verificar_propiedad_voluntariado(voluntariado_id: str, fundacion_id: str, db):
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
        nuevo_id = str(uuid.uuid4())  # ID tipo texto (UUID) para máxima unicidad

        await db.execute(
            """
            INSERT INTO voluntariados (id, meta_id, tipo_id, nombre, descripcion, modalidad_id, usuario_rol_id, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ABIERTO')
            """,
            [nuevo_id, datos.meta_id, datos.tipo_id, datos.nombre, datos.descripcion, datos.modalidad_id, datos.usuario_rol_id]
        )

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


async def eliminar_voluntariado(voluntariado_id: str, fundacion_id: str, db):
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


async def modificar_voluntariado(v_id: str, f_id: str, datos, db):
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
