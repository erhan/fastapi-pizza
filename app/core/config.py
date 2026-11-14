import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pizza API 🍕"
    version: str = "0.2.0"
    api_v1_prefix: str = "/api/v1"
    # SQLite needs no setup. Point this at PostgreSQL for anything real (see the README).
    database_url: str = "sqlite+aiosqlite:///./pizza.db"
    create_tables_on_startup: bool = True
    seed_on_startup: bool = True

    # Secrets have no built-in value. Without one in the environment (or .env) a random one is
    # made for this process, so a deployment never runs on a key that is printed in a README.
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(24))  # the chef's key
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))  # signs the JWTs
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        """`postgres://…` and `postgresql://…` (what most hosts hand out) → the psycopg 3 driver."""
        for prefix in ("postgres://", "postgresql://"):
            if self.database_url.startswith(prefix):
                return "postgresql+psycopg://" + self.database_url.removeprefix(prefix)
        return self.database_url


settings = Settings()
