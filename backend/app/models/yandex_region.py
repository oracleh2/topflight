# Создать файл backend/app/models/yandex_region.py

from sqlalchemy import Column, String, Integer, Text, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy import select, case, func, or_


from app.models.base import Base, UUIDMixin, TimestampMixin


class YandexRegion(Base, UUIDMixin, TimestampMixin):
    """Модель регионов Яндекса для поиска и геотаргетинга"""

    __tablename__ = "yandex_regions"

    # Основные поля из Яндекс API
    region_code = Column(String(10), unique=True, nullable=False, index=True)
    region_name = Column(String(255), nullable=False, index=True)
    country_code = Column(String(5), default="RU", nullable=False, index=True)

    # Дополнительные поля для расширенной информации
    parent_region_code = Column(String(10), nullable=True)  # Родительский регион
    region_type = Column(String(50), nullable=True)  # Тип: city, region, country
    timezone = Column(String(50), nullable=True)  # Временная зона

    # Координаты центра региона
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)

    # Дополнительная информация
    population = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Поля для поиска и отображения
    search_name = Column(
        String(255), nullable=True
    )  # Альтернативные названия для поиска
    display_name = Column(String(255), nullable=True)  # Отображаемое название

    def __repr__(self):
        return f"<YandexRegion(code='{self.region_code}', name='{self.region_name}', country='{self.country_code}')>"

    def __str__(self):
        return f"{self.region_name} ({self.region_code})"

    @classmethod
    def get_by_code(cls, session, region_code: str):
        """Получить регион по коду"""
        return session.query(cls).filter(cls.region_code == region_code).first()

    @classmethod
    async def search_by_name_async(
        cls, session: AsyncSession, query: str, limit: int = 10
    ):
        """Асинхронный поиск регионов по названию с умной сортировкой"""
        query_lower = query.lower().strip()

        # Паттерны для поиска
        exact_pattern = query_lower  # Точное совпадение
        starts_with_pattern = f"{query_lower}%"  # Начинается с
        contains_pattern = f"%{query_lower}%"  # Содержит

        # Условия для сортировки по приоритету
        priority_case = case(
            # Приоритет 1: Точное совпадение кода региона
            (func.lower(cls.region_code) == exact_pattern, 1),
            # Приоритет 2: Точное совпадение названия
            (func.lower(cls.region_name) == exact_pattern, 2),
            # Приоритет 3: Точное совпадение display_name
            (func.lower(cls.display_name) == exact_pattern, 3),
            # Приоритет 4: Код начинается с запроса
            (func.lower(cls.region_code).like(starts_with_pattern), 4),
            # Приоритет 5: Название начинается с запроса
            (func.lower(cls.region_name).like(starts_with_pattern), 5),
            # Приоритет 6: Display_name начинается с запроса
            (func.lower(cls.display_name).like(starts_with_pattern), 6),
            # Приоритет 7: Search_name начинается с запроса
            (func.lower(cls.search_name).like(starts_with_pattern), 7),
            # Приоритет 8: Код содержит запрос
            (func.lower(cls.region_code).like(contains_pattern), 8),
            # Приоритет 9: Название содержит запрос
            (func.lower(cls.region_name).like(contains_pattern), 9),
            # Приоритет 10: Display_name содержит запрос
            (func.lower(cls.display_name).like(contains_pattern), 10),
            # Приоритет 11: Search_name содержит запрос
            (func.lower(cls.search_name).like(contains_pattern), 11),
            # Приоритет 12: Все остальные
            else_=12,
        )

        # Условия поиска
        search_conditions = or_(
            # Точные совпадения
            func.lower(cls.region_code) == exact_pattern,
            func.lower(cls.region_name) == exact_pattern,
            func.lower(cls.display_name) == exact_pattern,
            # Начинается с
            func.lower(cls.region_code).like(starts_with_pattern),
            func.lower(cls.region_name).like(starts_with_pattern),
            func.lower(cls.display_name).like(starts_with_pattern),
            func.lower(cls.search_name).like(starts_with_pattern),
            # Содержит
            func.lower(cls.region_code).like(contains_pattern),
            func.lower(cls.region_name).like(contains_pattern),
            func.lower(cls.display_name).like(contains_pattern),
            func.lower(cls.search_name).like(contains_pattern),
        )

        stmt = (
            select(cls)
            .where(cls.is_active == True, search_conditions)
            .order_by(
                priority_case,  # Сортировка по приоритету
                cls.region_name,  # Вторичная сортировка по названию
            )
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def search_with_region_type_priority(
        cls, session: AsyncSession, query: str, limit: int = 10
    ):
        """
        Поиск с учетом типа региона и дополнительными приоритетами
        """
        query_lower = query.lower().strip()

        # Паттерны для поиска
        exact_pattern = query_lower
        starts_with_pattern = f"{query_lower}%"
        contains_pattern = f"%{query_lower}%"

        # Улучшенная приоритизация с учетом типа региона
        priority_case = case(
            # Высший приоритет: точное совпадение кода
            (func.lower(cls.region_code) == exact_pattern, 1),
            # Приоритет 2: точное совпадение названия города
            (
                (func.lower(cls.region_name) == exact_pattern)
                & (cls.region_type == "city"),
                2,
            ),
            # Приоритет 3: точное совпадение названия региона
            (
                (func.lower(cls.region_name) == exact_pattern)
                & (cls.region_type == "region"),
                3,
            ),
            # Приоритет 4: точное совпадение display_name
            (func.lower(cls.display_name) == exact_pattern, 4),
            # Приоритет 5: код начинается с запроса
            (func.lower(cls.region_code).like(starts_with_pattern), 5),
            # Приоритет 6: название города начинается с запроса
            (
                (func.lower(cls.region_name).like(starts_with_pattern))
                & (cls.region_type == "city"),
                6,
            ),
            # Приоритет 7: название региона начинается с запроса
            (
                (func.lower(cls.region_name).like(starts_with_pattern))
                & (cls.region_type == "region"),
                7,
            ),
            # Приоритет 8: display_name начинается с запроса
            (func.lower(cls.display_name).like(starts_with_pattern), 8),
            # Приоритет 9: search_name начинается с запроса
            (func.lower(cls.search_name).like(starts_with_pattern), 9),
            # Приоритет 10: города, содержащие запрос
            (
                (func.lower(cls.region_name).like(contains_pattern))
                & (cls.region_type == "city"),
                10,
            ),
            # Приоритет 11: регионы, содержащие запрос
            (
                (func.lower(cls.region_name).like(contains_pattern))
                & (cls.region_type == "region"),
                11,
            ),
            # Приоритет 12: остальные совпадения
            else_=12,
        )

        # Условия поиска
        search_conditions = or_(
            # Точные совпадения
            func.lower(cls.region_code) == exact_pattern,
            func.lower(cls.region_name) == exact_pattern,
            func.lower(cls.display_name) == exact_pattern,
            # Начинается с
            func.lower(cls.region_code).like(starts_with_pattern),
            func.lower(cls.region_name).like(starts_with_pattern),
            func.lower(cls.display_name).like(starts_with_pattern),
            func.lower(cls.search_name).like(starts_with_pattern),
            # Содержит
            func.lower(cls.region_code).like(contains_pattern),
            func.lower(cls.region_name).like(contains_pattern),
            func.lower(cls.display_name).like(contains_pattern),
            func.lower(cls.search_name).like(contains_pattern),
        )

        stmt = (
            select(cls)
            .where(cls.is_active == True, search_conditions)
            .order_by(
                priority_case,
                # Дополнительная сортировка: сначала города, потом регионы
                case(
                    (cls.region_type == "city", 1),
                    (cls.region_type == "region", 2),
                    else_=3,
                ),
                cls.region_name,
            )
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    def search_by_name(cls, session, query: str, limit: int = 10):
        """Синхронный поиск регионов по названию с умной сортировкой"""
        query_lower = query.lower().strip()

        # Паттерны для поиска
        exact_pattern = query_lower
        starts_with_pattern = f"{query_lower}%"
        contains_pattern = f"%{query_lower}%"

        # Условия для сортировки по приоритету
        priority_case = case(
            # Приоритет 1: Точное совпадение кода региона
            (func.lower(cls.region_code) == exact_pattern, 1),
            # Приоритет 2: Точное совпадение названия
            (func.lower(cls.region_name) == exact_pattern, 2),
            # Приоритет 3: Точное совпадение display_name
            (func.lower(cls.display_name) == exact_pattern, 3),
            # Приоритет 4: Код начинается с запроса
            (func.lower(cls.region_code).like(starts_with_pattern), 4),
            # Приоритет 5: Название начинается с запроса
            (func.lower(cls.region_name).like(starts_with_pattern), 5),
            # Приоритет 6: Display_name начинается с запроса
            (func.lower(cls.display_name).like(starts_with_pattern), 6),
            # Приоритет 7: Search_name начинается с запроса
            (func.lower(cls.search_name).like(starts_with_pattern), 7),
            # Приоритет 8: Остальные вхождения
            else_=8,
        )

        # Условия поиска
        search_conditions = or_(
            func.lower(cls.region_code) == exact_pattern,
            func.lower(cls.region_name) == exact_pattern,
            func.lower(cls.display_name) == exact_pattern,
            func.lower(cls.region_code).like(starts_with_pattern),
            func.lower(cls.region_name).like(starts_with_pattern),
            func.lower(cls.display_name).like(starts_with_pattern),
            func.lower(cls.search_name).like(starts_with_pattern),
            func.lower(cls.region_code).like(contains_pattern),
            func.lower(cls.region_name).like(contains_pattern),
            func.lower(cls.display_name).like(contains_pattern),
            func.lower(cls.search_name).like(contains_pattern),
        )

        return (
            session.query(cls)
            .filter(cls.is_active == True, search_conditions)
            .order_by(priority_case, cls.region_name)
            .limit(limit)
            .all()
        )

    @classmethod
    def get_by_country(cls, session, country_code: str = "RU"):
        """Получить все регионы страны"""
        return (
            session.query(cls)
            .filter(cls.country_code == country_code, cls.is_active == True)
            .order_by(cls.region_name)
            .all()
        )

    @classmethod
    def get_cities(cls, session):
        """Получить только города"""
        return (
            session.query(cls)
            .filter(cls.region_type == "city", cls.is_active == True)
            .order_by(cls.region_name)
            .all()
        )

    @classmethod
    def get_regions(cls, session):
        """Получить только области/регионы"""
        return (
            session.query(cls)
            .filter(cls.region_type == "region", cls.is_active == True)
            .order_by(cls.region_name)
            .all()
        )

    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            "id": str(self.id),
            "code": self.region_code,
            "name": self.region_name,
            "display_name": self.display_name or self.region_name,
            "country_code": self.country_code,
            "region_type": self.region_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
