# backend/app/core/vnc_cleanup_daemon.py
"""
Демон для автоматической очистки VNC сессий TopFlight
Запускается как systemd сервис или через Docker
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from datetime import datetime, timezone
import structlog

# Добавляем путь проекта
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/var/www/topflight"))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.vnc_cleanup import cleanup_service
from app.core.vnc_metrics import metrics_collector

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class VNCCleanupDaemon:
    """Демон очистки VNC сессий"""

    def __init__(self):
        self.running = False
        self.project_root = PROJECT_ROOT
        self.log_file = self.project_root / "logs" / "vnc_cleanup_daemon.log"

        # Создаем директорию логов если не существует
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Настройки из переменных окружения
        self.cleanup_interval = int(os.getenv("VNC_CLEANUP_INTERVAL", "300"))  # 5 минут
        self.session_timeout = int(os.getenv("VNC_SESSION_TIMEOUT", "3600"))  # 1 час

    async def start(self):
        """Запуск демона"""
        try:
            logger.info(
                "Starting TopFlight VNC Cleanup Daemon",
                project_root=str(self.project_root),
                cleanup_interval=self.cleanup_interval,
                session_timeout=self.session_timeout,
            )

            self.running = True

            # Настраиваем обработчики сигналов
            self._setup_signal_handlers()

            # Запускаем cleanup сервис
            cleanup_service.cleanup_interval = self.cleanup_interval
            cleanup_service.session_timeout = self.session_timeout

            await cleanup_service.start()

            # Основной цикл демона
            while self.running:
                try:
                    await asyncio.sleep(10)  # Короткий сон для проверки сигналов
                except asyncio.CancelledError:
                    break

        except Exception as e:
            logger.error("VNC Cleanup Daemon failed", error=str(e))
            sys.exit(1)

    async def stop(self):
        """Остановка демона"""
        if not self.running:
            return

        logger.info("Stopping TopFlight VNC Cleanup Daemon")
        self.running = False

        # Останавливаем cleanup сервис
        await cleanup_service.stop()

        logger.info("VNC Cleanup Daemon stopped")

    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


async def main():
    """Главная функция демона"""
    daemon = VNCCleanupDaemon()

    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error("Daemon crashed", error=str(e))
        sys.exit(1)
    finally:
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
