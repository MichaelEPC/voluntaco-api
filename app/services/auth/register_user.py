"""Lógica de negocio para el registro de voluntarios y fundaciones."""

import logging
import uuid

from fastapi import HTTPException, status

from app.core.constants import ROL_FUNDACION, ROL_VOLUNTARIO
from app.core.security import hash_password

logger = logging.getLogger(__name__)


async def registrar_usuario_voluntario(usuario, db):
    """Registra un nuevo voluntario: cuenta base, rol y perfil."""
    # 1. Verificar si el email ya existe en la tabla base
    check_email = await db.execute("SELECT id FROM usuarios WHERE email = ?", [usuario.email])
    if check_email.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya se encuentra registrado.",
        )

    # 2. Verificar si la cédula ya existe en el perfil de voluntarios
    check_cedula = await db.execute(
        "SELECT usuario_id FROM perfiles_voluntarios WHERE cedula = ?",
        [usuario.documento_identidad],
    )
    if check_cedula.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cédula ya se encuentra registrada.",
        )

    # 3. Cifrar la contraseña
    hashed_password = hash_password(usuario.password)
    nuevo_id_usuario = str(uuid.uuid4())

    try:
        # Operación Atómica con Batch
        await db.batch(
            [
                # A. Crear cuenta base
                (
                    "INSERT INTO usuarios (id, email, hashed_password, activo) VALUES (?, ?, ?, 1)",
                    [nuevo_id_usuario, usuario.email, hashed_password],
                ),
                # B. Asignar Rol en tabla intermedia
                (
                    "INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (?, ?)",
                    [nuevo_id_usuario, ROL_VOLUNTARIO],
                ),
                # C. Crear Perfil con nombre y cédula
                (
                    "INSERT INTO perfiles_voluntarios (usuario_id, nombre, cedula) VALUES (?, ?, ?)",
                    [nuevo_id_usuario, usuario.nombre_completo[:100], usuario.documento_identidad[:10]],
                ),
            ]
        )

        return {
            "status": "success",
            "message": f"Bienvenido {usuario.nombre_completo[:100]}, tu cuenta ha sido creada correctamente.",
            "usuario_id": nuevo_id_usuario,
        }

    except Exception:
        logger.exception("Error en registro de voluntario")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error crítico al procesar el registro en la base de datos.",
        ) from None


async def registrar_usuario_fundacion(usuario, db):
    """Registra una nueva fundación: cuenta base, rol y perfil."""
    # 1. Verificar si el email ya existe
    check_email = await db.execute("SELECT id FROM usuarios WHERE email = ?", [usuario.email])
    if check_email.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya se encuentra registrado.",
        )

    # 2. Verificar si el NIT ya existe
    check_nit = await db.execute(
        "SELECT usuario_id FROM perfiles_fundaciones WHERE nit = ?", [usuario.nit]
    )
    if check_nit.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El NIT ya se encuentra registrado por otra fundación.",
        )

    # 3. Cifrar la contraseña
    hashed_password = hash_password(usuario.password)
    nuevo_id_usuario = str(uuid.uuid4())

    try:
        # Operación Atómica
        await db.batch(
            [
                # A. Cuenta de usuario
                (
                    "INSERT INTO usuarios (id, email, hashed_password, activo) VALUES (?, ?, ?, 1)",
                    [nuevo_id_usuario, usuario.email, hashed_password],
                ),
                # B. Asignar Rol de Fundación
                (
                    "INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (?, ?)",
                    [nuevo_id_usuario, ROL_FUNDACION],
                ),
                # C. Perfil de Fundación
                (
                    "INSERT INTO perfiles_fundaciones (usuario_id, nombre_legal, nit) VALUES (?, ?, ?)",
                    [nuevo_id_usuario, usuario.nombre_legal[:100], usuario.nit[:10]],
                ),
            ]
        )

        return {
            "status": "success",
            "message": f"Fundación '{usuario.nombre_legal[:100]}' registrada con éxito.",
            "usuario_id": nuevo_id_usuario,
        }

    except Exception:
        logger.exception("Error en registro de fundación")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo completar el registro de la fundación.",
        ) from None
