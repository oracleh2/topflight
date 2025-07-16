# backend/app/tasks/profile_nurture_scheduler.py

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_session
from app.models import User, UserStrategy
from app.services.profile_nurture_limits_service import ProfileNurtureLimitsService
from app.constants.strategies import StrategyType
import structlog

logger = structlog.get_logger(__name__)


class ProfileNurtureScheduler:
    """Планировщик для автоматического поддержания лимитов профилей"""

    def __init__(self):
        self.running = False
        self.check_interval = 300  # 5 минут

    async def start(self):
        """Запустить планировщик"""
        self.running = True
        logger.info("Profile nurture scheduler started")

        while self.running:
            try:
                await self.check_all_strategies()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Error in profile nurture scheduler", error=str(e))
                await asyncio.sleep(60)  # Короткая пауза при ошибке

    async def stop(self):
        """Остановить планировщик"""
        self.running = False
        logger.info("Profile nurture scheduler stopped")

    async def check_all_strategies(self):
        """Проверить все стратегии и создать задачи при необходимости"""
        async with get_session() as session:
            # Получаем всех пользователей с активными стратегиями нагула
            query = (
                select(User.id)
                .join(UserStrategy, UserStrategy.user_id == User.id)
                .where(
                    UserStrategy.strategy_type == StrategyType.PROFILE_NURTURE,
                    UserStrategy.is_active == True,
                )
                .distinct()
            )

            result = await session.execute(query)
            user_ids = result.scalars().all()

            logger.info(
                "Checking profile nurture strategies", users_count=len(user_ids)
            )

            limits_service = ProfileNurtureLimitsService(session)

            for user_id in user_ids:
                try:
                    result = await limits_service.auto_maintain_all_strategies(
                        str(user_id)
                    )

                    if result["maintained_strategies"] > 0:
                        logger.info(
                            "Maintained strategies for user",
                            user_id=user_id,
                            strategies_count=result["maintained_strategies"],
                        )

                except Exception as e:
                    logger.error(
                        "Error maintaining strategies for user",
                        user_id=user_id,
                        error=str(e),
                    )


# Создаем глобальный экземпляр планировщика
profile_nurture_scheduler = ProfileNurtureScheduler()


# Функция для запуска планировщика (добавьте в main.py или startup)
async def start_profile_nurture_scheduler():
    """Запустить планировщик в фоновом режиме"""
    asyncio.create_task(profile_nurture_scheduler.start())


# Функция для остановки планировщика (добавьте в shutdown)
async def stop_profile_nurture_scheduler():
    """Остановить планировщик"""
    await profile_nurture_scheduler.stop()
