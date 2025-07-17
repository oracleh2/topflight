"""add nurture_strategy_id field in Profile model

Revision ID: 94e7129bb5f2
Revises: 97f5a35183d4
Create Date: 2025-07-17 10:30:38.690119

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "94e7129bb5f2"
down_revision: Union[str, None] = "97f5a35183d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Добавление поля nurture_strategy_id в таблицу profiles"""

    # Добавляем новое поле nurture_strategy_id
    op.add_column(
        "profiles",
        sa.Column(
            "nurture_strategy_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="ID стратегии нагула профиля",
        ),
    )

    # Добавляем Foreign Key constraint
    op.create_foreign_key(
        "fk_profiles_nurture_strategy_id",
        "profiles",
        "user_strategies",
        ["nurture_strategy_id"],
        ["id"],
        ondelete="SET NULL",  # При удалении стратегии, устанавливаем NULL
    )

    # Добавляем индекс для быстрого поиска профилей по стратегии
    op.create_index(
        "ix_profiles_nurture_strategy_id", "profiles", ["nurture_strategy_id"]
    )


def downgrade():
    """Откат изменений"""

    # Удаляем индекс
    op.drop_index("ix_profiles_nurture_strategy_id", table_name="profiles")

    # Удаляем Foreign Key constraint
    op.drop_constraint(
        "fk_profiles_nurture_strategy_id", "profiles", type_="foreignkey"
    )

    # Удаляем поле
    op.drop_column("profiles", "nurture_strategy_id")
