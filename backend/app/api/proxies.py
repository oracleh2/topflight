# backend/app/api/proxies.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.proxy_service import ProxyService
from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.models.proxy import ProxyType

router = APIRouter(prefix="/proxies", tags=["Proxies"])


class ProxyImportRequest(BaseModel):
    domain_id: str
    proxy_type: str  # "warmup" или "parsing"
    proxy_text: str


class ProxyUrlImportRequest(BaseModel):
    domain_id: str
    proxy_type: str
    url: HttpUrl


class ProxyResponse(BaseModel):
    success: bool
    total: Optional[int] = None
    successful: Optional[int] = None
    failed: Optional[int] = None
    errors: Optional[List[str]] = None
    error: Optional[str] = None


@router.get("/domain/{domain_id}")
async def get_domain_proxies(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить все прокси домена"""
    proxy_service = ProxyService(session)

    proxies = await proxy_service.get_domain_proxies(
        user_id=str(current_user.id), domain_id=domain_id
    )

    return {"success": True, "data": proxies}


@router.post("/import/manual", response_model=ProxyResponse)
async def import_proxies_manual(
    request: ProxyImportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси из текста"""

    # Валидация типа прокси
    try:
        proxy_type = ProxyType(request.proxy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип прокси. Допустимые значения: warmup, parsing",
        )

    proxy_service = ProxyService(session)

    result = await proxy_service.import_proxies_manual(
        user_id=str(current_user.id),
        domain_id=request.domain_id,
        proxy_type=proxy_type,
        proxy_text=request.proxy_text,
    )

    return ProxyResponse(**result)


@router.post("/import/url", response_model=ProxyResponse)
async def import_proxies_from_url(
    request: ProxyUrlImportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси по URL"""

    try:
        proxy_type = ProxyType(request.proxy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип прокси. Допустимые значения: warmup, parsing",
        )

    proxy_service = ProxyService(session)

    result = await proxy_service.import_proxies_from_url(
        user_id=str(current_user.id),
        domain_id=request.domain_id,
        proxy_type=proxy_type,
        url=str(request.url),
    )

    return ProxyResponse(**result)


@router.post("/import/file", response_model=ProxyResponse)
async def import_proxies_from_file(
    domain_id: str = Form(...),
    proxy_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси из файла"""

    try:
        proxy_type_enum = ProxyType(proxy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип прокси"
        )

    # Проверяем тип файла
    if not file.filename.endswith((".txt", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только файлы .txt и .csv",
        )

    try:
        # Читаем содержимое файла
        content = await file.read()
        proxy_text = content.decode("utf-8")

        proxy_service = ProxyService(session)

        result = await proxy_service.import_proxies_manual(
            user_id=str(current_user.id),
            domain_id=domain_id,
            proxy_type=proxy_type_enum,
            proxy_text=proxy_text,
        )

        return ProxyResponse(**result)

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


@router.post("/import/google-doc")
async def import_proxies_from_google_doc(
    domain_id: str = Form(...),
    proxy_type: str = Form(...),
    google_doc_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси из Google Документа"""

    try:
        proxy_type_enum = ProxyType(proxy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип прокси"
        )

    # Преобразуем Google Docs URL в формат для экспорта как текст
    if "docs.google.com" in google_doc_url:
        if "/edit" in google_doc_url:
            doc_id = google_doc_url.split("/d/")[1].split("/")[0]
            export_url = (
                f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат ссылки на Google Документ",
            )
    elif (
        "docs.google.com/document/d/" in google_doc_url
        and "/export?format=txt" in google_doc_url
    ):
        export_url = google_doc_url
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка должна быть на Google Документ",
        )

    proxy_service = ProxyService(session)

    result = await proxy_service.import_proxies_from_url(
        user_id=str(current_user.id),
        domain_id=domain_id,
        proxy_type=proxy_type_enum,
        url=export_url,
    )

    return ProxyResponse(**result)


@router.post("/import/google-sheets")
async def import_proxies_from_google_sheets(
    domain_id: str = Form(...),
    proxy_type: str = Form(...),
    google_sheets_url: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Импорт прокси из Google Таблиц"""

    try:
        proxy_type_enum = ProxyType(proxy_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип прокси"
        )

    # Преобразуем Google Sheets URL в формат для экспорта как CSV
    if "docs.google.com/spreadsheets" in google_sheets_url:
        if "/edit" in google_sheets_url:
            sheet_id = google_sheets_url.split("/d/")[1].split("/")[0]
            export_url = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            )

            # Если указан лист, добавляем его
            if sheet_name:
                export_url += f"&gid={sheet_name}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат ссылки на Google Таблицу",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка должна быть на Google Таблицу",
        )

    proxy_service = ProxyService(session)

    result = await proxy_service.import_proxies_from_url(
        user_id=str(current_user.id),
        domain_id=domain_id,
        proxy_type=proxy_type_enum,
        url=export_url,
    )

    return ProxyResponse(**result)


@router.delete("/{proxy_id}")
async def delete_proxy(
    proxy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удалить прокси"""

    proxy_service = ProxyService(session)

    success = await proxy_service.delete_proxy(
        user_id=str(current_user.id), proxy_id=proxy_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Прокси не найдена"
        )

    return {"success": True, "message": "Прокси удалена"}


@router.get("/test/{proxy_id}")
async def test_proxy(
    proxy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Тестировать прокси"""

    proxy_service = ProxyService(session)

    # Здесь можно добавить логику тестирования прокси
    # Например, попытка подключения к test-сайту через прокси

    return {
        "success": True,
        "message": "Функция тестирования будет реализована",
        "proxy_id": proxy_id,
    }


@router.get("/formats/help")
async def get_proxy_formats_help():
    """Получить справку по поддерживаемым форматам прокси"""

    formats = [
        {
            "format": "http://user:password@host:port",
            "example": "http://john:secret123@192.168.1.100:8080",
            "description": "HTTP/HTTPS прокси с авторизацией",
        },
        {
            "format": "host:port:user:password",
            "example": "192.168.1.100:8080:john:secret123",
            "description": "Популярный формат с двоеточиями",
        },
        {
            "format": "user:password@host:port",
            "example": "john:secret123@192.168.1.100:8080",
            "description": "Формат с @ разделителем",
        },
        {
            "format": "host:port@user:password",
            "example": "192.168.1.100:8080@john:secret123",
            "description": "Альтернативный формат с @",
        },
        {
            "format": "host:port",
            "example": "192.168.1.100:8080",
            "description": "Прокси без авторизации",
        },
        {
            "format": "socks5://user:password@host:port",
            "example": "socks5://john:secret123@192.168.1.100:1080",
            "description": "SOCKS5 прокси с авторизацией",
        },
        {
            "format": "socks5://host:port",
            "example": "socks5://192.168.1.100:1080",
            "description": "SOCKS5 прокси без авторизации",
        },
    ]

    return {
        "success": True,
        "supported_formats": formats,
        "notes": [
            "Каждая прокси должна быть на отдельной строке",
            "Строки начинающиеся с # игнорируются (комментарии)",
            "Пустые строки игнорируются",
            "Поддерживаются протоколы: HTTP, HTTPS, SOCKS4, SOCKS5",
        ],
    }
