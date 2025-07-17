"""add strategy_id field to Task model

Revision ID: 33881aa523cf
Revises: 94e7129bb5f2
Create Date: 2025-07-17 19:21:26.931732

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "33881aa523cf"
down_revision: Union[str, None] = "94e7129bb5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляем поле strategy_id в таблицу tasks"""

    # Добавляем поле strategy_id как nullable UUID
    op.add_column(
        "tasks",
        sa.Column(
            "strategy_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="ID стратегии для задачи (если применимо)",
        ),
    )

    # Создаем внешний ключ для связи с таблицей user_strategies
    op.create_foreign_key(
        "fk_tasks_strategy_id",  # Имя constraint
        "tasks",  # Исходная таблица
        "user_strategies",  # Целевая таблица
        ["strategy_id"],  # Поля в исходной таблице
        ["id"],  # Поля в целевой таблице
        ondelete="SET NULL",  # При удалении стратегии устанавливаем NULL
    )

    # Создаем индекс для производительности поиска по strategy_id
    op.create_index(
        "idx_tasks_strategy_id",
        "tasks",
        ["strategy_id"],
    )

    # Создаем составной индекс для быстрого поиска задач по пользователю и стратегии
    op.create_index(
        "idx_tasks_user_strategy",
        "tasks",
        ["user_id", "strategy_id"],
    )

    print("✅ Added strategy_id field to tasks table with foreign key and indexes")


def downgrade() -> None:
    """Удаляем добавленные изменения"""

    # Удаляем индексы
    op.drop_index("idx_tasks_user_strategy", table_name="tasks")
    op.drop_index("idx_tasks_strategy_id", table_name="tasks")

    # Удаляем внешний ключ
    op.drop_constraint("fk_tasks_strategy_id", "tasks", type_="foreignkey")

    # Удаляем поле
    op.drop_column("tasks", "strategy_id")

    print("✅ Removed strategy_id field and related constraints from tasks table")
