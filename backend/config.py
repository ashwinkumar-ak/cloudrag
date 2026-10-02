from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "cloudrag-api"

    environment: str = "development"

    database_url: str = (
        "postgresql://cloudrag:cloudrag-dev-password"
        "@localhost:5432/cloudrag"
    )

    retrieval_distance_threshold: float = 0.20

    jwt_secret_key: str = (
        "cloudrag-development-secret-change-this"
    )

    jwt_algorithm: str = "HS256"

    jwt_access_token_expire_minutes: int = 1440

    frontend_url: str = "http://localhost:5173"

    max_upload_size_bytes: int = 20 * 1024 * 1024

    security_headers_enabled: bool = True

    storage_backend: str = "local"
    local_storage_path: str = "./storage"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "documents"


    gemini_api_key: str | None = None

    gemini_model: str = "gemini-3.5-flash-lite"

    gemini_embedding_model: str = "gemini-embedding-2"

    gemini_api_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()