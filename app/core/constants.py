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
