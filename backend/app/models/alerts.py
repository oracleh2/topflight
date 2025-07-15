# backend/app/models/alerts.py
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Numeric,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, UUIDMixin
from datetime import datetime


class AlertRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alert_rules"

    # Основные поля правила
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")

    # Условия срабатывания
    condition_type = Column(String(50), nullable=False)
    condition_params = Column(JSON, nullable=False)
    threshold_value = Column(Numeric(10, 2), nullable=True)
    comparison_operator = Column(String(10), nullable=True)  # >, <, >=, <=, ==, !=

    # Частота проверки
    check_interval_minutes = Column(Integer, nullable=False, server_default="5")
    last_check_time = Column(DateTime, nullable=True)
    last_triggered_time = Column(DateTime, nullable=True)

    # Каналы уведомлений
    notification_channels = Column(JSON, nullable=False)
    cooldown_minutes = Column(Integer, nullable=False, server_default="30")

    # Метаданные
    created_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    alert_level = Column(
        String(20), nullable=False, server_default="warning"
    )  # info, warning, error, critical
    tags = Column(JSON, nullable=True)

    # Relationships
    created_by_user = relationship(
        "User", foreign_keys=[created_by_user_id], overlaps="created_alert_rules"
    )
    alert_history = relationship("AlertHistory", back_populates="alert_rule")


class AlertHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alert_history"

    # Связь с правилом
    alert_rule_id = Column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False
    )

    # Данные срабатывания
    triggered_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    status = Column(
        String(20), nullable=False, server_default="active"
    )  # active, resolved, acknowledged

    # Значения при срабатывании
    triggered_value = Column(Numeric(15, 2), nullable=True)
    threshold_value = Column(Numeric(15, 2), nullable=True)
    additional_data = Column(JSON, nullable=True)

    # Уведомления
    notifications_sent = Column(JSON, nullable=True)
    acknowledged_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    acknowledgement_note = Column(Text, nullable=True)

    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alert_history")
    acknowledged_by_user = relationship(
        "User", foreign_keys=[acknowledged_by_user_id], overlaps="acknowledged_alerts"
    )


class DebugVNCSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "debug_vnc_sessions"

    # Связь с задачей
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # VNC параметры
    vnc_port = Column(Integer, nullable=False, unique=True)
    vnc_display = Column(String(10), nullable=False, unique=True)  # :1, :2, etc.
    vnc_password = Column(String(255), nullable=True)

    # Дисплей параметры
    screen_resolution = Column(String(20), nullable=False)  # 1920x1080
    color_depth = Column(Integer, nullable=False, server_default="24")

    # Устройство для эмуляции
    device_type = Column(String(20), nullable=False)  # desktop, mobile, tablet
    device_profile = Column(JSON, nullable=True)

    # Статус сессии
    status = Column(
        String(20), nullable=False, server_default="initializing"
    )  # initializing, active, stopped, error
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)

    # Процессы
    xvfb_pid = Column(Integer, nullable=True)
    vnc_server_pid = Column(Integer, nullable=True)
    browser_process_id = Column(String(255), nullable=True)

    # Настройки сервера
    server_id = Column(String(255), nullable=True)
    worker_id = Column(String(255), nullable=True)

    # Логи и ошибки
    error_message = Column(Text, nullable=True)
    debug_logs = Column(JSON, nullable=True)

    # Метаданные
    session_timeout_minutes = Column(Integer, nullable=False, server_default="60")
    auto_cleanup = Column(Boolean, nullable=False, server_default="true")

    # Relationships
    user = relationship("User")
    task = relationship("Task")
