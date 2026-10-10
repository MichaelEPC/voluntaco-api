"""Utilidades de seguridad: hashing de contraseñas y JWT.

Punto único de verdad para toda la aplicación (antes duplicado entre
este módulo y app/services/auth/login_user.py).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt trunca a 72 bytes; dejamos que falle explícitamente si se excede
# en vez de truncar en silencio.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=True)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Crea un JWT a partir de `data`, agregando el claim de expiración."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY_LOGIN, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY_LOGIN, algorithms=[settings.ALGORITHM])
