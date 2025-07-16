# backend/app/api/strategy_proxy.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.strategy_proxy_service import StrategyProxyService
from ..database import get_session
from ..dependencies import get_current_user
from ..models import User
from ..schemas.strategy_proxy import (
    StrategyProxyImportRequest,
    StrategyProxyImportResponse,
    StrategyProxyStatsResponse,
    StrategyProxySourceResponse,
    StrategyProxySettings,
)

router = APIRouter(prefix="/strategies-proxy", tags=["Strategy Proxies"])


@router.post(
    "/{strategy_id}/proxy/import/manual", response_model=StrategyProxyImportResponse
)
async def import_strategy_proxy_manual(
    strategy_id: str,
    request: StrategyProxyImportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси для стратегии из текста"""

    if request.source_type != "manual_list":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот endpoint только для ручного импорта",
        )

    service = StrategyProxyService(session)
    result = await service.import_proxy_for_strategy(
        strategy_id=strategy_id,
        source_type=request.source_type,
        proxy_data=request.proxy_data,
    )

    return result


@router.post(
    "/{strategy_id}/proxy/import/url", response_model=StrategyProxyImportResponse
)
async def import_strategy_proxy_url(
    strategy_id: str,
    request: StrategyProxyImportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси для стратегии по URL"""

    if request.source_type != "url_import":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот endpoint только для импорта по URL",
        )

    service = StrategyProxyService(session)
    result = await service.import_proxy_for_strategy(
        strategy_id=strategy_id,
        source_type=request.source_type,
        source_url=str(request.source_url),
    )

    return result


@router.post(
    "/{strategy_id}/proxy/import/file", response_model=StrategyProxyImportResponse
)
async def import_strategy_proxy_file(
    strategy_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси для стратегии из файла"""

    # Проверяем тип файла
    if not file.filename.endswith((".txt", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только файлы .txt и .csv",
        )

    try:
        # Читаем содержимое файла
        content = await file.read()
        file_content = content.decode("utf-8")

        service = StrategyProxyService(session)
        result = await service.import_proxy_for_strategy(
            strategy_id=strategy_id,
            source_type="file_upload",
            file_content=file_content,
        )

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в кодировке UTF-8",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки файла: {str(e)}",
        )


@router.get("/{strategy_id}/proxy/sources/{source_id}/preview")
async def get_strategy_proxy_source_preview(
    strategy_id: str,
    source_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение превью прокси из динамического источника"""

    service = StrategyProxyService(session)
    preview = await service.get_source_preview(strategy_id, source_id)

    return preview


@router.post(
    "/{strategy_id}/proxy/import/google-doc", response_model=StrategyProxyImportResponse
)
async def import_strategy_proxy_google_doc(
    strategy_id: str,
    google_doc_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси для стратегии из Google Документа"""

    # Проверяем URL
    if "docs.google.com/document" not in google_doc_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка должна быть на Google Документ",
        )

    service = StrategyProxyService(session)
    result = await service.import_proxy_for_strategy(
        strategy_id=strategy_id, source_type="google_docs", source_url=google_doc_url
    )

    return result


@router.post(
    "/{strategy_id}/proxy/import/google-sheets",
    response_model=StrategyProxyImportResponse,
)
async def import_strategy_proxy_google_sheets(
    strategy_id: str,
    google_sheets_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси для стратегии из Google Таблиц"""

    # Проверяем URL
    if "docs.google.com/spreadsheets" not in google_sheets_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка должна быть на Google Таблицы",
        )

    service = StrategyProxyService(session)
    result = await service.import_proxy_for_strategy(
        strategy_id=strategy_id,
        source_type="google_sheets",
        source_url=google_sheets_url,
    )

    return result


@router.get("/{strategy_id}/proxy", response_model=List[dict])
async def get_strategy_proxies(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение прокси для стратегии"""

    service = StrategyProxyService(session)
    proxies = await service.get_strategy_proxies(strategy_id)

    return proxies


@router.get("/{strategy_id}/proxy/stats", response_model=StrategyProxyStatsResponse)
async def get_strategy_proxy_stats(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение статистики прокси стратегии"""

    service = StrategyProxyService(session)
    stats = await service.get_strategy_proxy_stats(strategy_id)

    return stats


@router.post("/{strategy_id}/proxy/rotate")
async def rotate_strategy_proxy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Ротация прокси для стратегии"""

    service = StrategyProxyService(session)
    new_proxy = await service.rotate_proxy_for_strategy(strategy_id)

    if not new_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено активных прокси для ротации",
        )

    return {
        "success": True,
        "new_proxy": new_proxy,
        "message": "Прокси успешно ротирована",
    }


@router.post("/{strategy_id}/proxy/assign/{profile_id}")
async def assign_proxy_to_profile(
    strategy_id: str,
    profile_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Назначение прокси профилю для стратегии"""

    service = StrategyProxyService(session)
    assigned_proxy = await service.assign_proxy_to_profile(profile_id, strategy_id)

    if not assigned_proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено активных прокси для назначения",
        )

    return {
        "success": True,
        "assigned_proxy": assigned_proxy,
        "message": "Прокси успешно назначена профилю",
    }


@router.get(
    "/{strategy_id}/proxy/sources", response_model=List[StrategyProxySourceResponse]
)
async def get_strategy_proxy_sources(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение источников прокси для стратегии"""

    from sqlalchemy import select
    from ..models.strategy_proxy import StrategyProxySource

    # Получаем источники прокси
    sources_result = await session.execute(
        select(StrategyProxySource).where(
            StrategyProxySource.strategy_id == strategy_id
        )
    )
    sources = sources_result.scalars().all()

    return [
        StrategyProxySourceResponse(
            id=str(source.id),
            strategy_id=str(source.strategy_id),
            source_type=source.source_type,
            source_url=source.source_url,
            file_path=source.file_path,
            proxy_count=0,  # Можно добавить подсчет
            is_active=source.is_active,
            created_at=source.created_at,
        )
        for source in sources
    ]


@router.delete("/{strategy_id}/proxy/sources/{source_id}")
async def delete_strategy_proxy_source(
    strategy_id: str,
    source_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаление источника прокси для стратегии"""

    from sqlalchemy import select, delete
    from ..models.strategy_proxy import StrategyProxySource

    # Проверяем существование источника
    source_result = await session.execute(
        select(StrategyProxySource).where(
            StrategyProxySource.id == source_id,
            StrategyProxySource.strategy_id == strategy_id,
        )
    )
    source = source_result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Источник прокси не найден"
        )

    # Удаляем источник
    await session.execute(
        delete(StrategyProxySource).where(StrategyProxySource.id == source_id)
    )
    await session.commit()

    return {"success": True, "message": "Источник прокси удален"}
