# backend/app/core/enhanced_vnc_manager.py - обновленная версия с правильными путями
"""
Улучшенный VNC Manager для TopFlight с правильными путями
"""

import asyncio
import os
import signal
import socket
import time
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import structlog

from app.models import DeviceType
from .vnc_metrics import metrics_collector

logger = structlog.get_logger(__name__)

# Пути проекта
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/var/www/topflight"))
VNC_DATA_DIR = PROJECT_ROOT / "data" / "vnc"
VNC_TOKENS_DIR = PROJECT_ROOT / "data" / "vnc_tokens"
LOGS_DIR = PROJECT_ROOT / "logs"


@dataclass
class VNCSession:
    """Информация о VNC сессии с обновленными путями"""

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
            "project_root": str(PROJECT_ROOT),
        }

    def _get_status(self) -> str:
        """Определяет статус сессии"""
        if self.vnc_process and self.vnc_process.returncode is None:
            if self.xvfb_process and self.xvfb_process.returncode is None:
                return "active"
            else:
                return "degraded"
        return "inactive"

    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now(timezone.utc)


class EnhancedVNCManager:
    """Улучшенный менеджер VNC сессий для TopFlight"""

    def __init__(self):
        self.active_sessions: Dict[str, VNCSession] = {}
        self.used_displays: set = set()
        self.base_display_num = 100
        self.max_sessions = int(os.getenv("VNC_MAX_SESSIONS", "10"))
        self.vnc_host = "127.0.0.1"
        self.session_timeout = int(os.getenv("VNC_SESSION_TIMEOUT", "3600"))

        # Создаем необходимые директории
        self._create_directories()

        # Проверяем доступность утилит
        self._verify_dependencies()

    def _create_directories(self):
        """Создает необходимые директории"""
        directories = [VNC_DATA_DIR, VNC_TOKENS_DIR, LOGS_DIR]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Устанавливаем права для пользователя topflight
            if os.getuid() == 0:  # Если запущено от root
                import pwd

                try:
                    topflight_uid = pwd.getpwnam("topflight").pw_uid
                    topflight_gid = pwd.getpwnam("topflight").pw_gid
                    os.chown(directory, topflight_uid, topflight_gid)
                except KeyError:
                    logger.warning("User 'topflight' not found, using current user")

        logger.info(
            "VNC directories created",
            vnc_data=str(VNC_DATA_DIR),
            vnc_tokens=str(VNC_TOKENS_DIR),
            logs=str(LOGS_DIR),
        )

    def _verify_dependencies(self):
        """Проверяет наличие необходимых утилит"""
        required_tools = ["Xvfb", "x11vnc"]
        missing_tools = []

        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)

        if missing_tools:
            logger.error("Missing required tools for VNC", missing_tools=missing_tools)
            raise RuntimeError(
                f"Missing tools: {', '.join(missing_tools)}. Run setup_xvfb.sh first."
            )

    async def create_debug_session(
        self, task_id: str, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Создает новую VNC сессию с правильными путями"""
        try:
            # Проверки
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
            # vnc_port = 5900 + (display_num - self.base_display_num)
            vnc_port = 5900
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

            # Логируем с информацией о путях
            logger.info(
                "VNC debug session created",
                task_id=task_id,
                vnc_port=vnc_port,
                display_num=display_num,
                resolution=resolution,
                device_type=device_type.value,
                project_root=str(PROJECT_ROOT),
            )

            return session.to_dict()

        except Exception as e:
            logger.error("Failed to create VNC session", task_id=task_id, error=str(e))
            metrics_collector.record_connection_error(
                "session_creation_failed", task_id
            )
            raise

    async def _start_xvfb_display(
        self, display_num: int, resolution: str
    ) -> asyncio.subprocess.Process:
        """Запускает Xvfb с правильными параметрами"""

        # ИСПРАВЛЕНИЕ: Убиваем существующий Xvfb на этом дисплее
        try:
            import subprocess

            subprocess.run(["pkill", "-f", f"Xvfb :{display_num}"], capture_output=True)
            # Удаляем lock файл
            lock_file = f"/tmp/.X{display_num}-lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
            await asyncio.sleep(1)  # Даем время на завершение
        except Exception:
            pass

        # Создаем директорию для дисплея
        display_dir = VNC_DATA_DIR / f"display_{display_num}"
        display_dir.mkdir(exist_ok=True)

        cmd = [
            "Xvfb",
            f":{display_num}",
            "-screen",
            "0",
            f"{resolution}x24",
            "-ac",
            "-nolisten",
            "tcp",
            "+extension",
            "GLX",
            "+extension",
            "RANDR",
            "-dpi",
            "96",
            "-fbdir",
            str(display_dir),  # Директория для frame buffer
        ]

        try:
            # Логируем команду
            logger.debug(
                "Starting Xvfb", command=" ".join(cmd), display_dir=str(display_dir)
            )

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
            )

            # Ждем запуска Xvfb
            await asyncio.sleep(2)

            if process.returncode is not None:
                stderr_output = await process.stderr.read()
                raise Exception(f"Xvfb failed to start: {stderr_output.decode()}")

            logger.info(
                "Xvfb started",
                display_num=display_num,
                resolution=resolution,
                pid=process.pid,
            )
            return process

        except Exception as e:
            logger.error("Failed to start Xvfb", display_num=display_num, error=str(e))
            metrics_collector.record_connection_error("xvfb_failed")
            raise

    async def _start_vnc_server(
        self, display_num: int, vnc_port: int
    ) -> asyncio.subprocess.Process:
        """Запускает VNC сервер с безопасными настройками"""
        # Создаем лог файл для VNC сервера
        vnc_log = LOGS_DIR / f"vnc_{display_num}_{vnc_port}.log"

        env = os.environ.copy()
        env["DISPLAY"] = f":{display_num}"
        env["WAYLAND_DISPLAY"] = ""  # Отключаем Wayland
        env["XDG_SESSION_TYPE"] = "x11"  # Принудительно X11
        env.pop("WAYLAND_DISPLAY", None)  # Полностью удаляем переменную
        env.pop("XDG_SESSION_DESKTOP", None)  # Удаляем desktop session
        env.pop("DESKTOP_SESSION", None)  # Удаляем desktop session
        env["GDK_BACKEND"] = "x11"  # Принудительно X11 для GTK
        env["QT_QPA_PLATFORM"] = "xcb"  # Принудительно X11 для Qt
        env["XAUTHORITY"] = ""

        cmd = [
            "x11vnc",
            "-display",
            f":{display_num}",
            "-forever",
            "-nopw",
            "-localhost",
            "-rfbport",
            str(vnc_port),
            "-no6",
            "-norc",
            # Убираем -quiet чтобы видеть вывод
            # "-quiet",
            "-logfile",
            str(vnc_log),
            # Добавляем дополнительные флаги для стабильности
            "-shared",
            "-permitfiletransfer",
        ]

        try:
            logger.debug(
                "Starting VNC server", command=" ".join(cmd), log_file=str(vnc_log)
            )

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,  # Изменено с DEVNULL на PIPE
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                # Добавляем переменные окружения
                env=env,
            )

            # Проверяем запуск VNC сервера
            await asyncio.sleep(3)

            if process.returncode is not None:
                stderr_output = await process.stderr.read()
                stdout_output = await process.stdout.read()
                logger.error(
                    "x11vnc process terminated",
                    returncode=process.returncode,
                    stderr=stderr_output.decode(),
                    stdout=stdout_output.decode(),
                    command=" ".join(cmd),
                )
                raise Exception(f"x11vnc failed to start: {stderr_output.decode()}")
            else:
                logger.info(f"x11vnc process is running with PID: {process.pid}")

            # Проверяем, что порт открыт
            # if not await self._check_vnc_port(vnc_port):
            #     raise Exception(f"VNC port {vnc_port} is not accessible")

            logger.info(
                "VNC server started",
                display_num=display_num,
                vnc_port=vnc_port,
                pid=process.pid,
                log_file=str(vnc_log),
            )
            return process

        except Exception as e:
            logger.error(
                "Failed to start VNC server", display_num=display_num, error=str(e)
            )
            metrics_collector.record_connection_error("vnc_failed")
            raise

    async def stop_debug_session(self, task_id: str) -> bool:
        """Останавливает VNC сессию с правильной очисткой"""
        try:
            if task_id not in self.active_sessions:
                logger.warning("VNC session not found for stop", task_id=task_id)
                return False

            session = self.active_sessions[task_id]
            success = True

            # Останавливаем процессы
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

            # Очищаем директории сессии
            display_dir = VNC_DATA_DIR / f"display_{session.display_num}"
            if display_dir.exists():
                try:
                    import shutil

                    shutil.rmtree(display_dir)
                    logger.debug(
                        "Cleaned display directory", display_dir=str(display_dir)
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to clean display directory",
                        display_dir=str(display_dir),
                        error=str(e),
                    )

            # Очищаем ресурсы
            self.used_displays.discard(session.display_num)
            del self.active_sessions[task_id]

            # Обновляем метрики
            metrics_collector.record_session_terminated(task_id, "manual")
            metrics_collector.update_active_sessions_count(len(self.active_sessions))

            logger.info(
                "VNC session stopped",
                task_id=task_id,
                success=success,
                display_num=session.display_num,
                vnc_port=session.vnc_port,
            )
            return success

        except Exception as e:
            logger.error("Error stopping VNC session", task_id=task_id, error=str(e))
            return False

    async def _check_vnc_port(self, port: int, timeout: float = 5.0) -> bool:
        """Проверяет доступность VNC порта"""
        try:
            # Увеличиваем timeout и добавляем retry логику
            for attempt in range(3):
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection("127.0.0.1", port), timeout=timeout
                    )
                    writer.close()
                    await writer.wait_closed()
                    logger.info(
                        f"VNC port {port} is accessible on attempt {attempt + 1}"
                    )
                    return True
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                    logger.debug(
                        f"VNC port {port} check failed (attempt {attempt + 1}): {e}"
                    )
                    if attempt < 2:  # Не последняя попытка
                        await asyncio.sleep(1)  # Пауза между попытками
                    continue

            logger.warning(f"VNC port {port} is not accessible after 3 attempts")
            return False

        except Exception as e:
            logger.error(f"Unexpected error checking VNC port {port}: {e}")
            return False

    def _find_available_display(self) -> Optional[int]:
        """Находит доступный номер дисплея"""
        for i in range(self.base_display_num, self.base_display_num + 100):
            if i not in self.used_displays:
                # Проверяем, что дисплей действительно свободен
                lock_file = Path(f"/tmp/.X{i}-lock")
                if not lock_file.exists():
                    return i
        return None

    def _get_optimal_vnc_resolution(self, device_type: DeviceType) -> str:
        """Определяет оптимальное разрешение для типа устройства"""
        resolutions = {
            DeviceType.DESKTOP: "1920x1080",
            DeviceType.MOBILE: "1366x768",
            DeviceType.TABLET: "1600x900",
        }
        return resolutions.get(device_type, "1920x1080")

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Возвращает список активных сессий с проверкой состояния"""
        active_sessions = []

        for task_id, session in list(self.active_sessions.items()):
            if session._get_status() == "active":
                session.update_activity()
                active_sessions.append(session.to_dict())
            else:
                logger.warning("Removing dead VNC session", task_id=task_id)
                await self.stop_debug_session(task_id)

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
            inactive_time = (current_time - session.last_activity).total_seconds()
            if inactive_time > self.session_timeout:
                sessions_to_remove.append(task_id)

        for task_id in sessions_to_remove:
            logger.info("Cleaning up inactive VNC session", task_id=task_id)
            await self.stop_debug_session(task_id)


# Создаем глобальный экземпляр
enhanced_vnc_manager = EnhancedVNCManager()
