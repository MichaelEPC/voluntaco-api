"""Endpoints de gestión de voluntariados publicados por fundaciones."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_fundacion
from app.db.session import get_db
from app.schemas.fundaciones import RequestFundacion, VoluntariadoCreate, VoluntariadoUpdate
from app.services.fundaciones import fundaciones as fundaciones_services

router = APIRouter(prefix="/fundaciones", tags=["Fundaciones"])


@router.post("/obtener-voluntariados-por-fundacion")
async def listar_voluntariados_fundacion(
    data: RequestFundacion,
    db=Depends(get_db),
    # current_user = Depends(get_current_user)  # Opcional: Para validar que el token sea válido
):
    # Usamos data.fundacionId que viene del body del fetch
    voluntariados_lista = await fundaciones_services.obtener_voluntariados_por_fundacion(
        data.fundacionId, db
    )

    if not voluntariados_lista:
        return []  # Devolvemos lista vacía si no hay nada

    return voluntariados_lista


@router.post("/voluntariados/crear")
async def post_voluntariado(
    datos: VoluntariadoCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),  # Esto decodifica el JWT
):
    fundacion_id = current_user["id"]
    return await fundaciones_services.crear_nuevo_voluntariado(fundacion_id, datos, db)


@router.delete("/voluntariados/{voluntariado_id}")
async def eliminar_voluntariado(
    voluntariado_id: int,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),  # SEGURIDAD: Solo fundaciones
):
    return await fundaciones_services.eliminar_voluntariado(voluntariado_id, usuario["id"], db)


@router.patch("/voluntariados/{voluntariado_id}")
async def actualizar_voluntariado(
    voluntariado_id: int,
    datos: VoluntariadoUpdate,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),
):
    return await fundaciones_services.modificar_voluntariado(voluntariado_id, usuario["id"], datos, db)
