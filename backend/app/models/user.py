from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, UUIDMixin
from datetime import datetime
from sqlalchemy import Enum

from .profile import DeviceType


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    subscription_plan = Column(String(50), default="basic")
    api_key = Column(String(255), unique=True, index=True)
    balance = Column(Numeric(10, 2), default=0.00)
    is_active = Column(Boolean, default=True)

    # Relationships (только существующие, без стратегий)
    domains = relationship("UserDomain", back_populates="user")
    transactions = relationship(
        "BalanceTransaction",
        back_populates="user",
        foreign_keys="BalanceTransaction.user_id",  # Явно указываем используемый внешний ключ
    )


class TariffPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tariff_plans"

    name = Column(String(100), nullable=False)
    description = Column(Text)
    cost_per_check = Column(Numeric(5, 2), nullable=False)
    min_monthly_topup = Column(Numeric(10, 2), default=0.00)
    server_binding_allowed = Column(Boolean, default=False)
    priority_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class UserBalance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_balance"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_balance = Column(Numeric(10, 2), default=0.00)
    reserved_balance = Column(Numeric(10, 2), default=0.00)
    last_topup_amount = Column(Numeric(10, 2))
    last_topup_date = Column(DateTime)

    # Relationships
    user = relationship("User")


class BalanceTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "balance_transactions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String(50), nullable=False)  # topup, charge, refund
    description = Column(Text)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    admin = relationship("User", foreign_keys=[admin_id])


class Region(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regions"

    region_code = Column(String(10), unique=True, nullable=False)
    region_name = Column(String(255), nullable=False)
    country_code = Column(String(5), default="RU")


class UserDomain(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_domains"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="domains")
    keywords = relationship("UserKeyword", back_populates="domain")
    settings = relationship("UserDomainSettings", back_populates="domain")


class UserKeyword(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_keywords"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False
    )
    keyword = Column(String(500), nullable=False)
    # region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    region_id = Column(
        UUID(as_uuid=True), ForeignKey("yandex_regions.id"), nullable=False
    )

    # НОВОЕ ПОЛЕ - тип устройства для этого ключевого слова
    device_type = Column(Enum(DeviceType), nullable=False, default=DeviceType.DESKTOP)

    is_active = Column(Boolean, default=True)
    check_frequency = Column(String(20), default="daily")  # daily, weekly, monthly

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain", back_populates="keywords")
    # region = relationship("Region")
    region = relationship("YandexRegion")


class UserDomainSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_domain_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False
    )
    # region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    region_id = Column(
        UUID(as_uuid=True), ForeignKey("yandex_regions.id"), nullable=False
    )

    # НОВОЕ ПОЛЕ - тип устройства для парсинга
    device_type = Column(Enum(DeviceType), nullable=False, default=DeviceType.DESKTOP)

    profile_cascade_enabled = Column(Boolean, default=True)
    cascade_warmup_sites_count = Column(Integer, default=5)
    delete_profile_after_cascade = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain", back_populates="settings")
    # region = relationship("Region")
    region = relationship("YandexRegion")


class UserServerPreferences(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_server_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    preferred_server_id = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
