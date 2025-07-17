# backend/app/workers/profile_nurture_worker.py

import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session_maker
from app.core.task_manager import TaskManager, TaskType, TaskStatus
from app.core.browser_manager import BrowserManager
from app.models import Task, Profile, DeviceType
from app.constants.strategies import ProfileNurtureType

logger = structlog.get_logger(__name__)


class ProfileNurtureWorker:
    """Worker для обработки задач нагула профилей"""

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

                logger.info(
                    "Starting profile nurture task",
                    task_id=str(task.id),
                    worker_id=self.worker_id,
                    strategy_id=task.parameters.get("strategy_id"),
                )

                # Извлекаем параметры задачи
                strategy_config = task.parameters.get("strategy_config", {})
                nurture_type = strategy_config.get("nurture_type", "search_based")
                device_type = DeviceType(task.device_type)

                # Выполняем нагул в зависимости от типа
                if nurture_type == "search_based":
                    result = await self._execute_search_based_nurture(
                        task, strategy_config, browser_manager, device_type
                    )
                elif nurture_type == "direct_visits":
                    result = await self._execute_direct_visits_nurture(
                        task, strategy_config, browser_manager, device_type
                    )
                elif nurture_type == "mixed_nurture":
                    result = await self._execute_mixed_nurture(
                        task, strategy_config, browser_manager, device_type
                    )
                else:
                    raise ValueError(f"Unsupported nurture type: {nurture_type}")

                # Отмечаем задачу как завершенную
                await task_manager.mark_task_completed(str(task.id), result)

                logger.info(
                    "Profile nurture task completed",
                    task_id=str(task.id),
                    worker_id=self.worker_id,
                    strategy_id=task.parameters.get("strategy_id"),
                    nurture_type=nurture_type,
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

        # Запускаем браузер
        browser = await browser_manager.launch_browser(profile)

        try:
            # Получаем параметры нагула
            target_cookies = config.get("target_cookies", {"min": 50, "max": 100})
            search_engines = config.get("search_engines", ["yandex.ru"])
            queries_source = config.get("queries_source", {})
            session_config = config.get("session_config", {})

            # Целевое количество куков
            target_count = random.randint(target_cookies["min"], target_cookies["max"])

            # Получаем список запросов для поиска
            queries = await self._get_search_queries(queries_source, limit=20)

            if not queries:
                raise ValueError("No search queries available for nurturing")

            cookies_collected = 0
            sites_visited = []

            for i, query in enumerate(queries[:target_count]):
                if cookies_collected >= target_count:
                    break

                # Выбираем случайную поисковую систему
                search_engine = random.choice(search_engines)

                # Выполняем поиск и переходы
                search_result = await self._perform_search_and_visits(
                    browser, query, search_engine, session_config
                )

                cookies_collected += search_result.get("cookies_added", 0)
                sites_visited.extend(search_result.get("sites_visited", []))

                # Случайная пауза между поисками
                delay = random.uniform(3, 8)
                await asyncio.sleep(delay)

            # Обновляем профиль
            await browser_manager.update_profile_cookies(profile, browser)

            return {
                "success": True,
                "nurture_type": "search_based",
                "profile_id": str(profile.id),
                "cookies_collected": cookies_collected,
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
                browser_manager.session, task.profile_id
            )
        else:
            profile = await browser_manager.create_profile(device_type=device_type)

        browser = await browser_manager.launch_browser(profile)

        try:
            # Получаем параметры
            target_cookies = config.get("target_cookies", {"min": 50, "max": 100})
            direct_sites_source = config.get("direct_sites_source", {})
            session_config = config.get("session_config", {})

            target_count = random.randint(target_cookies["min"], target_cookies["max"])

            # Получаем список сайтов для прямых заходов
            sites = await self._get_direct_sites(
                direct_sites_source, limit=target_count
            )

            if not sites:
                raise ValueError("No direct sites available for nurturing")

            cookies_collected = 0
            sites_visited = []

            for site in sites[:target_count]:
                if cookies_collected >= target_count:
                    break

                # Выполняем прямой заход на сайт
                visit_result = await self._perform_direct_visit(
                    browser, site, session_config
                )

                cookies_collected += visit_result.get("cookies_added", 0)
                sites_visited.append(site)

                # Пауза между заходами
                delay = random.uniform(2, 6)
                await asyncio.sleep(delay)

            # Обновляем профиль
            await browser_manager.update_profile_cookies(profile, browser)

            return {
                "success": True,
                "nurture_type": "direct_visits",
                "profile_id": str(profile.id),
                "cookies_collected": cookies_collected,
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
        # TODO: Реализовать получение запросов из различных источников
        # В зависимости от queries_source.type может быть:
        # - manual_input: из queries_source.queries
        # - file_upload: из загруженного файла
        # - url_endpoint: с внешнего URL
        # - google_docs/google_sheets: из Google документов

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

        # TODO: Добавить поддержку других источников
        return []

    async def _get_direct_sites(
        self, sites_source: Dict[str, Any], limit: int = 20
    ) -> List[str]:
        """Получить список сайтов для прямых заходов"""
        # TODO: Аналогично queries, поддержка разных источников

        source_type = sites_source.get("type", "manual_input")

        if source_type == "manual_input":
            return sites_source.get(
                "sites",
                [
                    "https://www.ozon.ru",
                    "https://www.wildberries.ru",
                    "https://market.yandex.ru",
                    "https://www.dns-shop.ru",
                    "https://www.mvideo.ru",
                    "https://www.eldorado.ru",
                    "https://www.lamoda.ru",
                    "https://www.sportmaster.ru",
                    "https://www.citilink.ru",
                    "https://www.technopark.ru",
                ],
            )[:limit]

        return []

    async def _perform_search_and_visits(
        self,
        browser,
        query: str,
        search_engine: str,
        session_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Выполнить поиск и переходы по результатам"""
        # TODO: Реализовать логику поиска и переходов
        # Возвращаем заглушку
        await asyncio.sleep(random.uniform(1, 3))
        return {
            "cookies_added": random.randint(3, 8),
            "sites_visited": [f"example{i}.com" for i in range(random.randint(1, 3))],
        }

    async def _perform_direct_visit(
        self,
        browser,
        site: str,
        session_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Выполнить прямой заход на сайт"""
        # TODO: Реализовать логику прямого захода
        # Возвращаем заглушку
        await asyncio.sleep(random.uniform(1, 2))
        return {
            "cookies_added": random.randint(2, 5),
        }


# Глобальный экземпляр worker'а
profile_nurture_worker = ProfileNurtureWorker()


async def start_profile_nurture_worker():
    """Запустить worker в фоновом режиме"""
    asyncio.create_task(profile_nurture_worker.start())


async def stop_profile_nurture_worker():
    """Остановить worker"""
    await profile_nurture_worker.stop()
