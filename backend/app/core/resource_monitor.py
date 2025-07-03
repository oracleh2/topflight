import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PerformanceMetrics, ServerConfig
from app.database import async_session_maker
import structlog

logger = structlog.get_logger(__name__)


class ResourceMonitor:
    """Мониторинг ресурсов сервера для автомасштабирования"""

    def __init__(self, server_id: str):
        self.server_id = server_id
        self.running = False

    async def start_monitoring(self):
        """Запуск мониторинга ресурсов"""
        self.running = True

        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(60)  # Собираем метрики каждую минуту
            except Exception as e:
                logger.error("Error in resource monitoring", error=str(e))
                await asyncio.sleep(5)

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False

    async def _collect_metrics(self):
        """Сбор метрик производительности"""
        async with async_session_maker() as session:
            try:
                # CPU метрики
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()

                # RAM метрики
                memory = psutil.virtual_memory()
                ram_percent = memory.percent
                ram_available_gb = memory.available / (1024 ** 3)

                # Disk метрики
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent

                # Network метрики (базовые)
                network = psutil.net_io_counters()

                # Сохраняем метрики
                metrics_data = [
                    PerformanceMetrics(
                        server_id=self.server_id,
                        metric_type="cpu_percent",
                        value=cpu_percent,
                        details={"cpu_count": cpu_count}
                    ),
                    PerformanceMetrics(
                        server_id=self.server_id,
                        metric_type="ram_percent",
                        value=ram_percent,
                        details={"available_gb": ram_available_gb}
                    ),
                    PerformanceMetrics(
                        server_id=self.server_id,
                        metric_type="disk_percent",
                        value=disk_percent,
                        details={"free_gb": disk.free / (1024 ** 3)}
                    )
                ]

                for metric in metrics_data:
                    session.add(metric)

                await session.commit()

                # Проверяем нужно ли масштабирование
                await self._check_scaling_needs(session, cpu_percent, ram_percent)

            except Exception as e:
                logger.error("Failed to collect metrics", error=str(e))

    async def _check_scaling_needs(self, session: AsyncSession,
                                   cpu_percent: float, ram_percent: float):
        """Проверяет необходимость масштабирования"""
        try:
            # Получаем конфигурацию сервера
            result = await session.execute(
                select(ServerConfig).where(ServerConfig.server_id == self.server_id)
            )
            config = result.scalar_one_or_none()

            if not config or not config.auto_scaling_enabled:
                return

            # Проверяем превышение лимитов
            cpu_overload = cpu_percent > config.max_cpu_percent
            ram_overload = ram_percent > config.max_ram_percent

            if cpu_overload or ram_overload:
                logger.warning("Resource overload detected",
                               cpu_percent=cpu_percent,
                               ram_percent=ram_percent,
                               cpu_limit=config.max_cpu_percent,
                               ram_limit=config.max_ram_percent)

                # Здесь можно добавить логику уведомлений админа
                # или автоматического снижения нагрузки

        except Exception as e:
            logger.error("Failed to check scaling needs", error=str(e))

    async def get_current_load(self) -> Dict[str, Any]:
        """Получает текущую загрузку системы"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }

    async def can_handle_more_tasks(self) -> bool:
        """Проверяет может ли система взять больше задач"""
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    select(ServerConfig).where(ServerConfig.server_id == self.server_id)
                )
                config = result.scalar_one_or_none()

                if not config:
                    return True  # По умолчанию разрешаем

                current_load = await self.get_current_load()

                return (
                        current_load["cpu_percent"] < config.max_cpu_percent and
                        current_load["ram_percent"] < config.max_ram_percent
                )

            except Exception as e:
                logger.error("Failed to check task capacity", error=str(e))
                return False