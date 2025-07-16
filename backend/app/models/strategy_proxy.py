# backend/app/models/strategy_proxy.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, UUIDMixin, TimestampMixin


class StrategyProxySource(Base, UUIDMixin, TimestampMixin):
    """Источники прокси для стратегий"""

    __tablename__ = "strategy_proxy_sources"

    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=False
    )

    # Тип источника данных
    source_type = Column(
        String(50), nullable=False
    )  # manual_list, file_upload, url_import, google_sheets, google_docs
    source_url = Column(String(500), nullable=True)
    proxy_data = Column(Text, nullable=True)  # Сырые данные прокси
    file_path = Column(String(500), nullable=True)

    # Статус и метаданные
    is_active = Column(Boolean, default=True, nullable=False)

    updated_at = None

    # Relationships
    strategy = relationship("UserStrategy", back_populates="proxy_sources")


# Обновляем модель UserStrategy для поддержки прокси
"""
Добавить в backend/app/models/strategies.py:

class UserStrategy(Base, UUIDMixin, TimestampMixin):
    # ... existing fields ...

    # Настройки прокси для стратегии
    proxy_settings = Column(JSON, nullable=True, comment="Настройки прокси для стратегии")

    # Relationships
    proxy_sources = relationship("StrategyProxySource", back_populates="strategy", cascade="all, delete-orphan")
"""


class StrategyProxyAssignment(Base, UUIDMixin, TimestampMixin):
    """Назначение конкретной прокси стратегии на профиль"""

    __tablename__ = "strategy_proxy_assignments"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=False
    )
    proxy_id = Column(
        UUID(as_uuid=True), ForeignKey("project_proxies.id"), nullable=False
    )

    # Метаданные назначения
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True)

    # Статистика использования
    total_uses = Column(Integer, default=0)
    successful_uses = Column(Integer, default=0)
    failed_uses = Column(Integer, default=0)

    # Relationships
    profile = relationship("Profile")
    strategy = relationship("UserStrategy")
    proxy = relationship("ProjectProxy")


class StrategyProxyRotation(Base, UUIDMixin, TimestampMixin):
    """Логика ротации прокси для стратегий"""

    __tablename__ = "strategy_proxy_rotations"

    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=False
    )
    current_proxy_id = Column(
        UUID(as_uuid=True), ForeignKey("project_proxies.id"), nullable=True
    )

    # Настройки ротации
    rotation_interval = Column(Integer, default=10)  # количество запросов
    current_usage_count = Column(Integer, default=0)

    # История ротации
    rotation_history = Column(JSON, nullable=True)  # История смены прокси

    # Relationships
    strategy = relationship("UserStrategy")
    current_proxy = relationship("ProjectProxy")


# Обновляем модель Profile для поддержки прокси стратегий
"""
Добавить в backend/app/models/profile.py:

class Profile(Base, UUIDMixin, TimestampMixin):
    # ... existing fields ...

    # Назначенная прокси для стратегии
    assigned_strategy_proxy_id = Column(UUID(as_uuid=True), ForeignKey("project_proxies.id"), nullable=True)

    # Relationships
    assigned_strategy_proxy = relationship("ProjectProxy", foreign_keys=[assigned_strategy_proxy_id])
    strategy_proxy_assignments = relationship("StrategyProxyAssignment", back_populates="profile")
"""
