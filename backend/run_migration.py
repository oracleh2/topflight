#!/usr/bin/env python3
"""
Скрипт для безопасного запуска миграции переноса региона из ключевых слов в домены
Использование: python run_migration.py [--dry-run] [--backup]
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    def __init__(self, db_url=None):
        """Инициализация с подключением к базе данных"""
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.conn = None
        self.backup_file = None

    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = False
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Отключение от базы данных"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def create_backup(self):
        """Создание резервной копии базы данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_file = f"backup_before_region_migration_{timestamp}.sql"

        try:
            logger.info(f"Creating backup: {self.backup_file}")

            # Извлекаем параметры подключения из DATABASE_URL
            from urllib.parse import urlparse

            parsed = urlparse(self.db_url)

            cmd = [
                "pg_dump",
                "-h",
                parsed.hostname,
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username,
                "-d",
                parsed.path[1:],  # Убираем первый слэш
                "-f",
                self.backup_file,
                "--verbose",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = parsed.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                raise Exception(f"Backup failed: {result.stderr}")

            logger.info(f"Backup created successfully: {self.backup_file}")
            return self.backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def get_migration_stats(self):
        """Получение статистики данных для миграции"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Количество доменов
                cur.execute("SELECT COUNT(*) as count FROM user_domains")
                domains_count = cur.fetchone()["count"]

                # Количество ключевых слов
                cur.execute("SELECT COUNT(*) as count FROM user_keywords")
                keywords_count = cur.fetchone()["count"]

                # Количество уникальных регионов в ключевых словах
                cur.execute(
                    """
                            SELECT COUNT(DISTINCT region_id) as count
                            FROM user_keywords
                            WHERE region_id IS NOT NULL
                            """
                )
                unique_regions = cur.fetchone()["count"]

                # Домены с конфликтующими регионами
                cur.execute(
                    """
                            SELECT COUNT(DISTINCT domain_id) as count
                            FROM (
                                     SELECT domain_id, COUNT(DISTINCT region_id) as region_count
                                     FROM user_keywords
                                     WHERE region_id IS NOT NULL
                                     GROUP BY domain_id
                                     HAVING COUNT(DISTINCT region_id) > 1
                                 ) conflicts
                            """
                )
                conflicting_domains = cur.fetchone()["count"]

                # Домены без ключевых слов
                cur.execute(
                    """
                            SELECT COUNT(*) as count
                            FROM user_domains ud
                                     LEFT JOIN user_keywords uk ON ud.id = uk.domain_id
                            WHERE uk.id IS NULL
                            """
                )
                domains_without_keywords = cur.fetchone()["count"]

                stats = {
                    "domains_count": domains_count,
                    "keywords_count": keywords_count,
                    "unique_regions": unique_regions,
                    "conflicting_domains": conflicting_domains,
                    "domains_without_keywords": domains_without_keywords,
                }

                logger.info("Migration statistics:")
                logger.info(f"- Total domains: {domains_count}")
                logger.info(f"- Total keywords: {keywords_count}")
                logger.info(f"- Unique regions in keywords: {unique_regions}")
                logger.info(
                    f"- Domains with conflicting regions: {conflicting_domains}"
                )
                logger.info(f"- Domains without keywords: {domains_without_keywords}")

                return stats

        except Exception as e:
            logger.error(f"Failed to get migration stats: {e}")
            raise

    def check_prerequisites(self):
        """Проверка предварительных условий для миграции"""
        logger.info("Checking prerequisites...")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Проверяем существование таблиц
                tables_to_check = ["user_domains", "user_keywords", "yandex_regions"]
                for table in tables_to_check:
                    cur.execute(
                        """
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = %s
                                )
                                """,
                        (table,),
                    )

                    if not cur.fetchone()["exists"]:
                        raise Exception(f"Required table '{table}' does not exist")

                # Проверяем, что у user_domains еще нет поля region_id
                cur.execute(
                    """
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'user_domains' AND column_name = 'region_id'
                            )
                            """
                )

                if cur.fetchone()["exists"]:
                    raise Exception(
                        "user_domains already has region_id column. Migration may have been run already."
                    )

                # Проверяем, что у user_keywords есть поле region_id
                cur.execute(
                    """
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'user_keywords' AND column_name = 'region_id'
                            )
                            """
                )

                if not cur.fetchone()["exists"]:
                    raise Exception(
                        "user_keywords does not have region_id column. Invalid starting state."
                    )

                # Проверяем, что есть хотя бы один регион в yandex_regions
                cur.execute("SELECT COUNT(*) as count FROM yandex_regions")
                regions_count = cur.fetchone()["count"]

                if regions_count == 0:
                    logger.warning(
                        "No regions found in yandex_regions table. Default region will be created."
                    )

                logger.info("Prerequisites check passed!")

        except Exception as e:
            logger.error(f"Prerequisites check failed: {e}")
            raise

    def run_dry_run(self):
        """Выполняет пробный запуск миграции без изменения данных"""
        logger.info("Running dry run...")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Показываем, какие регионы будут назначены каждому домену
                cur.execute(
                    """
                            SELECT
                                ud.domain,
                                ud.id as domain_id,
                                COALESCE(domain_regions.most_common_region_id, 'DEFAULT') as assigned_region_id,
                                COALESCE(yr.region_name, 'Moscow (default)') as region_name,
                                COALESCE(domain_regions.keywords_count, 0) as keywords_count,
                                COALESCE(domain_regions.conflicting_regions, 0) as conflicting_regions
                            FROM user_domains ud
                                     LEFT JOIN (
                                SELECT
                                    uk.domain_id,
                                    uk.region_id as most_common_region_id,
                                    COUNT(*) as keywords_count,
                                    COUNT(DISTINCT uk.region_id) as conflicting_regions,
                                    ROW_NUMBER() OVER (
                                        PARTITION BY uk.domain_id
                                        ORDER BY COUNT(*) DESC, uk.created_at ASC
                                        ) as rn
                                FROM user_keywords uk
                                WHERE uk.region_id IS NOT NULL
                                GROUP BY uk.domain_id, uk.region_id, uk.created_at
                            ) domain_regions ON ud.id = domain_regions.domain_id AND domain_regions.rn = 1
                                     LEFT JOIN yandex_regions yr ON domain_regions.most_common_region_id = yr.id
                            ORDER BY ud.domain
                            """
                )

                results = cur.fetchall()

                logger.info("Dry run results:")
                logger.info("-" * 80)
                logger.info(
                    f"{'Domain':<30} {'Region':<20} {'Keywords':<10} {'Conflicts':<10}"
                )
                logger.info("-" * 80)

                for row in results:
                    logger.info(
                        f"{row['domain']:<30} {row['region_name']:<20} {row['keywords_count']:<10} {row['conflicting_regions']:<10}"
                    )

                # Статистика конфликтов
                conflicts = [r for r in results if r["conflicting_regions"] > 1]
                if conflicts:
                    logger.warning(
                        f"Found {len(conflicts)} domains with conflicting regions:"
                    )
                    for conflict in conflicts:
                        logger.warning(
                            f"  - {conflict['domain']}: {conflict['conflicting_regions']} different regions"
                        )

                logger.info("Dry run completed successfully!")

        except Exception as e:
            logger.error(f"Dry run failed: {e}")
            raise

    def run_migration(self):
        """Запускает миграцию с помощью Alembic"""
        logger.info("Running Alembic migration...")

        try:
            # Запускаем миграцию Alembic
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

            if result.returncode != 0:
                logger.error(f"Alembic migration failed: {result.stderr}")
                raise Exception(f"Alembic migration failed: {result.stderr}")

            logger.info("Alembic migration completed successfully!")
            logger.info(f"Alembic output: {result.stdout}")

        except Exception as e:
            logger.error(f"Failed to run Alembic migration: {e}")
            raise

    def verify_migration(self):
        """Проверяет результаты миграции"""
        logger.info("Verifying migration results...")

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Проверяем, что все домены имеют region_id
                cur.execute(
                    "SELECT COUNT(*) as count FROM user_domains WHERE region_id IS NULL"
                )
                domains_without_region = cur.fetchone()["count"]

                if domains_without_region > 0:
                    raise Exception(
                        f"Found {domains_without_region} domains without region_id"
                    )

                # Проверяем, что у user_keywords больше нет region_id
                cur.execute(
                    """
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'user_keywords' AND column_name = 'region_id'
                            )
                            """
                )

                if cur.fetchone()["exists"]:
                    raise Exception("user_keywords still has region_id column")

                # Проверяем количество доменов до и после
                cur.execute("SELECT COUNT(*) as count FROM user_domains")
                domains_after = cur.fetchone()["count"]

                logger.info(f"Verification passed!")
                logger.info(f"All {domains_after} domains have region_id")
                logger.info(f"user_keywords.region_id column successfully removed")

        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            raise


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Run region migration")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run dry run without making changes"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before migration"
    )
    parser.add_argument(
        "--db-url", help="Database URL (default: from DATABASE_URL env var)"
    )

    args = parser.parse_args()

    try:
        runner = MigrationRunner(args.db_url)
        runner.connect()

        # Получаем статистику
        runner.get_migration_stats()

        # Проверяем предварительные условия
        runner.check_prerequisites()

        if args.dry_run:
            # Только пробный запуск
            runner.run_dry_run()
        else:
            # Создаем резервную копию если нужно
            if args.backup:
                runner.create_backup()

            # Запускаем миграцию
            runner.run_migration()

            # Проверяем результаты
            runner.verify_migration()

            logger.info("Migration completed successfully!")

            if runner.backup_file:
                logger.info(f"Backup file: {runner.backup_file}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

    finally:
        runner.disconnect()


if __name__ == "__main__":
    main()
