"""Catálogos de apoyo para voluntariados: roles, modalidades, tipos y habilidades."""


async def obtener_catalogo_roles_voluntarios(db):
    query = "SELECT id, nombre FROM voluntarios_roles ORDER BY nombre ASC"
    result = await db.execute(query)
    return [{"id": row[0], "nombre": row[1]} for row in result.rows]


async def obtener_catalogo_modalidades_voluntariados(db):
    query = "SELECT id, nombre FROM modalidades"
    result = await db.execute(query)
    return [{"id": row[0], "nombre": row[1]} for row in result.rows]


async def obtener_catalogo_tipos_voluntariado(db):
    query = "SELECT id, nombre FROM tipos_voluntariado ORDER BY nombre ASC"
    result = await db.execute(query)
    return [{"id": row[0], "nombre": row[1]} for row in result.rows]


async def obtener_catalogo_habilidades_voluntariados(db):
    query = "SELECT id, nombre FROM habilidades"
    result = await db.execute(query)
    return [{"id": row[0], "nombre": row[1]} for row in result.rows]
