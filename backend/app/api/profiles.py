# backend/app/api/profiles.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.models.profile import Profile, ProfileFingerprint, ProfileLifecycle, DeviceType
from app.models.proxy import ProfileProxyAssignment

from pydantic import BaseModel

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileResponse(BaseModel):
    id: str
    name: str
    device_type: str
    created_at: datetime
    cookies_count: int
    visited_sites_count: int
    nurture_strategy: str
    status: str
    is_warmed_up: bool
    last_used: Optional[datetime]
    user_agent: str
    proxy_assigned: bool
    corruption_reason: Optional[str]

    class Config:
        from_attributes = True


class ProfileDetailResponse(BaseModel):
    id: str
    name: str
    device_type: str
    created_at: datetime
    updated_at: datetime

    # Основная информация
    user_agent: str
    browser_settings: dict
    cookies_count: int
    visited_sites_count: int
    is_warmed_up: bool
    status: str
    last_used: Optional[datetime]

    # Fingerprint данные
    fingerprint: Optional[dict]

    # Lifecycle информация
    lifecycle: Optional[dict]

    # Прокси информация
    proxy_info: Optional[dict]

    class Config:
        from_attributes = True


class ProfilesListResponse(BaseModel):
    profiles: List[ProfileResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/", response_model=ProfilesListResponse)
async def get_profiles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_warmed_up: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение списка профилей с фильтрацией, поиском и сортировкой"""

    # Базовый запрос
    query = select(Profile).options(
        selectinload(Profile.fingerprint_data),
        selectinload(Profile.lifecycle),
        selectinload(Profile.assigned_warmup_proxy),
    )

    # Условия фильтрации
    conditions = []

    # Поиск
    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(
            or_(
                func.lower(Profile.name).like(search_term),
                func.lower(Profile.user_agent).like(search_term),
                func.lower(Profile.device_type).like(search_term),
            )
        )

    # Фильтр по типу устройства
    if device_type:
        conditions.append(Profile.device_type == device_type)

    # Фильтр по статусу
    if status:
        conditions.append(Profile.status == status)

    # Фильтр по прогреву
    if is_warmed_up is not None:
        conditions.append(Profile.is_warmed_up == is_warmed_up)

    # Применяем условия
    if conditions:
        query = query.where(and_(*conditions))

    # Сортировка
    sort_column = getattr(Profile, sort_by, Profile.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Подсчет общего количества
    count_query = select(func.count(Profile.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Пагинация
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Выполнение запроса
    result = await session.execute(query)
    profiles = result.scalars().all() or []

    # Формирование ответа
    profile_responses = []
    for profile in profiles:
        # Подсчет кук
        cookies_count = len(profile.cookies) if profile.cookies else 0

        # Определение стратегии нагула
        nurture_strategy = "Не задана"
        if profile.lifecycle:
            stage = profile.lifecycle.cascade_stage
            if stage == 0:
                nurture_strategy = "Свежий профиль"
            elif stage == 1:
                nurture_strategy = "Использованный"
            elif stage == 2:
                nurture_strategy = "Догуливание"
            elif stage == 3:
                nurture_strategy = "Готов повторно"

        # Информация о прокси
        proxy_assigned = profile.assigned_warmup_proxy_id is not None

        profile_responses.append(
            ProfileResponse(
                id=str(profile.id),
                name=profile.name,
                device_type=profile.device_type,
                created_at=profile.created_at,
                cookies_count=cookies_count,
                visited_sites_count=profile.warmup_sites_visited or 0,
                nurture_strategy=nurture_strategy,
                status=profile.status,
                is_warmed_up=profile.is_warmed_up,
                last_used=profile.last_used,
                user_agent=profile.user_agent,
                proxy_assigned=proxy_assigned,
                corruption_reason=(
                    profile.lifecycle.corruption_reason if profile.lifecycle else None
                ),
            )
        )

    total_pages = (total + per_page - 1) // per_page

    return ProfilesListResponse(
        profiles=profile_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{profile_id}", response_model=ProfileDetailResponse)
async def get_profile_details(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение подробной информации о профиле"""

    # Получаем профиль с загруженными связями
    query = (
        select(Profile)
        .options(
            selectinload(Profile.fingerprint_data),
            selectinload(Profile.lifecycle),
            selectinload(Profile.assigned_warmup_proxy),
        )
        .where(Profile.id == profile_id)
    )

    result = await session.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    # Подсчет кук
    cookies_count = len(profile.cookies) if profile.cookies else 0

    # Формирование данных fingerprint
    fingerprint_data = None
    if profile.fingerprint_data:
        fingerprint_data = {
            "user_agent": profile.fingerprint_data.user_agent,
            "screen_resolution": profile.fingerprint_data.screen_resolution,
            "viewport_size": profile.fingerprint_data.viewport_size,
            "timezone": profile.fingerprint_data.timezone,
            "language": profile.fingerprint_data.language,
            "platform": profile.fingerprint_data.platform,
            "cpu_cores": profile.fingerprint_data.cpu_cores,
            "memory_size": profile.fingerprint_data.memory_size,
            "color_depth": profile.fingerprint_data.color_depth,
            "pixel_ratio": profile.fingerprint_data.pixel_ratio,
            "webdriver_present": profile.fingerprint_data.webdriver_present,
            "automation_detected": profile.fingerprint_data.automation_detected,
            "connection_type": profile.fingerprint_data.connection_type,
        }

    # Формирование данных lifecycle
    lifecycle_data = None
    if profile.lifecycle:
        lifecycle_data = {
            "current_usage_count": profile.lifecycle.current_usage_count,
            "cascade_stage": profile.lifecycle.cascade_stage,
            "is_corrupted": profile.lifecycle.is_corrupted,
            "corruption_reason": profile.lifecycle.corruption_reason,
            "last_health_check": profile.lifecycle.last_health_check,
            "next_health_check": profile.lifecycle.next_health_check,
        }

    # Формирование данных прокси
    proxy_info = None
    if profile.assigned_warmup_proxy:
        proxy_info = {
            "host": profile.assigned_warmup_proxy.host,
            "port": profile.assigned_warmup_proxy.port,
            "proxy_type": profile.assigned_warmup_proxy.proxy_type,
            "is_active": profile.assigned_warmup_proxy.is_active,
        }

    return ProfileDetailResponse(
        id=str(profile.id),
        name=profile.name,
        device_type=profile.device_type,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        user_agent=profile.user_agent,
        browser_settings=profile.browser_settings or {},
        cookies_count=cookies_count,
        visited_sites_count=profile.warmup_sites_visited or 0,
        is_warmed_up=profile.is_warmed_up,
        status=profile.status,
        last_used=profile.last_used,
        fingerprint=fingerprint_data,
        lifecycle=lifecycle_data,
        proxy_info=proxy_info,
    )


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаление профиля"""

    # Проверяем существование профиля
    query = select(Profile).where(Profile.id == profile_id)
    result = await session.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    # Удаляем профиль (связанные записи удалятся каскадно)
    await session.delete(profile)
    await session.commit()

    return {"success": True, "message": "Профиль успешно удален"}


@router.post("/bulk-delete")
async def bulk_delete_profiles(
    profile_ids: List[str],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Массовое удаление профилей"""

    if not profile_ids:
        raise HTTPException(
            status_code=400, detail="Список профилей не может быть пустым"
        )

    # Получаем профили для удаления
    query = select(Profile).where(Profile.id.in_(profile_ids))
    result = await session.execute(query)
    profiles = result.scalars().all()

    if len(profiles) != len(profile_ids):
        raise HTTPException(status_code=404, detail="Некоторые профили не найдены")

    # Удаляем профили
    for profile in profiles:
        await session.delete(profile)

    await session.commit()

    return {
        "success": True,
        "message": f"Успешно удалено {len(profiles)} профилей",
        "deleted_count": len(profiles),
    }


@router.get("/stats/summary")
async def get_profiles_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение статистики профилей"""

    # Общее количество профилей
    total_query = select(func.count(Profile.id))
    total_result = await session.execute(total_query)
    total = total_result.scalar() or 0

    # Количество прогретых профилей
    warmed_query = select(func.count(Profile.id)).where(Profile.is_warmed_up == True)
    warmed_result = await session.execute(warmed_query)
    warmed = warmed_result.scalar() or 0

    # Количество по типам устройств
    desktop_query = select(func.count(Profile.id)).where(
        Profile.device_type == DeviceType.DESKTOP
    )
    desktop_result = await session.execute(desktop_query)
    desktop = desktop_result.scalar() or 0

    mobile_query = select(func.count(Profile.id)).where(
        Profile.device_type == DeviceType.MOBILE
    )
    mobile_result = await session.execute(mobile_query)
    mobile = mobile_result.scalar() or 0

    # Количество испорченных профилей
    corrupted_query = select(func.count(ProfileLifecycle.id)).where(
        ProfileLifecycle.is_corrupted == True
    )
    corrupted_result = await session.execute(corrupted_query)
    corrupted = corrupted_result.scalar() or 0

    return {
        "total": total,
        "warmed_up": warmed,
        "desktop": desktop,
        "mobile": mobile,
        "corrupted": corrupted,
        "ready_to_use": warmed - corrupted,
    }
