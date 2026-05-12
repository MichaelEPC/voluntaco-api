import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status

from pydantic import BaseModel, EmailStr
from pathlib import Path

from app.db.base import get_db

import app.services.auth.register_user as register_user
import app.services.auth.login_user as login_user

router = APIRouter(prefix="/auth", tags=["Inicio de Sesión"])

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RegistroVoluntario(BaseModel):
    documento_identidad: str
    nombre_completo: str
    email: EmailStr
    password: str
    telefono: str
    rol_id: int

class RegistroFundacion(BaseModel):
    nit: str
    nombre_legal: str
    email: EmailStr
    password: str
    # telefono: str
    rol_id: int

@router.post("/iniciar-sesion", status_code=status.HTTP_200_OK)
async def iniciar_sesion(usuario: UserLogin, db = Depends(get_db)):
    # Verificar que el email y la contraseña no excedan los 72 caracteres
    if not len(usuario.email) <= 72 or not len(usuario.email) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El correo electrónico debe tener entre 1 y 72 caracteres."
        )
    # Verificar que la contraseña no exceda los 72 caracteres
    if not len(usuario.password) <= 72 or not len(usuario.password) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="La contraseña debe tener entre 1 y 72 caracteres."
        )
        
    inicio_sesion_response = await login_user.autenticar_y_generar_token(usuario.email, usuario.password, db)
    if not inicio_sesion_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return inicio_sesion_response

@router.post("/registro-voluntario", status_code=status.HTTP_200_OK)
async def registrar_voluntario(usuario: RegistroVoluntario, db = Depends(get_db)):
    # Verificar que el email y la contraseña no excedan los 72 caracteres
    if not len(usuario.email) <= 72 or not len(usuario.email) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El correo electrónico debe tener entre 1 y 72 caracteres."
        )
    # Verificar que la contraseña no exceda los 72 caracteres
    if not len(usuario.password) <= 72 or not len(usuario.password) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="La contraseña debe tener entre 1 y 72 caracteres."
        )

    # Verificar que el documento de identidad, nombre completo y teléfono tengan una longitud razonable
    if not len(usuario.documento_identidad) <= 10 or not len(usuario.documento_identidad) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El documento de identidad debe tener entre 1 y 10 caracteres."
        )
    
    # El nombre completo no debe ser demasiado largo ni vacío
    if not len(usuario.nombre_completo) <= 100 or not len(usuario.nombre_completo) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El nombre completo debe tener entre 1 y 100 caracteres."
        )

    # El teléfono no debe ser demasiado largo ni vacío
    if not len(usuario.telefono) <= 10 or not len(usuario.telefono) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El teléfono debe tener entre 1 y 10 caracteres."
        )
    
    respuesta_registro_voluntario = await register_user.registrar_usuario_voluntario(usuario, db)

    # Respuesta para el frontend (Next.js)
    return respuesta_registro_voluntario

@router.post("/registro-fundacion", status_code=status.HTTP_200_OK)
async def registrar_fundacion(usuario: RegistroFundacion, db = Depends(get_db)):
    # Verificar que el email y la contraseña no excedan los 72 caracteres
    if not len(usuario.email) <= 72 or not len(usuario.email) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El correo electrónico debe tener entre 1 y 72 caracteres."
        )
    # Verificar que la contraseña no exceda los 72 caracteres
    if not len(usuario.password) <= 72 or not len(usuario.password) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="La contraseña debe tener entre 1 y 72 caracteres."
        )

    # Verificar que el NIT tenga una longitud razonable
    if not len(usuario.nit) <= 10 or not len(usuario.nit) > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El NIT debe tener entre 1 y 10 caracteres."
        )
    
    # El nombre legal no debe ser demasiado largo ni vacío
    if not len(usuario.nombre_legal) <= 100 or not len(usuario.nombre_legal) > 5:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El nombre de la fundación debe tener entre 5 y 100 caracteres."
        )

    # # El teléfono no debe ser demasiado largo ni vacío
    # if not len(usuario.telefono) <= 10 or not len(usuario.telefono) > 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED, 
    #         detail="El teléfono debe tener entre 1 y 10 caracteres."
    #     )
    
    respuesta_registro_fundacion = await register_user.registrar_usuario_fundacion(usuario, db)

    # Respuesta para el frontend (Next.js)
    return respuesta_registro_fundacion