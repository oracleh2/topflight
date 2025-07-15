# backend/app/core/vnc_cleanup.py
import asyncio
import signal
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import structlog

from .vnc_manager import vnc_manager
from .vnc_metrics import metrics_collector

logger = structlog.get_logger(__name__)


class VNCCleanupService:
    """Сервис автоматической очистки VNC сессий"""

    def __init__(self):
        self.cleanup_interval = 300  # 5 минут
        self.session_timeout = 3600  # 1 час неактивности
        self.max_session_duration = 7200  # 2 часа максимум
        self.is_running = False
        self.cleanup_task = None

    async def start(self):
        """Запускает сервис очистки"""
        if self.is_running:
            logger.warning("VNC cleanup service already running")
            return

        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            "VNC cleanup service started",
            cleanup_interval=self.cleanup_interval,
            session_timeout=self.session_timeout,
        )

    async def stop(self):
        """Останавливает сервис очистки"""
        if not self.is_running:
            return

        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("VNC cleanup service stopped")

    async def _cleanup_loop(self):
        """Основной цикл очистки"""
        while self.is_running:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))
                await asyncio.sleep(60)  # Пауза при ошибке

    async def _perform_cleanup(self):
        """Выполняет очистку устаревших сессий"""
        try:
            sessions_to_cleanup = await self._identify_sessions_for_cleanup()

            if not sessions_to_cleanup:
                return

            logger.info("Starting VNC cleanup", sessions_count=len(sessions_to_cleanup))

            for session_info in sessions_to_cleanup:
                task_id = session_info["task_id"]
                reason = session_info["cleanup_reason"]

                try:
                    success = await vnc_manager.stop_debug_session(task_id)
                    if success:
                        metrics_collector.record_session_terminated(task_id, reason)
                        logger.info(
                            "Session cleaned up", task_id=task_id, reason=reason
                        )
                    else:
                        logger.warning("Failed to cleanup session", task_id=task_id)
                except Exception as e:
                    logger.error(
                        "Error cleaning up session", task_id=task_id, error=str(e)
                    )

            # Обновляем метрики
            active_sessions = await vnc_manager.get_active_sessions()
            metrics_collector.update_active_sessions_count(len(active_sessions))

        except Exception as e:
            logger.error("Error during VNC cleanup", error=str(e))

    async def _identify_sessions_for_cleanup(self) -> List[Dict]:
        """Определяет сессии для очистки"""
        sessions_to_cleanup = []
        current_time = datetime.now(timezone.utc)

        try:
            active_sessions = await vnc_manager.get_active_sessions()

            for session_data in active_sessions:
                task_id = session_data["task_id"]
                created_at = datetime.fromisoformat(
                    session_data["created_at"].replace("Z", "+00:00")
                )

                # Проверяем максимальную продолжительность сессии
                session_age = (current_time - created_at).total_seconds()
                if session_age > self.max_session_duration:
                    sessions_to_cleanup.append(
                        {
                            "task_id": task_id,
                            "cleanup_reason": "max_duration_exceeded",
                            "age_seconds": session_age,
                        }
                    )
                    continue

                # Проверяем активность сессии
                if await self._is_session_inactive(task_id, session_data):
                    sessions_to_cleanup.append(
                        {
                            "task_id": task_id,
                            "cleanup_reason": "timeout",
                            "age_seconds": session_age,
                        }
                    )
                    continue

                # Проверяем состояние процессов
                if await self._is_session_broken(task_id, session_data):
                    sessions_to_cleanup.append(
                        {
                            "task_id": task_id,
                            "cleanup_reason": "broken_process",
                            "age_seconds": session_age,
                        }
                    )

            return sessions_to_cleanup

        except Exception as e:
            logger.error("Error identifying sessions for cleanup", error=str(e))
            return []

    async def _is_session_inactive(self, task_id: str, session_data: Dict) -> bool:
        """Проверяет, неактивна ли сессия"""
        try:
            vnc_session = vnc_manager.get_session_by_task(task_id)
            if not vnc_session:
                return True

            # Проверяем время последней активности
            created_at = datetime.fromisoformat(
                session_data["created_at"].replace("Z", "+00:00")
            )
            inactive_time = (datetime.now(timezone.utc) - created_at).total_seconds()

            return inactive_time > self.session_timeout

        except Exception as e:
            logger.error(
                "Error checking session activity", task_id=task_id, error=str(e)
            )
            return False

    async def _is_session_broken(self, task_id: str, session_data: Dict) -> bool:
        """Проверяет, сломана ли сессия"""
        try:
            vnc_session = vnc_manager.get_session_by_task(task_id)
            if not vnc_session:
                return True

            # Проверяем состояние процессов VNC и Xvfb
            if vnc_session.vnc_process:
                if vnc_session.vnc_process.returncode is not None:
                    logger.warning(
                        "VNC process died",
                        task_id=task_id,
                        returncode=vnc_session.vnc_process.returncode,
                    )
                    return True

            if vnc_session.xvfb_process:
                if vnc_session.xvfb_process.returncode is not None:
                    logger.warning(
                        "Xvfb process died",
                        task_id=task_id,
                        returncode=vnc_session.xvfb_process.returncode,
                    )
                    return True

            return False

        except Exception as e:
            logger.error("Error checking session health", task_id=task_id, error=str(e))
            return False

    async def cleanup_all_sessions(self, reason: str = "manual_cleanup"):
        """Принудительная очистка всех сессий"""
        try:
            active_sessions = await vnc_manager.get_active_sessions()
            logger.info(
                "Force cleaning all VNC sessions",
                count=len(active_sessions),
                reason=reason,
            )

            for session_data in active_sessions:
                task_id = session_data["task_id"]
                try:
                    await vnc_manager.stop_debug_session(task_id)
                    metrics_collector.record_session_terminated(task_id, reason)
                except Exception as e:
                    logger.error(
                        "Error force cleaning session", task_id=task_id, error=str(e)
                    )

            logger.info("Force cleanup completed")

        except Exception as e:
            logger.error("Error during force cleanup", error=str(e))


# Глобальный сервис очистки
cleanup_service = VNCCleanupService()


# Graceful shutdown handler
async def graceful_shutdown():
    """Graceful shutdown для VNC сессий"""
    logger.info("Starting graceful VNC shutdown")
    await cleanup_service.cleanup_all_sessions("shutdown")
    await cleanup_service.stop()
    logger.info("VNC graceful shutdown completed")


# Регистрируем обработчики сигналов
def setup_signal_handlers():
    """Настраивает обработчики сигналов для graceful shutdown"""

    def signal_handler(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(graceful_shutdown())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
