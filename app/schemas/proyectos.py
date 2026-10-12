"""Esquemas Pydantic para los proyectos publicados por una fundación."""


from pydantic import BaseModel, Field


class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = None
    foto_url: str | None = None  # URL de la foto del proyecto (Cloudflare u otro bucket)
