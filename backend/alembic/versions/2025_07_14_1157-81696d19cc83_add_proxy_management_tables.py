"""Add proxy management tables

Revision ID: 81696d19cc83
Revises: 51bf77f2fc8d
Create Date: 2025-07-14 11:57:09.886478

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "81696d19cc83"
down_revision: Union[str, None] = "51bf77f2fc8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Таблица прокси проектов
    op.create_table(
        "project_proxies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "proxy_type", sa.String(20), nullable=False
        ),  # "warmup" или "parsing"
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("password", sa.String(255), nullable=True),
        sa.Column(
            "protocol", sa.String(10), nullable=False, server_default="http"
        ),  # "http", "https", "socks4", "socks5"
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),  # "active", "inactive", "checking", "banned"
        sa.Column("last_check", sa.DateTime(), nullable=True),
        sa.Column("response_time", sa.Integer(), nullable=True),
        sa.Column("success_rate", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("total_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("country", sa.String(3), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["user_domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "domain_id",
            "proxy_type",
            "host",
            "port",
            name="uq_user_domain_proxy_host_port",
        ),
    )
    # Таблица истории импорта прокси
    op.create_table(
        "proxy_import_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "proxy_type", sa.String(20), nullable=False
        ),  # "warmup" или "parsing"
        sa.Column("import_method", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_details", sa.JSON(), nullable=True),
        sa.Column("total_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "successful_imported", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("failed_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["user_domains.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Таблица привязки прокси к профилям
    op.create_table(
        "profile_proxy_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proxy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("last_used", sa.DateTime(), nullable=True),
        sa.Column("total_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["proxy_id"], ["project_proxies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "proxy_id", name="uq_profile_proxy_assignment"
        ),
    )
    # Добавляем поле в таблицу профилей для хранения назначенной прокси для нагула
    op.add_column(
        "profiles",
        sa.Column(
            "assigned_warmup_proxy_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.create_foreign_key(
        "fk_profiles_assigned_warmup_proxy",
        "profiles",
        "project_proxies",
        ["assigned_warmup_proxy_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Добавляем поля в user_domain_settings для настроек прокси
    op.add_column(
        "user_domain_settings",
        sa.Column(
            "use_warmup_proxy_for_parsing",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )

    op.add_column(
        "user_domain_settings",
        sa.Column(
            "use_fallback_for_parsing",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )

    # Создаем индексы для производительности
    op.create_index(
        "ix_project_proxies_user_domain_type",
        "project_proxies",
        ["user_id", "domain_id", "proxy_type"],
    )
    op.create_index("ix_project_proxies_status", "project_proxies", ["status"])
    op.create_index("ix_project_proxies_host_port", "project_proxies", ["host", "port"])

    op.create_index(
        "ix_proxy_import_history_user_domain",
        "proxy_import_history",
        ["user_id", "domain_id"],
    )

    op.create_index(
        "ix_profile_proxy_assignments_profile",
        "profile_proxy_assignments",
        ["profile_id"],
    )
    op.create_index(
        "ix_profile_proxy_assignments_proxy", "profile_proxy_assignments", ["proxy_id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("ix_profile_proxy_assignments_proxy")
    op.drop_index("ix_profile_proxy_assignments_profile")
    op.drop_index("ix_proxy_import_history_user_domain")
    op.drop_index("ix_project_proxies_host_port")
    op.drop_index("ix_project_proxies_status")
    op.drop_index("ix_project_proxies_user_domain_type")

    # Удаляем поля из user_domain_settings
    op.drop_column("user_domain_settings", "use_fallback_for_parsing")
    op.drop_column("user_domain_settings", "use_warmup_proxy_for_parsing")

    # Удаляем внешний ключ и поле из profiles
    op.drop_constraint(
        "fk_profiles_assigned_warmup_proxy", "profiles", type_="foreignkey"
    )
    op.drop_column("profiles", "assigned_warmup_proxy_id")

    # Удаляем таблицы
    op.drop_table("profile_proxy_assignments")
    op.drop_table("proxy_import_history")
    op.drop_table("project_proxies")
