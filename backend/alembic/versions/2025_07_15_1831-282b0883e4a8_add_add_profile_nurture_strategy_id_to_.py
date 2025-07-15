"""add add profile_nurture_strategy_id to project_strategies

Revision ID: 282b0883e4a8
Revises: 812f395d2e52
Create Date: 2025-07-15 18:31:01.983121

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "282b0883e4a8"
down_revision: Union[str, None] = "812f395d2e52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Получаем подключение к базе данных
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Получаем список колонок таблицы project_strategies
    columns = inspector.get_columns("project_strategies")
    column_names = [col["name"] for col in columns]

    # Проверяем, существует ли колонка profile_nurture_strategy_id
    if "profile_nurture_strategy_id" not in column_names:
        # Добавляем колонку profile_nurture_strategy_id в project_strategies
        op.add_column(
            "project_strategies",
            sa.Column(
                "profile_nurture_strategy_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )
        print("Added column profile_nurture_strategy_id to project_strategies")
    else:
        print("Column profile_nurture_strategy_id already exists in project_strategies")

    # Проверяем существование внешнего ключа
    foreign_keys = inspector.get_foreign_keys("project_strategies")
    fk_names = [fk["name"] for fk in foreign_keys]

    if "fk_project_strategies_profile_nurture_strategy" not in fk_names:
        # Добавляем внешний ключ для profile_nurture_strategy_id
        op.create_foreign_key(
            "fk_project_strategies_profile_nurture_strategy",
            "project_strategies",
            "user_strategies",
            ["profile_nurture_strategy_id"],
            ["id"],
            ondelete="SET NULL",
        )
        print("Added foreign key fk_project_strategies_profile_nurture_strategy")
    else:
        print(
            "Foreign key fk_project_strategies_profile_nurture_strategy already exists"
        )

    # Проверяем существование индекса
    indexes = inspector.get_indexes("project_strategies")
    index_names = [idx["name"] for idx in indexes]

    if "idx_project_strategies_profile_nurture_strategy_id" not in index_names:
        # Создаем индекс для новой колонки
        op.create_index(
            "idx_project_strategies_profile_nurture_strategy_id",
            "project_strategies",
            ["profile_nurture_strategy_id"],
        )
        print("Added index idx_project_strategies_profile_nurture_strategy_id")
    else:
        print("Index idx_project_strategies_profile_nurture_strategy_id already exists")

    # Обновляем комментарии для поддержки нового типа стратегии
    op.execute(
        """
        COMMENT ON COLUMN strategy_templates.strategy_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN user_strategies.strategy_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN strategy_execution_log.execution_type
        IS 'Values: warmup, position_check, profile_nurture'
    """
    )

    print("Updated column comments for profile_nurture strategy type")


def downgrade():
    # Получаем подключение к базе данных
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Проверяем существование внешнего ключа перед удалением
    foreign_keys = inspector.get_foreign_keys("project_strategies")
    fk_names = [fk["name"] for fk in foreign_keys]

    if "fk_project_strategies_profile_nurture_strategy" in fk_names:
        # Удаляем внешний ключ
        op.drop_constraint(
            "fk_project_strategies_profile_nurture_strategy",
            "project_strategies",
            type_="foreignkey",
        )
        print("Dropped foreign key fk_project_strategies_profile_nurture_strategy")

    # Проверяем существование индекса перед удалением
    indexes = inspector.get_indexes("project_strategies")
    index_names = [idx["name"] for idx in indexes]

    if "idx_project_strategies_profile_nurture_strategy_id" in index_names:
        # Удаляем индекс
        op.drop_index("idx_project_strategies_profile_nurture_strategy_id")
        print("Dropped index idx_project_strategies_profile_nurture_strategy_id")

    # Проверяем существование колонки перед удалением
    columns = inspector.get_columns("project_strategies")
    column_names = [col["name"] for col in columns]

    if "profile_nurture_strategy_id" in column_names:
        # Удаляем колонку
        op.drop_column("project_strategies", "profile_nurture_strategy_id")
        print("Dropped column profile_nurture_strategy_id from project_strategies")

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

    print("Reverted column comments")
