from pydantic import BaseModel, validator
from typing import Optional, List
from decimal import Decimal


class BalanceTopup(BaseModel):
    amount: Decimal

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма должна быть больше нуля')
        if v > Decimal('100000'):
            raise ValueError('Максимальная сумма пополнения: 100,000 рублей')
        return v


class BalanceResponse(BaseModel):
    success: bool
    transaction_id: Optional[str] = None
    new_balance: Optional[float] = None
    amount: Optional[float] = None
    errors: Optional[List[str]] = None


class TransactionHistory(BaseModel):
    id: str
    amount: float
    type: str
    description: str
    created_at: str


class TariffInfo(BaseModel):
    id: str
    name: str
    description: str
    cost_per_check: float
    min_monthly_topup: float
    server_binding_allowed: bool
    priority_level: int