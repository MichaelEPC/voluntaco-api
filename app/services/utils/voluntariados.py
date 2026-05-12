from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Depends
from fastapi.responses import FileResponse

from app.db.base import get_db

# Buscar perfiles de voluntarios
async def obtener_catalogo_roles_voluntarios(db):
    query = "SELECT id, nombre FROM voluntarios_roles ORDER BY nombre ASC"
    result = await db.execute(query)
    
    # Transformamos las filas en una lista de diccionarios
    roles = [{"id": row[0], "nombre": row[1]} for row in result.rows]
    return roles

async def obtener_catalogo_modalidades_voluntariados(db):
    query = "SELECT id, nombre FROM modalidades"
    result = await db.execute(query)
    
    # Transformamos las filas en una lista de diccionarios
    modalidades = [{"id": row[0], "nombre": row[1]} for row in result.rows]
    return modalidades

async def obtener_catalogo_habilidades_voluntariados(db):
    query = "SELECT id, nombre FROM habilidades"
    result = await db.execute(query)
    
    # Transformamos las filas en una lista de diccionarios
    habilidades = [{"id": row[0], "nombre": row[1]} for row in result.rows]
    return habilidades