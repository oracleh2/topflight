from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Numeric, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, UUIDMixin
from datetime import datetime, date


class SystemConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "system_configs"

    config_key = Column(String(255), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    updated_by_user = relationship("User")


class SystemLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "system_logs"

    level = Column(String(20), nullable=False)  # info, warning, error, critical
    component = Column(String(100), nullable=False)  # worker, parser, admin
    server_id = Column(String(255))
    message = Column(Text, nullable=False)
    details = Column(JSON)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User")


class AuditTrail(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_trail"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action_type = Column(String(100), nullable=False)
    table_name = Column(String(100))
    record_id = Column(UUID(as_uuid=True))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])


class ConfigChangesLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "config_changes_log"

    config_level = Column(String(50), nullable=False)  # system, server, user, domain
    entity_id = Column(UUID(as_uuid=True))
    config_key = Column(String(255), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    changed_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))

    # Relationships
    changed_by_user = relationship("User", foreign_keys=[changed_by_user_id])
    changed_by_admin = relationship("User", foreign_keys=[changed_by_admin_id])


class FinancialTransactionsLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "financial_transactions_log"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    balance_before = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)
    operation_type = Column(String(50), nullable=False)
    description = Column(Text)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])


class PerformanceMetrics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "performance_metrics"

    server_id = Column(String(255), nullable=False)
    metric_type = Column(String(100), nullable=False)  # cpu, ram, queue_size, response_time
    value = Column(Numeric(10, 2), nullable=False)
    measurement_time = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)


class BusinessMetrics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "business_metrics"

    date = Column(Date, default=date.today)
    metric_name = Column(String(100), nullable=False)  # registrations, conversions, arpu, retention
    value = Column(Numeric(15, 2), nullable=False)
    details = Column(JSON)


class UserActivityStats(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_activity_stats"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=date.today)
    checks_count = Column(Integer, default=0)
    domains_count = Column(Integer, default=0)
    last_login = Column(DateTime)
    total_spent = Column(Numeric(10, 2), default=0.00)
    registration_source = Column(String(100))

    # Relationships
    user = relationship("User")


class TaskAnalytics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_analytics"

    date = Column(Date, default=date.today)
    task_type = Column(String(50), nullable=False)
    total_created = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    avg_execution_time = Column(Numeric(10, 2))
    server_id = Column(String(255))


class ParsingAnalytics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "parsing_analytics"

    date = Column(Date, default=date.today)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False)
    successful_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 2), default=0.00)
    avg_position = Column(Numeric(5, 2))
    regions_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain")


class BackupSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "backup_schedule"

    backup_type = Column(String(50), nullable=False)  # full, incremental, profiles
    schedule_cron = Column(String(100), nullable=False)
    retention_days = Column(Integer, default=30)
    storage_path = Column(Text)
    last_backup_time = Column(DateTime)
    next_backup_time = Column(DateTime)
    is_enabled = Column(Boolean, default=True)


class BackupHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "backup_history"

    backup_type = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)  # размер в байтах
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(50), nullable=False)  # running, completed, failed
    error_message = Column(Text)


class CacheSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cache_settings"

    cache_key = Column(String(255), unique=True, nullable=False)
    cache_type = Column(String(50), nullable=False)  # serp, stats, config
    ttl_seconds = Column(Integer, nullable=False)
    is_enabled = Column(Boolean, default=True)