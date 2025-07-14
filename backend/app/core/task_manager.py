import asyncio
import random
import socket
import psutil
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from playwright.async_api import async_playwright
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
import structlog

from app.models import (
    Task,
    Profile,
    ServerConfig,
    WorkerNode,
    DeviceType,
    UserKeyword,
    UserDomain,
    ParseResult,
    PositionHistory,
)
from app.database import async_session_maker
from .browser_manager import BrowserManager
from .strategy_executor import StrategyExecutor

logger = structlog.get_logger(__name__)


class TaskType(Enum):
    WARMUP_PROFILE = "warmup_profile"
    PARSE_SERP = "parse_serp"
    CHECK_POSITIONS = "check_positions"
    HEALTH_CHECK = "health_check"
    MAINTAIN_PROFILES = "maintain_profiles"
    STRATEGY_WARMUP = "strategy_warmup"
    STRATEGY_POSITION_CHECK = "strategy_position_check"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskManager:
    """Менеджер задач для координации всех операций системы"""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.browser_manager = BrowserManager(db_session)
        # Импортируем только после инициализации browser_manager, чтобы избежать циклического импорта
        from .yandex_parser import YandexParser

        self.parser = YandexParser(db_session)
        self.running = False
        self.server_id = f"server-{socket.gethostname()}"
        self.worker_id = f"worker-{socket.gethostname()}-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.current_tasks = {}  # Словарь выполняющихся задач
        self.max_concurrent_tasks = 5  # По умолчанию
        self.strategy_executor = StrategyExecutor(self.browser_manager)

    async def get_session(self) -> AsyncSession:
        """Получает сессию БД"""
        if self.db:
            return self.db
        else:
            async with async_session_maker() as session:
                return session

    async def initialize(self):
        """Инициализация менеджера задач"""
        session = await self.get_session()

        try:
            # Получаем конфигурацию сервера
            server_config = await self._get_server_config(session)
            if server_config:
                self.max_concurrent_tasks = server_config.max_concurrent_workers or 5

            # Регистрируем worker node
            await self._register_worker_node(session)

            logger.info(
                "Task manager initialized",
                server_id=self.server_id,
                worker_id=self.worker_id,
                max_concurrent_tasks=self.max_concurrent_tasks,
            )

        except Exception as e:
            logger.error("Failed to initialize task manager", error=str(e))
            raise

    async def start(self):
        """Запуск основного цикла обработки задач"""
        await self.initialize()
        self.running = True

        logger.info("Task manager started")

        # Запускаем основные циклы
        await asyncio.gather(
            self._main_task_loop(),
            self._heartbeat_loop(),
            self._maintenance_loop(),
            return_exceptions=True,
        )

    async def stop(self):
        """Остановка менеджера задач"""
        self.running = False

        # Ждем завершения текущих задач
        if self.current_tasks:
            logger.info(
                "Waiting for current tasks to complete",
                active_tasks=len(self.current_tasks),
            )
            await asyncio.gather(*self.current_tasks.values(), return_exceptions=True)

        logger.info("Task manager stopped")

    async def _main_task_loop(self):
        """Основной цикл обработки задач"""
        while self.running:
            try:
                # Проверяем возможность взять новую задачу
                if len(self.current_tasks) < self.max_concurrent_tasks:
                    task = await self._get_next_task()

                    if task:
                        # Запускаем задачу асинхронно
                        task_coroutine = self._execute_task_wrapper(task)
                        self.current_tasks[str(task.id)] = asyncio.create_task(
                            task_coroutine
                        )

                        logger.info(
                            "Task started",
                            task_id=str(task.id),
                            task_type=task.task_type,
                            active_tasks=len(self.current_tasks),
                        )

                # Очищаем завершенные задачи
                await self._cleanup_completed_tasks()

                # Пауза перед следующей итерацией
                await asyncio.sleep(2)

            except Exception as e:
                logger.error("Error in main task loop", error=str(e))
                await asyncio.sleep(5)

    async def _heartbeat_loop(self):
        """Цикл отправки heartbeat"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat каждые 30 секунд
            except Exception as e:
                logger.error("Error in heartbeat loop", error=str(e))
                await asyncio.sleep(5)

    async def _maintenance_loop(self):
        """Цикл maintenance задач"""
        while self.running:
            try:
                # Проверяем нужно ли создать maintenance задачи
                await self._schedule_maintenance_tasks()
                await asyncio.sleep(300)  # Проверяем каждые 5 минут
            except Exception as e:
                logger.error("Error in maintenance loop", error=str(e))
                await asyncio.sleep(60)

    async def _get_next_task(self) -> Optional[Task]:
        """Получает следующую задачу для выполнения"""
        session = await self.get_session()

        try:
            # Получаем задачу с наивысшим приоритетом
            result = await session.execute(
                select(Task)
                .where(Task.status == TaskStatus.PENDING.value)
                .order_by(Task.priority.desc(), Task.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )

            task = result.scalar_one_or_none()

            if task:
                # Резервируем задачу
                task.status = TaskStatus.RUNNING.value
                task.started_at = datetime.now(timezone.utc)
                task.worker_id = self.worker_id
                await session.commit()

                return task

            return None

        except Exception as e:
            await session.rollback()
            logger.error("Failed to get next task", error=str(e))
            return None

    async def _execute_task_wrapper(self, task: Task):
        """Обертка для выполнения задачи с обработкой ошибок"""
        session = await self.get_session()

        try:
            logger.info(
                "Executing task", task_id=str(task.id), task_type=task.task_type
            )

            # Выполняем задачу в зависимости от типа
            if task.task_type == TaskType.WARMUP_PROFILE.value:
                await self._execute_warmup_profile_task(task, session)
            elif task.task_type == TaskType.PARSE_SERP.value:
                await self._execute_parse_serp_task(task, session)
            elif task.task_type == TaskType.CHECK_POSITIONS.value:
                await self._execute_check_positions_task(task, session)
            elif task.task_type == TaskType.HEALTH_CHECK.value:
                await self._execute_health_check_task(task, session)
            elif task.task_type == TaskType.MAINTAIN_PROFILES.value:
                await self._execute_maintain_profiles_task(task, session)
            elif task.task_type == TaskType.STRATEGY_WARMUP.value:
                await self._execute_strategy_warmup_task(task, session)
            elif task.task_type == TaskType.STRATEGY_POSITION_CHECK.value:
                await self._execute_strategy_position_check_task(task, session)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            # Отмечаем задачу как выполненную
            task.status = TaskStatus.COMPLETED.value
            task.completed_at = datetime.now(timezone.utc)
            await session.commit()

            logger.info("Task completed successfully", task_id=str(task.id))

        except Exception as e:
            # Отмечаем задачу как неудачную
            task.status = TaskStatus.FAILED.value
            task.completed_at = datetime.now(timezone.utc)
            task.error_message = str(e)
            await session.commit()

            logger.error("Task failed", task_id=str(task.id), error=str(e))

            # Планируем повторную попытку для некоторых типов задач
            await self._schedule_retry_if_needed(task, session)

        finally:
            # Убираем задачу из списка активных
            if str(task.id) in self.current_tasks:
                del self.current_tasks[str(task.id)]

    async def _execute_warmup_profile_task(self, task: Task, session: AsyncSession):
        """Выполняет задачу прогрева профиля"""
        parameters = task.parameters or {}
        profile_id = parameters.get("profile_id")
        device_type = DeviceType(parameters.get("device_type", "desktop"))

        if profile_id:
            # Получаем существующий профиль
            result = await session.execute(
                select(Profile).where(Profile.id == profile_id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
        else:
            # Создаем новый профиль
            profile = await self.browser_manager.create_profile(device_type=device_type)

        # Прогреваем профиль
        success = await self.browser_manager.warmup_profile(profile)

        task.result = {
            "profile_id": str(profile.id),
            "device_type": device_type.value,
            "success": success,
            "warmup_sites_visited": profile.warmup_sites_visited,
        }

        if not success:
            raise Exception("Profile warmup failed")

    async def _execute_parse_serp_task(self, task: Task, session: AsyncSession):
        """Выполняет задачу парсинга SERP"""
        parameters = task.parameters
        keyword = parameters["keyword"]
        device_type = DeviceType(parameters.get("device_type", "desktop"))
        pages = parameters.get("pages", 10)
        region_code = parameters.get("region_code", "213")
        profile_id = parameters.get("profile_id")

        # Получаем профиль
        if profile_id:
            result = await session.execute(
                select(Profile).where(Profile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
        else:
            profile = await self.browser_manager.get_ready_profile(device_type)

        if not profile:
            raise Exception(f"No ready {device_type.value} profile available")

        # Парсим SERP
        results = await self.parser.parse_serp(
            keyword=keyword, profile=profile, pages=pages, region_code=region_code
        )

        # Сохраняем результаты
        for result in results:
            result.task_id = task.id
            session.add(result)

        task.result = {
            "keyword": keyword,
            "device_type": device_type.value,
            "results_count": len(results),
            "profile_id": str(profile.id),
        }

        # Планируем каскад профиля если нужно
        await self._handle_profile_cascade(profile, session, parameters)

    async def _execute_check_positions_task(self, task: Task, session: AsyncSession):
        """Выполняет задачу проверки позиций"""
        parameters = task.parameters
        keyword_ids = parameters["keyword_ids"]  # Список ID ключевых слов
        device_type = DeviceType(parameters.get("device_type", "desktop"))

        # Получаем ключевые слова
        result = await session.execute(
            select(UserKeyword)
            .options(selectinload(UserKeyword.domain), selectinload(UserKeyword.region))
            .where(UserKeyword.id.in_(keyword_ids))
        )
        keywords = result.scalars().all()

        if not keywords:
            raise Exception("No keywords found")

        # Получаем профиль
        profile = await self.browser_manager.get_ready_profile(device_type)
        if not profile:
            raise Exception(f"No ready {device_type.value} profile available")

        results = []

        for keyword_obj in keywords:
            try:
                # Проверяем позицию домена
                position = await self.parser.check_position(
                    keyword=keyword_obj.keyword,
                    target_domain=keyword_obj.domain.domain,
                    profile=profile,
                    region_code=keyword_obj.region.region_code,
                )

                # Сохраняем результат в историю позиций
                position_record = PositionHistory(
                    user_id=keyword_obj.user_id,
                    domain_id=keyword_obj.domain_id,
                    keyword_id=keyword_obj.id,
                    position=position,
                    check_date=datetime.now(timezone.utc),
                )
                session.add(position_record)

                results.append(
                    {
                        "keyword_id": str(keyword_obj.id),
                        "keyword": keyword_obj.keyword,
                        "domain": keyword_obj.domain.domain,
                        "position": position,
                    }
                )

                # Пауза между проверками
                await asyncio.sleep(random.uniform(5, 15))

            except Exception as e:
                logger.error(
                    "Failed to check keyword position",
                    keyword_id=str(keyword_obj.id),
                    error=str(e),
                )
                results.append(
                    {
                        "keyword_id": str(keyword_obj.id),
                        "keyword": keyword_obj.keyword,
                        "domain": keyword_obj.domain.domain,
                        "position": None,
                        "error": str(e),
                    }
                )

        task.result = {
            "device_type": device_type.value,
            "checked_keywords": len(keywords),
            "results": results,
            "profile_id": str(profile.id),
        }

        # Планируем каскад профиля
        await self._handle_profile_cascade(profile, session, parameters)

    async def _execute_health_check_task(self, task: Task, session: AsyncSession):
        """Выполняет задачу проверки здоровья профилей"""
        parameters = task.parameters or {}
        device_type = parameters.get("device_type")

        # Получаем профили для проверки
        query = select(Profile).where(
            and_(Profile.is_warmed_up == True, Profile.status == "ready")
        )

        if device_type:
            query = query.where(Profile.device_type == DeviceType(device_type))

        # Фильтруем профили которые давно не проверялись
        check_threshold = datetime.now(timezone.utc) - timedelta(hours=1)
        query = query.where(
            or_(Profile.last_used < check_threshold, Profile.last_used.is_(None))
        ).limit(
            10
        )  # Проверяем максимум 10 профилей за раз

        result = await session.execute(query)
        profiles = result.scalars().all()

        checked_profiles = 0
        corrupted_profiles = 0

        for profile in profiles:
            try:
                is_healthy = await self.browser_manager.health_check_profile(profile)

                if not is_healthy:
                    corrupted_profiles += 1

                checked_profiles += 1

                # Пауза между проверками
                await asyncio.sleep(random.uniform(3, 8))

            except Exception as e:
                logger.error(
                    "Health check failed", profile_id=str(profile.id), error=str(e)
                )

        task.result = {
            "checked_profiles": checked_profiles,
            "corrupted_profiles": corrupted_profiles,
            "device_type": device_type,
        }

    async def _execute_maintain_profiles_task(self, task: Task, session: AsyncSession):
        """Выполняет задачу поддержания пула профилей"""
        await self.browser_manager.maintain_warm_profiles_pool()

        # Получаем статистику профилей
        desktop_count = await session.scalar(
            select(func.count(Profile.id)).where(
                and_(
                    Profile.device_type == DeviceType.DESKTOP,
                    Profile.is_warmed_up == True,
                    Profile.status == "ready",
                )
            )
        )

        mobile_count = await session.scalar(
            select(func.count(Profile.id)).where(
                and_(
                    Profile.device_type == DeviceType.MOBILE,
                    Profile.is_warmed_up == True,
                    Profile.status == "ready",
                )
            )
        )

        task.result = {
            "desktop_profiles": desktop_count,
            "mobile_profiles": mobile_count,
            "total_profiles": desktop_count + mobile_count,
        }

    async def _execute_strategy_warmup_task(self, task: Task, session: AsyncSession):
        """Выполнение задачи стратегии прогрева"""

        logger.info("Executing strategy warmup task", task_id=str(task.id))

        try:
            # Выполняем стратегию прогрева
            result = await self.strategy_executor.execute_warmup_strategy(task, session)

            # Сохраняем результат
            task.result = result

            # Обновляем лог выполнения стратегии
            await self._update_strategy_execution_log(task, "completed", result)

            logger.info(
                "Strategy warmup completed",
                task_id=str(task.id),
                actions_completed=result.get("actions_completed", 0),
                actions_failed=result.get("actions_failed", 0),
            )

        except Exception as e:
            # Обновляем лог выполнения стратегии с ошибкой
            await self._update_strategy_execution_log(task, "failed", None, str(e))
            raise

    async def _execute_strategy_position_check_task(
        self, task: Task, session: AsyncSession
    ):
        """Выполнение задачи стратегии проверки позиций"""

        logger.info("Executing strategy position check task", task_id=str(task.id))

        try:
            # Получаем данные для выполнения
            execution_data = task.parameters.get("execution_data", {})
            keywords = execution_data.get("keywords", [])

            if not keywords:
                raise Exception("No keywords provided for position check strategy")

            # Выполняем проверки позиций для каждого ключевого слова
            results = []
            total_checks = 0
            successful_checks = 0

            for keyword in keywords:
                try:
                    # Создаем подзадачу для проверки позиции
                    check_result = await self._execute_strategic_position_check(
                        keyword, execution_data, task.parameters.get("user_id"), session
                    )

                    results.append(
                        {"keyword": keyword, "success": True, "result": check_result}
                    )

                    successful_checks += 1

                except Exception as e:
                    results.append(
                        {"keyword": keyword, "success": False, "error": str(e)}
                    )

                    logger.warning(
                        "Strategic position check failed", keyword=keyword, error=str(e)
                    )

                total_checks += 1

                # Пауза между проверками
                await asyncio.sleep(random.uniform(3, 8))

            # Сохраняем общий результат
            summary_result = {
                "total_keywords": len(keywords),
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "success_rate": (
                    (successful_checks / total_checks * 100) if total_checks > 0 else 0
                ),
                "results": results,
            }

            task.result = summary_result

            # Обновляем лог выполнения стратегии
            await self._update_strategy_execution_log(task, "completed", summary_result)

            logger.info(
                "Strategy position check completed",
                task_id=str(task.id),
                total_checks=total_checks,
                successful_checks=successful_checks,
            )

        except Exception as e:
            # Обновляем лог выполнения стратегии с ошибкой
            await self._update_strategy_execution_log(task, "failed", None, str(e))
            raise

    async def _execute_strategic_position_check(
        self, keyword: str, execution_data: Dict, user_id: str, session: AsyncSession
    ) -> Dict:
        """Выполнение стратегической проверки позиции"""

        # Получаем конфигурацию
        search_config = execution_data.get("search_config", {})
        behavior_config = execution_data.get("behavior", {})

        # Получаем профиль для проверки
        device_types = search_config.get("device_types", ["desktop"])
        device_type = DeviceType(random.choice(device_types))

        profile = await self.browser_manager.get_ready_profile(device_type=device_type)
        if not profile:
            profile = await self.browser_manager.create_profile(device_type=device_type)
            await self.browser_manager.warmup_profile(profile)

        # Выполняем проверку позиции с учетом стратегического поведения
        result = await self._strategic_serp_parsing(
            keyword, profile, search_config, behavior_config, session
        )

        return result

    async def _strategic_serp_parsing(
        self,
        keyword: str,
        profile: Profile,
        search_config: Dict,
        behavior_config: Dict,
        session: AsyncSession,
    ) -> Dict:
        """SERP парсинг с учетом стратегического поведения"""

        async with async_playwright() as p:
            # Запускаем браузер с профилем
            browser = await self.strategy_executor._launch_browser_with_profile(
                p, profile
            )
            context = (
                browser.contexts[0] if browser.contexts else await browser.new_context()
            )
            page = await context.new_page()

            try:
                # Формируем URL поиска
                yandex_domain = search_config.get("yandex_domain", "yandex.ru")
                pages_to_check = search_config.get("pages_to_check", 10)

                search_url = f"https://{yandex_domain}/search/?text={keyword}"
                await page.goto(search_url, wait_until="networkidle", timeout=30000)

                # Проверяем наличие капчи
                captcha_present = await page.query_selector(".captcha") is not None
                if captcha_present:
                    raise Exception("Captcha detected during strategic position check")

                # Стратегическое поведение на SERP
                if behavior_config.get("scroll_serp", True):
                    await self.strategy_executor._scroll_serp_naturally(page)

                # Время на изучение SERP
                time_config = behavior_config.get("time_on_serp", {"min": 5, "max": 15})
                await asyncio.sleep(
                    random.uniform(time_config["min"], time_config["max"])
                )

                # Простой парсинг результатов поиска (заглушка)
                results = await self._parse_serp_results_basic(page, pages_to_check)

                # Стратегические клики на конкурентов
                competitor_click_prob = behavior_config.get("click_competitors", 0.1)
                if random.random() < competitor_click_prob:
                    await self.strategy_executor._click_search_result(page, {})

                # Обновляем профиль
                cookies = await context.cookies()
                profile.cookies = cookies
                profile.last_used = datetime.now(timezone.utc)
                await session.commit()

                return {
                    "keyword": keyword,
                    "results_found": len(results),
                    "results": results,
                    "captcha_encountered": False,
                    "strategic_behavior_applied": True,
                }

            except Exception as e:
                logger.error(
                    "Strategic SERP parsing failed",
                    keyword=keyword,
                    profile_id=str(profile.id),
                    error=str(e),
                )
                raise

            finally:
                await browser.close()

    async def _parse_serp_results_basic(self, page, pages_to_check: int) -> List[Dict]:
        """Базовый парсинг результатов поиска (заглушка)"""
        try:
            # Ищем органические результаты
            results = []
            organic_results = await page.query_selector_all(".serp-item")

            for i, result_element in enumerate(organic_results[:pages_to_check]):
                try:
                    # Получаем заголовок
                    title_element = await result_element.query_selector("h3")
                    title = (
                        await title_element.inner_text()
                        if title_element
                        else f"Result {i+1}"
                    )

                    # Получаем URL
                    link_element = await result_element.query_selector("a")
                    url = (
                        await link_element.get_attribute("href") if link_element else ""
                    )

                    results.append(
                        {"position": i + 1, "title": title, "url": url, "snippet": ""}
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse result {i+1}", error=str(e))
                    continue

            return results
        except Exception as e:
            logger.error("Failed to parse SERP results", error=str(e))
            return []

    async def _handle_profile_cascade(
        self, profile: Profile, session: AsyncSession, parameters: Dict[str, Any]
    ):
        """Обрабатывает каскад профиля после использования"""
        try:
            cascade_enabled = parameters.get("cascade_enabled", True)

            if not cascade_enabled:
                return

            # Планируем задачу догуливания профиля
            cascade_task = Task(
                task_type=TaskType.WARMUP_PROFILE.value,
                status=TaskStatus.PENDING.value,
                priority=1,  # Низкий приоритет
                parameters={
                    "profile_id": str(profile.id),
                    "device_type": profile.device_type.value,
                    "cascade_mode": True,
                },
            )

            session.add(cascade_task)

        except Exception as e:
            logger.error(
                "Failed to handle profile cascade",
                profile_id=str(profile.id),
                error=str(e),
            )

    async def _schedule_retry_if_needed(self, task: Task, session: AsyncSession):
        """Планирует повторную попытку для задачи если нужно"""
        # Считаем количество попыток
        retry_count = task.parameters.get("retry_count", 0) if task.parameters else 0
        max_retries = 3

        if retry_count < max_retries and task.task_type in [
            TaskType.PARSE_SERP.value,
            TaskType.CHECK_POSITIONS.value,
            TaskType.WARMUP_PROFILE.value,
        ]:
            # Создаем новую задачу с увеличенным счетчиком
            retry_parameters = task.parameters.copy() if task.parameters else {}
            retry_parameters["retry_count"] = retry_count + 1

            retry_task = Task(
                task_type=task.task_type,
                status=TaskStatus.PENDING.value,
                priority=max(0, task.priority - 1),  # Снижаем приоритет
                parameters=retry_parameters,
            )

            session.add(retry_task)

            logger.info(
                "Retry task scheduled",
                original_task_id=str(task.id),
                retry_count=retry_count + 1,
            )

    async def _cleanup_completed_tasks(self):
        """Очищает завершенные задачи из памяти"""
        completed_task_ids = []

        for task_id, task_coroutine in self.current_tasks.items():
            if task_coroutine.done():
                completed_task_ids.append(task_id)

        for task_id in completed_task_ids:
            del self.current_tasks[task_id]

    async def _get_server_config(self, session: AsyncSession) -> Optional[ServerConfig]:
        """Получает конфигурацию сервера"""
        result = await session.execute(
            select(ServerConfig).where(ServerConfig.server_id == self.server_id)
        )
        return result.scalar_one_or_none()

    async def _register_worker_node(self, session: AsyncSession):
        """Регистрирует worker node в системе"""
        try:
            # Проверяем существует ли уже worker node
            result = await session.execute(
                select(WorkerNode).where(WorkerNode.node_id == self.worker_id)
            )
            worker_node = result.scalar_one_or_none()

            if not worker_node:
                worker_node = WorkerNode(
                    node_id=self.worker_id,
                    hostname=socket.gethostname(),
                    max_workers=self.max_concurrent_tasks,
                    capabilities={
                        "browsers": ["chrome", "firefox"],
                        "device_types": ["desktop", "mobile"],
                    },
                )
                session.add(worker_node)

            worker_node.status = "online"
            worker_node.last_heartbeat = datetime.now(timezone.utc)

            await session.commit()

        except Exception as e:
            logger.error("Failed to register worker node", error=str(e))

    async def _send_heartbeat(self):
        """Отправляет heartbeat"""
        session = await self.get_session()

        try:
            # Обновляем статус worker node
            await session.execute(
                update(WorkerNode)
                .where(WorkerNode.node_id == self.worker_id)
                .values(last_heartbeat=datetime.now(timezone.utc), status="online")
            )
            await session.commit()

        except Exception as e:
            logger.error("Failed to send heartbeat", error=str(e))

    async def _schedule_maintenance_tasks(self):
        """Планирует maintenance задачи"""
        session = await self.get_session()

        try:
            # Проверяем нужно ли создать задачу поддержания профилей
            last_maintain_task = await session.execute(
                select(Task)
                .where(Task.task_type == TaskType.MAINTAIN_PROFILES.value)
                .order_by(Task.created_at.desc())
                .limit(1)
            )

            last_task = last_maintain_task.scalar_one_or_none()

            # Создаем задачу если последняя была более 30 минут назад
            should_create = True
            if last_task:
                time_diff = datetime.now(timezone.utc) - last_task.created_at
                should_create = time_diff.total_seconds() > 1800  # 30 минут

            if should_create:
                maintain_task = Task(
                    task_type=TaskType.MAINTAIN_PROFILES.value,
                    status=TaskStatus.PENDING.value,
                    priority=5,
                    parameters={},
                )
                session.add(maintain_task)
                await session.commit()

                logger.info("Maintenance task scheduled")

            # Планируем health check задачи
            await self._schedule_health_check_tasks(session)

        except Exception as e:
            logger.error("Failed to schedule maintenance tasks", error=str(e))

    async def _schedule_health_check_tasks(self, session: AsyncSession):
        """Планирует задачи health check"""
        try:
            # Проверяем когда последний раз делали health check
            for device_type in [DeviceType.DESKTOP, DeviceType.MOBILE]:
                last_check = await session.execute(
                    select(Task)
                    .where(
                        and_(
                            Task.task_type == TaskType.HEALTH_CHECK.value,
                            Task.parameters.op("->>")("device_type")
                            == device_type.value,
                        )
                    )
                    .order_by(Task.created_at.desc())
                    .limit(1)
                )

                last_task = last_check.scalar_one_or_none()

                should_create = True
                if last_task:
                    time_diff = datetime.now(timezone.utc) - last_task.created_at
                    should_create = time_diff.total_seconds() > 3600  # 1 час

                if should_create:
                    health_check_task = Task(
                        task_type=TaskType.HEALTH_CHECK.value,
                        status=TaskStatus.PENDING.value,
                        priority=3,
                        parameters={"device_type": device_type.value},
                    )
                    session.add(health_check_task)

            await session.commit()

        except Exception as e:
            logger.error("Failed to schedule health check tasks", error=str(e))

    async def _update_strategy_execution_log(
        self,
        task: Task,
        status: str,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        """Обновление лога выполнения стратегии"""

        try:
            # Ищем лог выполнения по task_id
            from app.models.strategies import StrategyExecutionLog

            session = await self.get_session()
            log_result = await session.execute(
                select(StrategyExecutionLog).where(
                    StrategyExecutionLog.task_id == str(task.id)
                )
            )
            execution_log = log_result.scalar_one_or_none()

            if execution_log:
                execution_log.status = status
                execution_log.result = result
                execution_log.error_message = error_message

                if status == "running" and not execution_log.started_at:
                    execution_log.started_at = datetime.now(timezone.utc)
                elif status in ["completed", "failed"]:
                    execution_log.completed_at = datetime.now(timezone.utc)

                await session.commit()

                logger.info(
                    "Strategy execution log updated",
                    log_id=str(execution_log.id),
                    status=status,
                )

        except Exception as e:
            logger.error(
                "Failed to update strategy execution log",
                task_id=str(task.id),
                error=str(e),
            )

    # Методы для создания задач извне

    async def create_parse_task(
        self,
        keyword: str,
        device_type: DeviceType = DeviceType.DESKTOP,
        pages: int = 10,
        region_code: str = "213",
        priority: int = 5,
        user_id: Optional[str] = None,
        reserved_amount: Optional[float] = None,
        **kwargs,
    ) -> Task:
        """Создает задачу парсинга SERP"""
        session = await self.get_session()

        parameters = {
            "keyword": keyword,
            "device_type": device_type.value,
            "pages": pages,
            "region_code": region_code,
            **kwargs,
        }

        task = Task(
            task_type=TaskType.PARSE_SERP.value,
            status=TaskStatus.PENDING.value,
            priority=priority,
            user_id=user_id,
            parameters=parameters,
            reserved_amount=reserved_amount,
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(
            "Parse task created", task_id=str(task.id), keyword=keyword, user_id=user_id
        )
        return task

    async def create_position_check_task(
        self,
        keyword_ids: List[str],
        device_type: DeviceType = DeviceType.DESKTOP,
        priority: int = 10,
        user_id: Optional[str] = None,
        reserved_amount: Optional[float] = None,
        **kwargs,
    ) -> Task:
        """Создает задачу проверки позиций"""
        session = await self.get_session()

        parameters = {
            "keyword_ids": keyword_ids,
            "device_type": device_type.value,
            **kwargs,
        }

        task = Task(
            task_type=TaskType.CHECK_POSITIONS.value,
            status=TaskStatus.PENDING.value,
            priority=priority,
            user_id=user_id,
            parameters=parameters,
            reserved_amount=reserved_amount,
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(
            "Position check task created",
            task_id=str(task.id),
            keywords_count=len(keyword_ids),
            user_id=user_id,
        )
        return task

    async def create_warmup_task(
        self,
        device_type: DeviceType = DeviceType.DESKTOP,
        profile_id: Optional[str] = None,
        priority: int = 2,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Task:
        """Создает задачу прогрева профиля"""
        session = await self.get_session()

        parameters = {"device_type": device_type.value, **kwargs}

        if profile_id:
            parameters["profile_id"] = profile_id

        task = Task(
            task_type=TaskType.WARMUP_PROFILE.value,
            status=TaskStatus.PENDING.value,
            priority=priority,
            user_id=user_id,
            parameters=parameters,
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info("Warmup task created", task_id=str(task.id), user_id=user_id)
        return task
