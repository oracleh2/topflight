from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshToken(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Новый пароль должен содержать минимум 8 символов')
        return v


class APIKeyResponse(BaseModel):
    api_key: str


class UserProfile(BaseModel):
    id: str
    email: str
    subscription_plan: str
    balance: float
    current_balance: float
    reserved_balance: float
    api_key: str
    created_at: str
    domains_count: int
    keywords_count: int
    last_topup_amount: Optional[float]
    last_topup_date: Optional[str]