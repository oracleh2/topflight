# backend/app/workers/profile_nurture_worker.py - обновленная версия с VNC debug

import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import random
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.database import async_session_maker
from app.core.task_manager import TaskManager, TaskType, TaskStatus
from app.core.browser_manager import BrowserManager
from app.models import Task, Profile, DeviceType
from app.constants.strategies import ProfileNurtureType

logger = structlog.get_logger(__name__)


class ProfileNurtureWorker:
    """Worker для обработки задач нагула профилей с поддержкой VNC debug"""

    def __init__(self):
        self.is_running = False
        self.worker_id = f"nurture_worker_{random.randint(1000, 9999)}"

    async def start(self):
        """Запустить worker"""
        self.is_running = True
        logger.info("Profile nurture worker started", worker_id=self.worker_id)

        while self.is_running:
            try:
                await self._process_batch()
                await asyncio.sleep(5)  # Пауза между обработками
            except Exception as e:
                logger.error(
                    "Error in worker main loop", worker_id=self.worker_id, error=str(e)
                )
                await asyncio.sleep(10)  # Увеличенная пауза при ошибке

    async def stop(self):
        """Остановить worker"""
        self.is_running = False
        logger.info("Profile nurture worker stopped", worker_id=self.worker_id)

    async def _process_batch(self):
        """Обработать пакет задач"""
        async with async_session_maker() as session:
            task_manager = TaskManager(session)

            # Получаем задачи для обработки
            tasks = await task_manager.get_pending_nurture_tasks(limit=5)

            if not tasks:
                return

            logger.info(
                "Processing nurture tasks batch",
                worker_id=self.worker_id,
                tasks_count=len(tasks),
            )

            # Обрабатываем задачи параллельно
            await asyncio.gather(
                *[self._process_task(task) for task in tasks], return_exceptions=True
            )

    async def _process_task(self, task: Task):
        """Обработать одну задачу нагула"""
        async with async_session_maker() as session:
            task_manager = TaskManager(session)
            browser_manager = BrowserManager(session)

            try:
                # Отмечаем задачу как запущенную
                success = await task_manager.mark_task_started(
                    str(task.id), self.worker_id
                )
                if not success:
                    logger.warning(
                        "Failed to mark task as started", task_id=str(task.id)
                    )
                    return

                # Проверяем, нужен ли debug режим
                debug_enabled = task.parameters.get("debug_enabled", False)
                device_type = DeviceType(task.device_type)

                if debug_enabled:
                    logger.info(
                        "🔍 Starting task in DEBUG mode",
                        task_id=str(task.id),
                        worker_id=self.worker_id,
                        device_type=device_type.value,
                    )
                    result = await self._execute_debug_task(
                        task, browser_manager, device_type
                    )
                else:
                    logger.info(
                        "Starting profile nurture task",
                        task_id=str(task.id),
                        worker_id=self.worker_id,
                        strategy_id=task.parameters.get("strategy_id"),
                    )
                    result = await self._execute_normal_task(
                        task, browser_manager, device_type
                    )

                # Отмечаем задачу как завершенную
                await task_manager.mark_task_completed(str(task.id), result)

                logger.info(
                    "Profile nurture task completed",
                    task_id=str(task.id),
                    worker_id=self.worker_id,
                    debug_mode=debug_enabled,
                    cookies_collected=result.get("cookies_collected", 0),
                )

            except Exception as e:
                logger.error(
                    "Profile nurture task failed",
                    task_id=str(task.id),
                    worker_id=self.worker_id,
                    error=str(e),
                )
                await task_manager.mark_task_failed(str(task.id), str(e))

    async def _execute_debug_task2(
        self, task: Task, browser_manager: BrowserManager, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить задачу в debug режиме - временно БЕЗ VNC"""
        try:
            logger.info(
                "🔍 Starting DEBUG task WITHOUT VNC (temporary)",
                task_id=str(task.id),
                device_type=device_type.value,
            )

            # Получаем или создаем профиль
            if task.profile_id:
                profile = await self._get_existing_profile(
                    browser_manager.db, task.profile_id
                )
            else:
                profile = await browser_manager.create_profile(device_type=device_type)

            # Запускаем браузер БЕЗ VNC (пока что)
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Все равно НЕ headless
                    slow_mo=2000,  # Очень медленно для наблюдения в логах
                    devtools=True,  # DevTools
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        f"--user-agent={profile.user_agent}",
                        "--window-size=1920,1080",
                        "--disable-web-security",
                        "--allow-running-insecure-content",
                    ],
                )

                # Создаем контекст
                context = await browser.new_context(
                    user_agent=profile.user_agent,
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,
                )

                # Добавляем debug скрипт
                await context.add_init_script(
                    f"""
                    console.log('🔍 DEBUG MODE: Browser started for task {task.id}');
                    console.log('🎯 Current URL:', window.location.href);

                    window.addEventListener('load', () => {{
                        console.log('📥 Loaded:', window.location.href);
                        console.log('🍪 Cookies:', document.cookie.split(';').length);
                    }});

                    window.DEBUG_TASK_ID = '{task.id}';
                """
                )

                # Создаем стартовую страницу
                page = await context.new_page()

                try:
                    logger.info("🚀 Starting debug nurture process")

                    # Выполняем debug нагул
                    result = await self._execute_debug_nurture(
                        task, page, context, device_type
                    )

                    # Получаем финальное количество куков
                    final_cookies = await context.cookies()
                    result["cookies_collected"] = len(final_cookies)
                    result["debug_mode"] = True
                    result["vnc_session"] = None  # Пока VNC не работает

                    logger.info(
                        "✅ Debug task completed successfully",
                        task_id=str(task.id),
                        cookies_collected=len(final_cookies),
                        sites_visited=result.get("sites_visited", 0),
                    )

                    return result

                finally:
                    # Держим браузер открытым для наблюдения
                    logger.info(
                        "🔍 Debug session completed. Keeping browser open for 30 seconds..."
                    )
                    await asyncio.sleep(30)

                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Debug task failed: {e}")
            raise

    async def _execute_debug_task(
        self, task: Task, browser_manager: BrowserManager, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить задачу в debug режиме с VNC"""
        try:
            # Импортируем enhanced vnc manager
            from app.core.enhanced_vnc_manager import enhanced_vnc_manager

            # Создаем VNC сессию
            vnc_session_data = await enhanced_vnc_manager.create_debug_session(
                str(task.id), device_type
            )
            vnc_session = enhanced_vnc_manager.get_session_by_task(str(task.id))

            if not vnc_session:
                raise Exception("Failed to create VNC session")

            # Получаем или создаем профиль
            if task.profile_id:
                profile = await self._get_existing_profile(
                    browser_manager.db, task.profile_id
                )
            else:
                profile = await browser_manager.create_profile(device_type=device_type)

            # Настраиваем окружение для VNC
            os.environ["DISPLAY"] = f":{vnc_session.display_num}"

            logger.info(
                "🎯 VNC Debug session ready",
                task_id=str(task.id),
                vnc_port=vnc_session.vnc_port,
                display=f":{vnc_session.display_num}",
                connect_command=f"vncviewer localhost:{vnc_session.vnc_port}",
            )

            # Запускаем браузер с VNC настройками
            async with async_playwright() as p:
                profile_dir = f"/tmp/browser_profile_{task.id}"
                os.makedirs(profile_dir, exist_ok=True)

                browser = await p.chromium.launch(
                    headless=False,  # ВАЖНО: НЕ headless для VNC
                    slow_mo=1500,  # Замедление для наблюдения
                    devtools=True,  # Включаем DevTools
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        f"--user-agent={profile.user_agent}",
                        f"--window-size={vnc_session.resolution.replace('x', ',')}",
                        "--start-maximized",
                        "--disable-web-security",
                        "--allow-running-insecure-content",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                        # Отключаем инкогнито режим:
                        "--disable-features=TranslateUI",
                        "--disable-extensions-except",
                        "--disable-component-extensions-with-background-pages=false",
                    ],
                )

                # Создаем контекст
                context = await browser.new_context(
                    user_agent=profile.user_agent,
                    viewport={
                        "width": int(vnc_session.resolution.split("x")[0]) - 100,
                        "height": int(vnc_session.resolution.split("x")[1]) - 100,
                    },
                    ignore_https_errors=True,
                )

                # Добавляем debug скрипт для логирования
                await context.add_init_script(
                    f"""
                    console.log('🔍 DEBUG MODE: Browser started for task {task.id}');
                    console.log('🎯 Current URL:', window.location.href);

                    // Логируем все переходы
                    window.addEventListener('beforeunload', () => {{
                        console.log('📤 Leaving:', window.location.href);
                    }});

                    window.addEventListener('load', () => {{
                        console.log('📥 Loaded:', window.location.href);
                        console.log('🍪 Cookies:', document.cookie.split(';').length);
                    }});

                    // Добавляем ID задачи в window для отладки
                    window.DEBUG_TASK_ID = '{task.id}';
                """
                )

                # Создаем стартовую страницу
                page = await context.new_page()

                try:
                    # Выполняем debug нагул
                    result = await self._execute_debug_nurture(
                        task, page, context, device_type
                    )

                    # Получаем финальное количество куков
                    final_cookies = await context.cookies()
                    result["cookies_collected"] = len(final_cookies)
                    result["debug_mode"] = True
                    result["vnc_session"] = {
                        "vnc_port": vnc_session.vnc_port,
                        "display_num": vnc_session.display_num,
                        "resolution": vnc_session.resolution,
                    }

                    return result

                finally:
                    # Держим браузер открытым для наблюдения
                    logger.info(
                        "🔍 Debug session completed. Browser will stay open for inspection."
                    )
                    logger.info(
                        f"🎯 Connect with: vncviewer localhost:{vnc_session.vnc_port}"
                    )

                    # Ждем 30 секунд перед закрытием
                    await asyncio.sleep(30)

                    await context.close()
                    await browser.close()

                    # Останавливаем VNC сессию
                    await enhanced_vnc_manager.stop_debug_session(str(task.id))

        except Exception as e:
            logger.error(f"❌ Debug task failed: {e}")
            # Очищаем VNC сессию при ошибке
            try:
                from app.core.enhanced_vnc_manager import enhanced_vnc_manager

                await enhanced_vnc_manager.stop_debug_session(str(task.id))
            except:
                pass
            raise

    async def _execute_debug_nurture(
        self, task: Task, page: Page, context: BrowserContext, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить нагул в debug режиме с реальным VNC"""

        # Список сайтов для дебага (включая ya.ru)
        debug_sites = [
            "https://ya.ru",
            "https://www.ozon.ru",
            "https://market.yandex.ru",
            "https://habr.com",
            "https://www.kinopoisk.ru",
        ]

        logger.info(f"🚀 Starting debug visits to {len(debug_sites)} sites")

        sites_visited = []
        total_interactions = 0

        for i, site in enumerate(debug_sites):
            try:
                logger.info(f"🌐 [{i+1}/{len(debug_sites)}] Visiting: {site}")

                # Переходим на сайт
                await page.goto(site, wait_until="domcontentloaded", timeout=30000)

                # Ждем загрузки
                await page.wait_for_timeout(3000)

                # Логируем в консоль браузера
                await page.evaluate(
                    f"""
                    console.log('🎯 DEBUG: Page loaded - {site}');
                    console.log('📄 Title:', document.title);
                    console.log('🍪 Cookies count:', document.cookie.split(';').filter(c => c.trim()).length);
                    console.log('🔗 Links count:', document.querySelectorAll('a').length);
                """
                )

                # Имитируем пользовательское поведение
                interactions = await self._perform_debug_interactions(page, site)
                total_interactions += interactions

                sites_visited.append(site)

                # Пауза для наблюдения
                await page.wait_for_timeout(5000)

                logger.info(
                    f"✅ Completed visit to {site} with {interactions} interactions"
                )

            except Exception as e:
                logger.error(f"❌ Failed to visit {site}: {e}")

        logger.info(
            f"🎉 Debug nurture completed. Visited {len(sites_visited)} sites with {total_interactions} total interactions"
        )

        return {
            "success": True,
            "nurture_type": "debug_visits",
            "sites_visited": len(sites_visited),
            "sites_list": sites_visited,
            "total_interactions": total_interactions,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _perform_debug_interactions(self, page: Page, site: str) -> int:
        """Выполняет интерактивные действия на странице для debug"""
        interactions = 0

        try:
            # Скроллинг
            for scroll in range(3):
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(1000)
                interactions += 1

            # Движения мыши
            for move in range(2):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(500)
                interactions += 1

            # Попробуем найти и кликнуть на ссылки (безопасно)
            try:
                links = await page.query_selector_all("a[href]")
                if links and len(links) > 0:
                    # Выберем случайную ссылку
                    link = random.choice(links[:5])  # Только первые 5 ссылок

                    # Проверим, видима ли ссылка
                    is_visible = await link.is_visible()
                    if is_visible:
                        href = await link.get_attribute("href")
                        if href and not href.startswith("javascript:"):
                            await page.evaluate(
                                f"""
                                console.log('🖱️ DEBUG: Clicking link:', '{href}');
                            """
                            )

                            await link.click()
                            await page.wait_for_timeout(2000)

                            # Возвращаемся назад
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                            interactions += 1

            except Exception as e:
                logger.debug(f"Could not interact with links on {site}: {e}")

            # Попробуем взаимодействовать с формами поиска
            try:
                search_inputs = await page.query_selector_all(
                    'input[type="search"], input[name*="search"], input[placeholder*="поиск"]'
                )
                if search_inputs:
                    search_input = search_inputs[0]
                    await search_input.fill("тест")
                    await page.wait_for_timeout(1000)
                    await search_input.clear()
                    interactions += 1

                    await page.evaluate(
                        """
                        console.log('🔍 DEBUG: Interacted with search input');
                    """
                    )

            except Exception as e:
                logger.debug(f"Could not interact with search on {site}: {e}")

        except Exception as e:
            logger.error(f"Error performing interactions on {site}: {e}")

        return interactions

    async def _execute_normal_task(
        self, task: Task, browser_manager: BrowserManager, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить задачу в обычном режиме (без VNC)"""
        # Извлекаем параметры задачи
        strategy_config = task.parameters.get("strategy_config", {})
        nurture_type = strategy_config.get("nurture_type", "search_based")

        # Выполняем нагул в зависимости от типа
        if nurture_type == "search_based":
            return await self._execute_search_based_nurture(
                task, strategy_config, browser_manager, device_type
            )
        elif nurture_type == "direct_visits":
            return await self._execute_direct_visits_nurture(
                task, strategy_config, browser_manager, device_type
            )
        elif nurture_type == "mixed_nurture":
            return await self._execute_mixed_nurture(
                task, strategy_config, browser_manager, device_type
            )
        else:
            raise ValueError(f"Unsupported nurture type: {nurture_type}")

    # ... (остальные методы остаются такими же как в предыдущей версии)

    async def _execute_search_based_nurture(
        self,
        task: Task,
        config: Dict[str, Any],
        browser_manager: BrowserManager,
        device_type: DeviceType,
    ) -> Dict[str, Any]:
        """Выполнить поисковый нагул"""

        # Создаем или получаем профиль
        if task.profile_id:
            profile = await self._get_existing_profile(
                browser_manager.db, task.profile_id
            )
        else:
            profile = await browser_manager.create_profile(device_type=device_type)

        # Запускаем браузер через playwright
        async with async_playwright() as p:
            browser = await browser_manager.launch_browser(p, profile)

            try:
                # Получаем параметры нагула
                target_cookies = config.get("target_cookies", {"min": 50, "max": 100})
                search_engines = config.get("search_engines", ["yandex.ru"])
                queries_source = config.get("queries_source", {})
                session_config = config.get("session_config", {})

                # Целевое количество куков
                target_count = random.randint(
                    target_cookies["min"], target_cookies["max"]
                )

                # Получаем список запросов для поиска
                queries = await self._get_search_queries(queries_source, limit=20)

                if not queries:
                    raise ValueError("No search queries available for nurturing")

                cookies_collected = 0
                sites_visited = []

                # Создаем контекст браузера
                context = await browser.new_context(
                    user_agent=profile.user_agent,
                    viewport={"width": 1920, "height": 1080},
                )

                page = await context.new_page()

                for i, query in enumerate(queries[:target_count]):
                    if cookies_collected >= target_count:
                        break

                    # Выбираем случайную поисковую систему
                    search_engine = random.choice(search_engines)

                    # Выполняем поиск и переходы
                    search_result = await self._perform_search_and_visits(
                        page, query, search_engine, session_config
                    )

                    cookies_collected += search_result.get("cookies_added", 0)
                    sites_visited.extend(search_result.get("sites_visited", []))

                    # Случайная пауза между поисками
                    delay = random.uniform(3, 8)
                    await asyncio.sleep(delay)

                # Получаем все куки из контекста
                cookies = await context.cookies()

                await context.close()

                return {
                    "success": True,
                    "nurture_type": "search_based",
                    "profile_id": str(profile.id),
                    "cookies_collected": len(cookies),
                    "target_cookies": target_count,
                    "sites_visited": len(sites_visited),
                    "sites_list": sites_visited,
                    "queries_used": len(queries),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }

            finally:
                await browser.close()

    async def _execute_direct_visits_nurture(
        self,
        task: Task,
        config: Dict[str, Any],
        browser_manager: BrowserManager,
        device_type: DeviceType,
    ) -> Dict[str, Any]:
        """Выполнить нагул прямыми заходами"""

        # Создаем или получаем профиль
        if task.profile_id:
            profile = await self._get_existing_profile(
                browser_manager.db, task.profile_id
            )
        else:
            profile = await browser_manager.create_profile(device_type=device_type)

        async with async_playwright() as p:
            browser = await browser_manager.launch_browser(p, profile)

            try:
                # Получаем параметры
                target_cookies = config.get("target_cookies", {"min": 50, "max": 100})
                direct_sites_source = config.get("direct_sites_source", {})
                session_config = config.get("session_config", {})

                target_count = random.randint(
                    target_cookies["min"], target_cookies["max"]
                )

                # Получаем список сайтов для прямых заходов
                sites = await self._get_direct_sites(
                    direct_sites_source, limit=target_count
                )

                if not sites:
                    raise ValueError("No direct sites available for nurturing")

                cookies_collected = 0
                sites_visited = []

                # Создаем контекст браузера
                context = await browser.new_context(
                    user_agent=profile.user_agent,
                    viewport={"width": 1920, "height": 1080},
                )

                page = await context.new_page()

                for site in sites[:target_count]:
                    if cookies_collected >= target_count:
                        break

                    # Выполняем прямой заход на сайт
                    visit_result = await self._perform_direct_visit(
                        page, site, session_config
                    )

                    cookies_collected += visit_result.get("cookies_added", 0)
                    sites_visited.append(site)

                    # Пауза между заходами
                    delay = random.uniform(2, 6)
                    await asyncio.sleep(delay)

                # Получаем все куки из контекста
                cookies = await context.cookies()

                await context.close()

                return {
                    "success": True,
                    "nurture_type": "direct_visits",
                    "profile_id": str(profile.id),
                    "cookies_collected": len(cookies),
                    "target_cookies": target_count,
                    "sites_visited": len(sites_visited),
                    "sites_list": sites_visited,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }

            finally:
                await browser.close()

    async def _execute_mixed_nurture(
        self,
        task: Task,
        config: Dict[str, Any],
        browser_manager: BrowserManager,
        device_type: DeviceType,
    ) -> Dict[str, Any]:
        """Выполнить смешанный нагул"""

        proportions = config.get(
            "proportions", {"search_percentage": 70, "direct_percentage": 30}
        )
        search_percentage = proportions.get("search_percentage", 70)

        # Разделяем нагрузку между поисковым и прямым нагулом
        target_cookies = config.get("target_cookies", {"min": 50, "max": 100})
        total_target = random.randint(target_cookies["min"], target_cookies["max"])

        search_target = int(total_target * search_percentage / 100)
        direct_target = total_target - search_target

        # Обновляем конфигурации для каждого типа
        search_config = config.copy()
        search_config["target_cookies"] = {"min": search_target, "max": search_target}

        direct_config = config.copy()
        direct_config["target_cookies"] = {"min": direct_target, "max": direct_target}

        # Выполняем оба типа нагула
        search_result = await self._execute_search_based_nurture(
            task, search_config, browser_manager, device_type
        )

        direct_result = await self._execute_direct_visits_nurture(
            task, direct_config, browser_manager, device_type
        )

        return {
            "success": True,
            "nurture_type": "mixed_nurture",
            "profile_id": search_result.get("profile_id"),
            "cookies_collected": search_result.get("cookies_collected", 0)
            + direct_result.get("cookies_collected", 0),
            "target_cookies": total_target,
            "search_cookies": search_result.get("cookies_collected", 0),
            "direct_cookies": direct_result.get("cookies_collected", 0),
            "sites_visited": search_result.get("sites_visited", 0)
            + direct_result.get("sites_visited", 0),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_existing_profile(
        self, session: AsyncSession, profile_id: str
    ) -> Profile:
        """Получить существующий профиль"""
        result = await session.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        return profile

    async def _get_search_queries(
        self, queries_source: Dict[str, Any], limit: int = 20
    ) -> List[str]:
        """Получить список поисковых запросов"""
        # Для дебага используем ya.ru
        source_type = queries_source.get("type", "manual_input")

        if source_type == "manual_input":
            return queries_source.get(
                "queries",
                [
                    "купить телефон",
                    "интернет магазин",
                    "доставка еды",
                    "онлайн курсы",
                    "строительные материалы",
                    "автозапчасти",
                    "мебель для дома",
                    "спортивные товары",
                    "детские игрушки",
                    "косметика и парфюмерия",
                    "книги онлайн",
                    "туры и отдых",
                ],
            )[:limit]

        return []

    async def _get_direct_sites(
        self, sites_source: Dict[str, Any], limit: int = 20
    ) -> List[str]:
        """Получить список сайтов для прямых заходов"""
        source_type = sites_source.get("type", "manual_input")

        if source_type == "manual_input":
            # Для дебага используем ya.ru и несколько других популярных сайтов
            return sites_source.get(
                "sites",
                [
                    "https://ya.ru",
                    "https://www.ozon.ru",
                    "https://www.wildberries.ru",
                    "https://market.yandex.ru",
                    "https://www.dns-shop.ru",
                    "https://www.mvideo.ru",
                    "https://www.eldorado.ru",
                    "https://www.lamoda.ru",
                    "https://www.sportmaster.ru",
                    "https://www.citilink.ru",
                ],
            )[:limit]

        return []

    async def _perform_search_and_visits(
        self,
        page: Page,
        query: str,
        search_engine: str,
        session_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """РЕАЛЬНАЯ реализация поиска и переходов по результатам"""
        try:
            logger.info(f"Performing search for query: {query} on {search_engine}")

            # Переходим на поисковую систему (пока используем ya.ru для дебага)
            await page.goto(
                "https://ya.ru", wait_until="domcontentloaded", timeout=30000
            )

            # Ждем загрузки страницы
            await page.wait_for_timeout(random.randint(2000, 4000))

            # Ищем поле поиска и вводим запрос
            search_input = page.locator(
                'input[name="text"], input[type="search"], input[placeholder*="Найти"], #text'
            )

            if await search_input.count() > 0:
                await search_input.first.fill(query)
                await page.wait_for_timeout(random.randint(500, 1500))

                # Нажимаем Enter или кнопку поиска
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(random.randint(3000, 6000))

                logger.info(f"Search performed for: {query}")
            else:
                logger.warning(f"Search input not found on {search_engine}")

            # Имитируем активность пользователя - скроллинг
            for _ in range(random.randint(2, 5)):
                await page.mouse.wheel(0, random.randint(200, 800))
                await page.wait_for_timeout(random.randint(1000, 3000))

            # Получаем текущие куки
            current_cookies = await page.context.cookies()

            return {
                "cookies_added": len(current_cookies),
                "sites_visited": ["ya.ru"],
                "search_performed": True,
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return {
                "cookies_added": 0,
                "sites_visited": [],
                "search_performed": False,
                "error": str(e),
            }

    async def _perform_direct_visit(
        self,
        page: Page,
        site: str,
        session_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """РЕАЛЬНАЯ реализация прямого захода на сайт"""
        try:
            logger.info(f"Performing direct visit to: {site}")

            # Переходим на сайт
            await page.goto(site, wait_until="domcontentloaded", timeout=30000)

            # Ждем загрузки страницы
            await page.wait_for_timeout(random.randint(3000, 6000))

            # Имитируем активность пользователя
            # Скроллинг по странице
            for _ in range(random.randint(3, 7)):
                await page.mouse.wheel(0, random.randint(200, 600))
                await page.wait_for_timeout(random.randint(1000, 2500))

            # Случайные движения мыши
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1000)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(500, 1500))

            # Попробуем кликнуть на случайные ссылки (безопасно)
            try:
                links = page.locator('a[href^="http"], a[href^="/"]')
                links_count = await links.count()

                if links_count > 0:
                    # Кликаем на 1-2 случайные ссылки
                    for _ in range(min(2, random.randint(1, 3))):
                        random_index = random.randint(0, min(links_count - 1, 10))
                        link = links.nth(random_index)

                        if await link.is_visible():
                            await link.click()
                            await page.wait_for_timeout(random.randint(2000, 4000))

                            # Возвращаемся назад
                            await page.go_back()
                            await page.wait_for_timeout(random.randint(1000, 3000))

            except Exception as e:
                logger.debug(f"Could not interact with links on {site}: {e}")

            # Получаем текущие куки
            current_cookies = await page.context.cookies()

            logger.info(
                f"Successfully visited {site}, collected {len(current_cookies)} cookies"
            )

            return {
                "cookies_added": len(current_cookies),
                "visit_successful": True,
                "site": site,
            }

        except Exception as e:
            logger.error(f"Error performing direct visit to {site}: {e}")
            return {
                "cookies_added": 0,
                "visit_successful": False,
                "site": site,
                "error": str(e),
            }


# Глобальный экземпляр worker'а
profile_nurture_worker = ProfileNurtureWorker()


async def start_profile_nurture_worker():
    """Запустить worker в фоновом режиме"""
    asyncio.create_task(profile_nurture_worker.start())


async def stop_profile_nurture_worker():
    """Остановить worker"""
    await profile_nurture_worker.stop()
