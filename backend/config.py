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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()