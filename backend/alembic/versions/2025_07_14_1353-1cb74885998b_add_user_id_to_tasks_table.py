"""Add user_id to tasks table

Revision ID: 1cb74885998b
Revises: 81696d19cc83
Create Date: 2025-07-14 13:53:22.714152

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1cb74885998b"
down_revision: Union[str, None] = "81696d19cc83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем только user_id в таблицу tasks
    op.add_column(
        "tasks", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Создаем foreign key constraint
    op.create_foreign_key(
        "fk_tasks_user_id", "tasks", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )

    # Создаем индекс для быстрого поиска
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])

    # Обновляем существующие задачи (опционально)
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
                               UPDATE tasks
                               SET user_id = CAST(parameters->>'user_id' AS UUID)
                               WHERE parameters->>'user_id' IS NOT NULL
                                 AND parameters->>'user_id' != 'null'
                                 AND parameters->>'user_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                               """
        )
    )


def downgrade() -> None:
    # Удаляем индекс
    op.drop_index("ix_tasks_user_id", table_name="tasks")

    # Удаляем foreign key constraint
    op.drop_constraint("fk_tasks_user_id", "tasks", type_="foreignkey")

    # Удаляем колонку
    op.drop_column("tasks", "user_id")
