
import os
import libsql_client
from dotenv import load_dotenv

load_dotenv() # Para leer las variables desde un archivo .env

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

async def get_db():
    # Creamos un cliente asíncrono
    client = libsql_client.create_client(
        url=TURSO_URL, 
        auth_token=TURSO_AUTH_TOKEN
    )
    try:
        yield client
    finally:
        await client.close()