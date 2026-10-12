# Voluntaco API

API de FastAPI para la plataforma Voluntaco, que conecta fundaciones con
voluntarios. Usa [Turso](https://turso.tech/) (libsql) como base de datos,
accedida vía SQL crudo (sin ORM).

## Arquitectura

```
app/
├── api/
│   ├── deps.py            # Dependencias comunes: auth JWT, control de roles
│   └── v1/
│       ├── router.py       # Agregador de todos los endpoints de la v1
│       └── endpoints/      # Un módulo por dominio (auth, fundaciones, catalogos)
├── core/
│   ├── config.py           # Settings (variables de entorno, vía pydantic-settings)
│   ├── constants.py         # Constantes de negocio compartidas (roles, política de passwords)
│   ├── logging_config.py    # Configuración centralizada de logging
│   ├── security.py          # Hashing de contraseñas y JWT (único punto de verdad)
│   └── validators.py        # Validaciones reutilizables de payloads
├── db/
│   └── session.py           # Cliente Turso/libsql inyectado vía Depends(get_db)
├── schemas/                 # Modelos Pydantic de entrada/salida, por dominio
└── services/                # Lógica de negocio y acceso a datos, por dominio
```

Cadena de propiedad de datos: `fundación -> proyecto -> meta -> voluntariado`.
Como las tablas no siempre tienen una referencia directa a la fundación, la
pertenencia se valida mediante JOIN a través de la jerarquía completa.

## Requisitos

- Python 3.12+
- Una base de datos Turso (o compatible con libsql)

## Configuración local

1. Copia `.env.example` a `.env` y completa los valores reales:
   ```bash
   cp .env.example .env
   ```
2. Instala las dependencias (usa `requirements-dev.txt` para incluir
   herramientas de desarrollo como `pytest` y `ruff`):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Levanta el servidor en modo desarrollo:
   ```bash
   python main.py
   # o, equivalentemente:
   uvicorn app.main:app --reload
   ```
4. Documentación interactiva: `http://localhost:8000/api/v1/docs`.

## Tests

Los tests no golpean la base de datos real: el cliente Turso se sustituye
por un doble de prueba (`FakeDBClient`) vía `app.dependency_overrides`
(ver `tests/conftest.py`).

```bash
pytest tests/ -v
```

## Lint

```bash
ruff check app/ tests/ main.py
```

## CI

Cada push/PR corre lint (`ruff`) y la suite de tests vía GitHub Actions
(`.github/workflows/ci.yml`).

## Seguridad

- Las contraseñas se almacenan con `bcrypt` (vía `passlib`); nunca en texto plano.
- Las contraseñas de **registro** exigen mínimo 8 caracteres
  (`app/core/constants.py::PASSWORD_MIN_LENGTH`).
- Los tokens de acceso son JWT (HS256) con expiración configurable
  (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Todas las consultas SQL usan parámetros (`?`), nunca interpolación de
  strings con datos del usuario.
- `ALLOWED_ORIGINS` debe restringirse a los dominios reales del frontend en
  producción (evita `"*"` junto con `allow_credentials=True`).
- Nunca commitees el archivo `.env` (ya está en `.gitignore`); usa
  `.env.example` como plantilla.
