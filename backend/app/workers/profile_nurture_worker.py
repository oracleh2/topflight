# backend/app/workers/profile_nurture_worker.py - обновленная версия с VNC debug

import asyncio
import structlog
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import random
import os
import aiohttp
import re
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.core.task_manager import TaskManager, TaskType, TaskStatus
from app.core.browser_manager import BrowserManager
from app.models import Task, Profile, DeviceType
from app.constants.strategies import ProfileNurtureType
from playwright.async_api import ViewportSize
from playwright.async_api import Cookie
import shutil
from pathlib import Path

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

    # Исправленная структура _execute_debug_task с правильным finally
    async def _execute_debug_task(
        self, task: Task, browser_manager: BrowserManager, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить задачу в debug режиме с VNC (с временной папкой профиля)"""

        profile_temp_dir = None
        vnc_session = None
        exception_to_raise = None  # Инициализируем сразу
        result = None  # Для сохранения результата

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
                profile = await self._create_profile_with_strategy_from_task(
                    browser_manager, device_type, task
                )

            # Выбираем и назначаем прокси из стратегии
            selected_proxy = await self._select_and_assign_proxy(profile)
            if selected_proxy:
                logger.info(
                    f"🌐 Using proxy for debug task: {selected_proxy.get('host')}:{selected_proxy.get('port')}"
                )

            # Настраиваем окружение для VNC
            os.environ["DISPLAY"] = f":{vnc_session.display_num}"

            # Создаем временную директорию профиля
            profile_temp_dir = f"/var/www/topflight/data/profiles_temp/{profile.id}"
            Path(profile_temp_dir).mkdir(parents=True, exist_ok=True)

            logger.info(
                "🎯 VNC Debug session ready",
                task_id=str(task.id),
                vnc_port=vnc_session.vnc_port,
                display=f":{vnc_session.display_num}",
                connect_command=f"vncviewer localhost:{vnc_session.vnc_port}",
                profile_dir=profile_temp_dir,
            )

            # Подготавливаем аргументы браузера
            browser_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                f"--user-agent={profile.user_agent}",
                f"--window-size={vnc_session.resolution.replace('x', ',')}",
                "--start-maximized",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions-except",
                "--disable-component-extensions-with-background-pages=false",
                "--disable-features=TranslateUI",
                "--enable-features=NetworkService,NetworkServiceLogging",
                # f"--user-data-dir={profile_temp_dir}",
                "--disable-features=VizDisplayCompositor",
                "--enable-automation",
            ]

            # Добавляем прокси аргументы если прокси назначена
            if selected_proxy:
                proxy_args = self._build_proxy_args(selected_proxy)
                browser_args.extend(proxy_args)

            # Запускаем браузер с VNC настройками и временной папкой профиля
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # ВАЖНО: НЕ headless для VNC
                    slow_mo=1500,  # Замедление для наблюдения
                    devtools=True,  # Включаем DevTools
                    args=browser_args,
                )

                # Создаем контекст БЕЗ прокси (прокси уже в аргументах браузера)
                context = await browser.new_context(
                    user_agent=profile.user_agent,
                    viewport={
                        "width": int(vnc_session.resolution.split("x")[0]) - 100,
                        "height": int(vnc_session.resolution.split("x")[1]) - 100,
                    },
                    ignore_https_errors=True,
                )

                # Если есть cookies, устанавливаем их
                if profile.cookies:
                    await context.add_cookies(profile.cookies)

                # Добавляем debug скрипт для логирования
                await context.add_init_script(
                    f"""
                    console.log('🔍 DEBUG MODE: Browser started for task {task.id}');
                    console.log('🎯 Current URL:', window.location.href);

                    window.addEventListener('beforeunload', () => {{
                        console.log('📤 Leaving:', window.location.href);
                    }});

                    window.addEventListener('load', () => {{
                        console.log('📥 Loaded:', window.location.href);
                        console.log('🍪 Cookies:', document.cookie.split(';').length);
                    }});

                    window.DEBUG_TASK_ID = '{task.id}';
                """
                )

                # Создаем страницу
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

                    # Сохраняем cookies в базу данных
                    await self._save_cookies_to_profile(profile, final_cookies)

                    logger.info(
                        "🔍 Debug session completed. Browser will stay open for inspection."
                    )
                    logger.info(
                        f"🎯 Connect with: vncviewer localhost:{vnc_session.vnc_port}"
                    )

                    # Ждем 30 секунд перед закрытием
                    await asyncio.sleep(30)

                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Debug task failed: {e}")
            exception_to_raise = e

        finally:
            # Cleanup выполняется ВСЕГДА

            # Очищаем VNC сессию
            if vnc_session:
                try:
                    from app.core.enhanced_vnc_manager import enhanced_vnc_manager

                    await enhanced_vnc_manager.stop_debug_session(str(task.id))
                    logger.info(f"🧹 Stopped VNC session for task {task.id}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Failed to stop VNC session: {cleanup_error}")

            # Очищаем временную директорию профиля
            if profile_temp_dir and Path(profile_temp_dir).exists():
                try:
                    shutil.rmtree(profile_temp_dir)
                    logger.info(
                        f"🗑️ Cleaned up profile temp directory: {profile_temp_dir}"
                    )
                except Exception as cleanup_error:
                    logger.warning(
                        f"⚠️ Failed to clean up profile directory {profile_temp_dir}: {cleanup_error}"
                    )

        # После finally - проверяем что делать
        if exception_to_raise:
            raise exception_to_raise

        return result

    async def _create_profile_with_strategy_from_task(
        self, browser_manager: BrowserManager, device_type: DeviceType, task: Task
    ) -> Profile:
        """Создать профиль с назначенной стратегией из задачи"""

        # Создаем профиль обычным способом
        profile = await browser_manager.create_profile(device_type=device_type)

        # Если в задаче есть strategy_id - назначаем ее профилю
        strategy_id = None

        # Проверяем strategy_id в поле task.strategy_id (новое поле)
        if task.strategy_id:
            strategy_id = str(task.strategy_id)
            logger.info(f"📋 Using strategy_id from task.strategy_id: {strategy_id}")

        # Fallback: проверяем в параметрах задачи (для обратной совместимости)
        elif task.parameters and task.parameters.get("strategy_id"):
            strategy_id = task.parameters.get("strategy_id")
            logger.info(f"📋 Using strategy_id from task.parameters: {strategy_id}")

        # Назначаем стратегию профилю если найдена
        if strategy_id:
            try:
                async with async_session_maker() as session:
                    await session.execute(
                        update(Profile)
                        .where(Profile.id == profile.id)
                        .values(nurture_strategy_id=strategy_id)
                    )
                    await session.commit()

                    # Обновляем объект в памяти
                    profile.nurture_strategy_id = strategy_id

                    logger.info(
                        f"📋 Assigned strategy to profile",
                        profile_id=str(profile.id),
                        strategy_id=strategy_id,
                        task_id=str(task.id),
                    )

            except Exception as e:
                logger.error(f"❌ Failed to assign strategy to profile: {e}")
        else:
            logger.debug(
                f"No strategy_id found in task {task.id}, profile created without strategy"
            )

        return profile

    async def _execute_debug_nurture(
        self, task: Task, page: Page, context: BrowserContext, device_type: DeviceType
    ) -> Dict[str, Any]:
        """Выполнить нагул в debug режиме с реальным VNC"""

        # Список сайтов для дебага (включая ya.ru)
        debug_sites = [
            "https://2ip.ru",
            # "https://ya.ru",
            # "https://www.ozon.ru",
            # "https://market.yandex.ru",
            # "https://habr.com",
            # "https://www.kinopoisk.ru",
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
                # search_inputs = await page.query_selector_all(
                #     'input[type="search"], input[name*="search"], input[placeholder*="поиск"]'
                # )

                search_input = page.locator(
                    'input[type="search"], input[name*="search"], input[placeholder*="поиск"]'
                ).first

                await search_input.fill("тест")
                await page.wait_for_timeout(1000)
                # У Locator есть метод clear()
                await search_input.clear()
                interactions += 1
                await page.evaluate(
                    """
                    console.log('🔍 DEBUG: Interacted with search input');
                """
                )

                # if search_inputs:
                #     search_input = search_inputs[0]
                #     await search_input.fill("тест")
                #     await page.wait_for_timeout(1000)
                #     # await search_input.clear()
                #     await search_input.fill("")
                #     interactions += 1
                #
                #     await page.evaluate(
                #         """
                #         console.log('🔍 DEBUG: Interacted with search input');
                #     """
                #     )

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

    async def _execute_search_based_nurture(
        self,
        task: Task,
        config: Dict[str, Any],
        browser_manager: BrowserManager,
        device_type: DeviceType,
    ) -> Dict[str, Any]:
        """Выполнить поисковый нагул с временной папкой профиля"""

        profile_temp_dir = None
        exception_to_raise = None
        result = None

        try:
            # Создаем или получаем профиль
            if task.profile_id:
                profile = await self._get_existing_profile(
                    browser_manager.db, task.profile_id
                )
            else:
                profile = await browser_manager.create_profile(device_type=device_type)

            # Выбираем и назначаем прокси из стратегии
            selected_proxy = await self._select_and_assign_proxy(profile)
            if selected_proxy:
                logger.info(
                    f"🌐 Using proxy for nurture task: {selected_proxy.get('host')}:{selected_proxy.get('port')}"
                )

            # Создаем временную директорию профиля
            profile_temp_dir = f"/var/www/topflight/data/profiles_temp/{profile.id}"
            Path(profile_temp_dir).mkdir(parents=True, exist_ok=True)

            # Подготавливаем аргументы браузера
            browser_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                f"--user-agent={profile.user_agent}",
                "--window-size=1920,1080",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-features=TranslateUI",
                # f"--user-data-dir={profile_temp_dir}",
            ]

            # Добавляем прокси аргументы если прокси назначена
            if selected_proxy:
                proxy_args = self._build_proxy_args(selected_proxy)
                browser_args.extend(proxy_args)

            # Запускаем браузер с временной папкой профиля
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,  # Headless для продакшена
                    args=browser_args,
                )

                try:
                    # Получаем параметры нагула
                    target_cookies = config.get(
                        "target_cookies", {"min": 50, "max": 100}
                    )
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

                    # Получаем viewport из fingerprint профиля или используем дефолтные значения
                    viewport_width = 1920
                    viewport_height = 1080

                    if (
                        hasattr(profile, "fingerprint_data")
                        and profile.fingerprint_data
                    ):
                        if profile.fingerprint_data.viewport_size:
                            viewport_parts = (
                                profile.fingerprint_data.viewport_size.split("x")
                            )
                            if len(viewport_parts) == 2:
                                viewport_width = int(viewport_parts[0])
                                viewport_height = int(viewport_parts[1])

                    # Создаем контекст браузера с восстановлением cookies
                    context = await browser.new_context(
                        user_agent=profile.user_agent,
                        viewport=ViewportSize(
                            width=viewport_width, height=viewport_height
                        ),
                        storage_state=(
                            {
                                "cookies": profile.cookies if profile.cookies else [],
                                "origins": [],
                            }
                            if profile.cookies
                            else None
                        ),
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

                    # Сохраняем cookies в профиль
                    await self._save_cookies_to_profile(profile, cookies)

                    await context.close()

                    result = {
                        "success": True,
                        "nurture_type": "search_based",
                        "profile_id": str(profile.id),
                        "cookies_collected": len(cookies),
                        "target_cookies": target_count,
                        "sites_visited": len(sites_visited),
                        "sites_list": sites_visited,
                        "queries_used": len(queries),
                        "completed_at": datetime.utcnow().isoformat(),
                    }

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Search based nurture failed: {e}")
            exception_to_raise = e

        finally:
            # Очищаем временную директорию профиля
            if profile_temp_dir and Path(profile_temp_dir).exists():
                try:
                    shutil.rmtree(profile_temp_dir)
                    logger.info(
                        f"🗑️ Cleaned up profile temp directory: {profile_temp_dir}"
                    )
                except Exception as cleanup_error:
                    logger.warning(
                        f"⚠️ Failed to clean up profile directory {profile_temp_dir}: {cleanup_error}"
                    )

        # После finally - проверяем что делать
        if exception_to_raise:
            raise exception_to_raise

        return result

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
                    "https://2ip.ru",
                    # "https://ya.ru",
                    # "https://www.ozon.ru",
                    # "https://www.wildberries.ru",
                    # "https://market.yandex.ru",
                    # "https://www.dns-shop.ru",
                    # "https://www.mvideo.ru",
                    # "https://www.eldorado.ru",
                    # "https://www.lamoda.ru",
                    # "https://www.sportmaster.ru",
                    # "https://www.citilink.ru",
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

    async def _save_cookies_to_profile(
        self, profile: Profile, cookies: List[Cookie]
    ) -> None:
        """Сохранить cookies в профиль в базе данных"""
        try:
            async with async_session_maker() as session:
                # Преобразуем cookies из Playwright Cookie objects в dict
                cookies_json = []
                for cookie in cookies:
                    # Cookie объект уже имеет все нужные поля
                    cookie_data = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie.get("path", "/"),
                        "expires": cookie.get("expires", -1),
                        "httpOnly": cookie.get("httpOnly", False),
                        "secure": cookie.get("secure", False),
                        "sameSite": cookie.get("sameSite", "Lax"),
                    }
                    cookies_json.append(cookie_data)

                # ПРАВИЛЬНО: Используем datetime.utcnow() как в TimestampMixin
                # Это возвращает naive datetime, что нужно для TIMESTAMP WITHOUT TIME ZONE
                now_utc_naive = datetime.utcnow()

                # Обновляем профиль с новыми cookies
                await session.execute(
                    update(Profile)
                    .where(Profile.id == profile.id)
                    .values(
                        cookies=cookies_json,
                        last_used=now_utc_naive,  # naive datetime как в базе
                        warmup_sites_visited=len(cookies_json),
                        status="warmed_up" if len(cookies_json) > 10 else "warming",
                        # updated_at обновится автоматически через TimestampMixin
                    )
                )
                await session.commit()

                logger.info(
                    f"💾 Saved {len(cookies_json)} cookies to profile",
                    profile_id=str(profile.id),
                    cookies_count=len(cookies_json),
                )

        except Exception as e:
            logger.error(f"❌ Failed to save cookies to profile: {e}")

    async def _select_and_assign_proxy(
        self, profile: Profile
    ) -> Optional[Dict[str, Any]]:
        """Выбрать прокси из стратегии профиля и назначить его"""
        try:
            # ВАРИАНТ 1: Прокси из стратегии профиля
            if profile.nurture_strategy_id:
                selected_proxy = await self._get_proxy_from_strategy(
                    profile.nurture_strategy_id
                )
                if selected_proxy:
                    await self._save_proxy_to_profile_session(profile, selected_proxy)
                    logger.info(
                        f"🌐 Assigned proxy from strategy to profile",
                        profile_id=str(profile.id),
                        strategy_id=str(profile.nurture_strategy_id),
                        proxy_host=selected_proxy.get("host"),
                        proxy_type=selected_proxy.get("type", "http"),
                    )
                    return selected_proxy

            # ВАРИАНТ 2: Используем уже сохраненную прокси из profile.proxy_config
            if profile.proxy_config:
                logger.info(
                    f"🌐 Using existing proxy config from profile",
                    profile_id=str(profile.id),
                    proxy_host=profile.proxy_config.get("host"),
                    proxy_type=profile.proxy_config.get("type", "http"),
                )
                return profile.proxy_config

            # ВАРИАНТ 3: Тестовая прокси для дебага (если нет стратегии)
            if not profile.nurture_strategy_id:
                logger.debug(
                    f"Profile {profile.id} has no nurture strategy, creating test proxy for debug"
                )
                test_proxy = {
                    "type": "http",
                    "host": "127.0.0.1",
                    "port": 8080,
                    "username": "test",
                    "password": "test123",
                }
                await self._save_proxy_to_profile_session(profile, test_proxy)
                logger.info(f"🧪 Assigned test proxy for profile without strategy")
                return test_proxy

            logger.debug(f"No proxy available for profile {profile.id}")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to select proxy for profile {profile.id}: {e}")
            return None

    async def _get_proxy_from_strategy(
        self, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получить прокси из стратегии"""
        try:
            async with async_session_maker() as session:
                from app.models.strategies import UserStrategy
                from app.models.strategy_proxy import StrategyProxySource

                result = await session.execute(
                    select(UserStrategy)
                    .options(selectinload(UserStrategy.proxy_sources))
                    .where(UserStrategy.id == strategy_id)
                )
                strategy = result.scalar_one_or_none()

                if not strategy or not strategy.proxy_sources:
                    logger.debug(f"Strategy {strategy_id} has no proxy sources")
                    return None

                # Фильтруем активные источники прокси
                active_sources = [
                    source for source in strategy.proxy_sources if source.is_active
                ]
                if not active_sources:
                    logger.debug(f"Strategy {strategy_id} has no active proxy sources")
                    return None

                # Разделяем источники на статические и динамические
                static_sources = [
                    s
                    for s in active_sources
                    if s.source_type in ["manual_list", "file_upload"]
                ]
                dynamic_sources = [
                    s
                    for s in active_sources
                    if s.source_type in ["url_import", "google_sheets", "google_docs"]
                ]

                selected_proxy = None

                # Если есть оба типа - выбираем случайно
                if static_sources and dynamic_sources:
                    use_static = random.choice([True, False])
                    if use_static:
                        selected_proxy = await self._get_random_static_proxy(
                            static_sources
                        )
                    else:
                        selected_proxy = await self._get_random_dynamic_proxy(
                            dynamic_sources
                        )
                # Если только статические
                elif static_sources:
                    selected_proxy = await self._get_random_static_proxy(static_sources)
                # Если только динамические
                elif dynamic_sources:
                    selected_proxy = await self._get_random_dynamic_proxy(
                        dynamic_sources
                    )

                return selected_proxy

        except Exception as e:
            logger.error(f"❌ Failed to get proxy from strategy {strategy_id}: {e}")
            return None

    async def _save_proxy_to_profile_session(
        self, profile: Profile, proxy_config: Dict[str, Any]
    ) -> None:
        """Сохранить прокси в профиль (в рамках текущей сессии)"""
        try:
            # Логируем что именно сохраняем ПЕРЕД сохранением
            logger.error(f"🔍 BEFORE SAVE - proxy config: {proxy_config}")

            async with async_session_maker() as session:
                await session.execute(
                    update(Profile)
                    .where(Profile.id == profile.id)
                    .values(proxy_config=proxy_config)
                )
                await session.commit()

                # Обновляем объект профиля в памяти
                profile.proxy_config = proxy_config

                # Проверяем что сохранилось
                check_result = await session.execute(
                    select(Profile.proxy_config).where(Profile.id == profile.id)
                )
                saved_config = check_result.scalar_one()
                logger.error(f"🔍 AFTER SAVE - saved config: {saved_config}")

                logger.info(
                    f"💾 Saved proxy config to profile",
                    profile_id=str(profile.id),
                    proxy_host=proxy_config.get("host"),
                    proxy_port=proxy_config.get("port"),
                    proxy_type=proxy_config.get("type"),
                )

        except Exception as e:
            logger.error(f"❌ Failed to save proxy to profile: {e}")

    async def _get_random_static_proxy(
        self, static_sources: List
    ) -> Optional[Dict[str, Any]]:
        """Получить случайную прокси из статических источников"""
        try:
            # Собираем все прокси из статических источников
            all_proxies = []

            for source in static_sources:
                if source.proxy_data:
                    logger.info(
                        f"🔍 Processing proxy source: {source.proxy_data[:100]}..."
                    )
                    # Парсим прокси из текста
                    proxies = self._parse_proxy_list(source.proxy_data)
                    all_proxies.extend(proxies)

            if not all_proxies:
                logger.warning("No valid proxies found in static sources")
                return None

            # Выбираем случайную прокси
            selected_proxy = random.choice(all_proxies)
            logger.info(f"🎯 Selected proxy: {selected_proxy}")
            return selected_proxy

        except Exception as e:
            logger.error(f"❌ Failed to get static proxy: {e}")
            return None

    async def _get_random_dynamic_proxy(
        self, dynamic_sources: List
    ) -> Optional[Dict[str, Any]]:
        """Получить случайную прокси из динамических источников"""
        try:
            # Выбираем случайный динамический источник
            source = random.choice(dynamic_sources)

            if source.source_type == "url_import":
                return await self._fetch_proxy_from_url(source.source_url)
            elif source.source_type == "google_sheets":
                return await self._fetch_proxy_from_google_sheets(source.source_url)
            elif source.source_type == "google_docs":
                return await self._fetch_proxy_from_google_docs(source.source_url)

            return None

        except Exception as e:
            logger.error(f"❌ Failed to get dynamic proxy: {e}")
            return None

    async def _fetch_proxy_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Загрузить прокси из URL"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = self._parse_proxy_list(text)
                        if proxies:
                            return random.choice(proxies)
                    else:
                        logger.warning(
                            f"Failed to fetch proxy from URL {url}: HTTP {response.status}"
                        )

            return None

        except Exception as e:
            logger.error(f"❌ Failed to fetch proxy from URL {url}: {e}")
            return None

    async def _fetch_proxy_from_google_sheets(
        self, url: str
    ) -> Optional[Dict[str, Any]]:
        """Загрузить прокси из Google Sheets"""
        try:
            # Конвертируем URL в CSV export URL
            if "/edit" in url or "/view" in url:
                # Извлекаем ID таблицы
                sheet_id_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
                if sheet_id_match:
                    sheet_id = sheet_id_match.group(1)
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as session:
                        async with session.get(csv_url) as response:
                            if response.status == 200:
                                text = await response.text()
                                proxies = self._parse_proxy_list(text)
                                if proxies:
                                    return random.choice(proxies)

            return None

        except Exception as e:
            logger.error(f"❌ Failed to fetch proxy from Google Sheets {url}: {e}")
            return None

    async def _fetch_proxy_from_google_docs(self, url: str) -> Optional[Dict[str, Any]]:
        """Загрузить прокси из Google Docs"""
        try:
            # Конвертируем URL в текстовый export URL
            if "/edit" in url or "/view" in url:
                # Извлекаем ID документа
                doc_id_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
                if doc_id_match:
                    doc_id = doc_id_match.group(1)
                    txt_url = (
                        f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
                    )

                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as session:
                        async with session.get(txt_url) as response:
                            if response.status == 200:
                                text = await response.text()
                                proxies = self._parse_proxy_list(text)
                                if proxies:
                                    return random.choice(proxies)

            return None

        except Exception as e:
            logger.error(f"❌ Failed to fetch proxy from Google Docs {url}: {e}")
            return None

    def _parse_proxy_list(self, text: str) -> List[Dict[str, Any]]:
        """Парсинг списка прокси из текста - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        proxies = []

        logger.info(f"🔍 Parsing proxy list from text: {text[:200]}...")

        # ИСПРАВЛЕННЫЕ регулярные выражения
        patterns = [
            # protocol://username:password@host:port (САМЫЙ РАСПРОСТРАНЕННЫЙ ФОРМАТ)
            r"^(https?|socks[45]?)://([^:/@]+):([^@]+)@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$",
            # host:port:username:password (формат ip:port:user:pass)
            r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+):([^:\s]+):(.+)$",
            # username:password@host:port (без протокола)
            r"^([^:@\s]+):([^@\s]+)@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$",
            # protocol://host:port (без аутентификации)
            r"^(https?|socks[45]?)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$",
            # host:port (простейший формат)
            r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$",
        ]

        for line_num, line in enumerate(text.strip().split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            logger.debug(f"🔍 Parsing line {line_num}: {line}")

            proxy = None

            for pattern_num, pattern in enumerate(patterns, 1):
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    logger.debug(
                        f"🎯 Pattern {pattern_num} matched with groups: {groups}"
                    )

                    if pattern_num == 1:
                        # protocol://username:password@host:port
                        proxy = {
                            "type": groups[0],  # http, https, socks4, socks5
                            "host": groups[3],
                            "port": int(groups[4]),
                            "username": groups[1],
                            "password": groups[2],
                        }
                    elif pattern_num == 2:
                        # host:port:username:password
                        proxy = {
                            "type": "http",
                            "host": groups[0],
                            "port": int(groups[1]),
                            "username": groups[2],
                            "password": groups[3],
                        }
                    elif pattern_num == 3:
                        # username:password@host:port
                        proxy = {
                            "type": "http",
                            "host": groups[2],
                            "port": int(groups[3]),
                            "username": groups[0],
                            "password": groups[1],
                        }
                    elif pattern_num == 4:
                        # protocol://host:port
                        proxy = {
                            "type": groups[0],
                            "host": groups[1],
                            "port": int(groups[2]),
                            # НЕТ username/password
                        }
                    elif pattern_num == 5:
                        # host:port
                        proxy = {
                            "type": "http",
                            "host": groups[0],
                            "port": int(groups[1]),
                            # НЕТ username/password
                        }

                    if proxy is not None:
                        logger.info(f"✅ Parsed proxy from line {line_num}: {proxy}")
                        proxies.append(proxy)
                        break

            if proxy is None:
                logger.warning(f"⚠️ Could not parse line {line_num}: {line}")

        logger.info(f"🎉 Total parsed proxies: {len(proxies)}")
        return proxies

    async def _save_proxy_to_profile(
        self, session: AsyncSession, profile: Profile, proxy_config: Dict[str, Any]
    ) -> None:
        """Сохранить прокси в профиль"""
        try:
            await session.execute(
                update(Profile)
                .where(Profile.id == profile.id)
                .values(proxy_config=proxy_config)
            )
            await session.commit()

            logger.info(
                f"💾 Saved proxy config to profile",
                profile_id=str(profile.id),
                proxy_host=proxy_config.get("host"),
                proxy_port=proxy_config.get("port"),
            )

        except Exception as e:
            logger.error(f"❌ Failed to save proxy to profile: {e}")

    def _build_proxy_args(self, proxy_config: Dict[str, Any]) -> List[str]:
        """Построить аргументы командной строки для прокси"""
        proxy_args = []

        try:
            host = proxy_config.get("host")
            port = proxy_config.get("port")
            proxy_type = proxy_config.get("type", "http")
            username = proxy_config.get("username")
            password = proxy_config.get("password")

            # ОТЛАДОЧНОЕ ЛОГИРОВАНИЕ - показываем ВСЕ что пришло
            logger.error(f"🔍 FULL PROXY CONFIG DEBUG: {proxy_config}")
            logger.error(
                f"🔍 PARSED VALUES: type={repr(proxy_type)}, host={repr(host)}, port={repr(port)}, username={repr(username)}, password={repr(password)}"
            )

            if not host or not port:
                logger.warning("Invalid proxy config: missing host or port")
                return proxy_args

            # Проверяем что username НЕ равен type
            if username == proxy_type:
                logger.error(
                    f"🚨 BUG DETECTED: username equals proxy_type! username={username}, type={proxy_type}"
                )
                logger.error(
                    "🚨 This suggests parsing error in _parse_proxy_list method"
                )

            # Очищаем proxy_type от протокола если он там есть
            if proxy_type.startswith("http://"):
                clean_proxy_type = "http"
            elif proxy_type.startswith("https://"):
                clean_proxy_type = "http"  # Chromium использует http для HTTPS прокси
            elif proxy_type.startswith("socks4://"):
                clean_proxy_type = "socks4"
            elif proxy_type.startswith("socks5://"):
                clean_proxy_type = "socks5"
            else:
                clean_proxy_type = proxy_type.lower()

            # Формируем proxy-server аргумент
            if username and password and username != clean_proxy_type:
                # Для прокси с авторизацией включаем username:password в URL
                if clean_proxy_type in ["socks4", "socks5"]:
                    proxy_server = (
                        f"{clean_proxy_type}://{username}:{password}@{host}:{port}"
                    )
                else:
                    # Для HTTP/HTTPS всегда используем http://
                    proxy_server = f"http://{username}:{password}@{host}:{port}"
            else:
                # Прокси без авторизации ИЛИ некорректные данные
                if username == clean_proxy_type:
                    logger.warning(
                        f"⚠️ Skipping auth due to username={username} == type={clean_proxy_type}"
                    )

                if clean_proxy_type in ["socks4", "socks5"]:
                    proxy_server = f"{clean_proxy_type}://{host}:{port}"
                else:
                    # Для HTTP/HTTPS всегда используем http://
                    proxy_server = f"http://{host}:{port}"

            proxy_args.append(f"--proxy-server={proxy_server}")

            # Отключаем прокси для localhost
            proxy_args.append("--proxy-bypass-list=localhost,127.0.0.1")

            logger.info(f"🌐 Built proxy args: {proxy_args}")
            logger.info(f"🌐 Final proxy URL: {proxy_server}")

        except Exception as e:
            logger.error(f"❌ Failed to build proxy args: {e}")

        return proxy_args


# Глобальный экземпляр worker'а
profile_nurture_worker = ProfileNurtureWorker()


async def start_profile_nurture_worker():
    """Запустить worker в фоновом режиме"""
    asyncio.create_task(profile_nurture_worker.start())


async def stop_profile_nurture_worker():
    """Остановить worker"""
    await profile_nurture_worker.stop()
