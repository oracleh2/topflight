"""add Yandex Region model

Revision ID: 3068d50fd76c
Revises: 3ad302a485a0
Create Date: 2025-07-15 13:11:46.424181

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3068d50fd76c"
down_revision: Union[str, None] = "3ad302a485a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создаем пустую таблицу yandex_regions"""

    # Создаем таблицу yandex_regions
    op.create_table(
        "yandex_regions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Основные поля
        sa.Column("region_code", sa.String(length=10), nullable=False),
        sa.Column("region_name", sa.String(length=255), nullable=False),
        sa.Column("country_code", sa.String(length=5), nullable=False),
        # Дополнительные поля
        sa.Column("parent_region_code", sa.String(length=10), nullable=True),
        sa.Column("region_type", sa.String(length=50), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        # Координаты
        sa.Column("latitude", sa.String(length=20), nullable=True),
        sa.Column("longitude", sa.String(length=20), nullable=True),
        # Дополнительная информация
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        # Поля для поиска
        sa.Column("search_name", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        # Ограничения
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_code"),
    )

    # Создаем индексы для оптимизации поиска
    op.create_index("ix_yandex_regions_region_code", "yandex_regions", ["region_code"])
    op.create_index(
        "ix_yandex_regions_country_code", "yandex_regions", ["country_code"]
    )
    op.create_index("ix_yandex_regions_region_name", "yandex_regions", ["region_name"])
    op.create_index("ix_yandex_regions_is_active", "yandex_regions", ["is_active"])
    op.create_index("ix_yandex_regions_region_type", "yandex_regions", ["region_type"])

    # Устанавливаем значения по умолчанию
    op.alter_column("yandex_regions", "country_code", server_default="RU")
    op.alter_column("yandex_regions", "is_active", server_default="true")

    print("✅ Пустая таблица yandex_regions создана успешно")
    print(
        "📝 Для заполнения таблицы запустите: python scripts/import_yandex_regions.py"
    )


def downgrade() -> None:
    """Удаляем таблицу yandex_regions"""

    # Удаляем индексы
    op.drop_index("ix_yandex_regions_region_type", table_name="yandex_regions")
    op.drop_index("ix_yandex_regions_is_active", table_name="yandex_regions")
    op.drop_index("ix_yandex_regions_region_name", table_name="yandex_regions")
    op.drop_index("ix_yandex_regions_country_code", table_name="yandex_regions")
    op.drop_index("ix_yandex_regions_region_code", table_name="yandex_regions")

    # Удаляем таблицу
    op.drop_table("yandex_regions")

    print("🗑️ Таблица yandex_regions удалена")
