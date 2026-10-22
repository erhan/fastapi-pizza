from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pizza API 🍕"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./pizza.db"
    api_key: str = "demo-chef-key"  # demo only: set your own in .env
    create_tables_on_startup: bool = True
    seed_on_startup: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
