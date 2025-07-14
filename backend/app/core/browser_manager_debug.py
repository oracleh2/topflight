# backend/app/core/browser_manager_debug.py
import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import structlog

from app.models import Profile, DeviceType
from .vnc_manager import vnc_manager

logger = structlog.get_logger(__name__)

# Добавьте эти методы в класс BrowserManager


async def launch_debug_browser(
    self, task_id: str, device_type: DeviceType, profile: Optional[Profile] = None
) -> Dict[str, Any]:
    """Запускает браузер в режиме дебага с VNC"""
    try:
        # Создаем VNC сессию
        vnc_session_data = await vnc_manager.create_debug_session(task_id, device_type)
        vnc_session = vnc_manager.get_session_by_task(task_id)

        if not vnc_session:
            raise Exception("Failed to create VNC session")

        # Получаем или создаем профиль
        if not profile:
            profile = await self.get_ready_profile(device_type)
            if not profile:
                profile = await self.create_profile(device_type=device_type)

        result = vnc_session_data.copy()
        result.update(
            {
                "browser_launched": True,
                "profile_id": str(profile.id),
                "debug_instructions": {
                    "vnc_client_command": f"vncviewer {vnc_session.vnc_host}:{vnc_session.vnc_port}",
                    "ssh_tunnel_command": f"ssh -L {vnc_session.vnc_port}:localhost:{vnc_session.vnc_port} user@server",
                    "resolution": vnc_session.resolution,
                    "device_emulation": device_type.value,
                },
            }
        )

        logger.info(
            "Debug browser launched with VNC",
            task_id=task_id,
            vnc_port=vnc_session.vnc_port,
            profile_id=str(profile.id),
        )

        return result

    except Exception as e:
        logger.error("Failed to launch debug browser", task_id=task_id, error=str(e))
        # Очищаем VNC сессию при ошибке
        await vnc_manager.stop_debug_session(task_id)
        raise


async def get_debug_session_info(self, task_id: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о debug сессии"""
    vnc_session = vnc_manager.get_session_by_task(task_id)
    if vnc_session:
        return vnc_session.to_dict()
    return None


async def take_debug_screenshot(self, task_id: str) -> Optional[bytes]:
    """Делает скриншот debug сессии"""
    try:
        vnc_session = vnc_manager.get_session_by_task(task_id)
        if not vnc_session:
            return None

        # Используем import для создания скриншота X11 дисплея
        cmd = [
            "import",
            "-window",
            "root",
            "-display",
            f":{vnc_session.display_num}",
            "/tmp/screenshot.png",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Читаем PNG файл
            with open("/tmp/screenshot.png", "rb") as f:
                screenshot_data = f.read()

            # Очищаем временный файл
            os.remove("/tmp/screenshot.png")

            return screenshot_data

        return None

    except Exception as e:
        logger.error("Failed to take debug screenshot", task_id=task_id, error=str(e))
        return None
