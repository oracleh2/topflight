# backend/app/schemas/strategies.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List, Literal, Self
from datetime import datetime

from app.constants.strategies import (
    StrategyType as StrategyTypeConstants,
    DataSourceType as DataSourceTypeConstants,
    ExecutionStatus as ExecutionStatusConstants,
    ProfileNurtureType as ProfileNurtureTypeConstants,
    SearchEngineType as SearchEngineTypeConstants,
    QuerySourceType as QuerySourceTypeConstants,
    validate_warmup_config,
    validate_position_check_config,
    validate_profile_nurture_config,
)

# Используем Literal для ограничения значений
StrategyType = Literal["warmup", "position_check", "profile_nurture"]
DataSourceType = Literal[
    "manual_list", "file_upload", "url_import", "google_sheets", "google_docs"
]
ExecutionStatus = Literal["pending", "running", "completed", "failed"]
ProfileNurtureType = Literal["search_based", "direct_visits", "mixed_nurture"]
SearchEngineType = Literal[
    "yandex.ru",
    "yandex.by",
    "yandex.kz",
    "yandex.tr",
    "yandex.ua",
    "mail.ru",
    "dzen.ru",
    "ya.ru",
]
QuerySourceType = Literal[
    "manual_input", "file_upload", "url_endpoint", "google_docs", "google_sheets"
]


# Strategy Templates
class StrategyTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    strategy_type: StrategyType
    config: Dict[str, Any]
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Profile Nurture Configuration Schemas
class ProfileNurtureTargetCookies(BaseModel):
    """Схема для настройки целевого количества куков"""

    min: int = Field(50, ge=1, description="Минимальное количество куков")
    max: int = Field(100, ge=1, description="Максимальное количество куков")

    @model_validator(mode="after")
    def validate_min_max(self) -> Self:
        if self.min > self.max:
            raise ValueError(
                "Минимальное количество куков не может быть больше максимального"
            )
        return self


class ProfileNurtureSessionConfig(BaseModel):
    """Схема для настройки сессии нагула"""

    timeout_per_site: int = Field(
        15, ge=5, le=120, description="Время на сайте в секундах"
    )
    min_timeout: int = Field(10, ge=5, description="Минимальный таймаут")
    max_timeout: int = Field(30, ge=5, description="Максимальный таймаут")

    @model_validator(mode="after")
    def validate_timeouts(self) -> Self:
        if self.min_timeout > self.max_timeout:
            raise ValueError("Минимальный таймаут не может быть больше максимального")
        return self


class ProfileNurtureQueriesSource(BaseModel):
    """Схема для источника запросов"""

    type: QuerySourceType
    source_url: Optional[str] = None
    data_content: Optional[str] = None
    refresh_on_each_cycle: bool = Field(
        default=False,  # Добавляем значение по умолчанию
        description="Обновлять данные на каждом цикле (для URL)",
    )

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.type in ["url_endpoint", "google_docs", "google_sheets"]:
            if not self.source_url:
                raise ValueError(f"URL обязателен для типа источника {self.type}")

        if self.type == "manual_input" and not self.data_content:
            raise ValueError("Содержимое обязательно для ручного ввода")

        return self


class ProfileNurtureBehavior(BaseModel):
    """Схема для настройки поведения при нагуле"""

    return_to_search: bool = Field(True, description="Возвращаться в поиск после сайта")
    close_browser_after_cycle: bool = Field(
        False, description="Закрывать браузер после цикла"
    )
    emulate_human_actions: bool = Field(
        True, description="Эмулировать действия человека"
    )
    scroll_pages: bool = Field(True, description="Прокручивать страницы")
    random_clicks: bool = Field(True, description="Случайные клики")


class ProfileNurtureProportions(BaseModel):
    """Схема для пропорций смешанного нагула"""

    search_visits: int = Field(
        70, ge=1, le=100, description="Процент поисковых заходов"
    )
    direct_visits: int = Field(30, ge=1, le=100, description="Процент прямых заходов")

    @model_validator(mode="after")
    def validate_proportions(self) -> Self:
        total = self.search_visits + self.direct_visits
        if total != 100:
            raise ValueError("Сумма пропорций должна равняться 100%")
        return self


