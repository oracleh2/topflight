"""fix change Region model within YandexRegion

Revision ID: aab2c5499137
Revises: 3068d50fd76c
Create Date: 2025-07-15 13:35:56.564722

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "aab2c5499137"
down_revision: Union[str, None] = "3068d50fd76c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем старые FK
    op.drop_constraint(
        "user_keywords_region_id_fkey", "user_keywords", type_="foreignkey"
    )
    op.drop_constraint(
        "user_domain_settings_region_id_fkey",
        "user_domain_settings",
        type_="foreignkey",
    )

    # Добавляем новые FK на yandex_regions
    op.create_foreign_key(
        "user_keywords_region_id_fkey",
        "user_keywords",
        "yandex_regions",
        ["region_id"],
        ["id"],
    )
    op.create_foreign_key(
        "user_domain_settings_region_id_fkey",
        "user_domain_settings",
        "yandex_regions",
        ["region_id"],
        ["id"],
    )

    # Удаляем старую таблицу regions
    op.drop_table("regions")


def downgrade() -> None:
    """Откатываем изменения: восстанавливаем таблицу regions и обновляем FK"""

    # 1. Создаем обратно старую таблицу regions
    op.create_table(
        "regions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("region_code", sa.String(length=10), nullable=False),
        sa.Column("region_name", sa.String(length=255), nullable=False),
        sa.Column("country_code", sa.String(length=5), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_code"),
    )

    # 2. Создаем индексы для старой таблицы
    op.create_index("ix_regions_region_code", "regions", ["region_code"])

    # 3. Переносим данные из yandex_regions в regions (только базовые поля)
    connection = op.get_bind()

    # Вставляем данные из yandex_regions в regions
    connection.execute(
        sa.text(
            """
                               INSERT INTO regions (id, created_at, updated_at, region_code, region_name, country_code)
                               SELECT id, created_at, updated_at, region_code, region_name, country_code
                               FROM yandex_regions
                               WHERE is_active = true
                               """
        )
    )

    # 4. Удаляем новые FK на yandex_regions
    op.drop_constraint(
        "user_keywords_region_id_fkey", "user_keywords", type_="foreignkey"
    )
    op.drop_constraint(
        "user_domain_settings_region_id_fkey",
        "user_domain_settings",
        type_="foreignkey",
    )

    # 5. Создаем старые FK на таблицу regions
    op.create_foreign_key(
        "user_keywords_region_id_fkey",
        "user_keywords",
        "regions",
        ["region_id"],
        ["id"],
    )
    op.create_foreign_key(
        "user_domain_settings_region_id_fkey",
        "user_domain_settings",
        "regions",
        ["region_id"],
        ["id"],
    )

    # 6. Удаляем таблицу yandex_regions
    op.drop_table("yandex_regions")

    print("🔄 Откат выполнен: восстановлена таблица regions")
    print("⚠️  Внимание: данные из дополнительных полей YandexRegion потеряны")
