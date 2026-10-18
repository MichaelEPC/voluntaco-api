"""Endpoints de gestión de voluntariados publicados por fundaciones."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import require_fundacion
from app.db.session import get_db
from app.schemas.fundaciones import RequestFundacion, VoluntariadoCreate, VoluntariadoUpdate
from app.schemas.metas import MetaCreate
from app.schemas.proyectos import ProyectoCreate
from app.services.fundaciones import fundaciones as fundaciones_services
from app.services.metas import metas as metas_services
from app.services.proyectos import proyectos as proyectos_services
from app.services.storage.r2_storage import CloudStorageService, get_storage_service

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


@router.get("/proyectos")
async def get_proyectos_fundacion(
    db=Depends(get_db),
    storage: CloudStorageService = Depends(get_storage_service),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones ven sus propios proyectos
):
    return await proyectos_services.obtener_proyectos_por_fundacion(usuario["id"], db, storage)


@router.post("/proyectos/crear")
async def post_proyecto(
    datos: ProyectoCreate = Depends(ProyectoCreate.as_form),
    foto: UploadFile | None = File(None),  # Foto principal del proyecto
    foto_cabeza: UploadFile | None = File(None),  # Foto de encabezado del proyecto
    db=Depends(get_db),
    storage: CloudStorageService = Depends(get_storage_service),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones pueden crear proyectos
):
    return await proyectos_services.crear_nuevo_proyecto(
        usuario["id"], datos, foto, foto_cabeza, db, storage
    )


@router.post("/proyectos/{proyecto_id}")
async def post_proyecto_individual(
    proyecto_id: str,
    db=Depends(get_db),
    storage: CloudStorageService = Depends(get_storage_service),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones pueden crear metas
):
    return await proyectos_services.obtener_proyecto_invididual_fundacion(
        usuario["id"], proyecto_id, db, storage
    )


@router.post("/proyectos/{proyecto_id}/metas/crear")
async def post_meta(
    proyecto_id: str,
    datos: MetaCreate,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones pueden crear metas
):
    return await metas_services.crear_nueva_meta(proyecto_id, usuario["id"], datos, db)


@router.get("/proyectos/{proyecto_id}/metas")
async def get_metas_proyecto(
    proyecto_id: str,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones consultan metas de sus proyectos
):
    return await metas_services.obtener_metas_por_proyecto(proyecto_id, usuario["id"], db)


@router.post("/voluntariados/crear")
async def post_voluntariado(
    datos: VoluntariadoCreate,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),  # Solo fundaciones pueden publicar voluntariados
):
    return await fundaciones_services.crear_nuevo_voluntariado(usuario["id"], datos, db)


@router.get("/voluntariados/{voluntariado_id}")
async def get_voluntariado_individual(
    voluntariado_id: str,
    db=Depends(get_db),
    storage: CloudStorageService = Depends(get_storage_service),
):
    return await fundaciones_services.obtener_voluntariado_por_id(voluntariado_id, db, storage)


@router.delete("/voluntariados/eliminar/{voluntariado_id}")
async def eliminar_voluntariado(
    voluntariado_id: str,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),  # SEGURIDAD: Solo fundaciones
):
    return await fundaciones_services.eliminar_voluntariado(voluntariado_id, usuario["id"], db)


@router.patch("/voluntariados/actualizar/{voluntariado_id}")
async def actualizar_voluntariado(
    voluntariado_id: str,
    datos: VoluntariadoUpdate,
    db=Depends(get_db),
    usuario: dict = Depends(require_fundacion),
):
    return await fundaciones_services.modificar_voluntariado(voluntariado_id, usuario["id"], datos, db)


@router.get("/voluntariados/metas/{meta_id}")
async def get_voluntariados_por_meta(
    meta_id: str,
    db=Depends(get_db),
):
    return await fundaciones_services.obtener_voluntariados_por_metas(meta_id, db)