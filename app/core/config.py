from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App
    APP_NAME: str = "Voluntaco API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY_LOGIN: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 45

    # Database
    TURSO_DATABASE_URL: str
    TURSO_AUTH_TOKEN: str

    ALLOWED_ORIGINS: list[str] = ["*"]

    # Cloudflare R2 (almacenamiento de imágenes de proyectos y otros archivos)
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    # Dominio público (custom domain / CDN) servido por R2, si está configurado.
    # Si no se define, se persiste solo la key del objeto en el bucket.
    R2_PUBLIC_BASE_URL: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
