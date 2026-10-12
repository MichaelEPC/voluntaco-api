"""Esquemas Pydantic para las metas (necesidades) de un proyecto."""


from pydantic import BaseModel, Field


class MetaCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = None  # Detalle de la necesidad o problemática social
