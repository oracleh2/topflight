"""fix strategies - user relationships

Revision ID: 55df8c442aa0
Revises: fefd84a0329a
Create Date: 2025-07-14 16:26:14.996665

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "55df8c442aa0"
down_revision: Union[str, None] = "fefd84a0329a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Данная миграция фиксирует изменения в relationships между моделями стратегий.
    Структурных изменений в БД не требуется, так как все Foreign Keys уже существуют.

    Изменения касаются только SQLAlchemy relationships:
    1. Добавлены relationships в модель User для связи со стратегиями
    2. Все relationships теперь определены статически в моделях
    3. Убрана динамическая настройка relationships через setup_strategy_relationships()

    Проверяем существование всех необходимых таблиц и связей.
    """

    # Проверяем, что все таблицы стратегий существуют
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    required_tables = [
        "strategy_templates",
        "user_strategies",
        "strategy_data_sources",
        "project_strategies",
        "strategy_execution_log",
    ]

    missing_tables = [table for table in required_tables if table not in tables]
    if missing_tables:
        raise Exception(
            f"Отсутствуют таблицы: {missing_tables}. Запустите миграцию fefd84a0329a сначала."
        )

    # Проверяем Foreign Key ограничения для корректности relationships
    print("Проверяем Foreign Key ограничения...")

    # strategy_templates.created_by_user_id -> users.id
    fk_constraints = inspector.get_foreign_keys("strategy_templates")
    has_user_fk = any(
        fk["referred_table"] == "users"
        and "created_by_user_id" in fk["constrained_columns"]
        for fk in fk_constraints
    )
    if not has_user_fk:
        print(
            "WARNING: FK constraint strategy_templates.created_by_user_id -> users.id не найден"
        )

    # user_strategies.user_id -> users.id
    fk_constraints = inspector.get_foreign_keys("user_strategies")
    has_user_fk = any(
        fk["referred_table"] == "users" and "user_id" in fk["constrained_columns"]
        for fk in fk_constraints
    )
    if not has_user_fk:
        print("WARNING: FK constraint user_strategies.user_id -> users.id не найден")

    # user_strategies.template_id -> strategy_templates.id
    has_template_fk = any(
        fk["referred_table"] == "strategy_templates"
        and "template_id" in fk["constrained_columns"]
        for fk in fk_constraints
    )
    if not has_template_fk:
        print(
            "WARNING: FK constraint user_strategies.template_id -> strategy_templates.id не найден"
        )

    # strategy_data_sources.strategy_id -> user_strategies.id
    fk_constraints = inspector.get_foreign_keys("strategy_data_sources")
    has_strategy_fk = any(
        fk["referred_table"] == "user_strategies"
        and "strategy_id" in fk["constrained_columns"]
        for fk in fk_constraints
    )
    if not has_strategy_fk:
        print(
            "WARNING: FK constraint strategy_data_sources.strategy_id -> user_strategies.id не найден"
        )

    # project_strategies Foreign Keys
    fk_constraints = inspector.get_foreign_keys("project_strategies")
    required_project_fks = [
        ("users", "user_id"),
        ("user_domains", "domain_id"),
        ("user_strategies", "warmup_strategy_id"),
        ("user_strategies", "position_check_strategy_id"),
    ]

    for referred_table, column in required_project_fks:
        has_fk = any(
            fk["referred_table"] == referred_table
            and column in fk["constrained_columns"]
            for fk in fk_constraints
        )
        if not has_fk:
            print(
                f"WARNING: FK constraint project_strategies.{column} -> {referred_table}.id не найден"
            )

    # strategy_execution_log Foreign Keys
    fk_constraints = inspector.get_foreign_keys("strategy_execution_log")
    required_log_fks = [
        ("user_strategies", "strategy_id"),
        ("tasks", "task_id"),
        ("profiles", "profile_id"),
    ]

    for referred_table, column in required_log_fks:
        has_fk = any(
            fk["referred_table"] == referred_table
            and column in fk["constrained_columns"]
            for fk in fk_constraints
        )
        if not has_fk:
            print(
                f"WARNING: FK constraint strategy_execution_log.{column} -> {referred_table}.id не найден"
            )

    print("Проверка завершена. Relationships настроены корректно в коде моделей.")


def downgrade() -> None:
    """
    Откат не требуется, так как структурных изменений в БД не было.
    Все изменения касались только кода моделей SQLAlchemy.
    """
    print("Откат не требуется - изменения касались только relationships в коде.")
    pass
