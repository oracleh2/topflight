# backend/app/models/proxy.py

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class ProxyType(enum.Enum):
    WARMUP = "warmup"  # Прокси для нагула
    PARSING = "parsing"  # Прокси для замера позиций


class ProxyProtocol(enum.Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyStatus(enum.Enum):
    ACTIVE = "active"  # Рабочая прокси
    INACTIVE = "inactive"  # Не работает
    CHECKING = "checking"  # Проверяется
    BANNED = "banned"  # Заблокирована


class ProjectProxy(Base, UUIDMixin, TimestampMixin):
    """Прокси для проектов пользователей"""

    __tablename__ = "project_proxies"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False
    )

    # Тип прокси (для нагула или для замеров) - строка вместо enum
    proxy_type = Column(String(20), nullable=False)  # "warmup" или "parsing"

    # Данные прокси
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    protocol = Column(
        String(10), nullable=False, default="http"
    )  # "http", "https", "socks4", "socks5"

    # Статус и метрики
    status = Column(
        String(20), default="active"
    )  # "active", "inactive", "checking", "banned"
    last_check = Column(DateTime)
    response_time = Column(Integer)  # ms
    success_rate = Column(Integer, default=100)  # %
    total_uses = Column(Integer, default=0)
    failed_uses = Column(Integer, default=0)

    # Дополнительные данные
    country = Column(String(3))  # ISO country code
    city = Column(String(100))
    provider = Column(String(100))
    notes = Column(Text)

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain")


class ProxyImportHistory(Base, UUIDMixin, TimestampMixin):
    """История импорта прокси"""

    __tablename__ = "proxy_import_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False
    )
    proxy_type = Column(String(20), nullable=False)  # "warmup" или "parsing"

    # Источник импорта
    import_method = Column(String(50), nullable=False)  # manual, file, google_doc, url
    source_url = Column(Text)  # URL источника (если применимо)
    source_details = Column(JSON)  # Дополнительные данные источника

    # Результаты импорта
    total_imported = Column(Integer, default=0)
    successful_imported = Column(Integer, default=0)
    failed_imported = Column(Integer, default=0)
    error_details = Column(JSON)

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain")


# Дополнение к модели Profile для привязки прокси
class ProfileProxyAssignment(Base, UUIDMixin, TimestampMixin):
    """Привязка прокси к профилям"""

    __tablename__ = "profile_proxy_assignments"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    proxy_id = Column(
        UUID(as_uuid=True), ForeignKey("project_proxies.id"), nullable=False
    )

    # Когда была назначена и использована
    assigned_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

    # Статистика использования
    total_uses = Column(Integer, default=0)
    successful_uses = Column(Integer, default=0)
    failed_uses = Column(Integer, default=0)

    # Relationships
    profile = relationship("Profile")
    proxy = relationship("ProjectProxy")


# Обновление модели Profile для хранения текущей прокси
"""
Добавить в models/profile.py:

class Profile(Base, UUIDMixin, TimestampMixin):
    # ... existing fields ...

    # Текущая назначенная прокси для нагула
    assigned_warmup_proxy_id = Column(UUID(as_uuid=True), ForeignKey("project_proxies.id"))

    # Relationships
    assigned_warmup_proxy = relationship("ProjectProxy", foreign_keys=[assigned_warmup_proxy_id])
"""
