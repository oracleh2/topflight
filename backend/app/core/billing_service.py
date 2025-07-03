from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
import structlog

from app.models import (
    User, UserBalance, BalanceTransaction, TariffPlan,
    FinancialTransactionsLog
)

logger = structlog.get_logger(__name__)


class BillingService:
    """Сервис биллинга и тарификации"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_balance(self, user_id: str, amount: Decimal,
                          description: str = "Пополнение баланса",
                          admin_id: Optional[str] = None) -> Dict[str, Any]:
        """Пополняет баланс пользователя"""
        try:
            amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if amount <= 0:
                return {
                    "success": False,
                    "errors": ["Сумма должна быть больше нуля"]
                }

            # Получаем пользователя и его баланс
            result = await self.session.execute(
                select(User, UserBalance)
                .join(UserBalance, User.id == UserBalance.user_id)
                .where(User.id == user_id)
            )

            user_data = result.first()
            if not user_data:
                return {
                    "success": False,
                    "errors": ["Пользователь не найден"]
                }

            user, balance = user_data
            old_balance = balance.current_balance

            # Обновляем баланс
            balance.current_balance += amount
            balance.last_topup_amount = amount
            balance.last_topup_date = datetime.utcnow()

            # Обновляем баланс в модели User (для совместимости)
            user.balance = balance.current_balance

            # Создаем транзакцию
            transaction = BalanceTransaction(
                user_id=user_id,
                amount=amount,
                type="topup",
                description=description,
                admin_id=admin_id
            )

            self.session.add(transaction)
            await self.session.flush()

            # Создаем детальный лог
            transaction_log = FinancialTransactionsLog(
                user_id=user_id,
                transaction_id=transaction.id,
                amount=amount,
                balance_before=old_balance,
                balance_after=balance.current_balance,
                operation_type="topup",
                description=description,
                admin_id=admin_id
            )

            self.session.add(transaction_log)
            await self.session.commit()

            # Проверяем изменение тарифа
            await self._check_tariff_upgrade(user_id)

            logger.info("Balance added",
                        user_id=user_id,
                        amount=float(amount),
                        new_balance=float(balance.current_balance))

            return {
                "success": True,
                "transaction_id": str(transaction.id),
                "new_balance": float(balance.current_balance),
                "amount": float(amount)
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to add balance",
                         user_id=user_id, amount=float(amount), error=str(e))
            return {
                "success": False,
                "errors": ["Ошибка пополнения баланса"]
            }

    async def charge_balance(self, user_id: str, amount: Decimal,
                             description: str = "Списание за услуги",
                             admin_id: Optional[str] = None) -> Dict[str, Any]:
        """Списывает средства с баланса пользователя"""
        try:
            amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if amount <= 0:
                return {
                    "success": False,
                    "errors": ["Сумма должна быть больше нуля"]
                }

            # Получаем пользователя и его баланс
            result = await self.session.execute(
                select(User, UserBalance)
                .join(UserBalance, User.id == UserBalance.user_id)
                .where(User.id == user_id)
            )

            user_data = result.first()
            if not user_data:
                return {
                    "success": False,
                    "errors": ["Пользователь не найден"]
                }

            user, balance = user_data

            # Проверяем достаточность средств
            if balance.current_balance < amount:
                return {
                    "success": False,
                    "errors": ["Недостаточно средств на балансе"]
                }

            old_balance = balance.current_balance

            # Списываем средства
            balance.current_balance -= amount
            user.balance = balance.current_balance

            # Создаем транзакцию
            transaction = BalanceTransaction(
                user_id=user_id,
                amount=-amount,  # Отрицательная сумма для списания
                type="charge",
                description=description,
                admin_id=admin_id
            )

            self.session.add(transaction)
            await self.session.flush()

            # Создаем детальный лог
            transaction_log = FinancialTransactionsLog(
                user_id=user_id,
                transaction_id=transaction.id,
                amount=-amount,
                balance_before=old_balance,
                balance_after=balance.current_balance,
                operation_type="charge",
                description=description,
                admin_id=admin_id
            )

            self.session.add(transaction_log)
            await self.session.commit()

            logger.info("Balance charged",
                        user_id=user_id,
                        amount=float(amount),
                        new_balance=float(balance.current_balance))

            return {
                "success": True,
                "transaction_id": str(transaction.id),
                "new_balance": float(balance.current_balance),
                "charged_amount": float(amount)
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to charge balance",
                         user_id=user_id, amount=float(amount), error=str(e))
            return {
                "success": False,
                "errors": ["Ошибка списания средств"]
            }

    async def reserve_balance(self, user_id: str, amount: Decimal) -> Dict[str, Any]:
        """Резервирует средства на балансе"""
        try:
            amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if amount <= 0:
                return {
                    "success": False,
                    "errors": ["Сумма должна быть больше нуля"]
                }

            result = await self.session.execute(
                select(UserBalance).where(UserBalance.user_id == user_id)
            )

            balance = result.scalar_one_or_none()
            if not balance:
                return {
                    "success": False,
                    "errors": ["Баланс пользователя не найден"]
                }

            # Проверяем достаточность свободных средств
            available_balance = balance.current_balance - balance.reserved_balance
            if available_balance < amount:
                return {
                    "success": False,
                    "errors": ["Недостаточно свободных средств"]
                }

            # Резервируем средства
            balance.reserved_balance += amount
            await self.session.commit()

            logger.info("Balance reserved",
                        user_id=user_id,
                        amount=float(amount),
                        reserved_balance=float(balance.reserved_balance))

            return {
                "success": True,
                "reserved_amount": float(amount),
                "total_reserved": float(balance.reserved_balance)
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to reserve balance",
                         user_id=user_id, amount=float(amount), error=str(e))
            return {
                "success": False,
                "errors": ["Ошибка резервирования средств"]
            }

    async def release_reservation(self, user_id: str, amount: Decimal) -> Dict[str, Any]:
        """Снимает резервирование средств"""
        try:
            amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            result = await self.session.execute(
                select(UserBalance).where(UserBalance.user_id == user_id)
            )

            balance = result.scalar_one_or_none()
            if not balance:
                return {
                    "success": False,
                    "errors": ["Баланс пользователя не найден"]
                }

            # Снимаем резервирование
            balance.reserved_balance = max(Decimal('0'), balance.reserved_balance - amount)
            await self.session.commit()

            logger.info("Balance reservation released",
                        user_id=user_id,
                        amount=float(amount),
                        reserved_balance=float(balance.reserved_balance))

            return {
                "success": True,
                "released_amount": float(amount),
                "total_reserved": float(balance.reserved_balance)
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to release reservation",
                         user_id=user_id, amount=float(amount), error=str(e))
            return {
                "success": False,
                "errors": ["Ошибка снятия резервирования"]
            }

    async def get_current_tariff(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает текущий тариф пользователя"""
        try:
            # Получаем пользователя
            user = await self.session.get(User, user_id)
            if not user:
                return None

            # Получаем тарифный план
            result = await self.session.execute(
                select(TariffPlan).where(TariffPlan.name == user.subscription_plan)
            )

            tariff = result.scalar_one_or_none()
            if not tariff:
                return None

            return {
                "id": str(tariff.id),
                "name": tariff.name,
                "description": tariff.description,
                "cost_per_check": float(tariff.cost_per_check),
                "min_monthly_topup": float(tariff.min_monthly_topup),
                "server_binding_allowed": tariff.server_binding_allowed,
                "priority_level": tariff.priority_level
            }

        except Exception as e:
            logger.error("Failed to get current tariff", user_id=user_id, error=str(e))
            return None

    async def calculate_check_cost(self, user_id: str, checks_count: int = 1) -> Decimal:
        """Вычисляет стоимость проверок для пользователя"""
        try:
            tariff = await self.get_current_tariff(user_id)
            if not tariff:
                # Дефолтная стоимость
                return Decimal('1.00') * checks_count

            return Decimal(str(tariff["cost_per_check"])) * checks_count

        except Exception as e:
            logger.error("Failed to calculate check cost",
                         user_id=user_id, error=str(e))
            return Decimal('1.00') * checks_count

    async def _check_tariff_upgrade(self, user_id: str):
        """Проверяет необходимость изменения тарифа пользователя"""
        try:
            # Получаем сумму пополнений за последние 30 дней
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            result = await self.session.execute(
                select(func.coalesce(func.sum(BalanceTransaction.amount), 0))
                .where(
                    and_(
                        BalanceTransaction.user_id == user_id,
                        BalanceTransaction.type == "topup",
                        BalanceTransaction.created_at >= thirty_days_ago
                    )
                )
            )

            monthly_topup = result.scalar() or Decimal('0')

            # Получаем подходящий тариф
            result = await self.session.execute(
                select(TariffPlan)
                .where(
                    and_(
                        TariffPlan.min_monthly_topup <= monthly_topup,
                        TariffPlan.is_active == True
                    )
                )
                .order_by(TariffPlan.min_monthly_topup.desc())
                .limit(1)
            )

            best_tariff = result.scalar_one_or_none()

            if best_tariff:
                # Обновляем тариф пользователя
                await self.session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(subscription_plan=best_tariff.name)
                )

                await self.session.commit()

                logger.info("Tariff upgraded",
                            user_id=user_id,
                            new_tariff=best_tariff.name,
                            monthly_topup=float(monthly_topup))

        except Exception as e:
            logger.error("Failed to check tariff upgrade",
                         user_id=user_id, error=str(e))

    async def get_transaction_history(self, user_id: str,
                                      limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Получает историю транзакций пользователя"""
        try:
            result = await self.session.execute(
                select(BalanceTransaction)
                .where(BalanceTransaction.user_id == user_id)
                .order_by(BalanceTransaction.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            transactions = result.scalars().all()

            return [
                {
                    "id": str(transaction.id),
                    "amount": float(transaction.amount),
                    "type": transaction.type,
                    "description": transaction.description,
                    "created_at": transaction.created_at.isoformat()
                }
                for transaction in transactions
            ]

        except Exception as e:
            logger.error("Failed to get transaction history",
                         user_id=user_id, error=str(e))
            return []