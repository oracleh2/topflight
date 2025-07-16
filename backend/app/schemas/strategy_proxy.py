# backend/app/schemas/strategy_proxy.py
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, HttpUrl, model_validator
from datetime import datetime


class StrategyProxySettings(BaseModel):
    """Настройки прокси для стратегии"""

    use_proxy: bool = True
    proxy_rotation: bool = True
    proxy_rotation_interval: int = Field(
        default=10, ge=1, le=100
    )  # количество запросов
    fallback_on_error: bool = True
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: int = Field(default=5, ge=1, le=60)  # секунды

    # Настройки для разных типов стратегий
    warmup_proxy_settings: Optional[dict] = None
    position_check_proxy_settings: Optional[dict] = None
    profile_nurture_proxy_settings: Optional[dict] = None


class StrategyProxySourceCreate(BaseModel):
    """Создание источника прокси для стратегии"""

    strategy_id: str
    source_type: Literal[
        "manual_list", "file_upload", "url_import", "google_sheets", "google_docs"
    ]
    source_url: Optional[HttpUrl] = None
    proxy_data: Optional[str] = None
    file_path: Optional[str] = None

    @model_validator(mode="after")
    def validate_source_data(self) -> "StrategyProxySourceCreate":
        source_type = self.source_type
        source_url = self.source_url
        proxy_data = self.proxy_data
        file_path = self.file_path

        if source_type in ["url_import", "google_sheets", "google_docs"]:
            if not source_url:
                raise ValueError(f"URL обязателен для типа источника {source_type}")

            if source_type == "google_sheets":
                if "docs.google.com/spreadsheets" not in str(source_url):
                    raise ValueError("Неверный формат URL Google Sheets")
            elif source_type == "google_docs":
                if "docs.google.com/document" not in str(source_url):
                    raise ValueError("Неверный формат URL Google Docs")

        if source_type == "manual_list" and not proxy_data:
            raise ValueError("Данные прокси обязательны для ручного ввода")

        if source_type == "file_upload" and not file_path:
            raise ValueError("Путь к файлу обязателен для загрузки файла")

        return self


class StrategyProxySourceResponse(BaseModel):
    """Ответ с данными источника прокси стратегии"""

    id: str
    strategy_id: str
    source_type: str
    source_url: Optional[str]
    file_path: Optional[str]
    proxy_count: int = 0
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyProxyImportRequest(BaseModel):
    """Запрос на импорт прокси для стратегии"""

    strategy_id: str
    source_type: Literal[
        "manual_list", "file_upload", "url_import", "google_sheets", "google_docs"
    ]
    proxy_data: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    file_content: Optional[str] = None


class StrategyProxyImportResponse(BaseModel):
    """Ответ на импорт прокси для стратегии"""

    success: bool
    total_parsed: int = 0
    successfully_imported: int = 0
    failed_imports: int = 0
    errors: List[str] = []
    source_id: Optional[str] = None


class StrategyProxyStatsResponse(BaseModel):
    """Статистика прокси стратегии"""

    total_proxies: int
    active_proxies: int
    failed_proxies: int
    last_check: Optional[datetime]
    average_response_time: Optional[float]
    success_rate: Optional[float]


class StrategyWithProxyResponse(BaseModel):
    """Стратегия с данными прокси"""

    id: str
    name: str
    strategy_type: str
    proxy_settings: Optional[StrategyProxySettings]
    proxy_sources: List[StrategyProxySourceResponse] = []
    proxy_stats: Optional[StrategyProxyStatsResponse] = None

    class Config:
        from_attributes = True


# Обновляем существующие схемы стратегий
class UserStrategyCreateWithProxy(BaseModel):
    """Создание стратегии с поддержкой прокси"""

    name: str
    strategy_type: str
    config: dict
    proxy_settings: Optional[StrategyProxySettings] = None
    template_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_strategy_type(self) -> "UserStrategyCreateWithProxy":
        allowed_types = ["warmup", "position_check", "profile_nurture"]
        if self.strategy_type not in allowed_types:
            raise ValueError(f"Тип стратегии должен быть одним из: {allowed_types}")
        return self


class UserStrategyUpdateWithProxy(BaseModel):
    """Обновление стратегии с поддержкой прокси"""

    name: Optional[str] = None
    config: Optional[dict] = None
    proxy_settings: Optional[StrategyProxySettings] = None
    is_active: Optional[bool] = None
