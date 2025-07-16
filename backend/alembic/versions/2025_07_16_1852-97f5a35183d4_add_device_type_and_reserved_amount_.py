"""add device_type and reserved_amount field to tasks table

Revision ID: 97f5a35183d4
Revises: 348f64471a1f
Create Date: 2025-07-16 18:52:16.399531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '97f5a35183d4'
down_revision: Union[str, None] = '348f64471a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Добавить поля device_type и reserved_amount в таблицу tasks"""

    # Добавляем колонку device_type
    op.add_column(
        "tasks",
        sa.Column(
            "device_type",
            sa.String(20),
            nullable=False,
            default="desktop",
            server_default="desktop"
        )
    )

    # Добавляем колонку reserved_amount
    op.add_column(
        "tasks",
        sa.Column(
            "reserved_amount",
            sa.Numeric(10, 2),
            nullable=True,
            default=None
        )
    )

    # Добавляем комментарии к колонкам
    op.execute(
        """
        COMMENT ON COLUMN tasks.device_type
        IS 'Device type for task execution: desktop, mobile, tablet'
        """
    )

    op.execute(
        """
        COMMENT ON COLUMN tasks.reserved_amount
        IS 'Amount reserved from user balance for this task execution'
        """
    )

    # Обновляем существующие записи на основе параметров
    op.execute(
        """
        UPDATE tasks
        SET device_type = COALESCE(
            parameters->>'device_type',
            'desktop'
                          )
        WHERE device_type = 'desktop'
        """
    )

    # Создаем индексы для оптимизации запросов
    op.create_index(
        "idx_tasks_device_type",
        "tasks",
        ["device_type"]
    )

    op.create_index(
        "idx_tasks_device_type_status",
        "tasks",
        ["device_type", "status"]
    )

    op.create_index(
        "idx_tasks_reserved_amount",
        "tasks",
        ["reserved_amount"]
    )

    # Составной индекс для поиска задач с резервированными средствами
    op.create_index(
        "idx_tasks_user_id_reserved_amount",
        "tasks",
        ["user_id", "reserved_amount"]
    )

    print("Added device_type and reserved_amount fields to tasks table")


def downgrade():
    """Удалить поля device_type и reserved_amount из таблицы tasks"""

    # Удаляем индексы
    op.drop_index("idx_tasks_user_id_reserved_amount", table_name="tasks")
    op.drop_index("idx_tasks_reserved_amount", table_name="tasks")
    op.drop_index("idx_tasks_device_type_status", table_name="tasks")
    op.drop_index("idx_tasks_device_type", table_name="tasks")

    # Удаляем колонки
    op.drop_column("tasks", "reserved_amount")
    op.drop_column("tasks", "device_type")

    print("Removed device_type and reserved_amount fields from tasks table")
