from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_session
from app.core.billing_service import BillingService
from app.dependencies import get_current_user, require_api_key
from app.schemas.user import (
    BalanceTopup, BalanceResponse, TransactionHistory, TariffInfo
)
from app.models import User

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/balance", response_model=dict)
async def get_balance(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Получение баланса пользователя"""
    billing_service = BillingService(session)

    # Получаем детальную информацию о балансе
    from app.core.user_service import UserService
    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль пользователя не найден"
        )

    return {
        "current_balance": profile["current_balance"],
        "reserved_balance": profile["reserved_balance"],
        "available_balance": profile["current_balance"] - profile["reserved_balance"]
    }


@router.post("/topup", response_model=BalanceResponse)
async def topup_balance(
        topup_data: BalanceTopup,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Пополнение баланса (для тестирования)"""
    billing_service = BillingService(session)
    result = await billing_service.add_balance(
        user_id=str(current_user.id),
        amount=topup_data.amount,
        description="Тестовое пополнение баланса"
    )

    return BalanceResponse(**result)


@router.get("/tariff", response_model=TariffInfo)
async def get_current_tariff(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Получение текущего тарифа"""
    billing_service = BillingService(session)
    tariff = await billing_service.get_current_tariff(str(current_user.id))

    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тариф не найден"
        )

    return TariffInfo(**tariff)


@router.get("/transactions", response_model=List[TransactionHistory])
async def get_transaction_history(
        limit: int = Query(50, le=100),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """История транзакций"""
    billing_service = BillingService(session)
    transactions = await billing_service.get_transaction_history(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )

    return [TransactionHistory(**transaction) for transaction in transactions]


@router.get("/check-cost", response_model=dict)
async def calculate_check_cost(
        checks_count: int = Query(1, ge=1, le=1000),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Расчет стоимости проверок"""
    billing_service = BillingService(session)
    cost = await billing_service.calculate_check_cost(
        user_id=str(current_user.id),
        checks_count=checks_count
    )

    return {
        "checks_count": checks_count,
        "total_cost": float(cost),
        "cost_per_check": float(cost / checks_count)
    }


# API endpoints для работы через API ключ
@router.get("/api/balance", response_model=dict)
async def api_get_balance(
        api_key: str = Query(..., description="API ключ"),
        session: AsyncSession = Depends(get_session)
):
    """Получение баланса через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    from app.core.user_service import UserService
    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль пользователя не найден"
        )

    return {
        "current_balance": profile["current_balance"],
        "reserved_balance": profile["reserved_balance"],
        "available_balance": profile["current_balance"] - profile["reserved_balance"]
    }