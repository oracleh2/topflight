"""add Add strategy proxy relation

Revision ID: 77a1aeb5024b
Revises: 282b0883e4a8
Create Date: 2025-07-16 14:12:02.738682

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "77a1aeb5024b"
down_revision: Union[str, None] = "282b0883e4a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для хранения настроек прокси в стратегии
    op.add_column(
        "user_strategies",
        sa.Column(
            "proxy_settings",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="Настройки прокси для стратегии",
        ),
    )

    # Создаем таблицу для связи стратегий с прокси
    op.create_table(
        "strategy_proxy_sources",
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
        sa.Column("proxy_data", sa.Text(), nullable=True),
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

    # Создаем индексы
    op.create_index(
        "idx_strategy_proxy_sources_strategy_id",
        "strategy_proxy_sources",
        ["strategy_id"],
    )
    op.create_index(
        "idx_strategy_proxy_sources_active",
        "strategy_proxy_sources",
        ["is_active"],
    )

    # Добавляем поле для текущей назначенной прокси в профиль
    op.add_column(
        "profiles",
        sa.Column(
            "assigned_strategy_proxy_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Создаем внешний ключ для связи профиля с прокси
    op.create_foreign_key(
        "fk_profiles_strategy_proxy",
        "profiles",
        "project_proxies",
        ["assigned_strategy_proxy_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Создаем индекс для производительности
    op.create_index(
        "idx_profiles_strategy_proxy_id",
        "profiles",
        ["assigned_strategy_proxy_id"],
    )


def downgrade() -> None:
    # Удаляем внешний ключ и индекс
    op.drop_constraint("fk_profiles_strategy_proxy", "profiles", type_="foreignkey")
    op.drop_index("idx_profiles_strategy_proxy_id", table_name="profiles")

    # Удаляем поле из профиля
    op.drop_column("profiles", "assigned_strategy_proxy_id")

    # Удаляем таблицу источников прокси стратегий
    op.drop_table("strategy_proxy_sources")

    # Удаляем поле из стратегий
    op.drop_column("user_strategies", "proxy_settings")
