# backend/app/services/profile_nurture_limits_service.py

from typing import Dict, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_manager import TaskManager
from app.models import Profile, UserStrategy, ProjectStrategy
from app.constants.strategies import StrategyType
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
        query = select(func.count(Profile.id)).where(
            and_(
                # Profile.nurture_strategy_id == strategy_id,
                Profile.is_warmed_up == True,
                Profile.status == "active",
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_strategy_limits(self, strategy_id: str) -> Dict[str, int]:
        """Получить лимиты для стратегии"""
        query = select(UserStrategy).where(
            and_(
                UserStrategy.id == strategy_id,
                UserStrategy.strategy_type == StrategyType.PROFILE_NURTURE,
            )
        )
        result = await self.session.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            return {"min_limit": 0, "max_limit": 0}

        config = strategy.config or {}
        return {
            "min_limit": config.get("min_profiles_limit", 10),
            "max_limit": config.get("max_profiles_limit", 100),
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
                UserStrategy.strategy_type == StrategyType.PROFILE_NURTURE,
                UserStrategy.is_active == True,
            )
        )
        result = await self.session.execute(query)
        strategies = result.scalars().all()

        statuses = []
        for strategy in strategies:
            status = await self.check_strategy_status(str(strategy.id))
            status["strategy_id"] = str(strategy.id)
            status["strategy_name"] = strategy.name
            statuses.append(status)

        return statuses

    async def spawn_nurture_tasks_if_needed(self, strategy_id: str) -> Dict[str, any]:
        """Создать задачи нагула если нужно"""
        status = await self.check_strategy_status(strategy_id)

        if not status["needs_nurture"]:
            return {
                "success": True,
                "message": "Нагул не требуется",
                "tasks_created": 0,
            }

        # Рассчитываем сколько профилей нужно создать
        needed_profiles = status["max_limit"] - status["current_count"]

        # Создаем задачи на нагул
        tasks_created = 0
        try:
            for i in range(needed_profiles):
                task = await self.task_manager.create_profile_nurture_task(
                    strategy_id=strategy_id, priority=3  # Средний приоритет
                )
                tasks_created += 1

            logger.info(
                "Created nurture tasks",
                strategy_id=strategy_id,
                tasks_created=tasks_created,
                needed_profiles=needed_profiles,
            )

            return {
                "success": True,
                "message": f"Создано {tasks_created} задач нагула",
                "tasks_created": tasks_created,
            }

        except Exception as e:
            logger.error(
                "Failed to create nurture tasks", strategy_id=strategy_id, error=str(e)
            )
            return {
                "success": False,
                "message": f"Ошибка создания задач: {str(e)}",
                "tasks_created": tasks_created,
            }

    async def auto_maintain_all_strategies(self, user_id: str) -> Dict[str, any]:
        """Автоматически поддерживать все стратегии пользователя"""
        strategies_status = await self.get_all_strategies_status(user_id)

        results = []
        for strategy_status in strategies_status:
            if strategy_status["needs_nurture"]:
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

        return {
            "success": True,
            "maintained_strategies": len(results),
            "results": results,
        }
