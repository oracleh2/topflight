import asyncio
import signal
import sys
from app.core.task_manager import TaskManager
from app.core.resource_monitor import ResourceMonitor
from app.database import async_session_maker
import structlog

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class Worker:
    def __init__(self):
        self.task_manager = None
        self.resource_monitor = None
        self.running = False

    async def start(self):
        """Запуск worker'а"""
        try:
            logger.info("Starting worker...")

            # Инициализируем компоненты
            async with async_session_maker() as session:
                self.task_manager = TaskManager(session)
                await self.task_manager.initialize()

            self.resource_monitor = ResourceMonitor(self.task_manager.server_id)

            # Настраиваем обработку сигналов
            self._setup_signal_handlers()

            self.running = True

            # Запускаем компоненты
            await asyncio.gather(
                self.task_manager.start(),
                self.resource_monitor.start_monitoring(),
                return_exceptions=True
            )

        except Exception as e:
            logger.error("Failed to start worker", error=str(e))
            sys.exit(1)

    async def stop(self):
        """Остановка worker'а"""
        if not self.running:
            return

        logger.info("Stopping worker...")
        self.running = False

        # Останавливаем компоненты
        if self.task_manager:
            await self.task_manager.stop()

        if self.resource_monitor:
            await self.resource_monitor.stop_monitoring()

        logger.info("Worker stopped")

    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""

        def signal_handler(signum, frame):
            logger.info("Received signal", signal=signum)
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    worker = Worker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())