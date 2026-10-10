"""Endpoints de autenticación: inicio de sesión y registro de usuarios."""

from fastapi import APIRouter, Depends, status

from app.core.validators import validate_length_range
from app.db.session import get_db
from app.schemas.auth import RegistroFundacion, RegistroVoluntario, UserLogin
from app.services.auth import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Inicio de Sesión"])

MSG_EMAIL = "El correo electrónico debe tener entre 1 y 72 caracteres."
MSG_PASSWORD = "La contraseña debe tener entre 1 y 72 caracteres."


@router.post("/iniciar-sesion", status_code=status.HTTP_200_OK)
async def iniciar_sesion(usuario: UserLogin, db=Depends(get_db)):
    validate_length_range(usuario.email, 0, 72, MSG_EMAIL)
    validate_length_range(usuario.password, 0, 72, MSG_PASSWORD)

    return await login_user.autenticar_y_generar_token(usuario.email, usuario.password, db)


@router.post("/registro-voluntario", status_code=status.HTTP_200_OK)
async def registrar_voluntario(usuario: RegistroVoluntario, db=Depends(get_db)):
    validate_length_range(usuario.email, 0, 72, MSG_EMAIL)
    validate_length_range(usuario.password, 0, 72, MSG_PASSWORD)
    validate_length_range(
        usuario.documento_identidad, 0, 10,
        "El documento de identidad debe tener entre 1 y 10 caracteres.",
    )
    validate_length_range(
        usuario.nombre_completo, 0, 100,
        "El nombre completo debe tener entre 1 y 100 caracteres.",
    )
    validate_length_range(
        usuario.telefono, 0, 10,
        "El teléfono debe tener entre 1 y 10 caracteres.",
    )

    return await register_user.registrar_usuario_voluntario(usuario, db)


@router.post("/registro-fundacion", status_code=status.HTTP_200_OK)
async def registrar_fundacion(usuario: RegistroFundacion, db=Depends(get_db)):
    validate_length_range(usuario.email, 0, 72, MSG_EMAIL)
    validate_length_range(usuario.password, 0, 72, MSG_PASSWORD)
    validate_length_range(
        usuario.nit, 0, 10,
        "El NIT debe tener entre 1 y 10 caracteres.",
    )
    validate_length_range(
        usuario.nombre_legal, 5, 100,
        "El nombre de la fundación debe tener entre 5 y 100 caracteres.",
    )

    return await register_user.registrar_usuario_fundacion(usuario, db)
