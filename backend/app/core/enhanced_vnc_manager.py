# backend/app/core/enhanced_vnc_manager.py
import asyncio
import os
import signal
import socket
import time
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

from app.models import DeviceType
from .vnc_metrics import metrics_collector

logger = structlog.get_logger(__name__)


@dataclass
class VNCSession:
    """Улучшенная информация о VNC сессии"""

    task_id: str
    display_num: int
    vnc_port: int
    vnc_host: str
    resolution: str
    device_type: DeviceType
    xvfb_process: Optional[asyncio.subprocess.Process]
    vnc_process: Optional[asyncio.subprocess.Process]
    created_at: datetime
    last_activity: datetime
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
            "last_activity": self.last_activity.isoformat(),
            "browser_pid": self.browser_pid,
            "vnc_url": f"vnc://{self.vnc_host}:{self.vnc_port}",
            "web_vnc_url": f"http://{self.vnc_host}:6080/vnc.html?host={self.vnc_host}&port={self.vnc_port}",
            "status": self._get_status(),
            "uptime_seconds": int(
                (datetime.now(timezone.utc) - self.created_at).total_seconds()
            ),
        }

    def _get_status(self) -> str:
        """Определяет статус сессии"""
        if self.vnc_process and self.vnc_process.returncode is None:
            if self.xvfb_process and self.xvfb_process.returncode is None:
                return "active"
            else:
                return "degraded"  # VNC работает, но Xvfb нет
        return "inactive"

    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now(timezone.utc)


