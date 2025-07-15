"""fix change delete region reletion from keyword and add to domain

Revision ID: e1fffc129580
Revises: aab2c5499137
Create Date: 2025-07-15 15:16:57.882330

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers, used by Alembic.
revision: str = "e1fffc129580"
down_revision: Union[str, None] = "aab2c5499137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def constraint_exists(connection, table_name, constraint_name):
    """Проверяет существование constraint"""
    result = connection.execute(
        text(
            """
                                     SELECT EXISTS (
                                         SELECT 1 FROM information_schema.table_constraints
                                         WHERE table_name = :table_name
                                           AND constraint_name = :constraint_name
                                           AND constraint_type = 'FOREIGN KEY'
                                     )
                                     """
        ),
        {"table_name": table_name, "constraint_name": constraint_name},
    )
    return result.scalar()


def get_foreign_key_constraints(connection, table_name):
    """Получает список всех внешних ключей для таблицы"""
    result = connection.execute(
        text(
            """
                                     SELECT
                                         tc.constraint_name,
                                         tc.table_name,
                                         kcu.column_name,
                                         ccu.table_name AS foreign_table_name,
                                         ccu.column_name AS foreign_column_name
                                     FROM information_schema.table_constraints AS tc
                                              JOIN information_schema.key_column_usage AS kcu
                                                   ON tc.constraint_name = kcu.constraint_name
                                              JOIN information_schema.constraint_column_usage AS ccu
                                                   ON ccu.constraint_name = tc.constraint_name
                                     WHERE tc.constraint_type = 'FOREIGN KEY'
                                       AND tc.table_name = :table_name
                                     """
        ),
        {"table_name": table_name},
    )

    return result.fetchall()


def index_exists(connection, index_name):
    """Проверяет существование индекса"""
    result = connection.execute(
        text(
            """
                                     SELECT EXISTS (
                                         SELECT 1 FROM pg_indexes
                                         WHERE indexname = :index_name
                                     )
                                     """
        ),
        {"index_name": index_name},
    )
    return result.scalar()


def column_exists(connection, table_name, column_name):
    """Проверяет существование колонки"""
    result = connection.execute(
        text(
            """
                                     SELECT EXISTS (
                                         SELECT 1 FROM information_schema.columns
                                         WHERE table_name = :table_name
                                           AND column_name = :column_name
                                     )
                                     """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar()


def upgrade():
    """Выполняет миграцию: переносит region_id из user_keywords в user_domains"""

    connection = op.get_bind()

    # Проверяем текущее состояние базы данных
    print("Checking current database state...")

    # Проверяем, есть ли уже region_id в user_domains
    if column_exists(connection, "user_domains", "region_id"):
        print("WARNING: user_domains already has region_id column!")
        print("This might indicate the migration was partially run before.")

        # Проверяем, есть ли еще region_id в user_keywords
        if not column_exists(connection, "user_keywords", "region_id"):
            print("Migration appears to be already completed. Skipping...")
            return
        else:
            print("Continuing migration from where it left off...")
    else:
        # Шаг 1: Добавляем поле region_id в таблицу user_domains (временно nullable)
        print("Adding region_id column to user_domains...")
        op.add_column(
            "user_domains",
            sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

        # Шаг 2: Добавляем внешний ключ на yandex_regions
        print("Adding foreign key constraint...")
        op.create_foreign_key(
            "fk_user_domains_region_id",
            "user_domains",
            "yandex_regions",
            ["region_id"],
            ["id"],
        )

        # Шаг 3: Заполняем region_id в user_domains на основе данных из user_keywords
        print("Migrating region data from keywords to domains...")

        # Находим регион для каждого домена на основе его ключевых слов
        # Если у домена есть ключевые слова с разными регионами, берем самый популярный
        migrate_regions_query = text(
            """
                                     UPDATE user_domains
                                     SET region_id = domain_regions.most_common_region_id
                                     FROM (
                                              SELECT
                                                  uk.domain_id,
                                                  uk.region_id as most_common_region_id,
                                                  ROW_NUMBER() OVER (
                                                      PARTITION BY uk.domain_id
                                                      ORDER BY COUNT(*) DESC, uk.created_at ASC
                                                      ) as rn
                                              FROM user_keywords uk
                                              WHERE uk.region_id IS NOT NULL
                                              GROUP BY uk.domain_id, uk.region_id, uk.created_at
                                          ) domain_regions
                                     WHERE user_domains.id = domain_regions.domain_id
                                       AND domain_regions.rn = 1
                                     """
        )

        connection.execute(migrate_regions_query)

        # Шаг 4: Для доменов без ключевых слов или с ключевыми словами без региона
        # устанавливаем регион по умолчанию (Москва - 213)
        print("Setting default region for domains without keywords...")

        # Находим ID региона Москвы (код 213)
        moscow_region_query = text(
            """
                                   SELECT id FROM yandex_regions
                                   WHERE region_code = '213'
                                   LIMIT 1
                                   """
        )

        result = connection.execute(moscow_region_query)
        moscow_region_id = result.scalar()

        if moscow_region_id:
            default_region_query = text(
                """
                                        UPDATE user_domains
                                        SET region_id = :region_id
                                        WHERE region_id IS NULL
                                        """
            )

            connection.execute(default_region_query, {"region_id": moscow_region_id})
        else:
            # Если региона с кодом 213 нет, создаем его
            print("Creating default Moscow region...")
            create_moscow_query = text(
                """
                                       INSERT INTO yandex_regions (id, region_code, region_name, country_code, region_type, is_active)
                                       VALUES (:id, '213', 'Москва', 'RU', 'city', true)
                                       """
            )

            moscow_id = str(uuid.uuid4())
            connection.execute(create_moscow_query, {"id": moscow_id})

            # Теперь устанавливаем этот регион для доменов без региона
            connection.execute(default_region_query, {"region_id": moscow_id})

        # Шаг 5: Делаем поле region_id обязательным в user_domains
        print("Making region_id NOT NULL in user_domains...")
        op.alter_column("user_domains", "region_id", nullable=False)

        # Шаг 6: Создаем индекс для улучшения производительности
        print("Creating index on user_domains.region_id...")
        if not index_exists(connection, "ix_user_domains_region_id"):
            op.create_index("ix_user_domains_region_id", "user_domains", ["region_id"])

    # Проверяем, есть ли еще region_id в user_keywords
    if not column_exists(connection, "user_keywords", "region_id"):
        print("user_keywords.region_id already removed. Skipping removal steps...")
        return

    # Шаг 7: Удаляем поле region_id из user_keywords
    print("Removing region_id from user_keywords...")

    # Сначала получаем все внешние ключи для user_keywords
    print("Checking foreign key constraints for user_keywords...")
    fk_constraints = get_foreign_key_constraints(connection, "user_keywords")

    # Ищем constraint, который ссылается на region_id
    region_fk_constraint = None
    for constraint in fk_constraints:
        if constraint.column_name == "region_id":
            region_fk_constraint = constraint.constraint_name
            break

    if region_fk_constraint:
        print(f"Found region FK constraint: {region_fk_constraint}")
        try:
            op.drop_constraint(
                region_fk_constraint, "user_keywords", type_="foreignkey"
            )
            print(f"Dropped FK constraint: {region_fk_constraint}")
        except Exception as e:
            print(f"Warning: Could not drop FK constraint {region_fk_constraint}: {e}")
    else:
        print("No foreign key constraint found for region_id in user_keywords")

    # Пытаемся удалить различные возможные имена индексов
    possible_indexes = [
        "ix_user_keywords_region_id",
        "user_keywords_region_id_idx",
        "idx_user_keywords_region_id",
    ]

    for index_name in possible_indexes:
        if index_exists(connection, index_name):
            try:
                op.drop_index(index_name, table_name="user_keywords")
                print(f"Dropped index: {index_name}")
                break
            except Exception as e:
                print(f"Warning: Could not drop index {index_name}: {e}")

    # Удаляем саму колонку
    print("Dropping region_id column from user_keywords...")
    op.drop_column("user_keywords", "region_id")

    # Шаг 8: Обновляем уникальные ограничения в user_keywords
    print("Updating unique constraints in user_keywords...")

    # Получаем все unique constraints для user_keywords
    unique_constraints_query = text(
        """
                                    SELECT constraint_name
                                    FROM information_schema.table_constraints
                                    WHERE table_name = 'user_keywords'
                                      AND constraint_type = 'UNIQUE'
                                    """
    )

    unique_constraints = connection.execute(unique_constraints_query).fetchall()

    # Удаляем старые ограничения, которые могут включать region_id
    for constraint in unique_constraints:
        constraint_name = constraint.constraint_name
        if "region" in constraint_name.lower():
            try:
                op.drop_constraint(constraint_name, "user_keywords", type_="unique")
                print(f"Dropped unique constraint: {constraint_name}")
            except Exception as e:
                print(
                    f"Warning: Could not drop unique constraint {constraint_name}: {e}"
                )

    # Создаем новое ограничение без region_id
    print("Creating new unique constraint...")
    try:
        op.create_unique_constraint(
            "uq_user_keywords_user_domain_keyword_device",
            "user_keywords",
            ["user_id", "domain_id", "keyword", "device_type"],
        )
        print("Created new unique constraint successfully")
    except Exception as e:
        print(f"Warning: Could not create new unique constraint: {e}")

    print("Migration completed successfully!")


def downgrade():
    """Откатывает миграцию: возвращает region_id обратно в user_keywords"""

    print("Rolling back migration...")
    connection = op.get_bind()

    # Проверяем текущее состояние
    if column_exists(connection, "user_keywords", "region_id"):
        print("user_keywords already has region_id column. Skipping downgrade...")
        return

    # Шаг 1: Добавляем поле region_id обратно в user_keywords
    print("Adding region_id back to user_keywords...")
    op.add_column(
        "user_keywords",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Шаг 2: Восстанавливаем внешний ключ
    print("Restoring foreign key constraint...")
    op.create_foreign_key(
        "fk_user_keywords_region_id",
        "user_keywords",
        "yandex_regions",
        ["region_id"],
        ["id"],
    )

    # Шаг 3: Заполняем region_id в user_keywords на основе данных из user_domains
    print("Migrating region data from domains back to keywords...")

    migrate_back_query = text(
        """
                              UPDATE user_keywords
                              SET region_id = ud.region_id
                              FROM user_domains ud
                              WHERE user_keywords.domain_id = ud.id
                              """
    )

    connection.execute(migrate_back_query)

    # Шаг 4: Делаем поле region_id обязательным в user_keywords
    print("Making region_id NOT NULL in user_keywords...")
    op.alter_column("user_keywords", "region_id", nullable=False)

    # Шаг 5: Восстанавливаем индекс
    print("Recreating index on user_keywords.region_id...")
    if not index_exists(connection, "ix_user_keywords_region_id"):
        op.create_index("ix_user_keywords_region_id", "user_keywords", ["region_id"])

    # Шаг 6: Восстанавливаем старые ограничения
    print("Restoring old unique constraints...")

    # Удаляем новое ограничение
    try:
        op.drop_constraint(
            "uq_user_keywords_user_domain_keyword_device",
            "user_keywords",
            type_="unique",
        )
    except Exception as e:
        print(f"Warning: Could not drop new unique constraint: {e}")

    # Восстанавливаем старое ограничение
    try:
        op.create_unique_constraint(
            "uq_user_keywords_user_domain_keyword_region_device",
            "user_keywords",
            ["user_id", "domain_id", "keyword", "region_id", "device_type"],
        )
    except Exception as e:
        print(f"Warning: Could not create old unique constraint: {e}")

    # Шаг 7: Удаляем поле region_id из user_domains
    print("Removing region_id from user_domains...")

    # Удаляем внешний ключ
    try:
        op.drop_constraint(
            "fk_user_domains_region_id", "user_domains", type_="foreignkey"
        )
    except Exception as e:
        print(f"Warning: Could not drop FK constraint: {e}")

    # Удаляем индекс
    if index_exists(connection, "ix_user_domains_region_id"):
        try:
            op.drop_index("ix_user_domains_region_id", table_name="user_domains")
        except Exception as e:
            print(f"Warning: Could not drop index: {e}")

    # Удаляем колонку
    op.drop_column("user_domains", "region_id")

    print("Rollback completed successfully!")


def cleanup_failed_migration():
    """Очищает следы неудачной миграции"""

    print("Cleaning up failed migration...")
    connection = op.get_bind()

    # Если user_domains уже имеет region_id, но user_keywords все еще имеет region_id,
    # то миграция была прервана посередине
    domains_has_region = column_exists(connection, "user_domains", "region_id")
    keywords_has_region = column_exists(connection, "user_keywords", "region_id")

    if domains_has_region and keywords_has_region:
        print("Detected partial migration. Cleaning up...")

        # Удаляем region_id из user_domains чтобы начать заново
        try:
            op.drop_constraint(
                "fk_user_domains_region_id", "user_domains", type_="foreignkey"
            )
        except Exception:
            pass

        try:
            op.drop_index("ix_user_domains_region_id", table_name="user_domains")
        except Exception:
            pass

        try:
            op.drop_column("user_domains", "region_id")
            print("Cleaned up user_domains.region_id")
        except Exception as e:
            print(f"Could not clean up user_domains.region_id: {e}")

    print("Cleanup completed.")


# Дополнительная функция для диагностики
def diagnose_database_state():
    """Диагностирует текущее состояние базы данных"""

    connection = op.get_bind()

    print("=== Database State Diagnosis ===")

    # Проверяем колонки
    domains_has_region = column_exists(connection, "user_domains", "region_id")
    keywords_has_region = column_exists(connection, "user_keywords", "region_id")

    print(f"user_domains.region_id exists: {domains_has_region}")
    print(f"user_keywords.region_id exists: {keywords_has_region}")

    # Проверяем внешние ключи
    domains_fks = get_foreign_key_constraints(connection, "user_domains")
    keywords_fks = get_foreign_key_constraints(connection, "user_keywords")

    print(f"user_domains foreign keys: {[fk.constraint_name for fk in domains_fks]}")
    print(f"user_keywords foreign keys: {[fk.constraint_name for fk in keywords_fks]}")

    # Проверяем индексы
    domains_indexes = connection.execute(
        text(
            """
                                              SELECT indexname FROM pg_indexes WHERE tablename = 'user_domains'
                                              """
        )
    ).fetchall()

    keywords_indexes = connection.execute(
        text(
            """
                                               SELECT indexname FROM pg_indexes WHERE tablename = 'user_keywords'
                                               """
        )
    ).fetchall()

    print(f"user_domains indexes: {[idx.indexname for idx in domains_indexes]}")
    print(f"user_keywords indexes: {[idx.indexname for idx in keywords_indexes]}")

    print("=== End Diagnosis ===")
