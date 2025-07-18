# backend/app/api/strategies.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json
import csv
import io
import traceback

from app.models import Task
from app.constants.strategies import (
    validate_warmup_config,
    validate_position_check_config,
    validate_profile_nurture_config,
)
from app.database import get_session
from app.dependencies import get_current_user
from app.models import User, UserStrategy
from app.services.profile_nurture_limits_service import ProfileNurtureLimitsService

router = APIRouter(prefix="/strategies", tags=["Strategies"])

# Попробуем импортировать сервис и схемы с обработкой ошибок
try:
    from app.core.strategy_service import StrategyService
except ImportError as e:
    print(f"Warning: Could not import StrategyService: {e}")
    StrategyService = None

try:
    from app.schemas.strategies import (
        StrategyTemplateResponse,
        UserStrategyCreate,
        UserStrategyUpdate,
        UserStrategyResponse,
        DataSourceCreate,
        ProjectStrategyCreate,
        StrategyValidationResponse,
        StrategyValidationRequest,
        StrategyType,
        DataSourceResponse,
    )
    from app.constants.strategies import StrategyType as StrategyTypeEnum
except ImportError as e:
    print(f"Warning: Could not import some strategy schemas: {e}")
    # Создаем базовые схемы для работы
    from pydantic import BaseModel
    from datetime import datetime
    from typing import Dict, Any

    class StrategyTemplateResponse(BaseModel):
        id: str
        name: str
        description: Optional[str]
        strategy_type: str
        config: Dict[str, Any]
        is_system: bool
        created_at: datetime

    class UserStrategyCreate(BaseModel):
        name: str
        strategy_type: str
        config: Dict[str, Any]

    class UserStrategyUpdate(BaseModel):
        name: Optional[str] = None
        config: Optional[Dict[str, Any]] = None

    class UserStrategyResponse(BaseModel):
        id: str
        user_id: str
        template_id: Optional[str]
        name: str
        strategy_type: StrategyType
        config: Dict[str, Any]
        created_at: datetime
        updated_at: datetime
        is_active: bool
        data_sources: List["DataSourceResponse"] = []
        nurture_status: Optional[Dict[str, Any]] = None

        class Config:
            from_attributes = True

    class DataSourceCreate(BaseModel):
        source_type: str
        source_url: Optional[str] = None
        data_content: Optional[str] = None

    class ProjectStrategyCreate(BaseModel):
        domain_id: Optional[str] = None
        warmup_strategy_id: Optional[str] = None
        position_check_strategy_id: Optional[str] = None


# Попробуем импортировать дополнительные схемы
try:
    from app.schemas.strategies import (
        ProfileNurtureConfigCreate,
        WarmupConfigCreate,
        PositionCheckConfigCreate,
    )
except ImportError as e:
    print(f"Warning: Could not import profile nurture schemas: {e}")
    # Создаем базовые схемы
    from pydantic import BaseModel

    class ProfileNurtureConfigCreate(BaseModel):
        nurture_type: str = "search_based"
        target_cookies: Dict[str, int] = {"min": 50, "max": 100}
        session_config: Dict[str, int] = {"timeout_per_site": 15}

    class WarmupConfigCreate(BaseModel):
        type: str = "mixed"
        min_sites: int = 3
        max_sites: int = 7

    class PositionCheckConfigCreate(BaseModel):
        check_frequency: str = "daily"
        max_pages: int = 10


@router.get("/health")
async def health_check():
    """Проверка работоспособности API стратегий"""
    return {
        "status": "healthy",
        "message": "Strategies API is working",
        "service_available": StrategyService is not None,
    }


@router.get("/default-configs")
async def get_default_configs():
    """Получение конфигураций по умолчанию для разных типов стратегий"""
    try:
        from app.constants.strategies import (
            DEFAULT_WARMUP_CONFIG,
            DEFAULT_POSITION_CHECK_CONFIG,
            DEFAULT_PROFILE_NURTURE_CONFIG,
        )

        return {
            "warmup": DEFAULT_WARMUP_CONFIG,
            "position_check": DEFAULT_POSITION_CHECK_CONFIG,
            "profile_nurture": DEFAULT_PROFILE_NURTURE_CONFIG,
        }
    except ImportError as e:
        # Возвращаем базовые конфигурации если импорт не удался
        return {
            "warmup": {
                "type": "mixed",
                "proportions": {"direct_visits": 30, "search_visits": 70},
                "min_sites": 3,
                "max_sites": 7,
                "session_timeout": 15,
                "yandex_domain": "yandex.ru",
                "device_type": "desktop",
            },
            "position_check": {
                "check_frequency": "daily",
                "yandex_domain": "yandex.ru",
                "device_type": "desktop",
                "max_pages": 10,
                "behavior": {
                    "random_delays": True,
                    "scroll_pages": True,
                    "human_like_clicks": True,
                },
            },
            "profile_nurture": {
                "nurture_type": "search_based",
                "target_cookies": {"min": 50, "max": 100},
                "session_config": {"timeout_per_site": 15},
                "search_engines": ["yandex.ru"],
                "queries_source": {
                    "type": "manual_input",
                    "refresh_on_each_cycle": False,
                },
                "behavior": {
                    "return_to_search": True,
                    "close_browser_after_cycle": False,
                    "emulate_human_actions": True,
                    "scroll_pages": True,
                    "random_clicks": True,
                },
            },
        }


