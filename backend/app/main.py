import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.admin.debug import router as debug_router
from .api import (
    auth,
    domains,
    billing,
    tasks,
    proxies,
    strategies,
    profiles,
    strategy_proxy,
)
from .config import settings

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Yandex Position Parser API",
    description="API для мониторинга позиций в поисковой выдаче Яндекса",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(domains.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(proxies.router, prefix="/api/v1")
app.include_router(strategies.router, prefix="/api/v1")
app.include_router(strategy_proxy.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")

app.include_router(debug_router, prefix="/api/v1/admin")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(
        "Unhandled exception",
        url=str(request.url),
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.debug else str(exc)},
    )


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Yandex Position Parser API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
