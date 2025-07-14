# backend/app/api/auth.py - ДОПОЛНЕНИЯ для админ проверки
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user_service import UserService
from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    RefreshToken,
    PasswordChange,
    APIKeyResponse,
    UserProfile,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register_user(
    user_data: UserRegister, session: AsyncSession = Depends(get_session)
):
    """Регистрация нового пользователя"""
    user_service = UserService(session)
    result = await user_service.create_user(
        email=user_data.email, password=user_data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["errors"]
        )

    return {
        "success": True,
        "message": "Пользователь успешно зарегистрирован",
        "user_id": result["user_id"],
        "api_key": result["api_key"],
    }


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin, session: AsyncSession = Depends(get_session)
):
    """Авторизация пользователя"""
    user_service = UserService(session)
    result = await user_service.authenticate_and_login(
        email=user_data.email, password=user_data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["errors"][0] if result["errors"] else "Ошибка авторизации",
        )

    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post("/refresh", response_model=dict)
async def refresh_access_token(
    token_data: RefreshToken, session: AsyncSession = Depends(get_session)
):
    """Обновление access token"""
    user_service = UserService(session)
    result = await user_service.refresh_access_token(token_data.refresh_token)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                result["errors"][0]
                if result["errors"]
                else "Недействительный refresh token"
            ),
        )

    return {"access_token": result["access_token"], "token_type": result["token_type"]}


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение профиля пользователя"""
    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль пользователя не найден",
        )

    return UserProfile(**profile)


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Изменение пароля"""
    user_service = UserService(session)
    result = await user_service.change_password(
        user_id=str(current_user.id),
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["errors"]
        )

    return {"success": True, "message": "Пароль успешно изменен"}


@router.post("/regenerate-api-key", response_model=APIKeyResponse)
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Генерация нового API ключа"""
    user_service = UserService(session)
    result = await user_service.regenerate_api_key(str(current_user.id))

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["errors"]
        )

    return APIKeyResponse(api_key=result["api_key"])


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Проверяет, что текущий пользователь является администратором.
    Возвращает пользователя или поднимает HTTPException.
    """

    # Проверяем админские права
    # В зависимости от вашей модели User, проверка может отличаться
    # Варианты реализации:

    # Вариант 1: Если есть поле is_admin
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        return current_user

    # Вариант 2: Если есть поле role
    if hasattr(current_user, "role") and current_user.role == "admin":
        return current_user

    # Вариант 3: Проверка по email (временное решение для разработки)
    admin_emails = ["oracleh2@gmail.com"]  # Замените на реальные
    if current_user.email in admin_emails:
        return current_user

    # Вариант 4: Если админы определяются subscription_plan
    if (
        hasattr(current_user, "subscription_plan")
        and current_user.subscription_plan == "admin"
    ):
        return current_user

    # Если ни одна проверка не прошла - доступ запрещен
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
    )


# Альтернативная функция для проверки конкретных разрешений
async def require_permission(permission: str):
    """
    Декоратор-зависимость для проверки конкретных разрешений.
    Пример использования: Depends(require_permission("debug_tasks"))
    """

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # Здесь можно реализовать более сложную систему разрешений
        # Например, через таблицу user_permissions или role_permissions

        # Для debug системы достаточно проверки на админа
        admin_permissions = [
            "debug_tasks",
            "manage_vnc",
            "view_all_tasks",
            "system_monitoring",
        ]

        if permission in admin_permissions:
            return get_current_admin_user(current_user)

        return current_user

    return permission_checker


# Middleware для логирования админских действий
async def log_admin_action(
    action: str,
    resource_type: str,
    resource_id: str,
    admin_user: User,
    session: AsyncSession,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Логирует действия администраторов для аудита.
    """
    try:
        # Можно сохранять в БД если есть таблица audit_log
        # Или просто логировать в файл

        import structlog

        logger = structlog.get_logger(__name__)

        logger.info(
            "Admin action performed",
            admin_id=str(admin_user.id),
            admin_email=admin_user.email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Если есть таблица audit_trail, сохраняем туда
        # audit_record = AuditTrail(
        #     user_id=admin_user.id,
        #     action_type=action,
        #     table_name=resource_type,
        #     record_id=resource_id,
        #     new_values=details,
        #     created_at=datetime.now(timezone.utc)
        # )
        # session.add(audit_record)
        # await session.commit()

    except Exception as e:
        # Ошибки логирования не должны прерывать основной процесс
        import structlog

        logger = structlog.get_logger(__name__)
        logger.error("Failed to log admin action", error=str(e))
