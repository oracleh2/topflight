# backend/app/models/strategies.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone

from app.database import Base


class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    # Values: 'warmup', 'position_check'
    strategy_type = Column(String(50), nullable=False)
    is_system = Column(Boolean, server_default="false")
    config = Column(JSON, nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, server_default="true")

    # Relationships - только внутренние, без связи с User
    user_strategies = relationship("UserStrategy", back_populates="template")


class UserStrategy(Base):
    __tablename__ = "user_strategies"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("strategy_templates.id"))
    name = Column(String(255), nullable=False)
    # Values: 'warmup', 'position_check'
    strategy_type = Column(String(50), nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, server_default="true")

    # Relationships - только внутренние, без связи с User
    template = relationship("StrategyTemplate", back_populates="user_strategies")
    data_sources = relationship(
        "StrategyDataSource", back_populates="strategy", cascade="all, delete-orphan"
    )
    execution_logs = relationship("StrategyExecutionLog", back_populates="strategy")
    warmup_projects = relationship(
        "ProjectStrategy",
        foreign_keys="ProjectStrategy.warmup_strategy_id",
        back_populates="warmup_strategy",
    )
    position_check_projects = relationship(
        "ProjectStrategy",
        foreign_keys="ProjectStrategy.position_check_strategy_id",
        back_populates="position_check_strategy",
    )
    profile_nurture_projects = relationship(
        "ProjectStrategy",
        foreign_keys="ProjectStrategy.profile_nurture_strategy_id",
        back_populates="profile_nurture_strategy",
    )


class StrategyDataSource(Base):
    __tablename__ = "strategy_data_sources"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=False
    )
    # Values: 'manual_list', 'file_upload', 'url_import', 'google_sheets', 'google_docs'
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(500))
    data_content = Column(Text)
    file_path = Column(String(500))
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy = relationship("UserStrategy", back_populates="data_sources")


class ProjectStrategy(Base):
    __tablename__ = "project_strategies"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("user_domains.id"))
    warmup_strategy_id = Column(UUID(as_uuid=True), ForeignKey("user_strategies.id"))
    position_check_strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id")
    )
    profile_nurture_strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id")
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - используем прямые запросы вместо relationships с User/UserDomain
    warmup_strategy = relationship(
        "UserStrategy",
        foreign_keys=[warmup_strategy_id],
        back_populates="warmup_projects",
    )
    position_check_strategy = relationship(
        "UserStrategy",
        foreign_keys=[position_check_strategy_id],
        back_populates="position_check_projects",
    )


class StrategyExecutionLog(Base):
    __tablename__ = "strategy_execution_log"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("user_strategies.id"), nullable=False
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    # Values: 'warmup', 'position_check'
    execution_type = Column(String(50), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    parameters = Column(JSON)
    result = Column(JSON)
    # Values: 'pending', 'running', 'completed', 'failed'
    status = Column(String(50), server_default="'pending'")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # Relationships - только внутренние между стратегиями
    strategy = relationship("UserStrategy", back_populates="execution_logs")
