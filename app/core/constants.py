"""Constantes de negocio compartidas por toda la aplicación.

Único punto de verdad para valores que antes estaban duplicados
(por ejemplo, los IDs de rol se repetían en app/api/deps.py y en
app/services/auth/register_user.py).
"""

# Roles de negocio (coinciden con las filas sembradas en la tabla `roles`)
ROL_VOLUNTARIO = 1
ROL_FUNDACION = 2

# Política de contraseñas
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72  # límite real de bcrypt

# Imágenes de proyectos (foto principal y foto de encabezado) subidas a Cloudflare R2.
# Mapea content-type permitido -> extensión de archivo a usar en la key del bucket.
IMAGENES_PROYECTO_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
IMAGEN_PROYECTO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB por imagen
