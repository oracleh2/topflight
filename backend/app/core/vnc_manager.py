# backend/app/core/vnc_manager.py - СОЗДАТЬ ФАЙЛ для заглушки:

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog
import random

from app.models.profile import DeviceType

logger = structlog.get_logger(__name__)


class VNCSession:
    """Класс для представления VNC сессии"""

    def __init__(self, task_id: str, device_type: DeviceType):
        self.task_id = task_id
        self.device_type = device_type
        self.display_num = random.randint(100, 999)
        self.vnc_port = 5900 + (self.display_num - 100)
        self.vnc_host = "localhost"
        self.resolution = self._get_resolution_for_device(device_type)
        self.created_at = datetime.now(timezone.utc)
        self.browser_pid = None
        self.status = "active"

    def _get_resolution_for_device(self, device_type: DeviceType) -> str:
        """Получает разрешение для типа устройства"""
        if device_type == DeviceType.MOBILE:
            return "800x1200"
        else:
            return "1920x1080"

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует сессию в словарь"""
        return {
            "task_id": self.task_id,
            "device_type": self.device_type.value,
            "display_num": self.display_num,
            "vnc_port": self.vnc_port,
            "vnc_host": self.vnc_host,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
            "browser_pid": self.browser_pid,
            "status": self.status,
        }


class VNCManager:
    """Менеджер VNC сессий (заглушка для тестирования)"""

    def __init__(self):
        self.active_sessions: Dict[str, VNCSession] = {}

    async def create_debug_session(
        self, task_id: str, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Создает debug сессию (заглушка)"""
        try:
            logger.info(f"Creating debug session for task {task_id}")

            # Создаем VNC сессию
            vnc_session = VNCSession(task_id, device_type)
            self.active_sessions[task_id] = vnc_session

            logger.info(
                "Debug session created",
                task_id=task_id,
                vnc_port=vnc_session.vnc_port,
                display_num=vnc_session.display_num,
            )

            return {
                "success": True,
                "task_id": task_id,
                "vnc_port": vnc_session.vnc_port,
                "vnc_host": vnc_session.vnc_host,
                "display_num": vnc_session.display_num,
                "resolution": vnc_session.resolution,
                "device_type": device_type.value,
                "status": "active",
                "created_at": vnc_session.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create debug session: {e}")
            raise

    async def stop_debug_session(self, task_id: str) -> bool:
        """Останавливает debug сессию"""
        try:
            if task_id in self.active_sessions:
                vnc_session = self.active_sessions[task_id]
                vnc_session.status = "stopped"
                del self.active_sessions[task_id]

                logger.info(f"Debug session stopped for task {task_id}")
                return True
            else:
                logger.warning(f"No active debug session found for task {task_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to stop debug session: {e}")
            return False

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Получает список активных сессий"""
        return [session.to_dict() for session in self.active_sessions.values()]

    async def cleanup_inactive_sessions(self):
        """Очищает неактивные сессии"""
        # Заглушка - в реальной реализации здесь будет логика очистки
        pass

    def get_session_by_task(self, task_id: str) -> Optional[VNCSession]:
        """Получает сессию по ID задачи"""
        return self.active_sessions.get(task_id)


# Создаем глобальный экземпляр менеджера
vnc_manager = VNCManager()
