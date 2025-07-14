import asyncio
import random
import socket
import os
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
from app.core.vnc_manager import vnc_manager

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
                        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    }
                )

                visited_sites = 0
                target_sites = random.randint(3, 7)

                # Посещаем случайные сайты для прогрева
                sites_to_visit = random.sample(
                    self.warmup_sites, min(target_sites, len(self.warmup_sites))
                )

                for site in sites_to_visit:
                    try:
                        logger.info(
                            "Warming up profile", profile_id=str(profile.id), site=site
                        )

                        # Переходим на сайт
                        await page.goto(site, wait_until="networkidle", timeout=30000)

                        # Имитируем человеческое поведение
                        await self._simulate_human_behavior(page)

                        visited_sites += 1

                        # Случайная пауза между сайтами
                        await asyncio.sleep(random.uniform(2, 8))

                    except Exception as e:
                        logger.warning(
                            "Failed to visit site during warmup",
                            profile_id=str(profile.id),
                            site=site,
                            error=str(e),
                        )
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

    async def _launch_browser(self, playwright, profile: Profile):
        """Запуск браузера с настройками профиля"""
        browser_settings = profile.browser_settings

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
        browser_settings = profile.browser_settings

        context_options = {
            "viewport": browser_settings["viewport"],
            "user_agent": browser_settings["user_agent"],
            "locale": browser_settings["locale"],
            "timezone_id": browser_settings["timezone_id"],
            "device_scale_factor": browser_settings["device_scale_factor"],
            "has_touch": browser_settings["has_touch"],
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
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """
        )

        return context

    async def _simulate_human_behavior(self, page: Page):
        """Имитация человеческого поведения на странице"""
        try:
            # Случайное время ожидания загрузки
            await asyncio.sleep(random.uniform(1, 3))

            # Скроллинг страницы
            for _ in range(random.randint(1, 4)):
                scroll_distance = random.randint(200, 800)
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                await asyncio.sleep(random.uniform(0.5, 2))

            # Случайные движения мыши
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.3, 1))

            # Возможный клик по элементу (осторожно!)
            if random.random() < 0.3:  # 30% шанс
                try:
                    # Ищем безопасные элементы для клика
                    safe_selectors = [
                        'a[href="#"]',
                        'button:not([type="submit"])',
                        ".menu",
                        ".logo",
                    ]
                    for selector in safe_selectors:
                        element = await page.query_selector(selector)
                        if element:
                            await element.click()
                            await asyncio.sleep(random.uniform(1, 2))
                            break
                except:
                    pass  # Игнорируем ошибки кликов

        except Exception as e:
            logger.warning("Error in human behavior simulation", error=str(e))

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

    async def mark_profile_corrupted(self, profile: Profile, reason: str):
        """Помечает профиль как испорченный"""
        session = await self.get_session()

        try:
            profile.status = "corrupted"

            # Обновляем lifecycle
            lifecycle_result = await session.execute(
                select(ProfileLifecycle).where(
                    ProfileLifecycle.profile_id == profile.id
                )
            )
            lifecycle = lifecycle_result.scalar_one_or_none()

            if lifecycle:
                lifecycle.is_corrupted = True
                lifecycle.corruption_reason = reason

            await session.commit()
            logger.warning(
                "Profile marked as corrupted", profile_id=str(profile.id), reason=reason
            )

        except Exception as e:
            logger.error(
                "Failed to mark profile as corrupted",
                profile_id=str(profile.id),
                error=str(e),
            )

    async def health_check_profile(self, profile: Profile) -> bool:
        """Проверка здоровья профиля"""
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p, profile)
                context = await self._create_context(browser, profile)
                page = await context.new_page()

                # Пытаемся зайти на Яндекс
                await page.goto(
                    "https://yandex.ru", wait_until="networkidle", timeout=15000
                )

                # Проверяем что нет капчи или блокировки
                captcha_present = await page.query_selector(".captcha") is not None
                blocked = "blocked" in await page.url() or "captcha" in await page.url()

                await browser.close()

                if captcha_present or blocked:
                    await self.mark_profile_corrupted(
                        profile, "Captcha or blocking detected"
                    )
                    return False

                return True

        except Exception as e:
            logger.warning(
                "Health check failed", profile_id=str(profile.id), error=str(e)
            )
            return False

    async def maintain_warm_profiles_pool(self):
        """Поддержание пула теплых профилей для разных типов устройств"""
        session = await self.get_session()

        try:
            # Получаем конфигурацию сервера
            server_config_result = await session.execute(
                select(ServerConfig).where(ServerConfig.server_id == self.server_id)
            )
            server_config = server_config_result.scalar_one_or_none()

            if not server_config:
                logger.warning("Server config not found", server_id=self.server_id)
                return

            # Проверяем desktop профили
            await self._maintain_device_profiles(
                session,
                server_config,
                DeviceType.DESKTOP,
                server_config.warm_desktop_profiles_target,
            )

            # Проверяем mobile профили
            await self._maintain_device_profiles(
                session,
                server_config,
                DeviceType.MOBILE,
                server_config.warm_mobile_profiles_target,
            )

        except Exception as e:
            logger.error("Failed to maintain warm profiles pool", error=str(e))

    async def _maintain_device_profiles(
        self,
        session: AsyncSession,
        server_config: ServerConfig,
        device_type: DeviceType,
        target_count: int,
    ):
        """Поддержание пула профилей для конкретного типа устройства"""

        # Считаем текущие теплые профили этого типа
        ready_profiles_result = await session.execute(
            select(Profile).where(
                and_(
                    Profile.is_warmed_up == True,
                    Profile.status == "ready",
                    Profile.device_type == device_type,
                )
            )
        )
        ready_profiles_count = len(ready_profiles_result.scalars().all())

        profiles_needed = target_count - ready_profiles_count

        logger.info(
            "Warm profiles status",
            device_type=device_type.value,
            current=ready_profiles_count,
            target=target_count,
            needed=profiles_needed,
        )

        # Создаем недостающие профили
        if profiles_needed > 0:
            for i in range(profiles_needed):
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

            # Запускаем браузер с VNC дисплеем
            browser = await self._launch_debug_browser_with_vnc(vnc_session, profile)

            # Сохраняем PID браузера в сессии
            vnc_session.browser_pid = browser.pid if hasattr(browser, "pid") else None

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
            logger.error(
                "Failed to launch debug browser", task_id=task_id, error=str(e)
            )
            # Очищаем VNC сессию при ошибке
            await vnc_manager.stop_debug_session(task_id)
            raise

    async def launch_production_browser(
        self, device_type: DeviceType, profile: Optional[Profile] = None
    ) -> Browser:
        """Запускает браузер в обычном продакшн режиме (существующий метод)"""
        # Это обертка над существующим _launch_browser с указанием обычного режима
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

    async def _launch_debug_browser_with_vnc(
        self, vnc_session, profile: Profile
    ) -> Browser:
        """Запускает браузер с привязкой к VNC дисплею"""

        # Устанавливаем DISPLAY для VNC
        display_env = f":{vnc_session.display_num}"
        os.environ["DISPLAY"] = display_env

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
                f"--display={display_env}",
                # Настройки окна для адаптации под разрешение
                f"--window-size={vnc_session.resolution.replace('x', ',')}",
                "--start-maximized",
            ],
        }

        # Применяем настройки профиля
        if browser_settings:
            launch_options.update(browser_settings)

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
                display=display_env,
                resolution=vnc_session.resolution,
                task_id=vnc_session.task_id,
            )

            return browser

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
        await context.add_init_script(
            """
            // Debug режим - показываем больше информации
            console.log('🐛 Debug mode active - Task ID:', arguments[0]);

            // Стандартные анти-детекция скрипты
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru'],
            });

            window.chrome = {
                runtime: {},
            };

            // Debug: выводим важные события в консоль
            window.addEventListener('load', () => {
                console.log('🚀 Page loaded:', location.href);
            });

            window.addEventListener('beforeunload', () => {
                console.log('👋 Page unloading:', location.href);
            });
        """,
            vnc_session.task_id,
        )

        return context

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

            # Используем xwd для создания скриншота X11 дисплея
            cmd = [
                "xwd",
                "-root",
                "-display",
                f":{vnc_session.display_num}",
                "-out",
                "/tmp/screenshot.xwd",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Конвертируем XWD в PNG используя ImageMagick
                convert_cmd = ["convert", "/tmp/screenshot.xwd", "/tmp/screenshot.png"]

                convert_process = await asyncio.create_subprocess_exec(
                    *convert_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                await convert_process.communicate()

                if convert_process.returncode == 0:
                    # Читаем PNG файл
                    with open("/tmp/screenshot.png", "rb") as f:
                        screenshot_data = f.read()

                    # Очищаем временные файлы
                    os.remove("/tmp/screenshot.xwd")
                    os.remove("/tmp/screenshot.png")

                    return screenshot_data

            return None

        except Exception as e:
            logger.error(
                "Failed to take debug screenshot", task_id=task_id, error=str(e)
            )
            return None

    # async def launch_debug_browser(
    #     self, task_id: str, device_type: DeviceType, profile: Optional[Profile] = None
    # ) -> Dict[str, Any]:
    #     """Запускает браузер в режиме дебага с VNC"""
    #     from .vnc_manager import vnc_manager
    #
    #     try:
    #         # Создаем VNC сессию
    #         vnc_session_data = await vnc_manager.create_debug_session(
    #             task_id, device_type
    #         )
    #         vnc_session = vnc_manager.get_session_by_task(task_id)
    #
    #         if not vnc_session:
    #             raise Exception("Failed to create VNC session")
    #
    #         # Получаем или создаем профиль
    #         if not profile:
    #             profile = await self.get_ready_profile(device_type)
    #             if not profile:
    #                 profile = await self.create_profile(device_type=device_type)
    #
    #         result = vnc_session_data.copy()
    #         result.update(
    #             {
    #                 "browser_launched": True,
    #                 "profile_id": str(profile.id),
    #                 "debug_instructions": {
    #                     "vnc_client_command": f"vncviewer {vnc_session.vnc_host}:{vnc_session.vnc_port}",
    #                     "resolution": vnc_session.resolution,
    #                     "device_emulation": device_type.value,
    #                 },
    #             }
    #         )
    #
    #         logger.info(
    #             "Debug browser launched with VNC",
    #             task_id=task_id,
    #             vnc_port=vnc_session.vnc_port,
    #             profile_id=str(profile.id),
    #         )
    #
    #         return result
    #
    #     except Exception as e:
    #         logger.error(
    #             "Failed to launch debug browser", task_id=task_id, error=str(e)
    #         )
    #         await vnc_manager.stop_debug_session(task_id)
    #         raise
    #
    # async def get_debug_session_info(self, task_id: str) -> Optional[Dict[str, Any]]:
    #     """Получает информацию о debug сессии"""
    #     from .vnc_manager import vnc_manager
    #
    #     vnc_session = vnc_manager.get_session_by_task(task_id)
    #     if vnc_session:
    #         return vnc_session.to_dict()
    #     return None
