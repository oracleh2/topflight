# backend/app/db_init.py
import asyncio
import os
import socket
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import async_session_maker
from app.models import (
    Region,
    TariffPlan,
    SystemConfig,
    ServerConfig,
    BackupSchedule,
    CacheSettings,
)


async def init_database():
    """Инициализация базы данных базовыми данными"""
    async with async_session_maker() as session:
        try:
            # Создаем базовые регионы
            regions = [
                Region(region_code="213", region_name="Москва", country_code="RU"),
                Region(
                    region_code="2", region_name="Санкт-Петербург", country_code="RU"
                ),
                Region(region_code="54", region_name="Екатеринбург", country_code="RU"),
                Region(region_code="65", region_name="Новосибирск", country_code="RU"),
                Region(region_code="35", region_name="Краснодар", country_code="RU"),
                Region(region_code="172", region_name="Воронеж", country_code="RU"),
            ]

            for region in regions:
                session.add(region)

            # Создаем базовые тарифные планы
            tariffs = [
                TariffPlan(
                    name="Базовый",
                    description="Базовый тариф для начинающих",
                    cost_per_check=1.00,
                    min_monthly_topup=0.00,
                    server_binding_allowed=False,
                    priority_level=0,
                ),
                TariffPlan(
                    name="Премиум",
                    description="Премиум тариф с дополнительными возможностями",
                    cost_per_check=0.80,
                    min_monthly_topup=20000.00,
                    server_binding_allowed=True,
                    priority_level=10,
                ),
            ]

            for tariff in tariffs:
                session.add(tariff)

            # Системные настройки
            system_configs = [
                SystemConfig(
                    config_key="logs_retention_days",
                    config_value="30",
                    description="Количество дней хранения логов",
                ),
                SystemConfig(
                    config_key="metrics_collection_interval",
                    config_value="300",
                    description="Интервал сбора метрик в секундах",
                ),
                SystemConfig(
                    config_key="database_backup_interval",
                    config_value="21600",
                    description="Интервал бэкапа БД в секундах (6 часов)",
                ),
                SystemConfig(
                    config_key="backup_retention_days",
                    config_value="30",
                    description="Количество дней хранения бэкапов",
                ),
            ]

            for config in system_configs:
                session.add(config)

            # Конфигурация сервера
            hostname = socket.gethostname()
            server_config = ServerConfig(
                server_id=f"server-{hostname}",
                hostname=hostname,
                warm_desktop_profiles_target=200,  # Задаем целевое количество desktop профилей
                warm_mobile_profiles_target=800,  # Задаем целевое количество mobile профилей
                # warm_profiles_target=1000,
                max_cpu_percent=75,
                max_ram_percent=70,
                spawn_queue_threshold=50,
                spawn_check_interval=180,
                profile_health_check_interval=1800,
                auto_scaling_enabled=True,
                auto_worker_spawn=True,
                max_workers_limit=16,
            )
            session.add(server_config)

            # Настройки бэкапов
            backup_schedules = [
                BackupSchedule(
                    backup_type="full",
                    schedule_cron="0 */6 * * *",  # каждые 6 часов
                    retention_days=30,
                    storage_path="/backup/full",
                    is_enabled=True,
                ),
                BackupSchedule(
                    backup_type="incremental",
                    schedule_cron="0 * * * *",  # каждый час
                    retention_days=7,
                    storage_path="/backup/incremental",
                    is_enabled=True,
                ),
            ]

            for schedule in backup_schedules:
                session.add(schedule)

            # Настройки кэширования
            cache_settings = [
                CacheSettings(
                    cache_key="serp_results",
                    cache_type="serp",
                    ttl_seconds=3600,
                    is_enabled=True,
                ),
                CacheSettings(
                    cache_key="user_stats",
                    cache_type="stats",
                    ttl_seconds=1800,
                    is_enabled=True,
                ),
                CacheSettings(
                    cache_key="system_config",
                    cache_type="config",
                    ttl_seconds=600,
                    is_enabled=True,
                ),
            ]

            for setting in cache_settings:
                session.add(setting)

            await session.commit()
            print("База данных успешно инициализирована!")

        except Exception as e:
            await session.rollback()
            print(f"Ошибка инициализации базы данных: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(init_database())
