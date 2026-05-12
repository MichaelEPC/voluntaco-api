from fastapi import APIRouter

# Iniciar session y registra usuario
from app.routers.auth_user import router as auth_router
from app.routers.fundaciones import router as fundaciones_router
from app.routers.utils import router as utils_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(fundaciones_router, tags=["fundaciones"])
router.include_router(utils_router, tags=["utilidades"])