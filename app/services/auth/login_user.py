import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from typing import Dict

from dotenv import load_dotenv

from app.db.base import get_db

# Cargar variables de entorno
load_dotenv()

# CONFIGURACIÓN
# Asegúrate de que los nombres coincidan con tu .env
SECRET_KEY = os.getenv("SECRET_KEY_LOGIN") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Creamos un JWT para el acceso seguro, con la información del usuario y una expiración
def crear_token_acceso(data: dict):
    para_encriptar = data.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    para_encriptar.update({"exp": expiracion})
    token_jwt = jwt.encode(para_encriptar, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt

# Autenticar al usuario y generar un token JWT si las credenciales son correctas
async def autenticar_y_generar_token(email, password, db):
    # 1. Buscar usuario en la tabla base
    query_user = "SELECT id, email, hashed_password FROM usuarios WHERE email = ? AND activo = 1"
    result = await db.execute(query_user, [email])
    usuario = result.rows[0] if result.rows else None

    # Revisamos si el correo existe y si la contraseña es correcta
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El email no se encuentra registrado."
        )

    # Verifica la contraseña usando Passlib, teniendo en cuenta el truncamiento a 72 caracteres
    if not pwd_context.verify(password, usuario[2]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Contraseña o email incorrecta."
        )
    # Obtener Rol y Nombre (Información para el Payload)
    # Hacemos un JOIN para saber si es Voluntario o Fundación en una sola consulta
    query_info = """
        SELECT r.id as rol_id, 
               COALESCE(pv.nombre, pf.nombre_legal) as nombre_display
        FROM usuario_roles ur
        JOIN roles r ON ur.rol_id = r.id
        LEFT JOIN perfiles_voluntarios pv ON ur.usuario_id = pv.usuario_id
        LEFT JOIN perfiles_fundaciones pf ON ur.usuario_id = pf.usuario_id
        WHERE ur.usuario_id = ?
    """
    info_result = await db.execute(query_info, [usuario[0]]) # usuario[0] es el id (UUID)
    info = info_result.rows[0] if info_result.rows else (None, "Usuario")

    # Crear el Payload del Token
    token_data = {
        "sub": usuario[0],       # UUID del usuario
        "email": usuario[1],     # Email
        "role": info[0],         # ID del Rol (1, 2 o 3)
        "name": info[1]          # Nombre para mostrar en el Front
    }

    token = crear_token_acceso(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": info[1],
            "role": info[0]
        }
    }

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodificamos el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extraemos la info que guardamos en el Login (sub y role)
        user_id: str = payload.get("sub")
        user_role: int = payload.get("role")
        
        if user_id is None:
            raise credentials_exception
            
        return {"id": user_id, "role": user_role}
        
    except JWTError:
        raise credentials_exception