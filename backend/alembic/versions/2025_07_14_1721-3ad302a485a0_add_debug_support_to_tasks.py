# backend/alembic/versions/2025_07_14_1721-3ad302a485a0_add_debug_support_to_tasks.py
"""Add debug support to tasks

Revision ID: 3ad302a485a0
Revises: 55df8c442aa0
Create Date: 2025-07-14 17:21:39.421108

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3ad302a485a0"
down_revision: Union[str, None] = "55df8c442aa0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    Добавляем поддержку debug режима для задач.

    В Task модели уже есть поле parameters (JSON), поэтому структурных изменений БД не требуется.
    Флаг debug_enabled будет храниться в parameters как JSON поле.

    Однако для удобства и производительности добавим индексы на часто используемые поля.
    """

    # Добавляем индекс на status для быстрого поиска задач по статусу
    op.create_index("idx_tasks_status", "tasks", ["status"])

    # Добавляем индекс на task_type для быстрого поиска по типу
    op.create_index("idx_tasks_task_type", "tasks", ["task_type"])

    # Добавляем составной индекс на status + created_at для сортировки
    op.create_index("idx_tasks_status_created_at", "tasks", ["status", "created_at"])

    # Добавляем индекс на user_id для быстрого поиска задач пользователя
    op.create_index("idx_tasks_user_id", "tasks", ["user_id"])

    # ИСПРАВЛЕНО: Указываем правильный оператор-класс для JSON GIN индекса
    # Добавляем GIN индекс на parameters для быстрого поиска по JSON полям
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_debug_enabled ON tasks ((parameters->>'debug_enabled')) WHERE parameters->>'debug_enabled' IS NOT NULL"
    )

    print("Debug support added to tasks - using existing parameters JSON field")


def downgrade():
    """Удаляем добавленные индексы"""

    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_index("idx_tasks_task_type", table_name="tasks")
    op.drop_index("idx_tasks_status_created_at", table_name="tasks")
    op.drop_index("idx_tasks_user_id", table_name="tasks")
    op.drop_index("idx_tasks_parameters_gin", table_name="tasks")
