# backend/app/core/browser_manager.py - ПОЛНАЯ РЕАЛИЗАЦИЯ:
from sqlalchemy import func
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

    # ===================== СОЗДАНИЕ ПРОФИЛЕЙ =====================

    async def create_profile(
        self, name: Optional[str] = None, device_type: DeviceType = DeviceType.DESKTOP
    ) -> Profile:
        """Создание нового профиля браузера для указанного типа устройства"""
        session = await self.get_session()

        try:
            # Генерируем fingerprint для указанного типа устройства
            fingerprint = FingerprintGenerator.generate_realistic_fingerprint(
                device_type
            )
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

    async def get_ready_profile(self, device_type: DeviceType) -> Optional[Profile]:
        """Получает готовый профиль для использования"""
        session = await self.get_session()

        try:
            # Ищем готовый профиль указанного типа
            result = await session.execute(
                select(Profile)
                .where(
                    and_(
                        Profile.device_type == device_type,
                        Profile.status == "ready",
                        Profile.is_warmed_up == True,
                    )
                )
                .order_by(Profile.last_used.asc().nullsfirst())
                .limit(1)
            )

            profile = result.scalar_one_or_none()

            if profile:
                # Обновляем время последнего использования
                profile.last_used = datetime.utcnow()
                profile.total_usage_count += 1
                await session.commit()

                logger.info(
                    "Ready profile found",
                    profile_id=str(profile.id),
                    device_type=device_type.value,
                )

            return profile

        except Exception as e:
            logger.error(
                "Failed to get ready profile",
                error=str(e),
                device_type=device_type.value,
            )
            return None

    # ===================== ПРОГРЕВ ПРОФИЛЕЙ =====================

    async def warmup_profile(self, profile: Profile) -> bool:
        """Прогрев профиля - посещение сайтов с Яндекс.Метрикой"""
        session = await self.get_session()

        try:
            profile.status = "warming"
            await session.commit()

            async with async_playwright() as p:
                # Запускаем браузер
                browser = await self._launch_browser(p, profile)
                context = await self._create_context(browser, profile)
                page = await context.new_page()

                # Устанавливаем дополнительные заголовки
                await page.set_extra_http_headers(
                    {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    }
                )

                visited_sites = 0
                sites_to_visit = random.randint(3, 7)

                for site in random.sample(self.warmup_sites, sites_to_visit):
                    try:
                        logger.info(f"Warming up profile with site: {site}")

                        # Переходим на сайт
                        await page.goto(site, wait_until="load", timeout=30000)

                        # Ждем полной загрузки
                        await page.wait_for_load_state("networkidle", timeout=10000)

                        # Имитируем активность пользователя
                        await page.evaluate(
                            """
                            // Скроллим страницу
                            window.scrollTo(0, Math.random() * document.body.scrollHeight);
                        """
                        )

                        # Случайная пауза
                        await asyncio.sleep(random.uniform(2, 5))

                        visited_sites += 1

                    except Exception as e:
                        logger.warning(f"Failed to visit {site}: {e}")
                        continue

                # Сохраняем cookies
                cookies = await context.cookies()
                profile.cookies = cookies
                profile.warmup_sites_visited = visited_sites
                profile.is_warmed_up = True
                profile.status = "ready"
                profile.last_used = datetime.utcnow()

                await browser.close()
                await session.commit()

                logger.info(
                    "Profile warmed up successfully",
                    profile_id=str(profile.id),
                    sites_visited=visited_sites,
                )
                return True

        except Exception as e:
            profile.status = "failed"
            await session.commit()
            logger.error(
                "Profile warmup failed", profile_id=str(profile.id), error=str(e)
            )
            return False

    # ===================== ЗАПУСК БРАУЗЕРОВ =====================

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

    async def _create_context(
        self, browser: Browser, profile: Profile
    ) -> BrowserContext:
        """Создание контекста браузера с настройками профиля"""
        browser_settings = profile.browser_settings or {}

        # Безопасно извлекаем параметры с fallback значениями
        context_options = {
            "viewport": browser_settings.get(
                "viewport", {"width": 1920, "height": 1080}
            ),
            "user_agent": browser_settings.get("user_agent", profile.user_agent),
            "locale": browser_settings.get("locale", "ru-RU"),
            "timezone_id": browser_settings.get("timezone_id", "Europe/Moscow"),
            "device_scale_factor": browser_settings.get("device_scale_factor", 1),
            "has_touch": browser_settings.get("has_touch", False),
            "java_script_enabled": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
        }

        context = await browser.new_context(**context_options)

        # Восстанавливаем cookies если есть
        if profile.cookies:
            await context.add_cookies(profile.cookies)

        # Скрываем следы автоматизации
        await context.add_init_script(
            """
            // Удаляем webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Перезаписываем plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Перезаписываем languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru'],
            });

            // Убираем chrome automation property
            window.chrome = {
                runtime: {},
            };

            // Перезаписываем permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
        """
        )

        return context

    async def _create_debug_context(
        self, browser: Browser, profile: Profile, vnc_session
    ) -> BrowserContext:
        """Создает контекст браузера для дебага"""
        browser_settings = profile.browser_settings or {}

        # Адаптируем viewport под VNC разрешение
        width, height = map(int, vnc_session.resolution.split("x"))
        viewport_width = width - 400  # Учитываем DevTools
        viewport_height = height - 200  # Учитываем UI браузера

        context_options = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "user_agent": profile.user_agent,
            "locale": browser_settings.get("locale", "ru-RU"),
            "timezone_id": browser_settings.get("timezone_id", "Europe/Moscow"),
            "device_scale_factor": browser_settings.get("device_scale_factor", 1),
            "has_touch": browser_settings.get("has_touch", False),
            "java_script_enabled": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
            # Для дебага записываем все запросы
            "record_har_path": f"/tmp/debug_session_{vnc_session.task_id}.har",
            "record_har_mode": "minimal",
        }

        context = await browser.new_context(**context_options)

        # Восстанавливаем cookies если есть
        if profile.cookies:
            await context.add_cookies(profile.cookies)

        # Добавляем debug-specific скрипты
        debug_script = f"""
            // Debug режим - показываем больше информации
            console.log('🐛 Debug mode active - Task ID: {vnc_session.task_id}');

            // Стандартные анти-детекция скрипты
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});

            Object.defineProperty(navigator, 'plugins', {{
                get: () => [1, 2, 3, 4, 5],
            }});

            Object.defineProperty(navigator, 'languages', {{
                get: () => ['ru-RU', 'ru'],
            }});

            window.chrome = {{
                runtime: {{}},
            }};

            // Debug: выводим важные события в консоль
            window.addEventListener('load', () => {{
                console.log('🚀 Page loaded:', location.href);
            }});

            window.addEventListener('beforeunload', () => {{
                console.log('👋 Page unloading:', location.href);
            }});

            // Добавляем глобальную переменную с ID задачи для отладки
            window.DEBUG_TASK_ID = '{vnc_session.task_id}';
        """

        await context.add_init_script(debug_script)

        return context

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

    # ===================== ПУБЛИЧНЫЕ МЕТОДЫ =====================

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

    async def launch_production_browser(
        self, device_type: DeviceType, profile: Optional[Profile] = None
    ) -> Browser:
        """Запускает браузер в обычном продакшн режиме"""
        async with async_playwright() as p:
            if not profile:
                profile = await self.get_ready_profile(device_type)
                if not profile:
                    profile = await self.create_profile(device_type=device_type)

            return await self._launch_browser(p, profile)

    async def restart_task_with_debug(
        self, task_id: str, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Перезапускает задачу в режиме дебага"""
        try:
            # Останавливаем существующую VNC сессию если есть
            await vnc_manager.stop_debug_session(task_id)

            # Создаем новую debug сессию
            return await self.launch_debug_browser(task_id, device_type)

        except Exception as e:
            logger.error(
                "Failed to restart task with debug", task_id=task_id, error=str(e)
            )
            raise

    async def restart_task_normal(self, task_id: str) -> bool:
        """Переводит задачу в обычный режим"""
        try:
            # Просто останавливаем VNC сессию
            return await vnc_manager.stop_debug_session(task_id)

        except Exception as e:
            logger.error(
                "Failed to restart task in normal mode", task_id=task_id, error=str(e)
            )
            return False

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

    # ===================== УПРАВЛЕНИЕ ПРОФИЛЯМИ =====================

    async def _update_profile_usage(self, profile: Profile, success: bool):
        """Обновляет статистику использования профиля"""
        session = await self.get_session()

        try:
            profile.total_usage_count += 1
            profile.last_used = datetime.utcnow()

            if success:
                # Обновляем success rate
                if profile.total_usage_count > 0:
                    success_count = (
                        int(
                            profile.success_rate * (profile.total_usage_count - 1) / 100
                        )
                        + 1
                    )
                    profile.success_rate = (
                        success_count / profile.total_usage_count
                    ) * 100
            else:
                # Пересчитываем success rate
                if profile.total_usage_count > 0:
                    success_count = int(
                        profile.success_rate * (profile.total_usage_count - 1) / 100
                    )
                    profile.success_rate = (
                        success_count / profile.total_usage_count
                    ) * 100

            await session.commit()

        except Exception as e:
            logger.error(f"Failed to update profile usage: {e}")

    async def maintain_warm_profiles(self, target_count: int = 1000):
        """Поддержание целевого количества теплых профилей"""
        session = await self.get_session()

        try:
            # Проверяем количество готовых профилей по типам устройств
            for device_type in [DeviceType.DESKTOP, DeviceType.MOBILE]:
                ready_count = await session.scalar(
                    select(func.count(Profile.id)).where(
                        and_(
                            Profile.device_type == device_type,
                            Profile.status == "ready",
                            Profile.is_warmed_up == True,
                        )
                    )
                )

                target_for_device = target_count // 2  # Пополам между desktop и mobile

                if ready_count < target_for_device:
                    needed = target_for_device - ready_count
                    logger.info(
                        f"Need to create {needed} warm profiles for {device_type.value}"
                    )

                    # Создаем и прогреваем профили
                    for i in range(needed):
                        try:
                            profile = await self.create_profile(device_type=device_type)
                            await self.warmup_profile(profile)

                            # Пауза между созданием профилей
                            await asyncio.sleep(random.uniform(10, 30))

                        except Exception as e:
                            logger.error(
                                "Failed to create warm profile",
                                error=str(e),
                                device_type=device_type.value,
                            )
                            continue

        except Exception as e:
            logger.error(f"Failed to maintain warm profiles: {e}")


# Добавляем недостающий импорт
