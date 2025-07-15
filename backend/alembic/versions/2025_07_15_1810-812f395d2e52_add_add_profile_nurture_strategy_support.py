"""add Add profile nurture strategy support

Revision ID: 812f395d2e52
Revises: ea06df9001a0
Create Date: 2025-07-15 18:10:35.630717

"""

from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "812f395d2e52"
down_revision: Union[str, None] = "ea06df9001a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем новый тип стратегии в существующие таблицы

    # Обновляем комментарий для strategy_type в strategy_templates
    op.execute(
        """
        COMMENT ON COLUMN strategy_templates.strategy_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    # Обновляем комментарий для strategy_type в user_strategies
    op.execute(
        """
        COMMENT ON COLUMN user_strategies.strategy_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    # Обновляем комментарий для execution_type в strategy_execution_log
    op.execute(
        """
        COMMENT ON COLUMN strategy_execution_log.execution_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    # Добавляем колонку profile_nurture_strategy_id в project_strategies
    op.add_column(
        "project_strategies",
        sa.Column(
            "profile_nurture_strategy_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )

    # Добавляем внешний ключ для profile_nurture_strategy_id
    op.create_foreign_key(
        "fk_project_strategies_profile_nurture_strategy",
        "project_strategies",
        "user_strategies",
        ["profile_nurture_strategy_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Создаем индекс для новой колонки
    op.create_index(
        "idx_project_strategies_profile_nurture_strategy_id",
        "project_strategies",
        ["profile_nurture_strategy_id"],
    )

    # Создаем таблицу для отслеживания прогресса нагула профилей
    op.create_table(
        "profile_nurture_progress",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_cookies_min", sa.Integer, nullable=False, default=50),
        sa.Column("target_cookies_max", sa.Integer, nullable=False, default=100),
        sa.Column("current_cookies_count", sa.Integer, nullable=False, default=0),
        sa.Column("sites_visited_count", sa.Integer, nullable=False, default=0),
        sa.Column("queries_used_count", sa.Integer, nullable=False, default=0),
        sa.Column(
            "total_session_time", sa.Integer, nullable=False, default=0
        ),  # in seconds
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            default="pending",
            comment="Values: pending, in_progress, completed, failed, paused",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "config_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["strategy_id"], ["user_strategies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
    )

    # Создаем индексы для profile_nurture_progress
    op.create_index(
        "idx_profile_nurture_progress_profile_id",
        "profile_nurture_progress",
        ["profile_id"],
    )
    op.create_index(
        "idx_profile_nurture_progress_strategy_id",
        "profile_nurture_progress",
        ["strategy_id"],
    )
    op.create_index(
        "idx_profile_nurture_progress_status", "profile_nurture_progress", ["status"]
    )
    op.create_index(
        "idx_profile_nurture_progress_started_at",
        "profile_nurture_progress",
        ["started_at"],
    )

    # Создаем уникальный индекс для profile_id + strategy_id
    op.create_index(
        "idx_unique_profile_strategy_nurture",
        "profile_nurture_progress",
        ["profile_id", "strategy_id"],
        unique=True,
    )

    # Создаем таблицу для детальной статистики нагула
    op.create_table(
        "profile_nurture_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("progress_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "session_type", sa.String(length=50), nullable=False
        ),  # search_visit, direct_visit
        sa.Column("search_engine", sa.String(length=100), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("visited_url", sa.Text(), nullable=True),
        sa.Column("session_duration", sa.Integer, nullable=False),  # in seconds
        sa.Column("cookies_collected", sa.Integer, nullable=False, default=0),
        sa.Column("success", sa.Boolean, nullable=False, default=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["progress_id"], ["profile_nurture_progress.id"], ondelete="CASCADE"
        ),
    )

    # Создаем индексы для profile_nurture_sessions
    op.create_index(
        "idx_profile_nurture_sessions_progress_id",
        "profile_nurture_sessions",
        ["progress_id"],
    )
    op.create_index(
        "idx_profile_nurture_sessions_type",
        "profile_nurture_sessions",
        ["session_type"],
    )
    op.create_index(
        "idx_profile_nurture_sessions_created_at",
        "profile_nurture_sessions",
        ["created_at"],
    )

    # Подготавливаем JSON конфигурации для шаблонов
    config_search_based = {
        "nurture_type": "search_based",
        "target_cookies": {"min": 50, "max": 100},
        "session_config": {
            "timeout_per_site": 15,
            "min_timeout": 10,
            "max_timeout": 30,
        },
        "search_engines": ["yandex.ru"],
        "queries_source": {"type": "manual_input", "refresh_on_each_cycle": False},
        "behavior": {
            "return_to_search": True,
            "close_browser_after_cycle": False,
            "emulate_human_actions": True,
            "scroll_pages": True,
            "random_clicks": True,
        },
    }

    config_direct_visits = {
        "nurture_type": "direct_visits",
        "target_cookies": {"min": 30, "max": 80},
        "session_config": {
            "timeout_per_site": 20,
            "min_timeout": 15,
            "max_timeout": 35,
        },
        "search_engines": [],
        "queries_source": {"type": "manual_input", "refresh_on_each_cycle": False},
        "behavior": {
            "return_to_search": False,
            "close_browser_after_cycle": True,
            "emulate_human_actions": True,
            "scroll_pages": True,
            "random_clicks": True,
        },
        "direct_sites_source": {"type": "manual_input", "refresh_on_each_cycle": False},
    }

    config_mixed_nurture = {
        "nurture_type": "mixed_nurture",
        "target_cookies": {"min": 70, "max": 150},
        "session_config": {
            "timeout_per_site": 18,
            "min_timeout": 12,
            "max_timeout": 25,
        },
        "search_engines": ["yandex.ru", "yandex.by"],
        "queries_source": {"type": "manual_input", "refresh_on_each_cycle": False},
        "behavior": {
            "return_to_search": True,
            "close_browser_after_cycle": False,
            "emulate_human_actions": True,
            "scroll_pages": True,
            "random_clicks": True,
        },
        "proportions": {"search_visits": 70, "direct_visits": 30},
        "direct_sites_source": {"type": "manual_input", "refresh_on_each_cycle": False},
    }

    config_url_dynamic = {
        "nurture_type": "mixed_nurture",
        "target_cookies": {"min": 80, "max": 120},
        "session_config": {
            "timeout_per_site": 15,
            "min_timeout": 10,
            "max_timeout": 30,
        },
        "search_engines": ["yandex.ru"],
        "queries_source": {"type": "url_endpoint", "refresh_on_each_cycle": True},
        "behavior": {
            "return_to_search": True,
            "close_browser_after_cycle": False,
            "emulate_human_actions": True,
            "scroll_pages": True,
            "random_clicks": True,
        },
        "proportions": {"search_visits": 60, "direct_visits": 40},
        "direct_sites_source": {"type": "url_endpoint", "refresh_on_each_cycle": True},
    }

    # Добавляем системные шаблоны для нагула профиля
    connection = op.get_bind()

    # Используем параметризованные запросы для безопасной вставки JSON
    connection.execute(
        sa.text(
            """
            INSERT INTO strategy_templates (name, description, strategy_type, config, is_system, is_active)
            VALUES
            (:name1, :desc1, 'profile_nurture', :config1, true, true),
            (:name2, :desc2, 'profile_nurture', :config2, true, true),
            (:name3, :desc3, 'profile_nurture', :config3, true, true),
            (:name4, :desc4, 'profile_nurture', :config4, true, true)
        """
        ),
        {
            "name1": "Поисковый нагул (базовый)",
            "desc1": "Базовая стратегия нагула профиля через поиск в Яндексе с переходами на сайты из топ-10",
            "config1": json.dumps(config_search_based),
            "name2": "Прямые заходы (базовый)",
            "desc2": "Базовая стратегия нагула профиля через прямые заходы на сайты",
            "config2": json.dumps(config_direct_visits),
            "name3": "Смешанный нагул (продвинутый)",
            "desc3": "Продвинутая стратегия комбинирующая поиск и прямые заходы для максимально естественного поведения",
            "config3": json.dumps(config_mixed_nurture),
            "name4": "URL-динамический нагул",
            "desc4": "Стратегия нагула с динамическим получением запросов и сайтов по URL",
            "config4": json.dumps(config_url_dynamic),
        },
    )


def downgrade():
    # Удаляем новые таблицы
    op.drop_table("profile_nurture_sessions")
    op.drop_table("profile_nurture_progress")

    # Удаляем колонку profile_nurture_strategy_id из project_strategies
    op.drop_constraint(
        "fk_project_strategies_profile_nurture_strategy",
        "project_strategies",
        type_="foreignkey",
    )
    op.drop_index("idx_project_strategies_profile_nurture_strategy_id")
    op.drop_column("project_strategies", "profile_nurture_strategy_id")

    # Удаляем шаблоны стратегий нагула профиля
    op.execute("DELETE FROM strategy_templates WHERE strategy_type = 'profile_nurture'")

    # Возвращаем старые комментарии
    op.execute(
        """
        COMMENT ON COLUMN strategy_templates.strategy_type
        IS 'Values: warmup, position_check'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN user_strategies.strategy_type
        IS 'Values: warmup, position_check'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN strategy_execution_log.execution_type
        IS 'Values: warmup, position_check'
    """
    )
