from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Depends
from fastapi.responses import FileResponse

from pathlib import Path

from app.db.base import get_db

# Extraer Voluntariados de una Fundación específica
async def obtener_voluntariados_por_fundacion(id_fundacion: str, db):
    # Seleccionamos los datos relevantes y hacemos JOIN para traer el nombre de la modalidad y el rol
    query = """
        SELECT 
            v.id, 
            v.nombre, 
            v.descripcion, 
            v.estado, 
            v.fecha_creacion,
            m.nombre as modalidad,
            vr.nombre as rol_buscado
        FROM voluntariados v
        LEFT JOIN modalidades m ON v.modalidad_id = m.id
        LEFT JOIN voluntarios_roles vr ON v.usuario_rol_id = vr.id
        WHERE v.fundacion_id = ?
        ORDER BY v.fecha_creacion DESC
    """
    
    result = await db.execute(query, [id_fundacion])
    
    # Transformamos las filas en una lista de diccionarios con nombres de columna claros
    voluntariados = [
        {
            "id": row[0], 
            "nombre": row[1],
            "descripcion": row[2],
            "estado": row[3],
            "fecha_creacion": row[4],
            "modalidad": row[5],
            "rol_buscado": row[6]
        } 
        for row in result.rows
    ]
    
    return voluntariados

async def crear_nuevo_voluntariado(fundacion_id: str, datos, db):
    try:
        # 1. Insertar el voluntariado principal
        # Nota: Usamos una transacción para obtener el ID generado
        res = await db.execute(
            """
            INSERT INTO voluntariados (fundacion_id, nombre, descripcion, modalidad_id, usuario_rol_id, estado)
            VALUES (?, ?, ?, ?, ?, 'ABIERTO')
            """,
            [fundacion_id, datos.nombre, datos.descripcion, datos.modalidad_id, datos.usuario_rol_id]
        )
        
        # Obtenemos el ID del voluntariado recién creado
        nuevo_id = res.last_insert_rowid

        # 2. Si hay habilidades, las insertamos en la tabla intermedia
        if datos.habilidades_ids:
            # Preparamos las tuplas para el batch
            operaciones_habilidades = [
                (
                    "INSERT INTO voluntariado_habilidades (voluntariado_id, habilidad_id) VALUES (?, ?)",
                    [nuevo_id, h_id]
                )
                for h_id in datos.habilidades_ids
            ]
            
            await db.batch(operaciones_habilidades)

        return {
            "status": "success",
            "message": "Convocatoria publicada correctamente.",
            "voluntariado_id": nuevo_id
        }

    except Exception as e:
        print(f"Error al crear voluntariado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar la convocatoria."
        )

async def eliminar_voluntariado(voluntariado_id: int, fundacion_id: str, db):
    # 1. Verificar que el voluntariado existe y pertenece a la fundación
    query_check = "SELECT id FROM voluntariados WHERE id = ? AND fundacion_id = ?"
    result = await db.execute(query_check, [voluntariado_id, fundacion_id])
    
    if not result.rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voluntariado no encontrado o no tienes permisos para eliminarlo."
        )

    try:
        # 2. Eliminar en cascada manualmente (si no tienes ON DELETE CASCADE en SQL)
        # Primero las habilidades asociadas
        await db.execute(
            "DELETE FROM voluntariado_habilidades WHERE voluntariado_id = ?",
            [voluntariado_id]
        )
        
        # Luego el voluntariado
        await db.execute(
            "DELETE FROM voluntariados WHERE id = ?",
            [voluntariado_id]
        )
        
        return {"status": "success", "message": "Voluntariado eliminado correctamente."}

    except Exception as e:
        print(f"Error al eliminar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al intentar eliminar el registro."
        )

async def modificar_voluntariado(v_id: int, f_id: str, datos, db):
    # 1. Verificar propiedad y existencia
    check = await db.execute(
        "SELECT id FROM voluntariados WHERE id = ? AND fundacion_id = ?", 
        [v_id, f_id]
    )
    if not check.rows:
        raise HTTPException(status_code=404, detail="Voluntariado no encontrado")

    # 2. Construir la query dinámica para los campos básicos
    campos = datos.dict(exclude={'habilidades_ids'}, exclude_unset=True)
    if campos:
        set_query = ", ".join([f"{k} = ?" for k in campos.keys()])
        valores = list(campos.values()) + [v_id, f_id]
        await db.execute(
            f"UPDATE voluntariados SET {set_query} WHERE id = ? AND fundacion_id = ?",
            valores
        )

    # 3. Actualizar habilidades (si se enviaron en el body)
    if datos.habilidades_ids is not None:
        # Borramos las anteriores
        await db.execute("DELETE FROM voluntariado_habilidades WHERE voluntariado_id = ?", [v_id])
        
        # Insertamos las nuevas
        if datos.habilidades_ids:
            batch_habilidades = [
                ("INSERT INTO voluntariado_habilidades (voluntariado_id, habilidad_id) VALUES (?, ?)", [v_id, h_id])
                for h_id in datos.habilidades_ids
            ]
            await db.batch(batch_habilidades)

    return {"message": "Voluntariado actualizado correctamente"}