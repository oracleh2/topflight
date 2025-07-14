# backend/app/core/strategy_service.py
import json
import random
import asyncio
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
    validate_warmup_config,
    validate_position_check_config,
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
            }
            for strategy in strategies
        ]

    async def get_user_strategy_by_id(
        self, strategy_id: str, user_id: str
    ) -> Optional[Dict]:
        """Получение стратегии по ID"""
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
        }

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
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": strategy.config,
            "created_at": strategy.created_at,
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
            # Удаляем вызов несуществующего метода
            raise Exception("Google Docs импорт пока не поддерживается")
        elif source_data.source_type == DataSourceTypeConstants.MANUAL_LIST:
            data_content = source_data.data_content

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
            "source_type": data_source.source_type,
            "items_count": len(data_content.split("\n")) if data_content else 0,
        }

    async def save_uploaded_file(
        self, user_id: str, strategy_id: str, filename: str, content: bytes
    ) -> str:
        """Сохранение загруженного файла"""
        # Создаем директорию для файлов пользователя
        user_dir = Path(f"uploads/users/{user_id}/strategies/{strategy_id}")
        user_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = user_dir / f"{timestamp}_{filename}"

        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(
            "File uploaded for strategy",
            user_id=user_id,
            strategy_id=strategy_id,
            filename=filename,
            file_path=str(file_path),
        )

        return str(file_path)

    async def _import_from_url(self, url: str) -> str:
        """Импорт данных по URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()

            if "text/plain" in content_type:
                return response.text
            elif "text/csv" in content_type:
                lines = response.text.split("\n")
                return "\n".join([line.strip() for line in lines if line.strip()])
            else:
                # Пытаемся парсить как текст
                return response.text

        except Exception as e:
            logger.error("Failed to import from URL", url=url, error=str(e))
            raise Exception(f"Ошибка импорта из URL: {str(e)}")

    async def _import_from_google_sheets(self, url: str) -> str:
        """Импорт из Google Sheets"""
        try:
            # Извлекаем ID таблицы из URL
            sheet_id = self._extract_google_sheet_id(url)
            if not sheet_id:
                raise Exception("Неверный формат URL Google Sheets")

            # Формируем URL для CSV экспорта
            csv_url = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            )

            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()

            # Парсим CSV и извлекаем первый столбец
            lines = response.text.split("\n")
            data_items = []

            for line in lines:
                if line.strip():
                    # Берем первый столбец (до первой запятой)
                    first_column = line.split(",")[0].strip('"')
                    if first_column:
                        data_items.append(first_column)

            return "\n".join(data_items)

        except Exception as e:
            logger.error("Failed to import from Google Sheets", url=url, error=str(e))
            raise Exception(f"Ошибка импорта из Google Sheets: {str(e)}")

    def _extract_google_sheet_id(self, url: str) -> Optional[str]:
        """Извлечение ID Google Sheets из URL"""
        import re

        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    async def execute_strategy(
        self, strategy_id: str, user_id: str, params: Dict = {}
    ) -> Dict:
        """Выполнение стратегии"""

        # Получаем стратегию
        strategy_result = await self.session.execute(
            select(UserStrategy).where(
                and_(UserStrategy.id == strategy_id, UserStrategy.user_id == user_id)
            )
        )
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise Exception("Стратегия не найдена")

        # Получаем источники данных - исправляем тип
        sources_result = await self.session.execute(
            select(StrategyDataSource).where(
                and_(
                    StrategyDataSource.strategy_id == strategy_id,
                    StrategyDataSource.is_active == True,
                )
            )
        )
        sources = list(sources_result.scalars().all())  # Конвертируем в список

        # Подготавливаем данные для выполнения
        execution_data = await self._prepare_execution_data(strategy, sources, params)

        # Создаем задачу выполнения стратегии
        if strategy.strategy_type == StrategyTypeConstants.WARMUP:
            task = await self._create_warmup_task(strategy, execution_data, user_id)
        elif strategy.strategy_type == StrategyTypeConstants.POSITION_CHECK:
            task = await self._create_position_check_task(
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
        )

        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)

        logger.info(
            "Strategies assigned to project",
            user_id=user_id,
            assignment_id=str(assignment.id),
            domain_id=assignment_data.get("domain_id"),
        )

        return {
            "id": str(assignment.id),
            "user_id": user_id,
            "domain_id": str(assignment.domain_id) if assignment.domain_id else None,
            "warmup_strategy_id": (
                str(assignment.warmup_strategy_id)
                if assignment.warmup_strategy_id
                else None
            ),
            "position_check_strategy_id": (
                str(assignment.position_check_strategy_id)
                if assignment.position_check_strategy_id
                else None
            ),
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
                "domain_id": (
                    str(assignment.domain_id) if assignment.domain_id else None
                ),
                "warmup_strategy_id": (
                    str(assignment.warmup_strategy_id)
                    if assignment.warmup_strategy_id
                    else None
                ),
                "position_check_strategy_id": (
                    str(assignment.position_check_strategy_id)
                    if assignment.position_check_strategy_id
                    else None
                ),
                "created_at": assignment.created_at,
            }
            for assignment in assignments
        ]

    async def get_strategy_execution_logs(
        self, strategy_id: str, user_id: str, limit: int = 50
    ) -> List[Dict]:
        """Получение логов выполнения стратегии"""

        # Сначала проверяем доступ к стратегии
        strategy = await self.get_user_strategy_by_id(strategy_id, user_id)
        if not strategy:
            raise Exception("Стратегия не найдена")

        result = await self.session.execute(
            select(StrategyExecutionLog)
            .where(StrategyExecutionLog.strategy_id == strategy_id)
            .order_by(StrategyExecutionLog.started_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        return [
            {
                "id": str(log.id),
                "strategy_id": str(log.strategy_id),
                "task_id": str(log.task_id) if log.task_id else None,
                "execution_type": log.execution_type,
                "profile_id": str(log.profile_id) if log.profile_id else None,
                "parameters": log.parameters,
                "result": log.result,
                "status": log.status,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "error_message": log.error_message,
            }
            for log in logs
        ]

    async def _prepare_execution_data(
        self, strategy: UserStrategy, sources: List[StrategyDataSource], params: Dict
    ) -> Dict:
        """Подготовка данных для выполнения стратегии"""

        # Собираем все данные из источников
        all_data = []
        for source in sources:
            if source.data_content:
                items = [
                    item.strip()
                    for item in source.data_content.split("\n")
                    if item.strip()
                ]
                all_data.extend(items)

        # Формируем конфигурацию выполнения
        execution_config = strategy.config.copy()
        execution_config.update(params)

        if strategy.strategy_type == StrategyTypeConstants.WARMUP:
            return await self._prepare_warmup_data(all_data, execution_config)
        elif strategy.strategy_type == StrategyTypeConstants.POSITION_CHECK:
            return await self._prepare_position_check_data(all_data, execution_config)

        return {"data": all_data, "config": execution_config}

    async def _prepare_warmup_data(self, data: List[str], config: Dict) -> Dict:
        """Подготовка данных для прогрева профилей"""

        warmup_type = config.get("type", "mixed")
        proportions = config.get(
            "proportions", {"direct_visits": 5, "search_visits": 1}
        )

        # Разделяем данные на сайты и ключевые слова
        sites = []
        keywords = []

        for item in data:
            if item.startswith(("http://", "https://", "www.")):
                sites.append(item)
            else:
                keywords.append(item)

        # Формируем план действий согласно пропорциям
        actions = []

        if warmup_type in ["direct", "mixed"]:
            direct_count = proportions.get("direct_visits", 5)
            for _ in range(direct_count):
                if sites:
                    actions.append(
                        {"type": "direct_visit", "target": random.choice(sites)}
                    )

        if warmup_type in ["search", "mixed"]:
            search_count = proportions.get("search_visits", 1)
            search_config = config.get("search_config", {})

            for _ in range(search_count):
                if keywords:
                    actions.append(
                        {
                            "type": "search_visit",
                            "keyword": random.choice(keywords),
                            "yandex_domain": random.choice(
                                search_config.get("yandex_domains", ["yandex.ru"])
                            ),
                        }
                    )

        # Перемешиваем действия
        random.shuffle(actions)

        return {
            "actions": actions,
            "config": config,
            "total_sites": len(sites),
            "total_keywords": len(keywords),
        }

    async def _prepare_position_check_data(self, data: List[str], config: Dict) -> Dict:
        """Подготовка данных для проверки позиций"""

        # data должна содержать ключевые слова для проверки
        keywords = [item.strip() for item in data if item.strip()]

        search_config = config.get("search_config", {})

        return {
            "keywords": keywords,
            "pages_to_check": search_config.get("pages_to_check", 10),
            "yandex_domain": search_config.get("yandex_domain", "yandex.ru"),
            "device_types": search_config.get("device_types", ["desktop"]),
            "regions": search_config.get("regions", ["213"]),
            "behavior": config.get("behavior", {}),
            "config": config,
        }

    async def _create_warmup_task(
        self, strategy: UserStrategy, execution_data: Dict, user_id: str
    ) -> Task:
        """Создание задачи прогрева профилей"""

        task = Task(
            task_type="strategy_warmup",
            status="pending",
            priority=5,
            user_id=user_id,
            parameters={
                "strategy_id": str(strategy.id),
                "user_id": user_id,
                "execution_data": execution_data,
            },
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        logger.info(
            "Strategy warmup task created",
            task_id=str(task.id),
            strategy_id=str(strategy.id),
            user_id=user_id,
        )

        return task

    async def _create_position_check_task(
        self, strategy: UserStrategy, execution_data: Dict, user_id: str
    ) -> Task:
        """Создание задачи проверки позиций по стратегии"""

        task = Task(
            task_type="strategy_position_check",
            status="pending",
            priority=5,
            user_id=user_id,
            parameters={
                "strategy_id": str(strategy.id),
                "user_id": user_id,
                "execution_data": execution_data,
            },
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        logger.info(
            "Strategy position check task created",
            task_id=str(task.id),
            strategy_id=str(strategy.id),
            user_id=user_id,
        )

        return task
