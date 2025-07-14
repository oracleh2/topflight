import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models import User
from app.config import settings

logger = structlog.get_logger(__name__)

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT настройки
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    """Сервис аутентификации и авторизации"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверяет пароль"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хеширует пароль"""
        return pwd_context.hash(password)

    @staticmethod
    def generate_api_key() -> str:
        """Генерирует API ключ"""
        return f"yp_{secrets.token_urlsafe(32)}"

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Создает JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Проверяет JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != token_type:
                return None

            user_id: str = payload.get("sub")
            if user_id is None:
                return None

            return payload

        except JWTError:
            return None

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
        """Аутентифицирует пользователя"""
        try:
            result = await session.execute(
                select(User).where(User.email == email.lower())
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not AuthService.verify_password(password, user.password_hash):
                return None

            if not user.is_active:
                return None

            logger.info("User authenticated", user_id=str(user.id), email=email)
            return user

        except Exception as e:
            logger.error("Authentication failed", email=email, error=str(e))
            return None

    @staticmethod
    async def get_user_by_token(session: AsyncSession, token: str) -> Optional[User]:
        """Получает пользователя по токену"""
        try:
            payload = AuthService.verify_token(token)
            if not payload:
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return None

            return user

        except Exception as e:
            logger.error("Failed to get user by token", error=str(e))
            return None

    @staticmethod
    async def get_user_by_api_key(session: AsyncSession, api_key: str) -> Optional[User]:
        """Получает пользователя по API ключу"""
        try:
            result = await session.execute(
                select(User).where(User.api_key == api_key)
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return None

            return user

        except Exception as e:
            logger.error("Failed to get user by API key", error=str(e))
            return None


class PasswordValidator:
    """Валидатор паролей"""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> Dict[str, Any]:
        """Валидирует пароль"""
        errors = []

        #TODO Не забыть включить обратно валидацию пароля

        # if len(password) < cls.MIN_LENGTH:
        #     errors.append(f"Пароль должен содержать минимум {cls.MIN_LENGTH} символов")
        #
        # if len(password) > cls.MAX_LENGTH:
        #     errors.append(f"Пароль должен содержать максимум {cls.MAX_LENGTH} символов")
        #
        # if not any(c.isupper() for c in password):
        #     errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        #
        # if not any(c.islower() for c in password):
        #     errors.append("Пароль должен содержать хотя бы одну строчную букву")
        #
        # if not any(c.isdigit() for c in password):
        #     errors.append("Пароль должен содержать хотя бы одну цифру")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class EmailValidator:
    """Валидатор email адресов"""

    @staticmethod
    def validate(email: str) -> Dict[str, Any]:
        """Валидирует email"""
        import re

        email = email.strip().lower()

        # Простая проверка формата email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            return {
                "valid": False,
                "errors": ["Некорректный формат email адреса"]
            }

        # Дополнительные проверки
        if len(email) > 254:
            return {
                "valid": False,
                "errors": ["Email адрес слишком длинный"]
            }

        return {
            "valid": True,
            "errors": []
        }