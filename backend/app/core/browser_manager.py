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
            "https://ok.ru"
        ]
        self.server_id = f"server-{socket.gethostname()}"

    async def get_session(self) -> AsyncSession:
        """Получает сессию БД"""
        if self.db:
            return self.db
        else:
            async with async_session_maker() as session:
                return session

    async def create_profile(self, name: Optional[str] = None, device_type: DeviceType = DeviceType.DESKTOP) -> Profile:
        """Создание нового профиля браузера для указанного типа устройства"""
        session = await self.get_session()

        try:
            # Генерируем fingerprint для указанного типа устройства
            fingerprint = FingerprintGenerator.generate_realistic_fingerprint(device_type)
            browser_settings = FingerprintGenerator.create_browser_settings(fingerprint)

            # Создаем имя профиля если не указано
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                device_suffix = device_type.value
                name = f"Profile_{device_suffix}_{timestamp}_{random.randint(1000, 9999)}"

            # Создаем профиль
            profile = Profile(
                name=name,
                device_type=device_type,
                user_agent=fingerprint["browser"]["user_agent"],
                fingerprint=fingerprint,
                browser_settings=browser_settings,
                status="new"
            )

            session.add(profile)
            await session.commit()
            await session.refresh(profile)

            logger.info("Profile created", profile_id=str(profile.id), name=name, device_type=device_type.value)
            return profile

        except Exception as e:
            await session.rollback()
            logger.error("Failed to create profile", error=str(e), device_type=device_type.value)
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
                await page.set_extra_http_headers({
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                })

                visited_sites = 0
                target_sites = random.randint(3, 7)

                # Посещаем случайные сайты для прогрева
                sites_to_visit = random.sample(self.warmup_sites, min(target_sites, len(self.warmup_sites)))

                for site in sites_to_visit:
                    try:
                        logger.info("Warming up profile", profile_id=str(profile.id), site=site)

                        # Переходим на сайт
                        await page.goto(site, wait_until="networkidle", timeout=30000)

                        # Имитируем человеческое поведение
                        await self._simulate_human_behavior(page)

                        visited_sites += 1

                        # Случайная пауза между сайтами
                        await asyncio.sleep(random.uniform(2, 8))

                    except Exception as e:
                        logger.warning("Failed to visit site during warmup",
                                       profile_id=str(profile.id), site=site, error=str(e))
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

                logger.info("Profile warmed up successfully",
                            profile_id=str(profile.id), sites_visited=visited_sites)
                return True

        except Exception as e:
            profile.status = "failed"
            await session.commit()
            logger.error("Profile warmup failed", profile_id=str(profile.id), error=str(e))
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
                f"--user-agent={profile.user_agent}"
            ]
        }

        return await playwright.chromium.launch(**launch_options)

    async def _create_context(self, browser: Browser, profile: Profile) -> BrowserContext:
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
            "ignore_https_errors": True
        }

        context = await browser.new_context(**context_options)

        # Восстанавливаем cookies если есть
        if profile.cookies:
            await context.add_cookies(profile.cookies)

        # Скрываем следы автоматизации
        await context.add_init_script("""
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
        """)

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
                    safe_selectors = ['a[href="#"]', 'button:not([type="submit"])', '.menu', '.logo']
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

    async def get_ready_profile(self, device_type: DeviceType, domain_id: Optional[str] = None) -> Optional[Profile]:
        """Получение готового профиля для указанного типа устройства"""
        session = await self.get_session()

        try:
            # Ищем готовый профиль указанного типа устройства
            query = select(Profile).where(
                and_(
                    Profile.is_warmed_up == True,
                    Profile.status == "ready",
                    Profile.device_type == device_type
                )
            ).order_by(Profile.last_used.asc())

            result = await session.execute(query)
            profile = result.scalar_one_or_none()

            if profile:
                # Обновляем время использования
                profile.last_used = datetime.utcnow()
                profile.total_usage_count += 1
                await session.commit()

                logger.info("Ready profile retrieved",
                            profile_id=str(profile.id),
                            device_type=device_type.value)
                return profile

            return None

        except Exception as e:
            logger.error("Failed to get ready profile",
                         error=str(e), device_type=device_type.value)
            return None

    async def mark_profile_corrupted(self, profile: Profile, reason: str):
        """Помечает профиль как испорченный"""
        session = await self.get_session()

        try:
            profile.status = "corrupted"

            # Обновляем lifecycle
            lifecycle_result = await session.execute(
                select(ProfileLifecycle).where(ProfileLifecycle.profile_id == profile.id)
            )
            lifecycle = lifecycle_result.scalar_one_or_none()

            if lifecycle:
                lifecycle.is_corrupted = True
                lifecycle.corruption_reason = reason

            await session.commit()
            logger.warning("Profile marked as corrupted",
                           profile_id=str(profile.id), reason=reason)

        except Exception as e:
            logger.error("Failed to mark profile as corrupted",
                         profile_id=str(profile.id), error=str(e))

    async def health_check_profile(self, profile: Profile) -> bool:
        """Проверка здоровья профиля"""
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p, profile)
                context = await self._create_context(browser, profile)
                page = await context.new_page()

                # Пытаемся зайти на Яндекс
                await page.goto("https://yandex.ru", wait_until="networkidle", timeout=15000)

                # Проверяем что нет капчи или блокировки
                captcha_present = await page.query_selector(".captcha") is not None
                blocked = "blocked" in await page.url() or "captcha" in await page.url()

                await browser.close()

                if captcha_present or blocked:
                    await self.mark_profile_corrupted(profile, "Captcha or blocking detected")
                    return False

                return True

        except Exception as e:
            logger.warning("Health check failed", profile_id=str(profile.id), error=str(e))
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
                session, server_config, DeviceType.DESKTOP,
                server_config.warm_desktop_profiles_target
            )

            # Проверяем mobile профили
            await self._maintain_device_profiles(
                session, server_config, DeviceType.MOBILE,
                server_config.warm_mobile_profiles_target
            )

        except Exception as e:
            logger.error("Failed to maintain warm profiles pool", error=str(e))

    async def _maintain_device_profiles(self, session: AsyncSession, server_config: ServerConfig,
                                        device_type: DeviceType, target_count: int):
        """Поддержание пула профилей для конкретного типа устройства"""

        # Считаем текущие теплые профили этого типа
        ready_profiles_result = await session.execute(
            select(Profile).where(
                and_(
                    Profile.is_warmed_up == True,
                    Profile.status == "ready",
                    Profile.device_type == device_type
                )
            )
        )
        ready_profiles_count = len(ready_profiles_result.scalars().all())

        profiles_needed = target_count - ready_profiles_count

        logger.info("Warm profiles status",
                    device_type=device_type.value,
                    current=ready_profiles_count,
                    target=target_count,
                    needed=profiles_needed)

        # Создаем недостающие профили
        if profiles_needed > 0:
            for i in range(profiles_needed):
                try:
                    profile = await self.create_profile(device_type=device_type)
                    await self.warmup_profile(profile)

                    # Пауза между созданием профилей
                    await asyncio.sleep(random.uniform(10, 30))

                except Exception as e:
                    logger.error("Failed to create warm profile",
                                 error=str(e), device_type=device_type.value)
                    continue