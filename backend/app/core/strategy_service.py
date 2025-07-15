# backend/app/core/strategy_service.py
import json
import random
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog
import requests
from pathlib import Path

from app.models import (
    StrategyTemplate,
    UserStrategy,
    StrategyDataSource,
    ProjectStrategy,
    StrategyExecutionLog,
    Task,
    Profile,
)
from app.schemas.strategies import UserStrategyCreate, DataSourceCreate
from app.constants.strategies import (
    StrategyType as StrategyTypeConstants,
    DataSourceType as DataSourceTypeConstants,
    ProfileNurtureType as ProfileNurtureTypeConstants,
    QuerySourceType as QuerySourceTypeConstants,
    validate_warmup_config,
    validate_position_check_config,
    validate_profile_nurture_config,
)

logger = structlog.get_logger()


class StrategyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_strategy_templates(
        self, strategy_type: Optional[str] = None
    ) -> List[Dict]:
        """Получение шаблонов стратегий"""
        query = select(StrategyTemplate).where(StrategyTemplate.is_active == True)

        if strategy_type:
            query = query.where(StrategyTemplate.strategy_type == strategy_type)

        result = await self.session.execute(query)
        templates = result.scalars().all()

        return [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "strategy_type": template.strategy_type,
                "config": template.config,
                "is_system": template.is_system,
                "created_at": template.created_at,
            }
            for template in templates
        ]

    async def get_user_strategies(
        self, user_id: str, strategy_type: Optional[str] = None
    ) -> List[Dict]:
        """Получение пользовательских стратегий"""
        query = select(UserStrategy).where(
            and_(UserStrategy.user_id == user_id, UserStrategy.is_active == True)
        )

        if strategy_type:
            query = query.where(UserStrategy.strategy_type == strategy_type)

        result = await self.session.execute(query)
        strategies = result.scalars().all()

        return [
            {
                "id": str(strategy.id),
                "user_id": strategy.user_id,
                "template_id": (
                    str(strategy.template_id) if strategy.template_id else None
                ),
                "name": strategy.name,
                "strategy_type": strategy.strategy_type,
                "config": strategy.config,
                "created_at": strategy.created_at,
                "updated_at": strategy.updated_at,
                "is_active": strategy.is_active,
                "data_sources": await self._get_strategy_data_sources(str(strategy.id)),
            }
            for strategy in strategies
        ]

    async def _get_strategy_data_sources(self, strategy_id: str) -> List[Dict]:
        """Получение источников данных для стратегии"""
        result = await self.session.execute(
            select(StrategyDataSource).where(
                and_(
                    StrategyDataSource.strategy_id == strategy_id,
                    StrategyDataSource.is_active == True,
                )
            )
        )
        sources = result.scalars().all()

        return [
            {
                "id": str(source.id),
                "strategy_id": str(source.strategy_id),
                "source_type": source.source_type,
                "source_url": source.source_url,
                "file_path": source.file_path,
                "items_count": (
                    len(source.data_content.split("\n")) if source.data_content else 0
                ),
                "is_active": source.is_active,
                "created_at": source.created_at,
            }
            for source in sources
        ]

    async def create_user_strategy(
        self, user_id: str, strategy_data: UserStrategyCreate
    ) -> Dict:
        """Создание пользовательской стратегии"""
        strategy = UserStrategy(
            user_id=user_id,
            template_id=strategy_data.template_id,
            name=strategy_data.name,
            strategy_type=strategy_data.strategy_type,
            config=strategy_data.config,
        )

        self.session.add(strategy)
        await self.session.commit()
        await self.session.refresh(strategy)

        logger.info(
            "Created user strategy",
            user_id=user_id,
            strategy_id=str(strategy.id),
            strategy_type=strategy.strategy_type,
        )

        return {
            "id": str(strategy.id),
            "user_id": strategy.user_id,
            "template_id": str(strategy.template_id) if strategy.template_id else None,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": strategy.config,
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at,
            "is_active": strategy.is_active,
            "data_sources": [],
        }

    async def get_user_strategy_by_id(
        self, strategy_id: str, user_id: str
    ) -> Optional[Dict]:
        """Получение стратегии пользователя по ID"""
        result = await self.session.execute(
            select(UserStrategy).where(
                and_(UserStrategy.id == strategy_id, UserStrategy.user_id == user_id)
            )
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            return None

        return {
            "id": str(strategy.id),
            "user_id": strategy.user_id,
            "template_id": str(strategy.template_id) if strategy.template_id else None,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": strategy.config,
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at,
            "is_active": strategy.is_active,
            "data_sources": await self._get_strategy_data_sources(strategy_id),
        }

    async def update_user_strategy(
        self, strategy_id: str, user_id: str, update_data: Dict
    ) -> Dict:
        """Обновление пользовательской стратегии"""
        result = await self.session.execute(
            select(UserStrategy).where(
                and_(UserStrategy.id == strategy_id, UserStrategy.user_id == user_id)
            )
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise Exception("Стратегия не найдена")

        # Обновляем поля
        for field, value in update_data.items():
            if hasattr(strategy, field) and value is not None:
                # Валидируем конфигурацию если она обновляется
                if field == "config":
                    if strategy.strategy_type == StrategyTypeConstants.WARMUP:
                        value = validate_warmup_config(value)
                    elif strategy.strategy_type == StrategyTypeConstants.POSITION_CHECK:
                        value = validate_position_check_config(value)
                    elif (
                        strategy.strategy_type == StrategyTypeConstants.PROFILE_NURTURE
                    ):
                        value = validate_profile_nurture_config(value)

                setattr(strategy, field, value)

        strategy.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(strategy)

        logger.info("Updated user strategy", user_id=user_id, strategy_id=strategy_id)

        return {
            "id": str(strategy.id),
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": strategy.config,
            "updated_at": strategy.updated_at,
        }

    async def delete_user_strategy(self, strategy_id: str, user_id: str) -> bool:
        """Удаление пользовательской стратегии"""
        result = await self.session.execute(
            select(UserStrategy).where(
                and_(UserStrategy.id == strategy_id, UserStrategy.user_id == user_id)
            )
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            return False

        # Помечаем как неактивную вместо удаления
        strategy.is_active = False
        await self.session.commit()

        logger.info("User strategy deleted", strategy_id=strategy_id, user_id=user_id)

        return True

    async def add_data_source(
        self, strategy_id: str, source_data: DataSourceCreate
    ) -> Dict:
        """Добавление источника данных к стратегии"""

        # Обрабатываем разные типы источников данных
        data_content = None

        if source_data.source_type == DataSourceTypeConstants.URL_IMPORT:
            data_content = await self._import_from_url(source_data.source_url)
        elif source_data.source_type == DataSourceTypeConstants.GOOGLE_SHEETS:
            data_content = await self._import_from_google_sheets(source_data.source_url)
        elif source_data.source_type == DataSourceTypeConstants.GOOGLE_DOCS:
            data_content = await self._import_from_google_docs(source_data.source_url)
        else:
            data_content = source_data.data_content

        # Создаем источник данных
        data_source = StrategyDataSource(
            strategy_id=strategy_id,
            source_type=source_data.source_type,
            source_url=source_data.source_url,
            data_content=data_content,
            file_path=source_data.file_path,
        )

        self.session.add(data_source)
        await self.session.commit()
        await self.session.refresh(data_source)

        logger.info(
            "Added data source to strategy",
            strategy_id=strategy_id,
            source_type=source_data.source_type,
        )

        return {
            "id": str(data_source.id),
            "strategy_id": str(data_source.strategy_id),
            "source_type": data_source.source_type,
            "source_url": data_source.source_url,
            "file_path": data_source.file_path,
            "items_count": len(data_content.split("\n")) if data_content else 0,
            "is_active": data_source.is_active,
            "created_at": data_source.created_at,
        }

    async def _import_from_url(self, url: str) -> str:
        """Импорт данных по URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Парсим содержимое в зависимости от типа
                        if url.endswith(".json"):
                            data = json.loads(content)
                            if isinstance(data, list):
                                return "\n".join(str(item) for item in data)
                            else:
                                return content
                        else:
                            # Обрабатываем как текст, разделенный переносами строк
                            lines = [
                                line.strip()
                                for line in content.split("\n")
                                if line.strip()
                            ]
                            return "\n".join(lines)
                    else:
                        raise Exception(
                            f"HTTP {response.status}: {await response.text()}"
                        )
        except Exception as e:
            logger.error("Failed to import from URL", url=url, error=str(e))
            raise Exception(f"Ошибка импорта из URL: {str(e)}")

    async def _import_from_google_sheets(self, url: str) -> str:
        """Импорт данных из Google Sheets"""
        try:
            # Конвертируем URL в CSV export format
            if "/edit" in url:
                csv_url = url.replace("/edit", "/export?format=csv")
            else:
                csv_url = f"{url}/export?format=csv"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    csv_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Парсим CSV и извлекаем данные
                        import csv
                        import io

                        reader = csv.reader(io.StringIO(content))
                        data_items = []
                        for row in reader:
                            if row:  # Пропускаем пустые строки
                                data_items.extend(
                                    [cell.strip() for cell in row if cell.strip()]
                                )

                        return "\n".join(data_items)
                    else:
                        raise Exception(
                            f"HTTP {response.status}: {await response.text()}"
                        )
        except Exception as e:
            logger.error("Failed to import from Google Sheets", url=url, error=str(e))
            raise Exception(f"Ошибка импорта из Google Sheets: {str(e)}")

    async def _import_from_google_docs(self, url: str) -> str:
        """Импорт данных из Google Docs"""
        try:
            # Конвертируем URL в текстовый export format
            if "/edit" in url:
                txt_url = url.replace("/edit", "/export?format=txt")
            else:
                txt_url = f"{url}/export?format=txt"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    txt_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Парсим текст и извлекаем строки
                        lines = [
                            line.strip() for line in content.split("\n") if line.strip()
                        ]
                        return "\n".join(lines)
                    else:
                        raise Exception(
                            f"HTTP {response.status}: {await response.text()}"
                        )
        except Exception as e:
            logger.error("Failed to import from Google Docs", url=url, error=str(e))
            raise Exception(f"Ошибка импорта из Google Docs: {str(e)}")

    async def save_uploaded_file(
        self, user_id: str, strategy_id: str, filename: str, content: bytes
    ) -> str:
        """Сохранение загруженного файла"""
        # Создаем директорию для пользователя
        upload_dir = Path(f"uploads/strategies/{user_id}/{strategy_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = upload_dir / f"{timestamp}_{filename}"

        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(
            "Saved uploaded file",
            user_id=user_id,
            strategy_id=strategy_id,
            file_path=str(file_path),
        )

        return str(file_path)

    async def execute_strategy(
        self, strategy_id: str, user_id: str, params: Dict[str, Any] = None
    ) -> Dict:
        """Запуск выполнения стратегии"""
        if params is None:
            params = {}

        # Получаем стратегию
        result = await self.session.execute(
            select(UserStrategy).where(
                and_(UserStrategy.id == strategy_id, UserStrategy.user_id == user_id)
            )
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise Exception("Стратегия не найдена")

        # Получаем источники данных
        sources_result = await self.session.execute(
            select(StrategyDataSource).where(
                and_(
                    StrategyDataSource.strategy_id == strategy_id,
                    StrategyDataSource.is_active == True,
                )
            )
        )
        sources = list(sources_result.scalars().all())

        # Подготавливаем данные для выполнения
        execution_data = await self._prepare_execution_data(strategy, sources, params)

        # Создаем задачу выполнения стратегии
        if strategy.strategy_type == StrategyTypeConstants.WARMUP:
            task = await self._create_warmup_task(strategy, execution_data, user_id)
        elif strategy.strategy_type == StrategyTypeConstants.POSITION_CHECK:
            task = await self._create_position_check_task(
                strategy, execution_data, user_id
            )
        elif strategy.strategy_type == StrategyTypeConstants.PROFILE_NURTURE:
            task = await self._create_profile_nurture_task(
                strategy, execution_data, user_id
            )
        else:
            raise Exception(f"Неподдерживаемый тип стратегии: {strategy.strategy_type}")

        # Записываем в лог выполнения
        execution_log = StrategyExecutionLog(
            strategy_id=strategy_id,
            task_id=str(task.id),
            execution_type=strategy.strategy_type,
            parameters=execution_data,
            status="pending",
        )

        self.session.add(execution_log)
        await self.session.commit()

        logger.info(
            "Strategy execution started",
            strategy_id=strategy_id,
            task_id=str(task.id),
            strategy_type=strategy.strategy_type,
        )

        return {
            "id": str(task.id),
            "strategy_type": strategy.strategy_type,
            "execution_log_id": str(execution_log.id),
        }

    async def _prepare_execution_data(
        self, strategy: UserStrategy, sources: List[StrategyDataSource], params: Dict
    ) -> Dict:
        """Подготовка данных для выполнения стратегии"""
        execution_data = {
            "strategy_config": strategy.config,
            "sources": [],
            "custom_params": params,
        }

        # Подготавливаем источники данных
        for source in sources:
            source_data = {
                "id": str(source.id),
                "type": source.source_type,
                "url": source.source_url,
                "data": source.data_content,
            }

            # Для URL источников в нагуле профиля - получаем свежие данные
            if (
                strategy.strategy_type == StrategyTypeConstants.PROFILE_NURTURE
                and source.source_type == DataSourceTypeConstants.URL_IMPORT
            ):
                config = strategy.config
                queries_source = config.get("queries_source", {})

                if queries_source.get("refresh_on_each_cycle", False):
                    try:
                        fresh_data = await self._import_from_url(source.source_url)
                        source_data["data"] = fresh_data
                        logger.info(
                            "Refreshed data from URL for profile nurture",
                            source_id=str(source.id),
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to refresh URL data, using cached",
                            source_id=str(source.id),
                            error=str(e),
                        )

            execution_data["sources"].append(source_data)

        return execution_data

    async def _create_warmup_task(
        self, strategy: UserStrategy, execution_data: Dict, user_id: str
    ) -> Task:
        """Создание задачи прогрева"""
        task = Task(
            task_type="warmup",
            parameters=execution_data,
            user_id=user_id,
            priority=2,  # Средний приоритет
            status="pending",
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def _create_position_check_task(
        self, strategy: UserStrategy, execution_data: Dict, user_id: str
    ) -> Task:
        """Создание задачи проверки позиций"""
        task = Task(
            task_type="position_check",
            parameters=execution_data,
            user_id=user_id,
            priority=1,  # Высокий приоритет
            status="pending",
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def _create_profile_nurture_task(
        self, strategy: UserStrategy, execution_data: Dict, user_id: str
    ) -> Task:
        """Создание задачи нагула профиля"""
        task = Task(
            task_type="profile_nurture",
            parameters=execution_data,
            user_id=user_id,
            priority=3,  # Низкий приоритет (фоновая задача)
            status="pending",
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def assign_strategies_to_project(
        self, user_id: str, assignment_data: Dict
    ) -> Dict:
        """Назначение стратегий для проекта/домена"""

        assignment = ProjectStrategy(
            user_id=user_id,
            domain_id=assignment_data.get("domain_id"),
            warmup_strategy_id=assignment_data.get("warmup_strategy_id"),
            position_check_strategy_id=assignment_data.get(
                "position_check_strategy_id"
            ),
            profile_nurture_strategy_id=assignment_data.get(
                "profile_nurture_strategy_id"
            ),
        )

        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)

        logger.info(
            "Assigned strategies to project",
            user_id=user_id,
            domain_id=assignment_data.get("domain_id"),
        )

        return {
            "id": str(assignment.id),
            "user_id": assignment.user_id,
            "domain_id": assignment.domain_id,
            "warmup_strategy_id": assignment.warmup_strategy_id,
            "position_check_strategy_id": assignment.position_check_strategy_id,
            "profile_nurture_strategy_id": assignment.profile_nurture_strategy_id,
            "created_at": assignment.created_at,
        }

    async def get_project_strategies(
        self, user_id: str, domain_id: Optional[str] = None
    ) -> List[Dict]:
        """Получение назначенных стратегий для проектов"""
        query = select(ProjectStrategy).where(ProjectStrategy.user_id == user_id)

        if domain_id:
            query = query.where(ProjectStrategy.domain_id == domain_id)

        result = await self.session.execute(query)
        assignments = result.scalars().all()

        return [
            {
                "id": str(assignment.id),
                "user_id": assignment.user_id,
                "domain_id": assignment.domain_id,
                "warmup_strategy_id": assignment.warmup_strategy_id,
                "position_check_strategy_id": assignment.position_check_strategy_id,
                "profile_nurture_strategy_id": assignment.profile_nurture_strategy_id,
                "created_at": assignment.created_at,
            }
            for assignment in assignments
        ]

    async def get_nurture_queries_from_source(
        self, source: Dict, config: Dict
    ) -> List[str]:
        """Получение запросов для нагула из источника данных"""
        queries = []

        source_type = source.get("type")
        source_data = source.get("data", "")
        source_url = source.get("url")

        if source_type == DataSourceTypeConstants.URL_IMPORT:
            # Для URL источников - всегда получаем свежие данные
            queries_source = config.get("queries_source", {})
            if queries_source.get("refresh_on_each_cycle", False) and source_url:
                try:
                    fresh_data = await self._import_from_url(source_url)
                    source_data = fresh_data
                except Exception as e:
                    logger.warning(
                        "Failed to refresh URL data", url=source_url, error=str(e)
                    )

        if source_data:
            queries = [line.strip() for line in source_data.split("\n") if line.strip()]

        return queries

    async def get_random_query_from_nurture_source(
        self, sources: List[Dict], config: Dict
    ) -> Optional[str]:
        """Получение случайного запроса из источников нагула"""
        all_queries = []

        for source in sources:
            queries = await self.get_nurture_queries_from_source(source, config)
            all_queries.extend(queries)

        if all_queries:
            return random.choice(all_queries)

        return None
