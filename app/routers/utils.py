import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status

from pydantic import BaseModel, EmailStr
from pathlib import Path

from app.db.base import get_db

import app.services.utils.voluntariados as voluntariados

router = APIRouter(prefix="/util", tags=["Utilidades"])

@router.get("/roles-voluntarios")
async def listar_roles(db = Depends(get_db)):
    roles = await voluntariados.obtener_catalogo_roles_voluntarios(db)
    return roles

@router.get("/modalidades-voluntariados")
async def listar_modalidades(db = Depends(get_db)):
    modalidades = await voluntariados.obtener_catalogo_modalidades_voluntariados(db)
    return modalidades

@router.get("/habilidades-voluntariados")
async def listar_habilidades(db = Depends(get_db)):
    habilidades = await voluntariados.obtener_catalogo_habilidades_voluntariados(db)
    return habilidades