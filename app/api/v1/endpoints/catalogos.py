"""Endpoints de catálogos de apoyo (roles, modalidades, habilidades)."""

from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.services.catalogos import catalogos

router = APIRouter(prefix="/util", tags=["Utilidades"])


@router.get("/roles-voluntarios")
async def listar_roles(db=Depends(get_db)):
    return await catalogos.obtener_catalogo_roles_voluntarios(db)


@router.get("/modalidades-voluntariados")
async def listar_modalidades(db=Depends(get_db)):
    return await catalogos.obtener_catalogo_modalidades_voluntariados(db)


@router.get("/habilidades-voluntariados")
async def listar_habilidades(db=Depends(get_db)):
    return await catalogos.obtener_catalogo_habilidades_voluntariados(db)
