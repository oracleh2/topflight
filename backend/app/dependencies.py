from fastapi import Depends, HTTPException, status, Security, Query, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_session
from app.core.auth import AuthService
from app.models import User

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_session)
) -> User:
    """Получает текущего пользователя по JWT токену"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user = await AuthService.get_user_by_token(session, credentials.credentials)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception


async def get_current_user_optional(
        session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Получает текущего пользователя (опционально)"""
    from fastapi import Request

    # Пытаемся получить токен из заголовка Authorization
    try:
        # Получаем request через dependency injection
        request = Request(scope={"type": "http"})
        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        user = await AuthService.get_user_by_token(session, token)
        return user
    except Exception:
        return None


async def get_user_by_api_key(
        api_key: str,
        session: AsyncSession = Depends(get_session)
) -> User:
    """Получает пользователя по API ключу"""

    user = await AuthService.get_user_by_api_key(session, api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return user


async def require_api_key(
        api_key: Optional[str] = Query(None, description="API ключ"),
        x_api_key: Optional[str] = Header(None, description="API ключ в заголовке"),
        session: AsyncSession = Depends(get_session)
) -> User:
    """Dependency для обязательной проверки API ключа"""

    # Пробуем получить API ключ из разных источников
    key = api_key or x_api_key

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    return await get_user_by_api_key(key, session)


async def optional_api_key(
        api_key: Optional[str] = Query(None, description="API ключ"),
        x_api_key: Optional[str] = Header(None, description="API ключ в заголовке"),
        session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Dependency для опциональной проверки API ключа"""

    # Пробуем получить API ключ из разных источников
    key = api_key or x_api_key

    if not key:
        return None

    try:
        return await get_user_by_api_key(key, session)
    except HTTPException:
        return None