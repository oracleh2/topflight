# backend/app/schemas/strategies.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List, Literal, Self
from datetime import datetime

from app.constants.strategies import (
    StrategyType as StrategyTypeConstants,
    DataSourceType as DataSourceTypeConstants,
    ExecutionStatus as ExecutionStatusConstants,
    validate_warmup_config,
    validate_position_check_config,
)

# Используем Literal для ограничения значений
StrategyType = Literal["warmup", "position_check"]
DataSourceType = Literal[
    "manual_list", "file_upload", "url_import", "google_sheets", "google_docs"
]
ExecutionStatus = Literal["pending", "running", "completed", "failed"]


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

    class Config:
        from_attributes = True


# Data Sources
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


# Project Strategy Assignment
class ProjectStrategyCreate(BaseModel):
    domain_id: Optional[str] = None
    warmup_strategy_id: Optional[str] = None
    position_check_strategy_id: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_strategy(self) -> Self:
        if not self.warmup_strategy_id and not self.position_check_strategy_id:
            raise ValueError("Необходимо указать хотя бы одну стратегию")
        return self


class ProjectStrategyResponse(BaseModel):
    id: str
    user_id: str
    domain_id: Optional[str]
    warmup_strategy: Optional[UserStrategyResponse]
    position_check_strategy: Optional[UserStrategyResponse]
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


# Strategy Statistics
class StrategyStatsResponse(BaseModel):
    strategy_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_execution: Optional[datetime]
    average_execution_time: Optional[float]  # в секундах
    success_rate: float  # в процентах


# Bulk operations
class BulkDataImport(BaseModel):
    items: List[str] = Field(..., min_length=1)
    source_type: DataSourceType = "manual_list"

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v):
        if not DataSourceTypeConstants.is_valid(v):
            raise ValueError(
                f"source_type must be one of: {', '.join(DataSourceTypeConstants.ALL)}"
            )
        return v

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        # Удаляем пустые строки и дубликаты
        cleaned_items = list(set([item.strip() for item in v if item.strip()]))

        if not cleaned_items:
            raise ValueError("Список не может быть пустым")

        if len(cleaned_items) > 10000:
            raise ValueError("Максимальное количество элементов: 10000")

        return cleaned_items


class BulkExecutionRequest(BaseModel):
    strategy_ids: List[str] = Field(..., min_length=1, max_length=10)
    execution_params: Dict[str, Any] = Field(default_factory=dict)


# Configuration schemas for specific strategy types
class WarmupConfigCreate(BaseModel):
    """Схема для создания конфигурации стратегии прогрева"""

    type: Literal["direct", "search", "mixed"]
    proportions: Optional[Dict[str, int]] = None
    search_config: Optional[Dict[str, Any]] = None
    direct_config: Optional[Dict[str, Any]] = None
    general: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_proportions(self) -> Self:
        if self.type == "mixed":
            proportions = self.proportions
            if (
                not proportions
                or not proportions.get("direct_visits")
                or not proportions.get("search_visits")
            ):
                raise ValueError(
                    "Для mixed стратегии необходимо указать пропорции direct_visits и search_visits"
                )

            if (
                proportions.get("direct_visits", 0) <= 0
                or proportions.get("search_visits", 0) <= 0
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


# File upload schemas
class FileUploadResponse(BaseModel):
    success: bool
    data_source_id: str
    items_count: int
    message: str


# Execution result schemas
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
    strategies_performance: List[Dict[str, Any]]


# Import/Export schemas
class StrategyExportRequest(BaseModel):
    strategy_ids: List[str]
    include_data_sources: bool = True
    include_execution_logs: bool = False


class StrategyImportRequest(BaseModel):
    strategies_data: List[Dict[str, Any]]
    overwrite_existing: bool = False


class StrategyImportResponse(BaseModel):
    success: bool
    imported_count: int
    skipped_count: int
    errors: List[str] = []
    imported_strategy_ids: List[str] = []


# Template management schemas
class StrategyTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    strategy_type: StrategyType
    config: Dict[str, Any]

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

        return self


# Data source management schemas
class DataSourceUpdate(BaseModel):
    source_url: Optional[str] = None
    data_content: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceBulkCreate(BaseModel):
    strategy_id: str
    sources: List[DataSourceCreate]


class DataSourceBulkResponse(BaseModel):
    success: bool
    created_count: int
    failed_count: int
    errors: List[str] = []
    created_source_ids: List[str] = []


# Update forward references
UserStrategyResponse.model_rebuild()
DataSourceResponse.model_rebuild()
ProjectStrategyResponse.model_rebuild()
