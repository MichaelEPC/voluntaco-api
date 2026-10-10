"""Esquemas Pydantic para voluntariados y sus relaciones con fundaciones."""

from typing import List, Optional

from pydantic import BaseModel, Field


class RequestFundacion(BaseModel):
    fundacionId: str


class VoluntariadoCreate(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: str
    modalidad_id: int
    usuario_rol_id: int  # El cargo buscado (ej: Analista)
    habilidades_ids: List[int] = []  # IDs de las habilidades requeridas


class VoluntariadoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    modalidad_id: Optional[int] = None
    usuario_rol_id: Optional[int] = None
    habilidades_ids: Optional[List[int]] = None  # Si viene, reemplazamos las anteriores
