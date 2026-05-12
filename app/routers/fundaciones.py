import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status

from pydantic import BaseModel, EmailStr, Field
from pathlib import Path
from typing import List, Optional

from app.db.base import get_db
from app.services.auth.login_user import get_current_user

import app.services.fundaciones.fundaciones as fundaciones_services

router = APIRouter(prefix="/fundaciones", tags=["Fundaciones"])

class RequestFundacion(BaseModel):
    fundacionId: str

class VoluntariadoCreate(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: str
    modalidad_id: int
    usuario_rol_id: int # El cargo buscado (ej: Analista)
    habilidades_ids: List[int] = [] # IDs de las habilidades requeridas

class VoluntariadoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    modalidad_id: Optional[int] = None
    usuario_rol_id: Optional[int] = None
    habilidades_ids: Optional[List[int]] = None # Si viene, reemplazamos las anteriores

@router.post("/obtener-voluntariados-por-fundacion")
async def listar_voluntariados_fundacion(
    data: RequestFundacion, 
    db = Depends(get_db),
    # current_user = Depends(get_current_user) # Opcional: Para validar que el token sea válido
):
    # Usamos data.fundacionId que viene del body del fetch
    voluntariados_lista = await fundaciones_services.obtener_voluntariados_por_fundacion(data.fundacionId, db)
    
    if not voluntariados_lista:
        return [] # Devolvemos lista vacía si no hay nada
        
    return voluntariados_lista

@router.post("/voluntariados/crear")
async def post_voluntariado(
    datos: VoluntariadoCreate, 
    db = Depends(get_db),
    current_user = Depends(get_current_user) # Esto decodifica el JWT
):
    # 1. Sacamos el ID que viene DENTRO del token
    # Dependiendo de cómo lo guardaste en el payload, puede ser 'sub' o 'id'
    fundacion_id = current_user.get("id") or current_user.get("sub")

    # 2. Se lo pasamos a la función que inserta en la DB
    return await fundaciones_services.crear_nuevo_voluntariado(fundacion_id, datos, db)

@router.delete("/voluntariados/{voluntariado_id}")
async def eliminar_voluntariado(
    voluntariado_id: int,
    db = Depends(get_db),
    usuario: dict = Depends(get_current_user) # Ahora que ya tienes esta función
):
    # SEGURIDAD: Solo fundaciones
    if usuario["role"] != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo las fundaciones pueden eliminar sus publicaciones."
        )

    # Llamamos al servicio pasando el ID del usuario extraído del Token
    return await fundaciones_services.eliminar_voluntariado(voluntariado_id, usuario["id"], db)

@router.patch("/voluntariados/{voluntariado_id}")
async def actualizar_voluntariado(
    voluntariado_id: int,
    datos: VoluntariadoUpdate,
    db = Depends(get_db),
    usuario: dict = Depends(get_current_user)
):
    if usuario["role"] != 2:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    return await fundaciones_services.modificar_voluntariado(voluntariado_id, usuario["id"], datos, db)