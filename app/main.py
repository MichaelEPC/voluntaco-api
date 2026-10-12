from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Versiones de API
from app.api.v1.router import router as v1_router

# Configuración de la aplicación
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging()

# En producción (DEBUG=false) ocultamos el esquema de la API para no
# exponer públicamente todos los endpoints, modelos y rutas internas.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }
