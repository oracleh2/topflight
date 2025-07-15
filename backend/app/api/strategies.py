# backend/app/api/strategies.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import csv
import io
import traceback

from app.database import get_session
from app.dependencies import get_current_user
from app.models import User

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
    )
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
        name: str
        strategy_type: str
        config: Dict[str, Any]
        created_at: datetime
        updated_at: datetime
        is_active: bool

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


router = APIRouter(prefix="/strategies", tags=["Strategies"])


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
            str(current_user.id), strategy_type
        )
        return strategies
    except Exception as e:
        print(f"Error in get_user_strategies: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
        strategy = await strategy_service.update_user_strategy(
            strategy_id, str(current_user.id), strategy_data
        )
        return strategy
    except Exception as e:
        print(f"Error in update_user_strategy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
