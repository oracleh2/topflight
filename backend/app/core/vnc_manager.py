# backend/app/core/vnc_manager.py
import asyncio
import os
import signal
import socket
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

# Исправляем импорт под вашу структуру
from app.models import DeviceType

logger = structlog.get_logger(__name__)


@dataclass
class VNCSession:
    """Класс для хранения информации о VNC сессии"""

    task_id: str
    display_num: int
    vnc_port: int
    vnc_host: str
    resolution: str
    device_type: DeviceType
    xvfb_process: Optional[asyncio.subprocess.Process]
    vnc_process: Optional[asyncio.subprocess.Process]
    created_at: datetime
    browser_pid: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "display_num": self.display_num,
            "vnc_port": self.vnc_port,
            "vnc_host": self.vnc_host,
            "resolution": self.resolution,
            "device_type": self.device_type.value,
            "created_at": self.created_at.isoformat(),
            "browser_pid": self.browser_pid,
            "vnc_url": f"vnc://{self.vnc_host}:{self.vnc_port}",
            "status": (
                "active"
                if self.vnc_process and self.vnc_process.returncode is None
                else "inactive"
            ),
        }


class VNCManager:
    """Менеджер VNC сессий для дебага браузеров"""

    def __init__(self):
        self.active_sessions: Dict[str, VNCSession] = {}  # task_id -> VNCSession
        self.used_displays: set = set()  # Занятые дисплеи
        self.base_display_num = 100  # Начальный номер дисплея для VNC
        self.max_sessions = 10  # Максимум одновременных VNC сессий

    async def create_debug_session(
        self, task_id: str, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Создает новую VNC сессию для отладки задачи"""
        try:
            # Проверяем лимит сессий
            if len(self.active_sessions) >= self.max_sessions:
                raise Exception(f"Достигнут лимит VNC сессий: {self.max_sessions}")

            # Проверяем, что сессия еще не создана
            if task_id in self.active_sessions:
                logger.warning("VNC session already exists", task_id=task_id)
                return self.active_sessions[task_id].to_dict()

            # Получаем свободный дисплей
            display_num = self._get_free_display()
            if display_num is None:
                raise Exception("Нет свободных дисплеев для VNC")

            # Вычисляем разрешение под тип устройства
            resolution = self._get_optimal_vnc_resolution(device_type)

            # Настраиваем VNC порт
            vnc_port = 5900 + (display_num - self.base_display_num)
            vnc_host = "localhost"  # Безопасность: только localhost

            # Создаем конфигурацию дисплея
            display_config = {
                "display_num": display_num,
                "resolution": resolution,
                "vnc_port": vnc_port,
                "vnc_host": vnc_host,
            }

            # Запускаем Xvfb дисплей
            xvfb_process = await self._start_xvfb_display(display_config)

            # Ждем инициализации дисплея
            await asyncio.sleep(2)

            # Запускаем VNC сервер
            vnc_process = await self._start_vnc_server(display_config)

            # Создаем сессию
            session = VNCSession(
                task_id=task_id,
                display_num=display_num,
                vnc_port=vnc_port,
                vnc_host=vnc_host,
                resolution=resolution,
                device_type=device_type,
                xvfb_process=xvfb_process,
                vnc_process=vnc_process,
                created_at=datetime.now(timezone.utc),
            )

            # Сохраняем сессию
            self.active_sessions[task_id] = session
            self.used_displays.add(display_num)

            logger.info(
                "VNC session created",
                task_id=task_id,
                display_num=display_num,
                vnc_port=vnc_port,
                resolution=resolution,
                device_type=device_type.value,
            )

            return session.to_dict()

        except Exception as e:
            logger.error("Failed to create VNC session", task_id=task_id, error=str(e))
            raise

    async def stop_debug_session(self, task_id: str) -> bool:
        """Останавливает VNC сессию"""
        try:
            if task_id not in self.active_sessions:
                logger.warning("VNC session not found", task_id=task_id)
                return False

            session = self.active_sessions[task_id]

            # Останавливаем процессы
            success = True

            # Останавливаем VNC сервер
            if session.vnc_process and session.vnc_process.returncode is None:
                try:
                    session.vnc_process.terminate()
                    await asyncio.wait_for(session.vnc_process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    session.vnc_process.kill()
                    await session.vnc_process.wait()
                except Exception as e:
                    logger.error("Failed to stop VNC process", error=str(e))
                    success = False

            # Останавливаем Xvfb
            if session.xvfb_process and session.xvfb_process.returncode is None:
                try:
                    session.xvfb_process.terminate()
                    await asyncio.wait_for(session.xvfb_process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    session.xvfb_process.kill()
                    await session.xvfb_process.wait()
                except Exception as e:
                    logger.error("Failed to stop Xvfb process", error=str(e))
                    success = False

            # Освобождаем ресурсы
            self.used_displays.discard(session.display_num)
            del self.active_sessions[task_id]

            logger.info("VNC session stopped", task_id=task_id, success=success)
            return success

        except Exception as e:
            logger.error("Failed to stop VNC session", task_id=task_id, error=str(e))
            return False

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Возвращает список активных VNC сессий"""
        sessions = []
        for session in self.active_sessions.values():
            sessions.append(session.to_dict())
        return sessions

    def get_session_by_task(self, task_id: str) -> Optional[VNCSession]:
        """Получает VNC сессию по ID задачи"""
        return self.active_sessions.get(task_id)

    async def cleanup_inactive_sessions(self):
        """Очищает неактивные сессии"""
        inactive_tasks = []

        for task_id, session in self.active_sessions.items():
            # Проверяем процессы
            xvfb_dead = (
                session.xvfb_process and session.xvfb_process.returncode is not None
            )
            vnc_dead = (
                session.vnc_process and session.vnc_process.returncode is not None
            )

            if xvfb_dead or vnc_dead:
                inactive_tasks.append(task_id)

        # Удаляем неактивные сессии
        for task_id in inactive_tasks:
            await self.stop_debug_session(task_id)
            logger.info("Cleaned up inactive VNC session", task_id=task_id)

    def _get_optimal_vnc_resolution(self, device_type: DeviceType) -> str:
        """Вычисляет оптимальное разрешение VNC под тип устройства"""

        # Базовые размеры viewports для устройств
        device_viewports = {
            DeviceType.DESKTOP: {"width": 1366, "height": 768},
            DeviceType.MOBILE: {"width": 375, "height": 667},
            DeviceType.TABLET: {"width": 768, "height": 1024},
        }

        viewport = device_viewports.get(
            device_type, device_viewports[DeviceType.DESKTOP]
        )

        # Добавляем отступы для DevTools и UI браузера
        vnc_width = viewport["width"] + 400  # +400px для DevTools
        vnc_height = viewport["height"] + 200  # +200px для адресной строки

        # Округляем до стандартных размеров
        if vnc_width <= 1024:
            return "1024x768"
        elif vnc_width <= 1366:
            return "1366x768"
        elif vnc_width <= 1920:
            return "1920x1080"
        else:
            return "2560x1440"

    def _get_free_display(self) -> Optional[int]:
        """Находит свободный номер дисплея"""
        for display_num in range(self.base_display_num, self.base_display_num + 50):
            if display_num not in self.used_displays:
                # Дополнительно проверяем, что дисплей не используется системой
                if not self._is_display_in_use(display_num):
                    return display_num
        return None

    def _is_display_in_use(self, display_num: int) -> bool:
        """Проверяет, используется ли дисплей системой"""
        # Проверяем существование X11 lock файла
        lock_file = f"/tmp/.X{display_num}-lock"
        return os.path.exists(lock_file)

    async def _start_xvfb_display(
        self, display_config: Dict[str, Any]
    ) -> asyncio.subprocess.Process:
        """Запускает виртуальный дисплей Xvfb"""
        display_num = display_config["display_num"]
        resolution = display_config["resolution"]

        # Команда для запуска Xvfb
        cmd = [
            "Xvfb",
            f":{display_num}",
            "-screen",
            "0",
            f"{resolution}x24",
            "-nolisten",
            "tcp",
            "-dpi",
            "96",
            "+extension",
            "GLX",
            "+extension",
            "RANDR",
            "-noreset",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            logger.info(
                "Xvfb display started",
                display_num=display_num,
                resolution=resolution,
                pid=process.pid,
            )

            return process

        except Exception as e:
            logger.error(
                "Failed to start Xvfb display", display_num=display_num, error=str(e)
            )
            raise

    async def _start_vnc_server(
        self, display_config: Dict[str, Any]
    ) -> asyncio.subprocess.Process:
        """Запускает VNC сервер"""
        display_num = display_config["display_num"]
        vnc_port = display_config["vnc_port"]

        # Команда для запуска x11vnc
        cmd = [
            "x11vnc",
            "-display",
            f":{display_num}",
            "-forever",
            "-nopw",  # Без пароля (только localhost)
            "-localhost",  # Только локальные подключения
            "-rfbport",
            str(vnc_port),
            "-shared",
            "-nodpms",
            "-nomodtweak",
            "-quiet",
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            logger.info(
                "VNC server started",
                display_num=display_num,
                vnc_port=vnc_port,
                pid=process.pid,
            )

            return process

        except Exception as e:
            logger.error(
                "Failed to start VNC server", display_num=display_num, error=str(e)
            )
            raise


# Глобальный экземпляр VNC менеджера
vnc_manager = VNCManager()
