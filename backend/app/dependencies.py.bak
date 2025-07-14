from fastapi import Depends, HTTPException, status, Security
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
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False),
        session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Получает текущего пользователя (опционально)"""

    if not credentials:
        return None

    try:
        user = await AuthService.get_user_by_token(session, credentials.credentials)
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


class RequireAPIKey:
    """Dependency для проверки API ключа из query параметра или заголовка"""

    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(
            self,
            api_key: Optional[str] = None,  # Query parameter
            x_api_key: Optional[str] = None,  # Header
            session: AsyncSession = Depends(get_session)
    ) -> Optional[User]:

        # Пробуем получить API ключ из разных источников
        key = api_key or x_api_key

        if not key:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required"
                )
            return None

        return await get_user_by_api_key(key, session)


require_api_key = RequireAPIKey()
optional_api_key = RequireAPIKey(auto_error=False)