class ProfileNurtureConfigCreate(BaseModel):
    """Схема для создания конфигурации стратегии нагула профиля"""

    nurture_type: ProfileNurtureType = "search_based"
    target_cookies: ProfileNurtureTargetCookies = Field(
        default_factory=ProfileNurtureTargetCookies
    )
    session_config: ProfileNurtureSessionConfig = Field(
        default_factory=ProfileNurtureSessionConfig
    )
    search_engines: List[SearchEngineType] = Field(default=["yandex.ru"])
    queries_source: ProfileNurtureQueriesSource = Field(
        default_factory=lambda: ProfileNurtureQueriesSource(
            type="manual_input", refresh_on_each_cycle=False
        )
    )
    behavior: ProfileNurtureBehavior = Field(default_factory=ProfileNurtureBehavior)
    proportions: Optional[ProfileNurtureProportions] = None

    # Дополнительные источники для прямых заходов
    direct_sites_source: Optional[ProfileNurtureQueriesSource] = None

    # НОВЫЕ ПОЛЯ для лимитов профилей
    min_profiles_limit: int = Field(
        10, ge=1, le=10000, description="Минимальное количество нагуленных профилей"
    )
    max_profiles_limit: int = Field(
        100, ge=1, le=10000, description="Максимальное количество нагуленных профилей"
    )

    @model_validator(mode="after")
    def validate_nurture_config(self) -> Self:
        # Для поискового и смешанного типа нужны поисковые системы
        if self.nurture_type in ["search_based", "mixed_nurture"]:
            if not self.search_engines:
                raise ValueError("Поисковые системы обязательны для поискового нагула")

        # Для смешанного типа нужны пропорции
        if self.nurture_type == "mixed_nurture":
            if not self.proportions:
                raise ValueError("Пропорции обязательны для смешанного нагула")

        # Для прямых и смешанных заходов нужен источник сайтов
        if self.nurture_type in ["direct_visits", "mixed_nurture"]:
            if not self.direct_sites_source:
                raise ValueError("Источник сайтов обязателен для прямых заходов")

        # Проверяем лимиты профилей
        if self.min_profiles_limit > self.max_profiles_limit:
            raise ValueError(
                "Минимальный лимит профилей не может быть больше максимального"
            )

        return self


# Обновляем существующие схемы
class WarmupConfigCreate(BaseModel):
    """Схема для создания конфигурации стратегии прогрева"""

    type: Literal["direct", "search", "mixed"] = "mixed"
    proportions: Optional[Dict[str, int]] = None
    min_sites: int = Field(3, ge=1, le=20)
    max_sites: int = Field(7, ge=1, le=20)
    session_timeout: int = Field(15, ge=5, le=120)
    yandex_domain: str = "yandex.ru"
    device_type: Literal["desktop", "mobile"] = "desktop"

    @model_validator(mode="after")
    def validate_mixed_strategy(self) -> Self:
        if self.type == "mixed":
            if not self.proportions:
                raise ValueError(
                    "Для смешанной стратегии необходимо указать пропорции direct_visits и search_visits"
                )

            if (
                self.proportions.get("direct_visits", 0) <= 0
                or self.proportions.get("search_visits", 0) <= 0
            ):
                raise ValueError("Пропорции должны быть положительными числами")

        return self


class PositionCheckConfigCreate(BaseModel):
    """Схема для создания конфигурации стратегии проверки позиций"""

    check_frequency: Literal["daily", "weekly", "monthly", "custom"] = "daily"
    custom_schedule: Optional[str] = None  # cron expression for custom frequency
    search_config: Optional[Dict[str, Any]] = None
    behavior: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_custom_schedule(self) -> Self:
        if self.check_frequency == "custom" and not self.custom_schedule:
            raise ValueError(
                "Для custom частоты необходимо указать custom_schedule (cron выражение)"
            )
        return self


# User Strategies
class UserStrategyCreate(BaseModel):
    template_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    strategy_type: StrategyType
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("strategy_type")
    @classmethod
    def validate_strategy_type(cls, v):
        if not StrategyTypeConstants.is_valid(v):
            raise ValueError(
                f"strategy_type must be one of: {', '.join(StrategyTypeConstants.ALL)}"
            )
        return v

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        strategy_type = self.strategy_type
        config = self.config

        if strategy_type == StrategyTypeConstants.WARMUP:
            self.config = validate_warmup_config(config)
        elif strategy_type == StrategyTypeConstants.POSITION_CHECK:
            self.config = validate_position_check_config(config)
        elif strategy_type == StrategyTypeConstants.PROFILE_NURTURE:
            self.config = validate_profile_nurture_config(config)

        return self


class UserStrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator("config")
    @classmethod
    def validate_config(cls, v):
        if v is None:
            return v

        # Здесь мы не знаем тип стратегии, поэтому только базовая валидация
        # Полная валидация будет выполнена в сервисе при получении стратегии из БД
        if not isinstance(v, dict):
            raise ValueError("config должен быть объектом")

        return v


