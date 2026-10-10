"""Lógica de negocio para el inicio de sesión."""

from fastapi import HTTPException, status

from app.core.security import create_access_token, verify_password


async def autenticar_y_generar_token(email: str, password: str, db):
    """Valida credenciales contra la base de datos y genera el JWT de acceso."""
    # 1. Buscar usuario en la tabla base
    query_user = "SELECT id, email, hashed_password FROM usuarios WHERE email = ? AND activo = 1"
    result = await db.execute(query_user, [email])
    usuario = result.rows[0] if result.rows else None

    # Revisamos si el correo existe y si la contraseña es correcta
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email no se encuentra registrado.",
        )

    if not verify_password(password, usuario[2]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña o email incorrecta.",
        )

    # Obtener Rol y Nombre (Información para el Payload).
    # Hacemos un JOIN para saber si es Voluntario o Fundación en una sola consulta.
    query_info = """
        SELECT r.id as rol_id,
               COALESCE(pv.nombre, pf.nombre_legal) as nombre_display
        FROM usuario_roles ur
        JOIN roles r ON ur.rol_id = r.id
        LEFT JOIN perfiles_voluntarios pv ON ur.usuario_id = pv.usuario_id
        LEFT JOIN perfiles_fundaciones pf ON ur.usuario_id = pf.usuario_id
        WHERE ur.usuario_id = ?
    """
    info_result = await db.execute(query_info, [usuario[0]])  # usuario[0] es el id (UUID)
    info = info_result.rows[0] if info_result.rows else (None, "Usuario")

    token_data = {
        "sub": usuario[0],  # UUID del usuario
        "email": usuario[1],
        "role": info[0],
        "name": info[1],
    }
    token = create_access_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": info[1],
            "role": info[0],
        },
    }
