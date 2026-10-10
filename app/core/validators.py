"""Validadores reutilizables para los payloads de entrada de la API.

Centraliza las comprobaciones de longitud que antes estaban duplicadas en
cada endpoint, preservando el mismo comportamiento (HTTP 401 + mensaje).
"""

from fastapi import HTTPException, status


def validate_length_range(value: str, min_len: int, max_len: int, error_message: str) -> None:
    """Valida que `len(value)` esté en el rango (min_len, max_len].

    Lanza HTTPException 401 con `error_message` si la longitud es inválida,
    replicando la validación histórica de los endpoints de autenticación.
    """
    if len(value) > max_len or len(value) <= min_len:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message,
        )
