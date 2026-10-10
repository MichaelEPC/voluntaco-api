"""Router agregador de la versión 1 de la API."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.catalogos import router as catalogos_router
from app.api.v1.endpoints.fundaciones import router as fundaciones_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(fundaciones_router, tags=["fundaciones"])
router.include_router(catalogos_router, tags=["utilidades"])
