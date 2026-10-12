"""Esquemas Pydantic para los proyectos publicados por una fundación."""


from datetime import UTC, datetime

from fastapi import Form, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ValidationError, field_validator


class ProyectoCreate(BaseModel):
    """Datos de texto del formulario de creación de proyecto.

    Las imágenes (`foto` y `foto_cabeza`) viajan como archivos independientes
    en el mismo `multipart/form-data` y se validan/suben por separado; no
    forman parte de este esquema porque Pydantic no las valida como `UploadFile`.
    """

    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = None
    # Fecha de creación enviada por el frontend (p. ej. para registrar proyectos
    # que iniciaron antes de cargarse en el sistema). Si no se envía, el backend
    # usa la fecha/hora actual del servidor.
    fecha_creacion: datetime | None = None

    @field_validator("fecha_creacion")
    @classmethod
    def _validar_fecha_creacion(cls, valor: datetime | None) -> datetime | None:
        """Normaliza a UTC y rechaza fechas futuras (una creación no puede ser a futuro)."""
        if valor is None:
            return None

        valor_utc = valor if valor.tzinfo else valor.replace(tzinfo=UTC)
        valor_utc = valor_utc.astimezone(UTC)
        if valor_utc > datetime.now(UTC):
            raise ValueError("La fecha de creación no puede ser una fecha futura.")
        return valor_utc

    @classmethod
    def as_form(
        cls,
        nombre: str = Form(..., min_length=1, max_length=150),
        descripcion: str | None = Form(None),
        fecha_creacion: datetime | None = Form(None),
    ) -> "ProyectoCreate":
        """Permite usar este esquema como dependencia de FastAPI sobre campos `Form`.

        Al validar manualmente con `cls(...)` (en vez de que FastAPI valide el
        `Body`), un `pydantic.ValidationError` no se traduce solo a un 422;
        hay que convertirlo explícitamente para preservar ese comportamiento.
        """
        try:
            return cls(nombre=nombre, descripcion=descripcion, fecha_creacion=fecha_creacion)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=jsonable_encoder(exc.errors()),
            ) from exc
