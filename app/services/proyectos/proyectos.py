"""Lógica de negocio para la gestión de proyectos de una fundación."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile, status

from app.core.validators import validate_image_upload
from app.services.storage.r2_storage import CloudStorageError, CloudStorageService

logger = logging.getLogger(__name__)

_CARPETA_IMAGENES_PROYECTO = "proyectos"


def _fila_a_proyecto(row) -> dict:
    """Mapea una fila de la tabla `proyectos` a un diccionario con nombres de columna claros."""
    return {
        "id": row[0],
        "nombre": row[1],
        "descripcion": row[2],
        "foto_url": row[3],
        "foto_cabeza_url": row[4],
        "estado": row[5],
        "fecha_creacion": row[6],
    }


def _fila_a_proyecto_resumen(row) -> dict:
    """Mapea una fila a la vista resumida usada en listados (tarjetas/desplegables).

    Solo incluye la foto principal (`foto_url`); la foto de encabezado
    (`foto_cabeza_url`) se reserva para la vista de detalle de un proyecto.
    """
    return {
        "id": row[0],
        "nombre": row[1],
        "descripcion": row[2],
        "foto_url": row[3],
        "estado": row[4],
        "fecha_creacion": row[5],
    }


async def obtener_proyectos_por_fundacion(fundacion_id: str, db, storage: CloudStorageService):
    """Obtiene todos los proyectos de la fundación autenticada (vista de listado).

    Cada proyecto incluye su foto principal (`foto_url`) ya resuelta a una URL
    accesible desde el navegador, lista para mostrarse en cada tarjeta.
    """
    query = """
        SELECT id, nombre, descripcion, foto_url, estado, fecha_creacion
        FROM proyectos
        WHERE fundacion_id = ?
        ORDER BY fecha_creacion DESC
    """

    result = await db.execute(query, [fundacion_id])

    proyectos = [_fila_a_proyecto_resumen(row) for row in result.rows]
    for proyecto in proyectos:
        proyecto["foto_url"] = _resolver_imagen_proyecto(proyecto["foto_url"], storage)
    return proyectos


async def obtener_proyectos_activos_por_fundacion(
    fundacion_id: str, db, storage: CloudStorageService
):
    """Obtiene todos los proyectos activos de la fundación autenticada (vista de listado).

    Cada proyecto incluye su foto principal (`foto_url`) ya resuelta a una URL
    accesible desde el navegador, lista para mostrarse en cada tarjeta.
    """
    query = """
        SELECT id, nombre, descripcion, foto_url, estado, fecha_creacion
        FROM proyectos
        WHERE fundacion_id = ? AND estado = 'ACTIVO'
        ORDER BY fecha_creacion DESC
    """

    result = await db.execute(query, [fundacion_id])

    proyectos = [_fila_a_proyecto_resumen(row) for row in result.rows]
    for proyecto in proyectos:
        proyecto["foto_url"] = _resolver_imagen_proyecto(proyecto["foto_url"], storage)
    return proyectos


async def obtener_proyecto_invididual_fundacion(
    fundacion_id: str, proyecto_id: str, db, storage: CloudStorageService
):
    """Obtiene un proyecto individual perteneciente a la fundación autenticada.

    Además de los datos del proyecto, resuelve `foto_url` y `foto_cabeza_url`
    (keys crudas o URLs guardadas en BD) a URLs accesibles desde el navegador
    consultando el servicio de almacenamiento (p. ej. generando una URL
    prefirmada si el bucket es privado).
    """
    query = """
        SELECT id, nombre, descripcion, foto_url, foto_cabeza_url, estado, fecha_creacion
        FROM proyectos
        WHERE fundacion_id = ? AND id = ?
        ORDER BY fecha_creacion DESC
    """

    result = await db.execute(query, [fundacion_id, proyecto_id])

    proyectos = [_fila_a_proyecto(row) for row in result.rows]
    if not proyectos:
        return None

    proyecto = proyectos[0]
    proyecto["foto_url"] = _resolver_imagen_proyecto(proyecto["foto_url"], storage)
    proyecto["foto_cabeza_url"] = _resolver_imagen_proyecto(proyecto["foto_cabeza_url"], storage)
    return proyecto


def _resolver_imagen_proyecto(valor: str | None, storage: CloudStorageService) -> str | None:
    """Convierte la key/URL guardada en BD a una URL accesible desde el navegador.

    Si la imagen no existe (`valor` es `None`) o si el almacenamiento falla al
    resolver la URL, se devuelve `None` en vez de romper toda la respuesta del
    proyecto; se registra una advertencia para diagnóstico.
    """
    if not valor:
        return None

    try:
        return storage.obtener_url_descarga(valor)
    except CloudStorageError:
        logger.warning(
            "No fue posible resolver la URL de la imagen de proyecto '%s'", valor, exc_info=True
        )
        return None


async def _subir_imagen_proyecto(
    archivo: UploadFile | None, proyecto_id: str, campo: str, storage: CloudStorageService
) -> str | None:
    """Valida y sube (si se envió) una imagen de proyecto a Cloudflare R2.

    Devuelve `None` si no se adjuntó archivo; de lo contrario, la URL (o key)
    resultante lista para persistir en la columna correspondiente.
    """
    if archivo is None or not archivo.filename:
        return None

    contenido, extension = await validate_image_upload(archivo)

    try:
        return storage.guardar_archivo(
            contenido,
            carpeta=f"{_CARPETA_IMAGENES_PROYECTO}/{proyecto_id}",
            nombre_base=campo,
            extension=extension,
            content_type=archivo.content_type,
        )
    except CloudStorageError as exc:
        logger.exception("Error al subir imagen de proyecto a almacenamiento en la nube")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No fue posible subir la imagen al almacenamiento en la nube.",
        ) from exc


async def crear_nuevo_proyecto(
    fundacion_id: str,
    datos,
    foto: UploadFile | None,
    foto_cabeza: UploadFile | None,
    db,
    storage: CloudStorageService,
):
    """Crea un nuevo proyecto perteneciente a la fundación autenticada.

    Si el frontend adjunta `foto` (imagen principal) y/o `foto_cabeza`
    (imagen de encabezado), ambas se suben a Cloudflare R2 antes de insertar
    el registro y sus URLs resultantes se guardan en `foto_url` y
    `foto_cabeza_url`. Ambas imágenes son opcionales.

    `datos.fecha_creacion` (si el frontend la envía) se usa como fecha de
    creación del proyecto; si no se envía, se usa la fecha/hora actual.
    """
    nuevo_id = str(uuid.uuid4())  # ID tipo texto (UUID) para máxima unicidad
    fecha_creacion = (datos.fecha_creacion or datetime.now(UTC)).isoformat()

    foto_url = await _subir_imagen_proyecto(foto, nuevo_id, "foto", storage)
    foto_cabeza_url = await _subir_imagen_proyecto(foto_cabeza, nuevo_id, "foto-cabeza", storage)

    try:
        await db.execute(
            """
            INSERT INTO proyectos
                (id, fundacion_id, nombre, descripcion, foto_url, foto_cabeza_url, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
            """,
            [
                nuevo_id,
                fundacion_id,
                datos.nombre,
                datos.descripcion,
                foto_url,
                foto_cabeza_url,
                fecha_creacion,
            ],
        )

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
