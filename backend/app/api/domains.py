from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_session
from app.core.user_service import UserService
from app.dependencies import get_current_user, require_api_key
from app.schemas.domain import (
    DomainAdd, DomainResponse, KeywordAdd, KeywordResponse, RegionResponse
)
from app.models import User, Region

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.get("/regions", response_model=List[RegionResponse])
async def get_regions(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    """Получение списка доступных регионов"""
    result = await session.execute(
        select(Region).order_by(Region.region_name)
    )
    regions = result.scalars().all()

    return [
        RegionResponse(
            id=str(region.id),
            code=region.region_code,
            name=region.region_name,
            country_code=region.country_code
        )
        for region in regions
    ]


@router.post("/", response_model=dict)
async def add_domain(
        domain_data: DomainAdd,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Добавление домена"""
    user_service = UserService(session)
    result = await user_service.add_domain(
        user_id=str(current_user.id),
        domain=domain_data.domain
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {
        "success": True,
        "message": "Домен успешно добавлен",
        "domain_id": result["domain_id"],
        "domain": result["domain"]
    }


@router.get("/", response_model=List[DomainResponse])
async def get_user_domains(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Получение доменов пользователя"""
    user_service = UserService(session)
    domains = await user_service.get_user_domains(str(current_user.id))

    return [DomainResponse(**domain) for domain in domains]


@router.delete("/{domain_id}", response_model=dict)
async def delete_domain(
        domain_id: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Удаление домена"""
    user_service = UserService(session)
    result = await user_service.delete_domain(
        user_id=str(current_user.id),
        domain_id=domain_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {"success": True, "message": "Домен успешно удален"}


@router.post("/{domain_id}/keywords", response_model=dict)
async def add_keyword(
        domain_id: str,
        keyword_data: KeywordAdd,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Добавление ключевого слова к домену"""
    user_service = UserService(session)
    result = await user_service.add_keyword(
        user_id=str(current_user.id),
        domain_id=domain_id,
        keyword=keyword_data.keyword,
        region_id=keyword_data.region_id,
        device_type=keyword_data.device_type
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {
        "success": True,
        "message": "Ключевое слово успешно добавлено",
        "keyword_id": result["keyword_id"]
    }


@router.get("/{domain_id}/keywords", response_model=List[KeywordResponse])
async def get_domain_keywords(
        domain_id: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Получение ключевых слов домена"""
    user_service = UserService(session)
    keywords = await user_service.get_domain_keywords(
        user_id=str(current_user.id),
        domain_id=domain_id
    )

    return [KeywordResponse(**keyword) for keyword in keywords]


@router.delete("/keywords/{keyword_id}", response_model=dict)
async def delete_keyword(
        keyword_id: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Удаление ключевого слова"""
    user_service = UserService(session)
    result = await user_service.delete_keyword(
        user_id=str(current_user.id),
        keyword_id=keyword_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {"success": True, "message": "Ключевое слово успешно удалено"}


# API endpoints для работы через API ключ
@router.post("/api/add", response_model=dict)
async def api_add_domain(
        domain_data: DomainAdd,
        api_key: str = Query(..., description="API ключ"),
        session: AsyncSession = Depends(get_session)
):
    """Добавление домена через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    user_service = UserService(session)
    result = await user_service.add_domain(
        user_id=str(current_user.id),
        domain=domain_data.domain
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"]
        )

    return {
        "success": True,
        "domain_id": result["domain_id"],
        "domain": result["domain"]
    }


@router.get("/api/list", response_model=List[DomainResponse])
async def api_get_domains(
        api_key: str = Query(..., description="API ключ"),
        session: AsyncSession = Depends(get_session)
):
    """Получение доменов через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    user_service = UserService(session)
    domains = await user_service.get_user_domains(str(current_user.id))

    return [DomainResponse(**domain) for domain in domains]