# backend/app/__init__.py
"""
Backend application initialization module.

This module initializes the FastAPI application with all necessary
configurations, middleware, and route handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from . import models
from .config import settings
from .database import engine

# Импортируем все модели для регистрации в metadata
from .models import (
    User,
    TariffPlan,
    UserBalance,
    BalanceTransaction,
    Region,
    UserDomain,
    UserKeyword,
    UserDomainSettings,
    UserServerPreferences,
    Profile,
    ProfileFingerprint,
    ProfileLifecycle,
    ServerConfig,
    WorkerNode,
    Task,
    ParseResult,
    PositionHistory,
    SystemConfig,
    SystemLog,
    AuditTrail,
    ConfigChangesLog,
    FinancialTransactionsLog,
    PerformanceMetrics,
    BusinessMetrics,
    UserActivityStats,
    TaskAnalytics,
    ParsingAnalytics,
    BackupSchedule,
    BackupHistory,
    CacheSettings,
    YandexRegion,
)
from .models.base import Base

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# models = {
#     "User": User,
#     "TariffPlan": TariffPlan,
#     "UserBalance": UserBalance,
#     "BalanceTransaction": BalanceTransaction,
#     "Region": Region,
#     "UserDomain": UserDomain,
#     "UserKeyword": UserKeyword,
#     "UserDomainSettings": UserDomainSettings,
#     "UserServerPreferences": UserServerPreferences,
#     "Profile": Profile,
#     "ProfileFingerprint": ProfileFingerprint,
#     "ProfileLifecycle": ProfileLifecycle,
#     "ServerConfig": ServerConfig,
#     "WorkerNode": WorkerNode,
#     "Task": Task,
#     "ParseResult": ParseResult,
#     "PositionHistory": PositionHistory,
#     "SystemConfig": SystemConfig,
#     "SystemLog": SystemLog,
#     "AuditTrail": AuditTrail,
#     "ConfigChangesLog": ConfigChangesLog,
#     "FinancialTransactionsLog": FinancialTransactionsLog,
#     "PerformanceMetrics": PerformanceMetrics,
#     "BusinessMetrics": BusinessMetrics,
#     "UserActivityStats": UserActivityStats,
#     "TaskAnalytics": TaskAnalytics,
#     "ParsingAnalytics": ParsingAnalytics,
#     "BackupSchedule": BackupSchedule,
#     "BackupHistory": BackupHistory,
#     "CacheSettings": CacheSettings,
#     "Base": Base,
# }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    Выполняется при запуске и остановке приложения.
    """
    # Startup
    logger.info("Starting up application...")

    # Здесь можно добавить инициализацию базы данных, если необходимо
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Создает и настраивает экземпляр FastAPI приложения.

    Returns:
        FastAPI: Настроенное приложение
    """
    app = FastAPI(
        title=(
            settings.app_name if hasattr(settings, "app_name") else "Yandex Parser API"
        ),
        description="Backend API for Yandex SERP parser application",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware для проверки доверенных хостов
    allowed_hosts = getattr(settings, "allowed_hosts", None)
    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Регистрация маршрутов
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """
    Регистрирует все маршруты приложения.

    Args:
        app: Экземпляр FastAPI приложения
    """

    # Создаем базовый маршрут для проверки работоспособности
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "message": "Yandex Parser API is running",
            "version": "1.0.0",
        }

    @app.get("/")
    async def root():
        return {"message": "Yandex Parser API", "version": "1.0.0", "docs": "/docs"}

    # Импортируем и регистрируем роутеры если они существуют
    # try:
    #     from app.routers import auth, users, main
    #
    #     # Регистрируем основные маршруты
    #     app.include_router(main.router, prefix="/api/v1")
    #     app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    #     app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    #
    #     logger.info("All routes registered successfully")
    #
    # except ImportError as e:
    #     logger.warning(f"Some routes could not be imported: {e}")
    #     logger.info("Application running with basic health check routes only")


# Создаем экземпляр приложения
app = create_app()

# Экспортируем основные компоненты для использования в других модулях
__all__ = [
    "app",
    "create_app",
    "lifespan",
    "models",
]