class UserStrategyResponse(BaseModel):
    id: str
    user_id: str
    template_id: Optional[str]
    name: str
    strategy_type: StrategyType
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    data_sources: List["DataSourceResponse"] = []
    nurture_status: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Data Sources - обновляем для поддержки нагула
class DataSourceCreate(BaseModel):
    source_type: DataSourceType
    source_url: Optional[str] = None
    data_content: Optional[str] = None
    file_path: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v):
        if not DataSourceTypeConstants.is_valid(v):
            raise ValueError(
                f"source_type must be one of: {', '.join(DataSourceTypeConstants.ALL)}"
            )
        return v

    @model_validator(mode="after")
    def validate_source_data(self) -> Self:
        source_type = self.source_type
        source_url = self.source_url
        data_content = self.data_content

        if source_type in [
            DataSourceTypeConstants.URL_IMPORT,
            DataSourceTypeConstants.GOOGLE_SHEETS,
            DataSourceTypeConstants.GOOGLE_DOCS,
        ]:
            if not source_url:
                raise ValueError(f"URL обязателен для типа источника {source_type}")

            if source_type == DataSourceTypeConstants.GOOGLE_SHEETS:
                if "docs.google.com/spreadsheets" not in source_url:
                    raise ValueError("Неверный формат URL Google Sheets")
            elif source_type == DataSourceTypeConstants.GOOGLE_DOCS:
                if "docs.google.com/document" not in source_url:
                    raise ValueError("Неверный формат URL Google Docs")

        if source_type == DataSourceTypeConstants.MANUAL_LIST and not data_content:
            raise ValueError("Содержимое обязательно для ручного ввода")

        return self


class DataSourceResponse(BaseModel):
    id: str
    strategy_id: str
    source_type: DataSourceType
    source_url: Optional[str]
    file_path: Optional[str]
    items_count: int = 0
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Project Strategy Assignment - обновляем для поддержки нагула
class ProjectStrategyCreate(BaseModel):
    domain_id: Optional[str] = None
    warmup_strategy_id: Optional[str] = None
    position_check_strategy_id: Optional[str] = None
    profile_nurture_strategy_id: Optional[str] = None  # Новое поле

    @model_validator(mode="after")
    def at_least_one_strategy(self) -> Self:
        strategies = [
            self.warmup_strategy_id,
            self.position_check_strategy_id,
            self.profile_nurture_strategy_id,
        ]

        if not any(strategies):
            raise ValueError("Необходимо указать хотя бы одну стратегию")
        return self


class ProjectStrategyResponse(BaseModel):
    id: str
    user_id: str
    domain_id: Optional[str]
    warmup_strategy: Optional[UserStrategyResponse]
    position_check_strategy: Optional[UserStrategyResponse]
    profile_nurture_strategy: Optional[UserStrategyResponse]  # Новое поле
    created_at: datetime

    class Config:
        from_attributes = True


# Strategy Execution
class StrategyExecutionCreate(BaseModel):
    execution_params: Dict[str, Any] = Field(default_factory=dict)


class StrategyExecutionResponse(BaseModel):
    id: str
    strategy_id: str
    task_id: Optional[str]
    execution_type: StrategyType
    profile_id: Optional[str]
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    status: ExecutionStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# Profile Nurture Execution Results
class ProfileNurtureExecutionResult(BaseModel):
    """Схема для результатов выполнения нагула профиля"""

    profile_id: str
    cookies_collected: int
    sites_visited: int
    search_queries_used: int
    session_duration: int  # в секундах
    success_rate: float
    errors: List[str] = []


# File upload schemas
class FileUploadResponse(BaseModel):
    success: bool
    data_source_id: str
    items_count: int
    message: str


# Strategy execution result schemas
class StrategyExecutionResultResponse(BaseModel):
    success: bool
    task_id: str
    message: str


# Strategy validation schemas
class StrategyValidationRequest(BaseModel):
    strategy_type: StrategyType
    config: Dict[str, Any]


class StrategyValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized_config: Optional[Dict[str, Any]] = None


# Analytics schemas
class StrategyAnalyticsRequest(BaseModel):
    strategy_ids: List[str]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class StrategyAnalyticsResponse(BaseModel):
    total_strategies: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_execution_time: Optional[float]
    executions_by_date: List[Dict[str, Any]]


# Strategy Statistics
class StrategyStatsResponse(BaseModel):
    strategy_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: Optional[float]
    last_execution: Optional[datetime]
    success_rate: float
