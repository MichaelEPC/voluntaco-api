"""Dependencias compartidas por los endpoints de la API (auth, roles, DB)."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.config import settings
from app.core.constants import ROL_FUNDACION
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/iniciar-sesion")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Decodifica el JWT del header Authorization y devuelve sus claims."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_exception from None

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    return {"id": user_id, "role": payload.get("role"), "name": payload.get("name")}


def require_fundacion(usuario: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Dependencia que exige que el usuario autenticado sea una fundación."""
    if usuario["role"] != ROL_FUNDACION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo las fundaciones pueden realizar esta acción.",
        )
    return usuario
