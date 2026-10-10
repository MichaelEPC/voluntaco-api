"""Esquemas Pydantic para autenticación y registro de usuarios."""

from pydantic import BaseModel, EmailStr


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
    rol_id: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
