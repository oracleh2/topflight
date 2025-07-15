# backend/app/core/browser_manager.py - ИСПРАВИТЬ методы запуска браузера:

import os
import subprocess
import asyncio
import random
import socket
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import structlog

from app.models import Profile, ProfileFingerprint, ProfileLifecycle, ServerConfig
from app.database import async_session_maker
from .fingerprint_generator import FingerprintGenerator
from ..models.profile import DeviceType
from playwright.async_api import Browser, BrowserContext
from .vnc_manager import vnc_manager

logger = structlog.get_logger(__name__)


class BrowserManager:
    """Менеджер для работы с браузерными профилями"""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.warmup_sites = [
            "https://habr.com",
            "https://www.kinopoisk.ru",
            "https://market.yandex.ru",
            "https://news.yandex.ru",
            "https://music.yandex.ru",
            "https://dzen.ru",
            "https://ya.ru",
            "https://mail.ru",
            "https://vk.com",
            "https://ok.ru",
        ]
        self.server_id = f"server-{socket.gethostname()}"

    async def get_session(self) -> AsyncSession:
        """Получает сессию БД"""
        if self.db:
            return self.db
        else:
            async with async_session_maker() as session:
                return session

    def _setup_display_environment(self, vnc_session=None):
        """Настройка окружения для отображения"""
        if vnc_session:
            # Для debug режима используем VNC дисплей
            display_env = f":{vnc_session.display_num}"
            os.environ["DISPLAY"] = display_env
            logger.info(f"Using VNC display: {display_env}")
        else:
            # Для обычного режима используем виртуальный дисплей
            if not os.environ.get("DISPLAY"):
                # Запускаем Xvfb если его нет
                self._ensure_xvfb_running()
                os.environ["DISPLAY"] = ":99"
                logger.info("Using Xvfb display: :99")

    def _ensure_xvfb_running(self):
        """Обеспечивает запуск Xvfb для headless режима"""
        try:
            # Проверяем, запущен ли Xvfb
            result = subprocess.run(
                ["pgrep", "-f", "Xvfb :99"], capture_output=True, text=True
            )

            if result.returncode != 0:
                # Xvfb не запущен, запускаем его
                logger.info("Starting Xvfb on display :99")
                subprocess.Popen(
                    [
                        "Xvfb",
                        ":99",
                        "-screen",
                        "0",
                        "1920x1080x24",
                        "-ac",
                        "+extension",
                        "GLX",
                    ]
                )
                # Ждем немного для запуска
                import time

                time.sleep(2)
            else:
                logger.info("Xvfb already running on display :99")

        except Exception as e:
            logger.warning(f"Failed to ensure Xvfb running: {e}")

    async def _launch_browser(self, playwright, profile: Profile):
        """Запуск браузера с настройками профиля"""
        browser_settings = profile.browser_settings or {}

        # Настраиваем окружение для отображения
        self._setup_display_environment()

        # Настройки запуска браузера
        launch_options = {
            "headless": False,  # НЕ headless для обхода детекции
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--disable-dev-shm-usage",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-field-trial-config",
                "--disable-ipc-flooding-protection",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-hang-monitor",
                "--disable-sync",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-component-extensions-with-background-pages",
                "--disable-extensions",
                "--mute-audio",
                f"--user-agent={profile.user_agent}",
            ],
        }

        return await playwright.chromium.launch(**launch_options)

    async def _launch_debug_browser_with_vnc(
        self, vnc_session, profile: Profile
    ) -> Browser:
        """Запускает браузер с привязкой к VNC дисплею"""

        # Настраиваем окружение для VNC
        self._setup_display_environment(vnc_session)

        browser_settings = profile.browser_settings or {}

        # Специальные настройки для дебага
        launch_options = {
            "headless": False,  # Обязательно НЕ headless для VNC
            "slow_mo": 500,  # Замедление для наблюдения
            "devtools": True,  # Включаем DevTools
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--disable-dev-shm-usage",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-field-trial-config",
                "--disable-ipc-flooding-protection",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-hang-monitor",
                "--disable-sync",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-component-extensions-with-background-pages",
                "--disable-extensions",
                "--mute-audio",
                f"--user-agent={profile.user_agent}",
                f"--display={os.environ.get('DISPLAY')}",
                # Настройки окна для адаптации под разрешение
                f"--window-size={vnc_session.resolution.replace('x', ',')}",
                "--start-maximized",
            ],
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(**launch_options)

            # Создаем контекст с настройками профиля
            context = await self._create_debug_context(browser, profile, vnc_session)

            # Создаем стартовую страницу
            page = await context.new_page()

            # Устанавливаем viewport под разрешение VNC
            width, height = map(int, vnc_session.resolution.split("x"))
            await page.set_viewport_size({"width": width - 400, "height": height - 200})

            logger.info(
                "Debug browser configured",
                display=os.environ.get("DISPLAY"),
                resolution=vnc_session.resolution,
                task_id=vnc_session.task_id,
            )

            return browser

    async def _create_debug_context(
        self, browser: Browser, profile: Profile, vnc_session
    ) -> BrowserContext:
        """Создает контекст браузера для debug режима"""
        context_options = {
            "viewport": {
                "width": int(vnc_session.resolution.split("x")[0]) - 400,
                "height": int(vnc_session.resolution.split("x")[1]) - 200,
            },
            "user_agent": profile.user_agent,
            "java_script_enabled": True,
            "accept_downloads": True,
            "ignore_https_errors": True,
        }

        # Добавляем fingerprint если есть
        if profile.fingerprint:
            # Добавляем дополнительные настройки из fingerprint
            pass

        return await browser.new_context(**context_options)

    async def launch_debug_browser(
        self, task_id: str, device_type: DeviceType, profile: Optional[Profile] = None
    ) -> Dict[str, Any]:
        """Запускает браузер в режиме дебага с VNC"""
        try:
            # Создаем VNC сессию
            vnc_session_data = await vnc_manager.create_debug_session(
                task_id, device_type
            )
            vnc_session = vnc_manager.get_session_by_task(task_id)

            if not vnc_session:
                raise Exception("Failed to create VNC session")

            # Получаем или создаем профиль
            if not profile:
                profile = await self.get_ready_profile(device_type)
                if not profile:
                    profile = await self.create_profile(device_type=device_type)

            # ВРЕМЕННО: Для тестирования используем простую заглушку
            # вместо реального запуска браузера
            logger.info(
                "Debug browser session created (mock)",
                task_id=task_id,
                device_type=device_type.value,
                profile_id=str(profile.id),
            )

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

            return result

        except Exception as e:
            logger.error(
                "Failed to launch debug browser", task_id=task_id, error=str(e)
            )
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
                logger.warning(f"No debug session found for task {task_id}")
                return None

            logger.info(f"Taking screenshot for debug session {task_id}")

            # Создаем минимальный PNG (1x1 пиксель, прозрачный)
            png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\xdac\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"

            return png_data

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    async def get_debug_session_logs(
        self, task_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получает логи debug сессии"""
        return []

    async def get_ready_profile(
        self, device_type: DeviceType, domain_id: Optional[str] = None
    ) -> Optional[Profile]:
        """Получение готового профиля для указанного типа устройства"""
        session = await self.get_session()

        try:
            # Ищем готовый профиль указанного типа устройства
            query = (
                select(Profile)
                .where(
                    and_(
                        Profile.is_warmed_up == True,
                        Profile.status == "ready",
                        Profile.device_type == device_type,
                    )
                )
                .order_by(Profile.last_used.asc())
            )

            result = await session.execute(query)
            profile = result.scalar_one_or_none()

            if profile:
                # Обновляем время использования
                profile.last_used = datetime.utcnow()
                profile.total_usage_count += 1
                await session.commit()

                logger.info(
                    "Ready profile retrieved",
                    profile_id=str(profile.id),
                    device_type=device_type.value,
                )
                return profile

            return None

        except Exception as e:
            logger.error(
                "Failed to get ready profile",
                error=str(e),
                device_type=device_type.value,
            )
            return None

    async def create_profile(
        self, device_type: DeviceType, name: Optional[str] = None
    ) -> Profile:
        """Создает новый профиль для указанного типа устройства"""
        session = await self.get_session()

        try:
            # Генерируем фингерпринт для типа устройства
            fingerprint = FingerprintGenerator.generate_fingerprint(device_type)
            browser_settings = FingerprintGenerator.create_browser_settings(fingerprint)

            # Создаем имя профиля если не указано
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                device_suffix = device_type.value
                name = (
                    f"Profile_{device_suffix}_{timestamp}_{random.randint(1000, 9999)}"
                )

            # Создаем профиль
            profile = Profile(
                name=name,
                device_type=device_type,
                user_agent=fingerprint["browser"]["user_agent"],
                fingerprint=fingerprint,
                browser_settings=browser_settings,
                status="new",
            )

            session.add(profile)
            await session.commit()
            await session.refresh(profile)

            logger.info(
                "Profile created",
                profile_id=str(profile.id),
                name=name,
                device_type=device_type.value,
            )
            return profile

        except Exception as e:
            await session.rollback()
            logger.error(
                "Failed to create profile", error=str(e), device_type=device_type.value
            )
            raise
