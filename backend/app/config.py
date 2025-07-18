# backend/app/config.py

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Yandex Parser API"
    secret_key: str = "your-secret-key-here"
    debug: bool = True
    environment: str = "development"

    # Добавляем недостающие поля
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_v1_str: str = "/api/v1"

    # CORS и безопасность
    allowed_origins: List[str] = ["*"]
    allowed_hosts: Optional[List[str]] = None

    # Database - все значения берутся из .env, но есть fallback для разработки
    postgres_host: str = "localhost"  # Fallback для разработки
    postgres_port: int = 5432
    postgres_db: str = "yandex_parser"
    postgres_user: str = "parser_user"  # Fallback для разработки
    postgres_password: str = "parser_password"  # Fallback для разработки

    # Добавляем поддержку DATABASE_URL напрямую (опционально)
    database_url: Optional[str] = None

    # Redis - все значения берутся из .env, но есть fallback для разработки
    redis_host: str = "localhost"  # Fallback для разработки
    redis_port: int = 6379
    redis_db: int = 0

    # Добавляем поддержку REDIS_URL напрямую (опционально)
    redis_url: Optional[str] = None

    # Celery - формируются динамически из redis настроек
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Server Configuration
    warm_profiles_target: int = 1000
    max_cpu_percent: int = 75
    max_ram_percent: int = 70
    spawn_queue_threshold: int = 50

    # VNC Debug Settings
    vnc_enabled: bool = True
    vnc_max_sessions: int = 10
    vnc_base_display: int = 100
    vnc_session_timeout: int = 7200  # 2 часа
    vnc_cleanup_interval: int = 900  # 15 минут

    # Debug Browser Settings
    debug_browser_slow_mo: int = 500
    debug_browser_devtools: bool = True
    debug_browser_timeout: int = 30000

    @property
    def effective_database_url(self) -> str:
        """Формирует URL базы данных из переменных окружения"""
        if self.database_url:
            return self.database_url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def effective_redis_url(self) -> str:
        """Формирует URL Redis из переменных окружения"""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def effective_celery_broker_url(self) -> str:
        """Формирует URL Celery broker из переменных окружения"""
        if self.celery_broker_url:
            return self.celery_broker_url
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def effective_celery_result_backend(self) -> str:
        """Формирует URL Celery result backend из переменных окружения"""
        if self.celery_result_backend:
            return self.celery_result_backend
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        # Разрешаем дополнительные поля из .env
        extra = "ignore"  # Игнорируем дополнительные поля
        # Принудительно читаем из .env для критичных настроек
        case_sensitive = False


settings = Settings()
