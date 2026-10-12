"""Validadores reutilizables para los payloads de entrada de la API.

Centraliza las comprobaciones de longitud que antes estaban duplicadas en
cada endpoint, preservando el mismo comportamiento (HTTP 401 + mensaje).
"""

from fastapi import HTTPException, UploadFile, status

from app.core.constants import IMAGEN_PROYECTO_MAX_BYTES, IMAGENES_PROYECTO_CONTENT_TYPES


def validate_length_range(value: str, min_len: int, max_len: int, error_message: str) -> None:
    """Valida que `len(value)` esté en el rango (min_len, max_len].

    Lanza HTTPException 401 con `error_message` si la longitud es inválida,
    replicando la validación histórica de los endpoints de autenticación.
    """
    if len(value) > max_len or len(value) <= min_len:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message,
        )


async def validate_image_upload(
    archivo: UploadFile,
    *,
    allowed_content_types: dict[str, str] = IMAGENES_PROYECTO_CONTENT_TYPES,
    max_bytes: int = IMAGEN_PROYECTO_MAX_BYTES,
) -> tuple[bytes, str]:
    """Valida tipo y tamaño de una imagen subida por el cliente.

    Devuelve una tupla `(contenido, extension)` lista para enviar a almacenamiento.
    Lanza HTTPException (415/413/400) si el archivo no cumple las reglas.
    """
    extension = allowed_content_types.get(archivo.content_type)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato de imagen no soportado. Usa JPEG, PNG o WEBP.",
        )

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de imagen está vacío.",
        )

    if len(contenido) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"La imagen supera el tamaño máximo permitido ({max_bytes // (1024 * 1024)} MB).",
        )

    return contenido, extension
