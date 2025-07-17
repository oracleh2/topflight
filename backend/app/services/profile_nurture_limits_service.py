# backend/app/services/profile_nurture_limits_service.py

from typing import Dict, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app import Task
from app.core.task_manager import TaskManager
from app.models import Profile, UserStrategy, ProjectStrategy
from app.constants.strategies import StrategyType as StrategyTypeEnum
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class ProfileNurtureLimitsService:
    """Сервис для управления лимитами профилей нагула"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_manager = TaskManager(session)

    async def get_nurtured_profiles_count(self, strategy_id: str) -> int:
        """Получить количество нагуленных профилей для стратегии"""

        # ИСПРАВЛЕНИЕ: правильная работа с JSON полем
        completed_tasks_query = select(func.count(Task.id)).where(
            and_(
                Task.task_type == "profile_nurture",
                Task.parameters.op("->>")("strategy_id")
                == strategy_id,  # Правильный оператор для JSONB
                Task.status == "completed",
            )
        )

        result = await self.session.execute(completed_tasks_query)
        completed_tasks_count = result.scalar() or 0

        logger.debug(
            "Counted nurtured profiles",
            strategy_id=strategy_id,
            count=completed_tasks_count,
        )

        return completed_tasks_count

    async def get_strategy_limits(self, strategy_id: str) -> Dict[str, int]:
        """Получить лимиты для стратегии"""

        print(f"Strategy type: {StrategyTypeEnum.PROFILE_NURTURE}")

        query = select(UserStrategy).where(
            and_(
                UserStrategy.id == strategy_id,
                UserStrategy.strategy_type == StrategyTypeEnum.PROFILE_NURTURE,
            )
        )
        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            print(f"❌ Strategy not found: {strategy_id}")
            return {"min_limit": 0, "max_limit": 0}

        config = strategy.config or {}

        # ✅ ИСПРАВЛЕНО: Используем правильные поля из конфигурации
        # Поскольку в конфигурации нет min_profiles_limit и max_profiles_limit,
        # используем target_cookies как базу для расчета лимитов

        # Сначала проверяем, есть ли уже установленные лимиты
        min_limit = config.get("min_profiles_limit", 10)
        max_limit = config.get("max_profiles_limit", 100)

        # Валидация
        if min_limit > max_limit:
            logger.warning(
                "Invalid limits configuration",
                strategy_id=strategy_id,
                min_limit=min_limit,
                max_limit=max_limit,
            )
            # Исправляем на разумные значения
            min_limit = min(min_limit, max_limit)

        return {
            "min_limit": min_limit,
            "max_limit": max_limit,
        }

    async def check_strategy_status(self, strategy_id: str) -> Dict[str, any]:
        """Проверить статус стратегии относительно лимитов"""
        current_count = await self.get_nurtured_profiles_count(strategy_id)
        limits = await self.get_strategy_limits(strategy_id)

        status = "normal"
        if current_count < limits["min_limit"]:
            status = "critical"
        elif current_count >= limits["max_limit"]:
            status = "max_reached"

        return {
            "current_count": current_count,
            "min_limit": limits["min_limit"],
            "max_limit": limits["max_limit"],
            "status": status,
            "needs_nurture": current_count < limits["max_limit"],
        }

    async def get_all_strategies_status(self, user_id: str) -> List[Dict[str, any]]:
        """Получить статус всех стратегий нагула пользователя"""
        query = select(UserStrategy).where(
            and_(
                UserStrategy.user_id == user_id,
                UserStrategy.strategy_type == StrategyTypeEnum.PROFILE_NURTURE,
                UserStrategy.is_active == True,
            )
        )
        result = await self.session.execute(query)
        strategies = result.scalars().all()

        statuses = []
        for strategy in strategies:
            try:
                status = await self.check_strategy_status(str(strategy.id))
                status["strategy_id"] = str(strategy.id)
                status["strategy_name"] = strategy.name
                statuses.append(status)
            except Exception as e:
                logger.error(
                    "Error checking strategy status",
                    strategy_id=str(strategy.id),
                    error=str(e),
                )
                # Добавляем стратегию с ошибкой
                statuses.append(
                    {
                        "strategy_id": str(strategy.id),
                        "strategy_name": strategy.name,
                        "current_count": 0,
                        "min_limit": 0,
                        "max_limit": 0,
                        "status": "error",
                        "needs_nurture": False,
                        "error": str(e),
                    }
                )

        return statuses

    async def spawn_nurture_tasks_if_needed(self, strategy_id: str) -> Dict[str, any]:
        """Создать задачи нагула если нужно"""
        try:
            status = await self.check_strategy_status(strategy_id)

            # print(f"Status: {status}")

            if not status["needs_nurture"]:
                return {
                    "success": True,
                    "message": "Нагул не требуется",
                    "tasks_created": 0,
                    "status": status,
                }

            # Рассчитываем сколько профилей нужно создать
            needed_profiles = status["max_limit"] - status["current_count"]

            # Ограничиваем количество одновременно создаваемых задач
            max_batch_size = 50  # Не создаем больше 50 задач за раз
            needed_profiles = min(needed_profiles, max_batch_size)

            # Создаем задачи на нагул
            tasks_created = 0
            created_task_ids = []

            for i in range(needed_profiles):
                task = await self.task_manager.create_profile_nurture_task(
                    strategy_id=strategy_id, priority=5  # Средний приоритет
                )
                tasks_created += 1
                created_task_ids.append(str(task.id))

            logger.info(
                "Created nurture tasks",
                strategy_id=strategy_id,
                tasks_created=tasks_created,
                needed_profiles=needed_profiles,
                task_ids=created_task_ids,
            )

            return {
                "success": True,
                "message": f"Создано {tasks_created} задач нагула",
                "tasks_created": tasks_created,
                "task_ids": created_task_ids,
                "status": status,
            }

        except Exception as e:
            logger.error(
                "Failed to create nurture tasks", strategy_id=strategy_id, error=str(e)
            )
            return {
                "success": False,
                "message": f"Ошибка создания задач: {str(e)}",
                "tasks_created": 0,
                "error": str(e),
            }

    async def auto_maintain_all_strategies(self, user_id: str) -> Dict[str, any]:
        """Автоматически поддерживать все стратегии пользователя"""
        strategies_status = await self.get_all_strategies_status(user_id)

        results = []
        total_tasks_created = 0

        for strategy_status in strategies_status:
            if strategy_status.get("needs_nurture", False):
                result = await self.spawn_nurture_tasks_if_needed(
                    strategy_status["strategy_id"]
                )
                results.append(
                    {
                        "strategy_id": strategy_status["strategy_id"],
                        "strategy_name": strategy_status["strategy_name"],
                        "result": result,
                    }
                )
                total_tasks_created += result.get("tasks_created", 0)

        logger.info(
            "Auto maintained strategies",
            user_id=user_id,
            strategies_maintained=len(results),
            total_tasks_created=total_tasks_created,
        )

        return {
            "success": True,
            "maintained_strategies": len(results),
            "total_tasks_created": total_tasks_created,
            "results": results,
        }
