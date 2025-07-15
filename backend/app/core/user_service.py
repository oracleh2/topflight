import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
import structlog

from app.models import (
    User,
    UserBalance,
    BalanceTransaction,
    TariffPlan,
    UserDomain,
    UserKeyword,
    UserDomainSettings,
    Region,
    YandexRegion,
    DeviceType,
)
from .auth import AuthService, PasswordValidator, EmailValidator

logger = structlog.get_logger(__name__)


class UserService:
    """Сервис для управления пользователями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self, email: str, password: str, subscription_plan: str = "basic"
    ) -> Dict[str, Any]:
        """Создает нового пользователя"""
        try:
            # Валидация email
            email_validation = EmailValidator.validate(email)
            if not email_validation["valid"]:
                return {"success": False, "errors": email_validation["errors"]}

            # Валидация пароля
            password_validation = PasswordValidator.validate(password)
            if not password_validation["valid"]:
                return {"success": False, "errors": password_validation["errors"]}

            email = email.lower().strip()

            # Проверяем существует ли пользователь
            existing_user = await self.session.execute(
                select(User).where(User.email == email)
            )

            if existing_user.scalar_one_or_none():
                return {
                    "success": False,
                    "errors": ["Пользователь с таким email уже существует"],
                }

            # Создаем пользователя
            user = User(
                email=email,
                password_hash=AuthService.get_password_hash(password),
                subscription_plan=subscription_plan,
                api_key=AuthService.generate_api_key(),
                balance=Decimal("0.00"),
                is_active=True,
            )

            self.session.add(user)
            await self.session.flush()  # Получаем ID пользователя

            # Создаем баланс пользователя
            user_balance = UserBalance(
                user_id=user.id,
                current_balance=Decimal("0.00"),
                reserved_balance=Decimal("0.00"),
            )

            self.session.add(user_balance)
            await self.session.commit()

            logger.info("User created", user_id=str(user.id), email=email)

            return {"success": True, "user_id": str(user.id), "api_key": user.api_key}

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to create user", email=email, error=str(e))
            return {"success": False, "errors": ["Ошибка создания пользователя"]}

    async def add_balance(
        self,
        user_id: Union[str, UUID],
        amount: Union[Decimal, float, int],  # Принимаем разные типы
        description: str = "Пополнение баланса",
        admin_id: Optional[Union[str, UUID]] = None,
    ) -> Dict[str, Any]:
        """Добавить средства на баланс пользователя"""
        try:
            # Преобразуем в UUID если строка
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            if isinstance(admin_id, str) and admin_id:
                admin_id = UUID(admin_id)

            # Преобразуем amount в Decimal
            if isinstance(amount, (float, int)):
                amount = Decimal(str(amount))
            elif not isinstance(amount, Decimal):
                amount = Decimal(str(amount))

            # Получить текущий баланс
            balance_stmt = select(UserBalance).where(UserBalance.user_id == user_id)
            balance_result = await self.session.execute(balance_stmt)
            user_balance = balance_result.scalar_one_or_none()

            if not user_balance:
                # Создать баланс если не существует
                user_balance = UserBalance(
                    user_id=user_id,
                    current_balance=Decimal("0.00"),
                    reserved_balance=Decimal("0.00"),
                )
                self.session.add(user_balance)
                await self.session.flush()

            # Сохранить старый баланс
            old_balance = user_balance.current_balance
            new_balance = old_balance + amount

            # Обновить баланс
            user_balance.current_balance = new_balance
            user_balance.last_topup_amount = amount
            user_balance.last_topup_date = datetime.utcnow()

            # Создать транзакцию
            transaction = BalanceTransaction(
                user_id=user_id,
                amount=amount,
                type="topup",
                description=description,
                admin_id=admin_id,
            )
            self.session.add(transaction)

            # Также обновить поле balance в таблице users
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if user:
                user.balance = new_balance

            await self.session.commit()

            logger.info("Balance added", user_id=str(user_id), amount=str(amount))

            return {
                "success": True,
                "transaction_id": str(transaction.id),
                "old_balance": float(old_balance),
                "new_balance": float(new_balance),
                "amount": float(amount),
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to add balance", user_id=str(user_id), error=str(e))
            return {"success": False, "errors": ["Ошибка пополнения баланса"]}

    async def authenticate_and_login(self, email: str, password: str) -> Dict[str, Any]:
        """Аутентифицирует пользователя и создает токены"""
        try:
            user = await AuthService.authenticate_user(self.session, email, password)

            if not user:
                return {"success": False, "errors": ["Неверный email или пароль"]}

            # Создаем токены
            token_data = {"sub": str(user.id), "email": user.email}
            access_token = AuthService.create_access_token(token_data)
            refresh_token = AuthService.create_refresh_token(token_data)

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "subscription_plan": user.subscription_plan,
                    "balance": float(user.balance),
                },
            }

        except Exception as e:
            logger.error("Login failed", email=email, error=str(e))
            return {"success": False, "errors": ["Ошибка авторизации"]}

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновляет access token используя refresh token"""
        try:
            payload = AuthService.verify_token(refresh_token, "refresh")
            if not payload:
                return {"success": False, "errors": ["Недействительный refresh token"]}

            user_id = payload.get("sub")
            user = await self.session.get(User, user_id)

            if not user or not user.is_active:
                return {
                    "success": False,
                    "errors": ["Пользователь не найден или неактивен"],
                }

            # Создаем новый access token
            token_data = {"sub": str(user.id), "email": user.email}
            access_token = AuthService.create_access_token(token_data)

            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
            }

        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            return {"success": False, "errors": ["Ошибка обновления токена"]}

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает профиль пользователя"""
        try:
            result = await self.session.execute(
                select(User, UserBalance)
                .join(UserBalance, User.id == UserBalance.user_id)
                .where(User.id == user_id)
            )

            user_data = result.first()
            if not user_data:
                return None

            user, balance = user_data

            # Получаем статистику доменов и ключевых слов
            domains_count = await self.session.scalar(
                select(func.count(UserDomain.id)).where(UserDomain.user_id == user_id)
            )

            keywords_count = await self.session.scalar(
                select(func.count(UserKeyword.id)).where(UserKeyword.user_id == user_id)
            )

            return {
                "id": str(user.id),
                "email": user.email,
                "subscription_plan": user.subscription_plan,
                "balance": float(user.balance),
                "current_balance": float(balance.current_balance),
                "reserved_balance": float(balance.reserved_balance),
                "api_key": user.api_key,
                "created_at": user.created_at.isoformat(),
                "domains_count": domains_count or 0,
                "keywords_count": keywords_count or 0,
                "last_topup_amount": (
                    float(balance.last_topup_amount)
                    if balance.last_topup_amount
                    else None
                ),
                "last_topup_date": (
                    balance.last_topup_date.isoformat()
                    if balance.last_topup_date
                    else None
                ),
            }

        except Exception as e:
            logger.error("Failed to get user profile", user_id=user_id, error=str(e))
            return None

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        """Изменяет пароль пользователя"""
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return {"success": False, "errors": ["Пользователь не найден"]}

            # Проверяем текущий пароль
            if not AuthService.verify_password(current_password, user.password_hash):
                return {"success": False, "errors": ["Неверный текущий пароль"]}

            # Валидируем новый пароль
            validation = PasswordValidator.validate(new_password)
            if not validation["valid"]:
                return {"success": False, "errors": validation["errors"]}

            # Обновляем пароль
            user.password_hash = AuthService.get_password_hash(new_password)
            await self.session.commit()

            logger.info("Password changed", user_id=user_id)

            return {"success": True}

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to change password", user_id=user_id, error=str(e))
            return {"success": False, "errors": ["Ошибка изменения пароля"]}

    async def regenerate_api_key(self, user_id: str) -> Dict[str, Any]:
        """Генерирует новый API ключ"""
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return {"success": False, "errors": ["Пользователь не найден"]}

            user.api_key = AuthService.generate_api_key()
            await self.session.commit()

            logger.info("API key regenerated", user_id=user_id)

            return {"success": True, "api_key": user.api_key}

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to regenerate API key", user_id=user_id, error=str(e))
            return {"success": False, "errors": ["Ошибка генерации API ключа"]}

    async def add_domain(self, user_id: str, domain: str) -> Dict[str, Any]:
        """Добавляет домен пользователю"""
        try:
            # Нормализуем домен
            domain = domain.lower().strip()
            if domain.startswith("http://") or domain.startswith("https://"):
                domain = domain.split("://")[1]
            if domain.startswith("www."):
                domain = domain[4:]
            domain = domain.rstrip("/")

            # Проверяем существует ли домен у пользователя
            existing_domain = await self.session.execute(
                select(UserDomain).where(
                    and_(UserDomain.user_id == user_id, UserDomain.domain == domain)
                )
            )

            if existing_domain.scalar_one_or_none():
                return {"success": False, "errors": ["Домен уже добавлен"]}

            # Добавляем домен
            user_domain = UserDomain(
                user_id=user_id,
                domain=domain,
                is_verified=False,  # Потом можно добавить верификацию
            )

            self.session.add(user_domain)
            await self.session.commit()
            await self.session.refresh(user_domain)

            logger.info("Domain added", user_id=user_id, domain=domain)

            return {"success": True, "domain_id": str(user_domain.id), "domain": domain}

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to add domain", user_id=user_id, domain=domain, error=str(e)
            )
            return {"success": False, "errors": ["Ошибка добавления домена"]}

    async def get_user_domains(self, user_id: str) -> List[Dict[str, Any]]:
        """Получает домены пользователя"""
        try:
            result = await self.session.execute(
                select(UserDomain)
                .options(selectinload(UserDomain.keywords))
                .where(UserDomain.user_id == user_id)
                .order_by(UserDomain.created_at.desc())
            )

            domains = result.scalars().all()

            return [
                {
                    "id": str(domain.id),
                    "domain": domain.domain,
                    "is_verified": domain.is_verified,
                    "created_at": domain.created_at.isoformat(),
                    "keywords_count": len(domain.keywords),
                }
                for domain in domains
            ]

        except Exception as e:
            logger.error("Failed to get user domains", user_id=user_id, error=str(e))
            return []

    async def add_keyword(
        self,
        user_id: str,
        domain_id: str,
        keyword: str,
        region_id: str,
        device_type: DeviceType = DeviceType.DESKTOP,
        check_frequency: str = "daily",
        is_active: bool = True,
    ) -> Dict[str, Any]:
        """Добавляет ключевое слово с дополнительными параметрами"""
        try:
            # Проверяем принадлежность домена пользователю
            domain = await self.session.execute(
                select(UserDomain).where(
                    and_(UserDomain.id == domain_id, UserDomain.user_id == user_id)
                )
            )

            domain_obj = domain.scalar_one_or_none()
            if not domain_obj:
                return {"success": False, "errors": ["Домен не найден"]}

            # Проверяем существование региона
            region = await self.session.get(YandexRegion, region_id)
            if not region:
                return {"success": False, "errors": ["Регион не найден"]}

            # Проверяем существует ли уже такое ключевое слово
            existing_keyword = await self.session.execute(
                select(UserKeyword).where(
                    UserKeyword.user_id == user_id,
                    UserKeyword.domain_id == domain_id,
                    UserKeyword.keyword == keyword.strip(),
                    UserKeyword.region_id == region_id,
                    UserKeyword.device_type == device_type,
                )
            )

            if existing_keyword.scalar_one_or_none():
                return {
                    "success": False,
                    "errors": [
                        "Ключевое слово уже добавлено для этого домена и региона"
                    ],
                }

            # Добавляем ключевое слово
            user_keyword = UserKeyword(
                user_id=user_id,
                domain_id=domain_id,
                keyword=keyword.strip(),
                region_id=region_id,
                device_type=device_type,
                check_frequency=check_frequency,
                is_active=is_active,
            )

            self.session.add(user_keyword)
            await self.session.commit()
            await self.session.refresh(user_keyword)

            logger.info(f"Keyword added: {keyword} for user {user_id}")

            return {
                "success": True,
                "keyword_id": str(user_keyword.id),
                "keyword": keyword,
                "device_type": device_type.value,
                "check_frequency": check_frequency,
                "is_active": is_active,
            }

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add keyword: {str(e)}")
            return {"success": False, "errors": ["Ошибка добавления ключевого слова"]}

    async def get_domain_keywords(
        self, user_id: str, domain_id: str
    ) -> List[Dict[str, Any]]:
        """Получает ключевые слова домена"""
        try:
            result = await self.session.execute(
                select(UserKeyword)
                .options(selectinload(UserKeyword.region))
                .where(
                    and_(
                        UserKeyword.user_id == user_id,
                        UserKeyword.domain_id == domain_id,
                    )
                )
                .order_by(UserKeyword.created_at.desc())
            )

            keywords = result.scalars().all()

            return [
                {
                    "id": str(keyword.id),
                    "keyword": keyword.keyword,
                    "region": {
                        "id": str(keyword.region.id),
                        "code": keyword.region.region_code,
                        "name": keyword.region.region_name,
                    },
                    "device_type": keyword.device_type.value,
                    "is_active": keyword.is_active,
                    "check_frequency": keyword.check_frequency,
                    "created_at": keyword.created_at.isoformat(),
                }
                for keyword in keywords
            ]

        except Exception as e:
            logger.error(
                "Failed to get domain keywords",
                user_id=user_id,
                domain_id=domain_id,
                error=str(e),
            )
            return []

    async def delete_keyword(self, user_id: str, keyword_id: str) -> Dict[str, Any]:
        """Удаляет ключевое слово"""
        try:
            keyword = await self.session.execute(
                select(UserKeyword).where(
                    and_(UserKeyword.id == keyword_id, UserKeyword.user_id == user_id)
                )
            )

            keyword_obj = keyword.scalar_one_or_none()
            if not keyword_obj:
                return {"success": False, "errors": ["Ключевое слово не найдено"]}

            await self.session.delete(keyword_obj)
            await self.session.commit()

            logger.info("Keyword deleted", user_id=user_id, keyword_id=keyword_id)

            return {"success": True}

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to delete keyword",
                user_id=user_id,
                keyword_id=keyword_id,
                error=str(e),
            )
            return {"success": False, "errors": ["Ошибка удаления ключевого слова"]}

    async def delete_domain(self, user_id: str, domain_id: str) -> Dict[str, Any]:
        """Удаляет домен и все связанные ключевые слова"""
        try:
            domain = await self.session.execute(
                select(UserDomain).where(
                    and_(UserDomain.id == domain_id, UserDomain.user_id == user_id)
                )
            )

            domain_obj = domain.scalar_one_or_none()
            if not domain_obj:
                return {"success": False, "errors": ["Домен не найден"]}

            # Удаляем домен (каскадно удалятся связанные ключевые слова)
            await self.session.delete(domain_obj)
            await self.session.commit()

            logger.info("Domain deleted", user_id=user_id, domain_id=domain_id)

            return {"success": True}

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to delete domain",
                user_id=user_id,
                domain_id=domain_id,
                error=str(e),
            )
            return {"success": False, "errors": ["Ошибка удаления домена"]}
