# backend/app/api/strategies.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import csv
import io

from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.core.strategy_service import StrategyService
from app.schemas.strategies import (
    StrategyTemplateResponse,
    UserStrategyCreate,
    UserStrategyUpdate,
    UserStrategyResponse,
    DataSourceCreate,
    ProjectStrategyCreate,
)

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.get("/templates", response_model=List[StrategyTemplateResponse])
async def get_strategy_templates(
    strategy_type: Optional[str] = None, session: AsyncSession = Depends(get_session)
):
    """Получение шаблонов стратегий"""
    strategy_service = StrategyService(session)
    templates = await strategy_service.get_strategy_templates(strategy_type)
    return templates


@router.get("/", response_model=List[UserStrategyResponse])
async def get_user_strategies(
    strategy_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение пользовательских стратегий"""
    strategy_service = StrategyService(session)
    strategies = await strategy_service.get_user_strategies(
        str(current_user.id), strategy_type
    )
    return strategies


@router.post("/", response_model=UserStrategyResponse)
async def create_user_strategy(
    strategy_data: UserStrategyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание пользовательской стратегии"""
    strategy_service = StrategyService(session)
    strategy = await strategy_service.create_user_strategy(
        str(current_user.id), strategy_data
    )
    return strategy


@router.put("/{strategy_id}", response_model=UserStrategyResponse)
async def update_user_strategy(
    strategy_id: str,
    strategy_data: UserStrategyUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновление пользовательской стратегии"""
    strategy_service = StrategyService(session)
    strategy = await strategy_service.update_user_strategy(
        strategy_id, str(current_user.id), strategy_data
    )
    return strategy


@router.delete("/{strategy_id}")
async def delete_user_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаление пользовательской стратегии"""
    strategy_service = StrategyService(session)
    await strategy_service.delete_user_strategy(strategy_id, str(current_user.id))
    return {"success": True}


@router.post("/{strategy_id}/data-sources")
async def add_data_source(
    strategy_id: str,
    source_data: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Добавление источника данных к стратегии"""
    strategy_service = StrategyService(session)

    # Проверяем права доступа к стратегии
    strategy = await strategy_service.get_user_strategy_by_id(
        strategy_id, str(current_user.id)
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    data_source = await strategy_service.add_data_source(strategy_id, source_data)
    return data_source


@router.post("/{strategy_id}/data-sources/upload-file")
async def upload_data_file(
    strategy_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Загрузка файла с данными для стратегии"""
    strategy_service = StrategyService(session)

    # Проверяем права доступа к стратегии
    strategy = await strategy_service.get_user_strategy_by_id(
        strategy_id, str(current_user.id)
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    # Проверяем тип файла
    if not file.filename.endswith((".txt", ".csv")):
        raise HTTPException(
            status_code=400, detail="Поддерживаются только файлы .txt и .csv"
        )

    # Читаем содержимое файла
    content = await file.read()
    text_content = content.decode("utf-8")

    # Парсим содержимое в зависимости от типа файла
    data_items = []
    if file.filename.endswith(".csv"):
        csv_reader = csv.reader(io.StringIO(text_content))
        for row in csv_reader:
            if row:  # пропускаем пустые строки
                data_items.extend(row)
    else:  # .txt
        data_items = [line.strip() for line in text_content.split("\n") if line.strip()]

    # Сохраняем данные
    file_path = await strategy_service.save_uploaded_file(
        str(current_user.id), strategy_id, file.filename, content
    )

    source_data = DataSourceCreate(
        source_type="file_upload",
        file_path=file_path,
        data_content="\n".join(data_items),
    )

    data_source = await strategy_service.add_data_source(strategy_id, source_data)

    return {
        "success": True,
        "data_source_id": data_source["id"],
        "items_count": len(data_items),
        "message": f"Загружено {len(data_items)} элементов",
    }


@router.post("/project-strategies")
async def assign_strategies_to_project(
    assignment_data: ProjectStrategyCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Назначение стратегий для проекта/домена"""
    strategy_service = StrategyService(session)

    assignment = await strategy_service.assign_strategies_to_project(
        str(current_user.id), assignment_data
    )

    return {
        "success": True,
        "assignment_id": assignment["id"],
        "message": "Стратегии успешно назначены",
    }


@router.get("/project-strategies")
async def get_project_strategies(
    domain_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение назначенных стратегий для проектов"""
    strategy_service = StrategyService(session)

    assignments = await strategy_service.get_project_strategies(
        str(current_user.id), domain_id
    )

    return assignments


@router.post("/{strategy_id}/execute")
async def execute_strategy(
    strategy_id: str,
    execution_params: dict = {},
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Запуск выполнения стратегии"""
    strategy_service = StrategyService(session)

    # Проверяем права доступа
    strategy = await strategy_service.get_user_strategy_by_id(
        strategy_id, str(current_user.id)
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")

    # Создаем задачу выполнения стратегии
    task = await strategy_service.execute_strategy(
        strategy_id, str(current_user.id), execution_params
    )

    return {
        "success": True,
        "task_id": task["id"],
        "message": "Стратегия поставлена в очередь выполнения",
    }
