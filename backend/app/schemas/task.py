from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.core.task_manager import TaskType
from app.models import DeviceType


class TaskTypeEnum(str, Enum):
    WARMUP_PROFILE = "warmup_profile"
    PARSE_SERP = "parse_serp"
    CHECK_POSITIONS = "check_positions"
    HEALTH_CHECK = "health_check"
    MAINTAIN_PROFILES = "maintain_profiles"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class DeviceTypeEnum(str, Enum):
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    TABLET = "TABLET"


# Request schemas
class TaskCreate(BaseModel):
    task_type: TaskTypeEnum
    parameters: Dict[str, Any]
    priority: int = Field(default=0, ge=0, le=10)
    device_type: DeviceType = DeviceType.DESKTOP
    profile_id: Optional[str] = None
    reserved_amount: Optional[float] = None


class TaskCreateRequest(BaseModel):
    """Схема для создания задачи"""

    task_type: TaskType
    priority: int = Field(5, ge=1, le=20)
    device_type: DeviceType = DeviceType.DESKTOP
    parameters: Dict[str, Any] = Field(default_factory=dict)
    profile_id: Optional[str] = None
    reserved_amount: Optional[float] = None


class ParseTaskCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=500)
    device_type: DeviceTypeEnum = DeviceTypeEnum.DESKTOP
    pages: int = Field(default=10, ge=1, le=20)
    region_code: str = Field(default="213", min_length=1, max_length=10)
    reserved_amount: Optional[float] = None
    priority: int = Field(5, ge=1, le=20)


class PositionCheckCreate(BaseModel):
    keyword_ids: List[str] = Field(..., min_items=1)
    device_type: DeviceTypeEnum = DeviceTypeEnum.DESKTOP
    reserved_amount: Optional[float] = None
    priority: int = Field(5, ge=1, le=20)


class WarmupTaskCreateRequest(BaseModel):
    """Схема для создания задачи прогрева"""

    device_type: DeviceType = DeviceType.DESKTOP
    profile_id: Optional[str] = None
    priority: int = Field(2, ge=1, le=20)
    reserved_amount: Optional[float] = None


class ProfileNurtureTaskCreateRequest(BaseModel):
    """Схема для создания задачи нагула профиля"""

    strategy_id: str
    device_type: DeviceType = DeviceType.DESKTOP
    priority: int = Field(3, ge=1, le=20)
    profile_id: Optional[str] = None
    reserved_amount: Optional[float] = None


# Response schemas
class TaskResponse(BaseModel):
    """Схема ответа для задачи"""

    id: str
    task_type: str
    status: str
    priority: int
    device_type: str  # Добавляем device_type
    reserved_amount: Optional[float]
    user_id: Optional[str]
    profile_id: Optional[str]
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParseResultResponse(BaseModel):
    id: str
    task_id: str
    keyword: str
    position: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    domain: Optional[str] = None
    page_number: Optional[int] = None
    parsed_at: datetime

    class Config:
        from_attributes = True


class PositionHistoryResponse(BaseModel):
    id: str
    user_id: str
    domain_id: str
    keyword_id: str
    position: Optional[int] = None
    url: Optional[str] = None
    check_date: datetime
    serp_features: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TasksListResponse(BaseModel):
    """Схема для списка задач"""

    tasks: List[TaskResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TaskStatusResponse(BaseModel):
    id: str
    status: str
    progress: Optional[int] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class ParseTaskResult(BaseModel):
    keyword: str
    total_results: int
    positions_found: List[ParseResultResponse]
    pages_parsed: int
    device_type: str
    region_code: str
    parsing_time_seconds: float
    reserved_amount: Optional[float] = None


class PositionCheckResult(BaseModel):
    keywords_checked: int
    positions_found: int
    positions_changed: int
    average_position: Optional[float] = None
    check_time_seconds: float
    device_type: str


class TaskStatsResponse(BaseModel):
    """Схема для статистики задач"""

    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    tasks_by_type: Dict[str, int]
    tasks_by_device_type: Dict[str, int]
