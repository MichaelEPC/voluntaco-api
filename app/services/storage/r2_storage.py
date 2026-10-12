"""Servicio genérico de almacenamiento en la nube (Cloudflare R2).

R2 expone una API compatible con S3, por lo que se usa boto3 apuntando a su
endpoint propio. Cualquier dominio de negocio que necesite subir archivos
(imágenes de proyectos, documentos, etc.) reutiliza `CloudStorageService` en
vez de hablar con boto3 directamente, lo que mantiene la lógica de
construcción de keys y manejo de errores en un único lugar.
"""

import logging
import re
import uuid
from datetime import UTC, datetime
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Vigencia por defecto de las URLs prefirmadas (presigned) generadas para leer
# archivos de un bucket privado sin dominio público configurado.
_URL_PRESIGNADA_EXPIRACION_SEGUNDOS_DEFAULT = 3600  # 1 hora

# Solo letras minúsculas, dígitos, "-" y "_" sobreviven al sanitizar un segmento de
# ruta: evita que un nombre de carpeta o archivo con datos inesperados ("..", "/", etc.)
# termine inyectando segmentos de ruta dentro del bucket.
_SEGMENTO_INVALIDO = re.compile(r"[^a-z0-9_-]+")


def _sanitizar_segmento(valor: str) -> str:
    limpio = valor.strip().lower().replace(" ", "-")
    limpio = _SEGMENTO_INVALIDO.sub("-", limpio).strip("-")
    return limpio or "archivo"


def construir_llave_archivo(
    carpeta: str, nombre_base: str, extension: str, fecha: datetime | None = None
) -> str:
    """Genera la key `<carpeta>/<anio>/<mes>/<nombre_base>-<sufijo>.<extension>` del bucket."""
    fecha = fecha or datetime.now(UTC)
    carpeta_limpia = _sanitizar_segmento(carpeta)
    nombre_limpio = _sanitizar_segmento(nombre_base)
    extension_limpia = _sanitizar_segmento(extension) or "bin"
    sufijo_unico = uuid.uuid4().hex[:12]
    return f"{carpeta_limpia}/{fecha:%Y}/{fecha:%m}/{nombre_limpio}-{sufijo_unico}.{extension_limpia}"


class CloudStorageError(Exception):
    """Error al subir un archivo al almacenamiento en la nube (R2)."""


class CloudStorageService:
    """Sube archivos (imágenes, documentos, etc.) a Cloudflare R2.

    Cada archivo se guarda bajo una key predecible
    `<carpeta>/<anio>/<mes>/<nombre_base>-<sufijo>.<extension>`, lo que permite
    ubicarlo por dominio y fecha. Si se configura `R2_PUBLIC_BASE_URL` (un
    dominio público / CDN apuntando al bucket), se devuelve la URL pública
    lista para servir; si no, se devuelve la key cruda para resolverla luego.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_base_url: str | None = None,
    ) -> None:
        if not all([account_id, access_key_id, secret_access_key, bucket_name]):
            raise ValueError("Credenciales de almacenamiento en la nube (R2) incompletas.")

        self._bucket_name = bucket_name
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self._client = boto3.client(
            service_name="s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}
            ),
        )

    def guardar_archivo(
        self, contenido: bytes, carpeta: str, nombre_base: str, extension: str, content_type: str
    ) -> str:
        """Sube `contenido` al bucket y devuelve la URL (pública o key) para persistir en BD.

        Lanza `CloudStorageError` si la subida falla; el llamador decide si eso
        debe o no impedir el resto del flujo.
        """
        file_key = construir_llave_archivo(carpeta, nombre_base, extension)

        try:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=file_key,
                Body=contenido,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise CloudStorageError(
                f"No fue posible subir el archivo a almacenamiento en la nube: {exc}"
            ) from exc

        return self._construir_url_publica(file_key)

    def obtener_url_descarga(self, valor_almacenado: str, expiracion_segundos: int | None = None) -> str:
        """Resuelve un valor guardado en BD (key cruda o URL pública) a una URL accesible.

        Si `valor_almacenado` ya es una URL completa (se guardó así porque había
        un dominio público configurado al subir el archivo), se devuelve tal
        cual. Si es una key cruda del bucket (bucket privado, sin dominio
        público), se genera una URL prefirmada (presigned) temporal para poder
        acceder al objeto desde el navegador.
        """
        if valor_almacenado.startswith(("http://", "https://")):
            return valor_almacenado

        if self._public_base_url:
            return f"{self._public_base_url}/{valor_almacenado}"

        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket_name, "Key": valor_almacenado},
                ExpiresIn=expiracion_segundos or _URL_PRESIGNADA_EXPIRACION_SEGUNDOS_DEFAULT,
            )
        except (BotoCoreError, ClientError) as exc:
            raise CloudStorageError(
                f"No fue posible generar la URL de acceso al archivo '{valor_almacenado}': {exc}"
            ) from exc

    def _construir_url_publica(self, file_key: str) -> str:
        if self._public_base_url:
            return f"{self._public_base_url}/{file_key}"
        return file_key


@lru_cache
def get_storage_service() -> CloudStorageService:
    """Dependencia de FastAPI: instancia (cacheada) del servicio de almacenamiento R2."""
    return CloudStorageService(
        account_id=settings.R2_ACCOUNT_ID,
        access_key_id=settings.R2_ACCESS_KEY_ID,
        secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        bucket_name=settings.R2_BUCKET_NAME,
        public_base_url=settings.R2_PUBLIC_BASE_URL,
    )
