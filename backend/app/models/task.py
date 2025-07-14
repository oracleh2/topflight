from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import DeviceType
from .base import Base, TimestampMixin, UUIDMixin
from datetime import datetime


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    task_type = Column(
        String(50), nullable=False
    )  # warmup_profile, parse_serp, check_positions
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    priority = Column(Integer, default=0)

    # ДОБАВЛЯЕМ ПОЛЕ USER_ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Параметры задачи в JSON
    parameters = Column(JSON)  # {"keyword": "...", "pages": 10, "profile_id": "..."}

    # Результаты
    result = Column(JSON)
    error_message = Column(Text)

    # Временные метки
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Связи
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    worker_id = Column(String(255))

    # Relationships
    profile = relationship("Profile")
    parse_results = relationship("ParseResult", back_populates="task")

    @property
    def debug_enabled(self) -> bool:
        """Проверяет, включен ли режим дебага для задачи"""
        if not self.parameters:
            return False
        return self.parameters.get("debug_enabled", False)

    @debug_enabled.setter
    def debug_enabled(self, value: bool):
        """Устанавливает флаг дебага"""
        if not self.parameters:
            self.parameters = {}
        self.parameters["debug_enabled"] = value

    @property
    def debug_info(self) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о debug сессии"""
        if not self.parameters or not self.debug_enabled:
            return None

        return {
            "device_type": self.parameters.get("debug_device_type", "desktop"),
            "started_by": self.parameters.get("debug_started_by"),
            "started_at": self.parameters.get("debug_started_at"),
            "stopped_by": self.parameters.get("debug_stopped_by"),
            "stopped_at": self.parameters.get("debug_stopped_at"),
            "restarted_by": self.parameters.get("debug_restarted_by"),
            "restarted_at": self.parameters.get("debug_restarted_at"),
        }

    def can_be_debugged(self) -> bool:
        """Проверяет, может ли задача быть отлажена"""
        return self.status in ["pending", "running", "failed"]

    def get_debug_device_type(self) -> DeviceType:
        """Возвращает тип устройства для debug сессии"""
        if self.parameters and "debug_device_type" in self.parameters:
            return DeviceType(self.parameters["debug_device_type"])

        # Fallback на device_type из основных параметров
        if self.parameters and "device_type" in self.parameters:
            return DeviceType(self.parameters["device_type"])

        return DeviceType.DESKTOP


class ParseResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "parse_results"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    keyword = Column(String(500), nullable=False)
    position = Column(Integer)
    url = Column(Text)
    title = Column(Text)
    snippet = Column(Text)
    domain = Column(String(255))
    page_number = Column(Integer)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="parse_results")


class PositionHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "position_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False
    )
    keyword_id = Column(
        UUID(as_uuid=True), ForeignKey("user_keywords.id"), nullable=False
    )
    position = Column(Integer)
    url = Column(Text)
    check_date = Column(DateTime, default=datetime.utcnow)
    serp_features = Column(JSON)  # дополнительные данные о выдаче

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain")
    keyword = relationship("UserKeyword")
