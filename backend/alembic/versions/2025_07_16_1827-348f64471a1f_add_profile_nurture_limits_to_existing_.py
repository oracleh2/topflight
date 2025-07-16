"""add profile nurture limits to existing strategies

Revision ID: 348f64471a1f
Revises: 5f3ddffa0a69
Create Date: 2025-07-16 18:27:25.578722

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "348f64471a1f"
down_revision: Union[str, None] = "5f3ddffa0a69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Добавить лимиты профилей в существующие стратегии нагула"""

    # Получаем подключение к базе данных
    connection = op.get_bind()

    # Обновляем существующие стратегии нагула, добавляя лимиты
    # Приводим config к JSONB типу для совместимости
    connection.execute(
        sa.text(
            """
            UPDATE user_strategies
            SET config = config::jsonb || '{"min_profiles_limit": 10, "max_profiles_limit": 100}'::jsonb
            WHERE strategy_type = 'profile_nurture'
              AND (config->>'min_profiles_limit') IS NULL
            """
        )
    )

    # Обновляем шаблоны стратегий
    connection.execute(
        sa.text(
            """
            UPDATE strategy_templates
            SET config = config::jsonb || '{"min_profiles_limit": 10, "max_profiles_limit": 100}'::jsonb
            WHERE strategy_type = 'profile_nurture'
              AND (config->>'min_profiles_limit') IS NULL
            """
        )
    )

    print("Added profile limits to existing nurture strategies")


def downgrade():
    """Удалить лимиты профилей из стратегий нагула"""

    # Получаем подключение к базе данных
    connection = op.get_bind()

    # Удаляем лимиты из пользовательских стратегий
    connection.execute(
        sa.text(
            """
            UPDATE user_strategies
            SET config = config::jsonb - 'min_profiles_limit' - 'max_profiles_limit'
            WHERE strategy_type = 'profile_nurture'
            """
        )
    )

    # Удаляем лимиты из шаблонов стратегий
    connection.execute(
        sa.text(
            """
            UPDATE strategy_templates
            SET config = config::jsonb - 'min_profiles_limit' - 'max_profiles_limit'
            WHERE strategy_type = 'profile_nurture'
            """
        )
    )

    print("Removed profile limits from nurture strategies")
