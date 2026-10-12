"""Esquemas Pydantic para voluntariados y sus relaciones con fundaciones."""


from pydantic import BaseModel, Field


class RequestFundacion(BaseModel):
    fundacionId: str


class VoluntariadoCreate(BaseModel):
    meta_id: int  # Meta (necesidad) del proyecto a la que pertenece
    tipo_id: int  # Tipo de voluntariado (Normal, Práctica Profesional, etc.)
    nombre: str = Field(..., max_length=100)
    descripcion: str
    modalidad_id: int
    usuario_rol_id: int  # El cargo buscado (ej: Analista)
    habilidades_ids: list[int] = []  # IDs de las habilidades requeridas


class VoluntariadoUpdate(BaseModel):
    meta_id: int | None = None
    tipo_id: int | None = None
    nombre: str | None = Field(None, max_length=100)
    descripcion: str | None = None
    modalidad_id: int | None = None
    usuario_rol_id: int | None = None
    habilidades_ids: list[int] | None = None  # Si viene, reemplazamos las anteriores
