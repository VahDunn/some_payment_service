from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbConfig(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str = "payments_db"
    user: str = "postgres"
    password: str = "postgres"
    echo: bool = False

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    db: DbConfig = Field(default_factory=DbConfig)


@lru_cache
def get_settings() -> AppConfig:
    return AppConfig()