@router.get("/templates", response_model=List[StrategyTemplateResponse])
async def get_strategy_templates(
    strategy_type: Optional[str] = None, session: AsyncSession = Depends(get_session)
):
    """Получение шаблонов стратегий"""
    if StrategyService is None:
        raise HTTPException(status_code=503, detail="Strategy service is not available")

    try:
        strategy_service = StrategyService(session)
        templates = await strategy_service.get_strategy_templates(strategy_type)
        return templates
    except Exception as e:
        print(f"Error in get_strategy_templates: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=List[UserStrategyResponse])
async def get_user_strategies(
    strategy_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение пользовательских стратегий"""
    if StrategyService is None:
        raise HTTPException(status_code=503, detail="Strategy service is not available")

    try:
        strategy_service = StrategyService(session)
        strategies = await strategy_service.get_user_strategies(
            str(current_user.id), strategy_type, session
        )
        return strategies
    except Exception as e:
        print(f"Error in get_user_strategies: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.get("/", response_model=List[UserStrategyResponse])
# async def get_user_strategies(
#     strategy_type: Optional[StrategyType] = None,
#     current_user: User = Depends(get_current_user),
#     session: AsyncSession = Depends(get_session),
# ):
#     """Получить список стратегий пользователя с информацией о лимитах"""
#
#     query = select(UserStrategy).where(UserStrategy.user_id == current_user.id)
#
#     if strategy_type:
#         query = query.where(UserStrategy.strategy_type == strategy_type)
#
#     query = query.order_by(UserStrategy.created_at.desc())
#
#     result = await session.execute(query)
#     strategies = result.scalars().all()
#
#     # Для стратегий нагула профилей добавляем информацию о лимитах
#     limits_service = ProfileNurtureLimitsService(session)
#     strategies_with_limits = []
#
#     for strategy in strategies:
#         strategy_dict = {
#             "id": str(strategy.id),
#             "name": strategy.name,
#             "description": strategy.description,
#             "strategy_type": strategy.strategy_type,
#             "config": strategy.config,
#             "is_active": strategy.is_active,
#             "created_at": strategy.created_at,
#             "updated_at": strategy.updated_at,
#         }
#
#         # Добавляем информацию о лимитах для стратегий нагула
#         if strategy.strategy_type == StrategyType.PROFILE_NURTURE:
#             status = await limits_service.check_strategy_status(str(strategy.id))
#             strategy_dict["nurture_status"] = status
#
#         strategies_with_limits.append(strategy_dict)
#
#     return strategies_with_limits


@router.post("/", response_model=UserStrategyResponse)
async def create_user_strategy(
    strategy_data: UserStrategyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание пользовательской стратегии"""
    if StrategyService is None:
        raise HTTPException(status_code=503, detail="Strategy service is not available")

    try:
        strategy_service = StrategyService(session)
        strategy = await strategy_service.create_user_strategy(
            str(current_user.id), strategy_data
        )
        return strategy
    except Exception as e:
        print(f"Error in create_user_strategy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test")
async def test_endpoint():
    """Тестовый endpoint для проверки работы API"""
    return {
        "status": "working",
        "message": "Strategies API is responding",
        "timestamp": "2025-07-15T19:00:00Z",
    }


@router.get("/profile-nurture/search-engines")
async def get_available_search_engines():
    """Получение списка доступных поисковых систем для нагула"""
    try:
        from app.constants.strategies import SearchEngineType

        engines = [
            {"value": SearchEngineType.YANDEX_RU, "label": "Яндекс.Россия (yandex.ru)"},
            {
                "value": SearchEngineType.YANDEX_BY,
                "label": "Яндекс.Беларусь (yandex.by)",
            },
            {
                "value": SearchEngineType.YANDEX_KZ,
                "label": "Яндекс.Казахстан (yandex.kz)",
            },
            {"value": SearchEngineType.YANDEX_TR, "label": "Яндекс.Турция (yandex.tr)"},
            {
                "value": SearchEngineType.YANDEX_UA,
                "label": "Яндекс.Украина (yandex.ua)",
            },
            {"value": SearchEngineType.MAIL_RU, "label": "Mail.ru Search (mail.ru)"},
            {"value": SearchEngineType.DZEN_RU, "label": "Дзен (dzen.ru)"},
            {"value": SearchEngineType.YA_RU, "label": "Яндекс (ya.ru)"},
        ]

        return {
            "search_engines": engines,
            "yandex_only": [
                e for e in engines if "yandex" in e["value"] or "ya.ru" in e["value"]
            ],
        }
    except ImportError as e:
        # Возвращаем базовый список если импорт не удался
        engines = [
            {"value": "yandex.ru", "label": "Яндекс.Россия (yandex.ru)"},
            {"value": "yandex.by", "label": "Яндекс.Беларусь (yandex.by)"},
            {"value": "yandex.kz", "label": "Яндекс.Казахстан (yandex.kz)"},
            {"value": "yandex.tr", "label": "Яндекс.Турция (yandex.tr)"},
            {"value": "yandex.ua", "label": "Яндекс.Украина (yandex.ua)"},
            {"value": "mail.ru", "label": "Mail.ru Search (mail.ru)"},
            {"value": "dzen.ru", "label": "Дзен (dzen.ru)"},
            {"value": "ya.ru", "label": "Яндекс (ya.ru)"},
        ]

        return {
            "search_engines": engines,
            "yandex_only": [
                e for e in engines if "yandex" in e["value"] or "ya.ru" in e["value"]
            ],
        }


# Остальные endpoints с аналогичной обработкой ошибок
@router.post("/project-strategies")
async def assign_strategies_to_project(
    assignment_data: ProjectStrategyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Назначение стратегий для проекта/домена"""
    if StrategyService is None:
        return {"success": False, "message": "Strategy service is not available"}

    try:
        strategy_service = StrategyService(session)
        assignment = await strategy_service.assign_strategies_to_project(
            str(current_user.id), assignment_data
        )

        return {
            "success": True,
            "assignment_id": assignment["id"],
            "message": "Стратегии успешно назначены",
        }
    except Exception as e:
        print(f"Error in assign_strategies_to_project: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}


@router.get("/project-strategies")
async def get_project_strategies(
    domain_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение назначенных стратегий для проектов"""
    if StrategyService is None:
        return []

    try:
        strategy_service = StrategyService(session)
        assignments = await strategy_service.get_project_strategies(
            str(current_user.id), domain_id
        )
        return assignments
    except Exception as e:
        print(f"Error in get_project_strategies: {e}")
        traceback.print_exc()
        return []


@router.post("/validate-config", response_model=StrategyValidationResponse)
async def validate_strategy_config(
    request: StrategyValidationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Валидация конфигурации стратегии"""
    try:
        strategy_type = request.strategy_type
        config = request.config

        errors = []
        warnings = []
        normalized_config = None

        # Валидация в зависимости от типа стратегии
        if strategy_type == "warmup":
            try:
                normalized_config = validate_warmup_config(config)
            except ValueError as e:
                errors.append(str(e))

        elif strategy_type == "position_check":
            try:
                normalized_config = validate_position_check_config(config)
            except ValueError as e:
                errors.append(str(e))

        elif strategy_type == "profile_nurture":
            try:
                normalized_config = validate_profile_nurture_config(config)
            except ValueError as e:
                errors.append(str(e))

        else:
            errors.append(f"Неизвестный тип стратегии: {strategy_type}")

        # Дополнительные проверки для нагула профиля
        if strategy_type == "profile_nurture" and not errors:
            nurture_type = config.get("nurture_type")

            # Проверяем источники данных
            if nurture_type in ["search_based", "mixed_nurture"]:
                queries_source = config.get("queries_source", {})
                if not queries_source.get("data_content") and not queries_source.get(
                    "source_url"
                ):
                    warnings.append("Не указан источник поисковых запросов")

            if nurture_type in ["direct_visits", "mixed_nurture"]:
                direct_sites_source = config.get("direct_sites_source", {})
                if not direct_sites_source.get(
                    "data_content"
                ) and not direct_sites_source.get("source_url"):
                    warnings.append("Не указан источник сайтов для прямых заходов")

        return StrategyValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_config=normalized_config if len(errors) == 0 else None,
        )

    except Exception as e:
        print(f"Error in validate_strategy_config: {e}")
        traceback.print_exc()
        return StrategyValidationResponse(
            is_valid=False,
            errors=[f"Ошибка валидации: {str(e)}"],
            warnings=[],
            normalized_config=None,
        )


@router.post(
    "/profile-nurture/validate-config", response_model=StrategyValidationResponse
)
async def validate_profile_nurture_config_endpoint(
    config: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """Специализированная валидация для стратегий нагула профиля"""
    try:
        errors = []
        warnings = []

        # Базовая валидация
        if not config.get("nurture_type"):
            errors.append("Тип нагула профиля обязателен")

        nurture_type = config.get("nurture_type")

        # Проверка целевых куков
        target_cookies = config.get("target_cookies", {})
        if target_cookies:
            min_cookies = target_cookies.get("min", 0)
            max_cookies = target_cookies.get("max", 0)

            if min_cookies <= 0 or max_cookies <= 0:
                errors.append("Количество куков должно быть положительным")

            if min_cookies > max_cookies:
                errors.append(
                    "Минимальное количество куков не может быть больше максимального"
                )

        # Проверка настроек сессии
        session_config = config.get("session_config", {})
        if session_config:
            timeout_per_site = session_config.get("timeout_per_site", 0)
            min_timeout = session_config.get("min_timeout", 0)
            max_timeout = session_config.get("max_timeout", 0)

            if timeout_per_site <= 0:
                errors.append("Время на сайте должно быть положительным")

            if min_timeout > max_timeout:
                errors.append("Минимальный таймаут не может быть больше максимального")

        # Проверка поисковых систем
        if nurture_type in ["search_based", "mixed_nurture"]:
            search_engines = config.get("search_engines", [])
            if not search_engines:
                errors.append("Поисковые системы обязательны для поискового нагула")

        # Проверка источника запросов
        if nurture_type in ["search_based", "mixed_nurture"]:
            queries_source = config.get("queries_source", {})
            if not queries_source:
                errors.append("Источник запросов обязателен для поискового нагула")
            else:
                source_type = queries_source.get("type")
                if source_type == "manual_input" and not queries_source.get(
                    "data_content"
                ):
                    warnings.append("Не указаны поисковые запросы")
                elif source_type in [
                    "url_endpoint",
                    "google_sheets",
                    "google_docs",
                ] and not queries_source.get("source_url"):
                    warnings.append("Не указан URL источника запросов")

        # Проверка источника сайтов
        if nurture_type in ["direct_visits", "mixed_nurture"]:
            direct_sites_source = config.get("direct_sites_source", {})
            if not direct_sites_source:
                errors.append("Источник сайтов обязателен для прямых заходов")
            else:
                source_type = direct_sites_source.get("type")
                if source_type == "manual_input" and not direct_sites_source.get(
                    "data_content"
                ):
                    warnings.append("Не указаны сайты для прямых заходов")
                elif source_type in [
                    "url_endpoint",
                    "google_sheets",
                    "google_docs",
                ] and not direct_sites_source.get("source_url"):
                    warnings.append("Не указан URL источника сайтов")

        # Проверка пропорций для смешанного типа
        if nurture_type == "mixed_nurture":
            proportions = config.get("proportions", {})
            if not proportions:
                errors.append("Пропорции обязательны для смешанного нагула")
            else:
                search_visits = proportions.get("search_visits", 0)
                direct_visits = proportions.get("direct_visits", 0)

                if search_visits + direct_visits != 100:
                    errors.append("Сумма пропорций должна равняться 100%")

        # Нормализация конфигурации
        normalized_config = None
        if len(errors) == 0:
            try:
                normalized_config = validate_profile_nurture_config(config)
            except ValueError as e:
                errors.append(str(e))

        return StrategyValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_config=normalized_config,
        )

    except Exception as e:
        print(f"Error in validate_profile_nurture_config: {e}")
        traceback.print_exc()
        return StrategyValidationResponse(
            is_valid=False,
            errors=[f"Ошибка валидации: {str(e)}"],
            warnings=[],
            normalized_config=None,
        )


@router.post("/test-data-source")
async def test_data_source(
    source_data: DataSourceCreate,
    session: AsyncSession = Depends(get_session),
):
    """Тестирование источника данных"""
    try:
        source_type = source_data.source_type
        source_url = source_data.source_url
        data_content = source_data.data_content

        items = []

        if source_type == "manual_input":
            if data_content:
                items = [
                    line.strip() for line in data_content.split("\n") if line.strip()
                ]

        elif source_type == "url_endpoint":
            if source_url:
                # Здесь можно добавить HTTP запрос для получения данных по URL
                # Пока возвращаем mock данные
                items = [f"test_item_{i}" for i in range(1, 6)]

        elif source_type == "google_sheets":
            if source_url:
                # Здесь можно добавить интеграцию с Google Sheets API
                # Пока возвращаем mock данные
                items = [f"google_sheet_item_{i}" for i in range(1, 4)]

        elif source_type == "google_docs":
            if source_url:
                # Здесь можно добавить интеграцию с Google Docs API
                # Пока возвращаем mock данные
                items = [f"google_doc_item_{i}" for i in range(1, 3)]

        return {
            "success": True,
            "message": f"Источник данных работает корректно",
            "items_count": len(items),
            "sample_items": items[:5],  # Первые 5 элементов для предпросмотра
            "source_type": source_type,
        }

    except Exception as e:
        print(f"Error in test_data_source: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Ошибка тестирования источника данных: {str(e)}",
            "items_count": 0,
            "sample_items": [],
            "source_type": source_type,
        }


@router.get("/profile-nurture/search-engines")
async def get_available_search_engines():
    """Получение списка доступных поисковых систем"""
    return {
        "search_engines": [
            {"value": "yandex.ru", "label": "Яндекс (yandex.ru)"},
            {"value": "yandex.by", "label": "Яндекс Беларусь (yandex.by)"},
            {"value": "yandex.kz", "label": "Яндекс Казахстан (yandex.kz)"},
            {"value": "yandex.tr", "label": "Яндекс Турция (yandex.tr)"},
            {"value": "mail.ru", "label": "Mail.ru Поиск"},
            {"value": "dzen.ru", "label": "Дзен Поиск"},
        ]
    }


@router.put("/{strategy_id}", response_model=UserStrategyResponse)
async def update_user_strategy(
    strategy_id: str,
    strategy_data: UserStrategyUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновление пользовательской стратегии"""
    if StrategyService is None:
        raise HTTPException(status_code=503, detail="Strategy service is not available")

    try:
        strategy_service = StrategyService(session)

        update_dict = strategy_data.model_dump(exclude_none=True)

        # strategy = await strategy_service.update_user_strategy(
        #     strategy_id, str(current_user.id), strategy_data
        # )
        strategy = await strategy_service.update_user_strategy(
            strategy_id,
            str(current_user.id),
            update_dict,  # ← Передаем словарь, а не объект
        )

        return strategy
    except Exception as e:
        print(f"Error in update_user_strategy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/profile-nurture/{strategy_id}/status")
async def get_profile_nurture_status(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить статус стратегии нагула профилей"""

    # Проверяем, что стратегия принадлежит пользователю
    query = select(UserStrategy).where(
        and_(
            UserStrategy.id == strategy_id,
            UserStrategy.user_id == current_user.id,
            UserStrategy.strategy_type == StrategyType.PROFILE_NURTURE,
        )
    )
    result = await session.execute(query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    limits_service = ProfileNurtureLimitsService(session)
    status = await limits_service.check_strategy_status(strategy_id)

    return {
        "success": True,
        "strategy_id": strategy_id,
        "strategy_name": strategy.name,
        "status": status,
    }


@router.post("/profile-nurture/{strategy_id}/spawn-tasks")
async def spawn_nurture_tasks(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создать задачи нагула для стратегии"""

    # Проверяем, что стратегия принадлежит пользователю
    query = select(UserStrategy).where(
        and_(
            UserStrategy.id == strategy_id,
            UserStrategy.user_id == current_user.id,
            UserStrategy.strategy_type == StrategyTypeEnum.PROFILE_NURTURE,
        )
    )
    result = await session.execute(query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    limits_service = ProfileNurtureLimitsService(session)
    result = await limits_service.spawn_nurture_tasks_if_needed(strategy_id)

    return result


@router.get("/profile-nurture/all-status")
async def get_all_profile_nurture_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить статус всех стратегий нагула пользователя"""

    limits_service = ProfileNurtureLimitsService(session)
    statuses = await limits_service.get_all_strategies_status(str(current_user.id))

    return {"success": True, "strategies": statuses}


@router.post("/profile-nurture/auto-maintain")
async def auto_maintain_strategies(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Автоматически поддерживать все стратегии нагула"""

    limits_service = ProfileNurtureLimitsService(session)
    result = await limits_service.auto_maintain_all_strategies(str(current_user.id))

    return result


@router.get("/profile-nurture/{strategy_id}/tasks")
async def get_strategy_nurture_tasks(
    strategy_id: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Фильтр по статусу задач"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить задачи нагула для конкретной стратегии"""

    # Проверяем, что стратегия принадлежит пользователю
    strategy_query = select(UserStrategy).where(
        and_(
            UserStrategy.id == strategy_id,
            UserStrategy.user_id == current_user.id,
            UserStrategy.strategy_type == StrategyTypeEnum.PROFILE_NURTURE,
        )
    )
    result = await session.execute(strategy_query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    # Получаем задачи
    tasks_query = (
        select(Task)
        .where(
            and_(
                Task.task_type == "profile_nurture",
                Task.parameters.op("->>")("strategy_id") == strategy_id,  # ИСПРАВЛЕНО
            )
        )
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        tasks_query = tasks_query.where(Task.status == status)

    tasks_result = await session.execute(tasks_query)
    tasks = tasks_result.scalars().all()

    # Подсчитываем общее количество
    count_query = select(func.count(Task.id)).where(
        and_(
            Task.task_type == "profile_nurture",
            Task.parameters.op("->>")("strategy_id") == strategy_id,
        )
    )
    if status:
        count_query = count_query.where(Task.status == status)

    count_result = await session.execute(count_query)
    total_count = count_result.scalar() or 0

    # Подсчитываем статистику
    stats_query = (
        select(Task.status, func.count(Task.id))
        .where(
            and_(
                Task.task_type == "profile_nurture",
                Task.parameters.op("->>")("strategy_id") == strategy_id,
            )
        )
        .group_by(Task.status)
    )

    stats_result = await session.execute(stats_query)
    stats = {status: count for status, count in stats_result.fetchall()}

    return {
        "success": True,
        "strategy_id": strategy_id,
        "strategy_name": strategy.name,
        "tasks": [
            {
                "task_id": str(task.id),
                "status": task.status,
                "priority": task.priority,
                "device_type": task.device_type,
                "profile_id": task.profile_id,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                "error_message": task.error_message,
                "worker_id": task.worker_id,
                "result": task.result,
                "parameters": task.parameters,
            }
            for task in tasks
        ],
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(tasks) < total_count,
        },
        "stats": {
            "total": total_count,
            "pending": stats.get("pending", 0),
            "running": stats.get("running", 0),
            "completed": stats.get("completed", 0),
            "failed": stats.get("failed", 0),
        },
    }


@router.delete("/profile-nurture/{strategy_id}/tasks/{task_id}")
async def cancel_nurture_task(
    strategy_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Отменить задачу нагула"""

    # Проверяем права доступа
    strategy_query = select(UserStrategy).where(
        and_(
            UserStrategy.id == strategy_id,
            UserStrategy.user_id == current_user.id,
            UserStrategy.strategy_type == StrategyType.PROFILE_NURTURE,
        )
    )
    result = await session.execute(strategy_query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    # Проверяем задачу
    task_query = select(Task).where(
        and_(
            Task.id == task_id,
            Task.task_type == "profile_nurture",
            Task.parameters["strategy_id"] == strategy_id,  # УБРАЛИ .astext
        )
    )
    task_result = await session.execute(task_query)
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Можно отменить только pending задачи
    if task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя отменить задачу в статусе {task.status}",
        )

    # Обновляем статус задачи
    update_query = (
        update(Task)
        .where(Task.id == task_id)
        .values(
            status="cancelled",
            completed_at=datetime.utcnow(),
            error_message="Отменено пользователем",
        )
    )

    await session.execute(update_query)
    await session.commit()

    return {
        "success": True,
        "message": "Задача отменена",
        "task_id": task_id,
    }


@router.post("/profile-nurture/worker/health")
async def nurture_worker_health():
    """Проверка состояния worker'а нагула"""
    from app.workers.profile_nurture_worker import profile_nurture_worker

    return {
        "success": True,
        "worker_id": profile_nurture_worker.worker_id,
        "is_running": profile_nurture_worker.is_running,
        "status": "healthy" if profile_nurture_worker.is_running else "stopped",
    }


@router.get("/profile-nurture/queue/stats")
async def get_nurture_queue_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить статистику очереди задач нагула"""

    # Общая статистика по задачам пользователя
    user_stats_query = (
        select(Task.status, func.count(Task.id))
        .where(
            and_(
                Task.task_type == "profile_nurture",
                Task.user_id == current_user.id,
            )
        )
        .group_by(Task.status)
    )

    user_stats_result = await session.execute(user_stats_query)
    user_stats = {status: count for status, count in user_stats_result.fetchall()}

    # Глобальная статистика очереди
    global_stats_query = (
        select(Task.status, func.count(Task.id))
        .where(Task.task_type == "profile_nurture")
        .group_by(Task.status)
    )

    global_stats_result = await session.execute(global_stats_query)
    global_stats = {status: count for status, count in global_stats_result.fetchall()}

    # Последние задачи пользователя
    recent_tasks_query = (
        select(Task)
        .where(
            and_(
                Task.task_type == "profile_nurture",
                Task.user_id == current_user.id,
            )
        )
        .order_by(Task.created_at.desc())
        .limit(5)
    )

    recent_tasks_result = await session.execute(recent_tasks_query)
    recent_tasks = recent_tasks_result.scalars().all()

    return {
        "success": True,
        "user_stats": {
            "total": sum(user_stats.values()),
            "pending": user_stats.get("pending", 0),
            "running": user_stats.get("running", 0),
            "completed": user_stats.get("completed", 0),
            "failed": user_stats.get("failed", 0),
        },
        "global_stats": {
            "total": sum(global_stats.values()),
            "pending": global_stats.get("pending", 0),
            "running": global_stats.get("running", 0),
            "completed": global_stats.get("completed", 0),
            "failed": global_stats.get("failed", 0),
        },
        "recent_tasks": [
            {
                "task_id": str(task.id),
                "status": task.status,
                "strategy_id": task.parameters.get("strategy_id"),
                "created_at": task.created_at.isoformat(),
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
            }
            for task in recent_tasks
        ],
    }


@router.delete("/{strategy_id}")
async def delete_user_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаление пользовательской стратегии"""
    if StrategyService is None:
        raise HTTPException(status_code=503, detail="Strategy service is not available")

    try:
        strategy_service = StrategyService(session)
        await strategy_service.delete_user_strategy(strategy_id, str(current_user.id))
        return {"success": True}
    except Exception as e:
        print(f"Error in delete_user_strategy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
