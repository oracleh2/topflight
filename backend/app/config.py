# backend/app/config.py

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Yandex Parser API"
    secret_key: str = "your-secret-key-here"
    debug: bool = True
    environment: str = "development"

    # CORS и безопасность
    allowed_origins: List[str] = ["*"]
    allowed_hosts: Optional[List[str]] = None

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "yandex_parser"
    postgres_user: str = "parser_user"
    postgres_password: str = "parser_password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Server Configuration
    warm_profiles_target: int = 1000
    max_cpu_percent: int = 75
    max_ram_percent: int = 70
    spawn_queue_threshold: int = 50

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"


settings = Settings()