class EnhancedVNCManager:
    """Улучшенный менеджер VNC сессий с метриками и безопасностью"""

    def __init__(self):
        self.active_sessions: Dict[str, VNCSession] = {}
        self.used_displays: set = set()
        self.base_display_num = 100
        self.max_sessions = int(os.getenv("VNC_MAX_SESSIONS", "10"))
        self.vnc_host = "127.0.0.1"  # Только localhost для безопасности
        self.session_timeout = int(os.getenv("VNC_SESSION_TIMEOUT", "3600"))  # 1 час

        # Проверяем доступность требуемых утилит
        self._verify_dependencies()

    def _verify_dependencies(self):
        """Проверяет наличие необходимых утилит"""
        required_tools = ["Xvfb", "x11vnc"]
        missing_tools = []

        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)

        if missing_tools:
            logger.error("Missing required tools for VNC", missing_tools=missing_tools)
            raise RuntimeError(f"Missing tools: {', '.join(missing_tools)}")

    async def create_debug_session(
        self, task_id: str, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Создает новую VNC сессию с улучшенной безопасностью"""
        try:
            # Проверки безопасности
            if len(self.active_sessions) >= self.max_sessions:
                metrics_collector.record_connection_error(
                    "session_limit_exceeded", task_id
                )
                raise Exception(f"Достигнут лимит VNC сессий: {self.max_sessions}")

            if task_id in self.active_sessions:
                logger.warning("VNC session already exists", task_id=task_id)
                return self.active_sessions[task_id].to_dict()

            # Находим свободный дисплей
            display_num = self._find_available_display()
            if display_num is None:
                metrics_collector.record_connection_error(
                    "no_available_display", task_id
                )
                raise Exception("Нет доступных дисплеев для VNC")

            # Получаем оптимальное разрешение
            resolution = self._get_optimal_vnc_resolution(device_type)

            # Создаем процессы Xvfb и VNC
            xvfb_process = await self._start_xvfb_display(display_num, resolution)
            vnc_port = 5900 + (display_num - self.base_display_num)
            vnc_process = await self._start_vnc_server(display_num, vnc_port)

            # Создаем объект сессии
            session = VNCSession(
                task_id=task_id,
                display_num=display_num,
                vnc_port=vnc_port,
                vnc_host=self.vnc_host,
                resolution=resolution,
                device_type=device_type,
                xvfb_process=xvfb_process,
                vnc_process=vnc_process,
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
            )

            # Сохраняем сессию
            self.active_sessions[task_id] = session
            self.used_displays.add(display_num)

            # Записываем метрики
            metrics_collector.record_session_created(task_id, device_type.value)
            metrics_collector.update_active_sessions_count(len(self.active_sessions))

            logger.info(
                "VNC debug session created",
                task_id=task_id,
                vnc_port=vnc_port,
                display_num=display_num,
                resolution=resolution,
                device_type=device_type.value,
            )

            return session.to_dict()

        except Exception as e:
            logger.error("Failed to create VNC session", task_id=task_id, error=str(e))
            metrics_collector.record_connection_error(
                "session_creation_failed", task_id
            )
            raise

    async def stop_debug_session(self, task_id: str) -> bool:
        """Останавливает VNC сессию с правильной очисткой"""
        try:
            if task_id not in self.active_sessions:
                logger.warning("VNC session not found for stop", task_id=task_id)
                return False

            session = self.active_sessions[task_id]
            success = True

            # Останавливаем процессы с graceful shutdown
            if session.vnc_process and session.vnc_process.returncode is None:
                try:
                    session.vnc_process.terminate()
                    await asyncio.wait_for(session.vnc_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(
                        "VNC process didn't terminate gracefully, killing",
                        task_id=task_id,
                    )
                    session.vnc_process.kill()
                    await session.vnc_process.wait()
                except Exception as e:
                    logger.error(
                        "Error stopping VNC process", task_id=task_id, error=str(e)
                    )
                    success = False

            if session.xvfb_process and session.xvfb_process.returncode is None:
                try:
                    session.xvfb_process.terminate()
                    await asyncio.wait_for(session.xvfb_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(
                        "Xvfb process didn't terminate gracefully, killing",
                        task_id=task_id,
                    )
                    session.xvfb_process.kill()
                    await session.xvfb_process.wait()
                except Exception as e:
                    logger.error(
                        "Error stopping Xvfb process", task_id=task_id, error=str(e)
                    )
                    success = False

            # Очищаем ресурсы
            self.used_displays.discard(session.display_num)
            del self.active_sessions[task_id]

            # Обновляем метрики
            metrics_collector.record_session_terminated(task_id, "manual")
            metrics_collector.update_active_sessions_count(len(self.active_sessions))

            logger.info("VNC session stopped", task_id=task_id, success=success)
            return success

        except Exception as e:
            logger.error("Error stopping VNC session", task_id=task_id, error=str(e))
            return False

    async def _start_xvfb_display(
        self, display_num: int, resolution: str
    ) -> asyncio.subprocess.Process:
        """Запускает Xvfb с улучшенными параметрами безопасности"""
        cmd = [
            "Xvfb",
            f":{display_num}",
            "-screen",
            "0",
            f"{resolution}x24",
            "-ac",  # Отключаем access control для localhost
            "-nolisten",
            "tcp",  # Безопасность: только Unix sockets
            "+extension",
            "GLX",  # Поддержка WebGL
            "+extension",
            "RANDR",  # Изменение разрешения
            "-dpi",
            "96",  # Стандартный DPI
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )

            # Ждем запуска Xvfb (проверяем существование display)
            await asyncio.sleep(1)

            if process.returncode is not None:
                stderr_output = await process.stderr.read()
                raise Exception(f"Xvfb failed to start: {stderr_output.decode()}")

            logger.info("Xvfb started", display_num=display_num, resolution=resolution)
            return process

        except Exception as e:
            logger.error("Failed to start Xvfb", display_num=display_num, error=str(e))
            metrics_collector.record_connection_error("xvfb_failed")
            raise

    async def _start_vnc_server(
        self, display_num: int, vnc_port: int
    ) -> asyncio.subprocess.Process:
        """Запускает VNC сервер с безопасными настройками"""
        cmd = [
            "x11vnc",
            "-display",
            f":{display_num}",
            "-forever",  # Не завершаться после отключения клиента
            "-nopw",  # Без пароля (безопасно т.к. только localhost)
            "-localhost",  # ВАЖНО: только localhost подключения
            "-rfbport",
            str(vnc_port),
            "-no6",  # Отключаем IPv6
            "-norc",  # Не читаем ~/.x11vncrc
            "-quiet",  # Меньше логов
            "-bg",  # Фоновый режим
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )

            # Проверяем запуск VNC сервера
            await asyncio.sleep(2)

            if process.returncode is not None:
                stderr_output = await process.stderr.read()
                raise Exception(f"x11vnc failed to start: {stderr_output.decode()}")

            # Проверяем, что порт открыт
            if not await self._check_vnc_port(vnc_port):
                raise Exception(f"VNC port {vnc_port} is not accessible")

            logger.info(
                "VNC server started", display_num=display_num, vnc_port=vnc_port
            )
            return process

        except Exception as e:
            logger.error(
                "Failed to start VNC server", display_num=display_num, error=str(e)
            )
            metrics_collector.record_connection_error("vnc_failed")
            raise

    async def _check_vnc_port(self, port: int, timeout: float = 5.0) -> bool:
        """Проверяет доступность VNC порта"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    def _find_available_display(self) -> Optional[int]:
        """Находит доступный номер дисплея"""
        for i in range(self.base_display_num, self.base_display_num + 100):
            if i not in self.used_displays:
                # Проверяем, что дисплей действительно свободен
                lock_file = f"/tmp/.X{i}-lock"
                if not os.path.exists(lock_file):
                    return i
        return None

    def _get_optimal_vnc_resolution(self, device_type: DeviceType) -> str:
        """Определяет оптимальное разрешение для типа устройства"""
        resolutions = {
            DeviceType.DESKTOP: "1920x1080",
            DeviceType.MOBILE: "1366x768",  # Больше места для мобильного дебага
            DeviceType.TABLET: "1600x900",
        }
        return resolutions.get(device_type, "1920x1080")

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Возвращает список активных сессий с проверкой состояния"""
        active_sessions = []

        for task_id, session in list(self.active_sessions.items()):
            # Обновляем активность если сессия живая
            if session._get_status() == "active":
                session.update_activity()
                active_sessions.append(session.to_dict())
            else:
                # Автоматически убираем мертвые сессии
                logger.warning("Removing dead VNC session", task_id=task_id)
                await self.stop_debug_session(task_id)

        # Обновляем метрики
        metrics_collector.update_active_sessions_count(len(active_sessions))

        return active_sessions

    def get_session_by_task(self, task_id: str) -> Optional[VNCSession]:
        """Получает сессию по ID задачи"""
        return self.active_sessions.get(task_id)

    async def cleanup_inactive_sessions(self):
        """Очищает неактивные сессии"""
        current_time = datetime.now(timezone.utc)
        sessions_to_remove = []

        for task_id, session in self.active_sessions.items():
            # Проверяем таймаут
            inactive_time = (current_time - session.last_activity).total_seconds()
            if inactive_time > self.session_timeout:
                sessions_to_remove.append(task_id)

        for task_id in sessions_to_remove:
            logger.info("Cleaning up inactive VNC session", task_id=task_id)
            await self.stop_debug_session(task_id)


# Создаем глобальный экземпляр
enhanced_vnc_manager = EnhancedVNCManager()
