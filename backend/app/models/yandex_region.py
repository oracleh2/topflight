# Создать файл backend/app/models/yandex_region.py

from sqlalchemy import Column, String, Integer, Text, Boolean
from sqlalchemy.orm import relationship
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
    def search_by_name(cls, session, query: str, limit: int = 10):
        """Поиск регионов по названию"""
        search_term = f"%{query.lower()}%"
        return (
            session.query(cls)
            .filter(
                cls.is_active == True,
                (
                    cls.region_name.ilike(search_term)
                    | cls.search_name.ilike(search_term)
                    | cls.display_name.ilike(search_term)
                ),
            )
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
