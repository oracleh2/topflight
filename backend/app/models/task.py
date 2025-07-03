from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, UUIDMixin
from datetime import datetime


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    task_type = Column(String(50), nullable=False)  # warmup_profile, parse_serp, check_positions
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    priority = Column(Integer, default=0)

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
    domain_id = Column(UUID(as_uuid=True), ForeignKey("user_domains.id"), nullable=False)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("user_keywords.id"), nullable=False)
    position = Column(Integer)
    url = Column(Text)
    check_date = Column(DateTime, default=datetime.utcnow)
    serp_features = Column(JSON)  # дополнительные данные о выдаче

    # Relationships
    user = relationship("User")
    domain = relationship("UserDomain")
    keyword = relationship("UserKeyword")