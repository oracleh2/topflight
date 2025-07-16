# backend/app/models/profile.py

import enum

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Float,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class DeviceType(enum.Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"  # на будущее


class Profile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "profiles"

    name = Column(String(255), nullable=False)

    # Тип устройства - НОВОЕ ПОЛЕ
    device_type = Column(Enum(DeviceType), nullable=False, default=DeviceType.DESKTOP)

    # Основные браузерные данные
    user_agent = Column(Text, nullable=False)
    cookies = Column(JSON)  # Хранение cookies в JSON

    # Детальный fingerprint
    fingerprint = Column(JSON)  # Полный fingerprint профиля

    # Браузерные настройки
    browser_settings = Column(JSON)  # Основные настройки браузера
    proxy_config = Column(JSON)  # Настройки прокси

    # Статус и использование
    is_warmed_up = Column(Boolean, default=False)
    last_used = Column(DateTime)
    warmup_sites_visited = Column(Integer, default=0)
    status = Column(
        String(50), default="new"
    )  # new, warming, ready, blocked, corrupted

    # Метрики использования
    total_usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # процент успешных использований

    # Relationships
    lifecycle = relationship("ProfileLifecycle", back_populates="profile")
    fingerprint_data = relationship(
        "ProfileFingerprint", back_populates="profile", uselist=False
    )

    # Текущая назначенная прокси для нагула
    assigned_warmup_proxy_id = Column(
        UUID(as_uuid=True), ForeignKey("project_proxies.id")
    )

    assigned_strategy_proxy_id = Column(
        UUID(as_uuid=True), ForeignKey("project_proxies.id"), nullable=True
    )

    # Relationships
    assigned_warmup_proxy = relationship(
        "ProjectProxy", foreign_keys=[assigned_warmup_proxy_id]
    )
    assigned_strategy_proxy = relationship(
        "ProjectProxy", foreign_keys=[assigned_strategy_proxy_id]
    )
    strategy_proxy_assignments = relationship(
        "StrategyProxyAssignment", back_populates="profile"
    )


class ProfileFingerprint(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "profile_fingerprints"

    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, unique=True
    )

    # Основные компоненты fingerprint
    user_agent = Column(Text, nullable=False)
    screen_resolution = Column(String(20))  # "1920x1080"
    viewport_size = Column(String(20))  # "1920x969"
    timezone = Column(String(50))
    language = Column(String(10))
    platform = Column(String(50))

    # Уникальные идентификаторы
    canvas_fingerprint = Column(Text)
    webgl_fingerprint = Column(Text)
    audio_fingerprint = Column(Text)
    fonts_hash = Column(Text)  # хеш списка доступных шрифтов

    # Технические характеристики
    cpu_cores = Column(Integer)
    memory_size = Column(Integer)  # в MB
    color_depth = Column(Integer)
    pixel_ratio = Column(Float)

    # Флаги безопасности
    webdriver_present = Column(Boolean, default=False)
    automation_detected = Column(Boolean, default=False)

    # Сетевые характеристики
    connection_type = Column(String(20))
    webrtc_ips = Column(JSON)  # список локальных IP (должен быть пустым)

    # Relationships
    profile = relationship("Profile", back_populates="fingerprint_data")


# Обновляем основную модель Profile
Profile.fingerprint_data = relationship(
    "ProfileFingerprint", back_populates="profile", uselist=False
)


class ProfileLifecycle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "profile_lifecycle"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("user_domains.id"))
    current_usage_count = Column(Integer, default=0)
    cascade_stage = Column(
        Integer, default=0
    )  # 0=fresh, 1=used_once, 2=dogwalking, 3=ready_again
    is_corrupted = Column(Boolean, default=False)
    corruption_reason = Column(Text)
    last_health_check = Column(DateTime)
    next_health_check = Column(DateTime)

    # Relationships
    profile = relationship("Profile", back_populates="lifecycle")
    domain = relationship("UserDomain")


class ServerConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "server_configs"

    server_id = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255), nullable=False)

    # Отдельные настройки для desktop и mobile
    warm_desktop_profiles_target = Column(Integer, default=200)
    warm_mobile_profiles_target = Column(Integer, default=800)

    max_cpu_cores = Column(Integer)
    max_cpu_percent = Column(Integer, default=75)
    max_ram_percent = Column(Integer, default=70)
    spawn_queue_threshold = Column(Integer, default=50)
    spawn_check_interval = Column(Integer, default=180)  # секунды
    max_concurrent_workers = Column(Integer)
    profile_health_check_interval = Column(Integer, default=1800)  # 30 минут
    auto_scaling_enabled = Column(Boolean, default=True)
    auto_worker_spawn = Column(Boolean, default=True)
    current_workers_count = Column(Integer, default=0)
    max_workers_limit = Column(Integer)


class WorkerNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "worker_nodes"

    node_id = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    location = Column(String(100))
    status = Column(String(50), default="offline")  # online, offline, busy, maintenance
    max_workers = Column(Integer, default=10)
    last_heartbeat = Column(DateTime)
    capabilities = Column(JSON)  # браузеры, прокси и т.д.
