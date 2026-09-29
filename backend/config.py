from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "cloudrag-api"
    environment: str = "development"
    database_url: str = "postgresql://cloudrag:cloudrag-dev-password@localhost:5432/cloudrag"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()