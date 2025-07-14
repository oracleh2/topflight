"""Add strategy models

Revision ID: fefd84a0329a
Revises: 1cb74885998b
Create Date: 2025-07-14 14:32:54.688894

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fefd84a0329a"
down_revision: Union[str, None] = "1cb74885998b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу strategy_templates
    op.create_table(
        "strategy_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "strategy_type",
            sa.String(length=50),
            nullable=False,
            comment="Values: warmup, position_check",
        ),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # Создаем индексы для strategy_templates
    op.create_index(
        "idx_strategy_templates_type", "strategy_templates", ["strategy_type"]
    )
    op.create_index(
        "idx_strategy_templates_active", "strategy_templates", ["is_active"]
    )

    # Создаем таблицу user_strategies
    op.create_table(
        "user_strategies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "strategy_type",
            sa.String(length=50),
            nullable=False,
            comment="Values: warmup, position_check",
        ),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=False),
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
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["strategy_templates.id"], ondelete="SET NULL"
        ),
    )

    # Создаем индексы для user_strategies
    op.create_index("idx_user_strategies_user_id", "user_strategies", ["user_id"])
    op.create_index("idx_user_strategies_type", "user_strategies", ["strategy_type"])
    op.create_index("idx_user_strategies_active", "user_strategies", ["is_active"])

    # Создаем таблицу strategy_data_sources
    op.create_table(
        "strategy_data_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
            comment="Values: manual_list, file_upload, url_import, google_sheets, google_docs",
        ),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("data_content", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["strategy_id"], ["user_strategies.id"], ondelete="CASCADE"
        ),
    )

    # Создаем индексы для strategy_data_sources
    op.create_index(
        "idx_strategy_data_sources_strategy_id",
        "strategy_data_sources",
        ["strategy_id"],
    )
    op.create_index(
        "idx_strategy_data_sources_active", "strategy_data_sources", ["is_active"]
    )

    # Создаем таблицу project_strategies
    op.create_table(
        "project_strategies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warmup_strategy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "position_check_strategy_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["domain_id"], ["user_domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["warmup_strategy_id"], ["user_strategies.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["position_check_strategy_id"], ["user_strategies.id"], ondelete="SET NULL"
        ),
    )

    # Создаем индексы для project_strategies
    op.create_index("idx_project_strategies_user_id", "project_strategies", ["user_id"])
    op.create_index(
        "idx_project_strategies_domain_id", "project_strategies", ["domain_id"]
    )

    # Создаем таблицу strategy_execution_log
    op.create_table(
        "strategy_execution_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "execution_type",
            sa.String(length=50),
            nullable=False,
            comment="Values: warmup, position_check",
        ),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parameters", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="'pending'",
            comment="Values: pending, running, completed, failed",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["strategy_id"], ["user_strategies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="SET NULL"),
    )

    # Создаем индексы для strategy_execution_log
    op.create_index(
        "idx_strategy_execution_log_strategy_id",
        "strategy_execution_log",
        ["strategy_id"],
    )
    op.create_index(
        "idx_strategy_execution_log_task_id", "strategy_execution_log", ["task_id"]
    )
    op.create_index(
        "idx_strategy_execution_log_status", "strategy_execution_log", ["status"]
    )
    op.create_index(
        "idx_strategy_execution_log_started_at",
        "strategy_execution_log",
        ["started_at"],
    )

    # Добавляем несколько системных шаблонов стратегий
    op.execute(
        """
        INSERT INTO strategy_templates (name, description, strategy_type, is_system, config) VALUES
        (
            'Базовая стратегия прогрева',
            'Комбинированная стратегия прогрева профилей с прямыми заходами и поиском',
            'warmup',
            true,
            '{
                "type": "mixed",
                "proportions": {"direct_visits": 5, "search_visits": 1},
                "search_config": {
                    "yandex_domains": ["yandex.ru"],
                    "keywords_per_session": {"min": 1, "max": 3},
                    "click_probability": 0.7,
                    "random_result_click": true
                },
                "direct_config": {
                    "sites_per_session": {"min": 3, "max": 7},
                    "time_per_site": {"min": 10, "max": 45},
                    "scroll_probability": 0.8,
                    "click_probability": 0.3
                },
                "general": {
                    "delay_between_actions": {"min": 2, "max": 8},
                    "user_agent_rotation": true,
                    "cookie_retention": true
                }
            }'::json
        ),
        (
            'Только прямые заходы',
            'Стратегия прогрева только через прямые заходы на сайты',
            'warmup',
            true,
            '{
                "type": "direct",
                "direct_config": {
                    "sites_per_session": {"min": 5, "max": 10},
                    "time_per_site": {"min": 15, "max": 60},
                    "scroll_probability": 0.9,
                    "click_probability": 0.4
                },
                "general": {
                    "delay_between_actions": {"min": 3, "max": 10},
                    "user_agent_rotation": true,
                    "cookie_retention": true
                }
            }'::json
        ),
        (
            'Только поиск в Яндексе',
            'Стратегия прогрева только через поиск в Яндексе',
            'warmup',
            true,
            '{
                "type": "search",
                "search_config": {
                    "yandex_domains": ["yandex.ru", "yandex.by"],
                    "keywords_per_session": {"min": 2, "max": 5},
                    "click_probability": 0.8,
                    "random_result_click": true
                },
                "general": {
                    "delay_between_actions": {"min": 5, "max": 15},
                    "user_agent_rotation": true,
                    "cookie_retention": true
                }
            }'::json
        ),
        (
            'Базовая проверка позиций',
            'Стандартная стратегия проверки позиций с естественным поведением',
            'position_check',
            true,
            '{
                "check_frequency": "daily",
                "search_config": {
                    "pages_to_check": 10,
                    "yandex_domain": "yandex.ru",
                    "device_types": ["desktop"],
                    "regions": ["213"]
                },
                "behavior": {
                    "scroll_serp": true,
                    "click_competitors": 0.1,
                    "time_on_serp": {"min": 5, "max": 15}
                }
            }'::json
        ),
        (
            'Агрессивная проверка позиций',
            'Стратегия с повышенной активностью для более естественного поведения',
            'position_check',
            true,
            '{
                "check_frequency": "daily",
                "search_config": {
                    "pages_to_check": 20,
                    "yandex_domain": "yandex.ru",
                    "device_types": ["desktop", "mobile"],
                    "regions": ["213", "2"]
                },
                "behavior": {
                    "scroll_serp": true,
                    "click_competitors": 0.2,
                    "time_on_serp": {"min": 10, "max": 30}
                }
            }'::json
        )
        """
    )


def downgrade() -> None:
    # Удаляем таблицы в обратном порядке
    op.drop_table("strategy_execution_log")
    op.drop_table("project_strategies")
    op.drop_table("strategy_data_sources")
    op.drop_table("user_strategies")
    op.drop_table("strategy_templates")
