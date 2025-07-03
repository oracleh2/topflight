from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.core.user_service import UserService
from app.dependencies import get_current_user
from app.schemas.auth import (
    UserRegister, UserLogin, Token, RefreshToken,
    PasswordChange, APIKeyResponse, UserProfile
)
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register_user(
        user_data: UserRegister,
        session: AsyncSession = Depends(get_session)
):
    """Регистрация нового пользователя"""
    user_service = UserService(session)
    result = await user_service.create_user(
        email=user_data.email,
        password=user_data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {
        "success": True,
        "message": "Пользователь успешно зарегистрирован",
        "user_id": result["user_id"],
        "api_key": result["api_key"]
    }


@router.post("/login", response_model=Token)
async def login_user(
        user_data: UserLogin,
        session: AsyncSession = Depends(get_session)
):
    """Авторизация пользователя"""
    user_service = UserService(session)
    result = await user_service.authenticate_and_login(
        email=user_data.email,
        password=user_data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["errors"][0] if result["errors"] else "Ошибка авторизации"
        )

    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"]
    )


@router.post("/refresh", response_model=dict)
async def refresh_access_token(
        token_data: RefreshToken,
        session: AsyncSession = Depends(get_session)
):
    """Обновление access token"""
    user_service = UserService(session)
    result = await user_service.refresh_access_token(token_data.refresh_token)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["errors"][0] if result["errors"] else "Недействительный refresh token"
        )

    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"]
    }


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Получение профиля пользователя"""
    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль пользователя не найден"
        )

    return UserProfile(**profile)


@router.post("/change-password", response_model=dict)
async def change_password(
        password_data: PasswordChange,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Изменение пароля"""
    user_service = UserService(session)
    result = await user_service.change_password(
        user_id=str(current_user.id),
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {"success": True, "message": "Пароль успешно изменен"}


@router.post("/regenerate-api-key", response_model=APIKeyResponse)
async def regenerate_api_key(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Генерация нового API ключа"""
    user_service = UserService(session)
    result = await user_service.regenerate_api_key(str(current_user.id))

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return APIKeyResponse(api_key=result["api_key"])