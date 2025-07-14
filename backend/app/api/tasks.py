from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_session
from app.core.task_manager import TaskManager
from app.core.billing_service import BillingService
from app.dependencies import get_current_user, require_api_key
from app.models import User, DeviceType

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/warmup", response_model=dict)
async def create_warmup_task(
    device_type: DeviceType = DeviceType.DESKTOP,
    profile_id: Optional[str] = Query(
        None, description="ID существующего профиля для прогрева"
    ),
    priority: int = Query(2, ge=1, le=20, description="Приоритет задачи"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание задачи на прогрев (нагул) профиля"""

    # Создаем задачу с передачей user_id
    task_manager = TaskManager(session)
    task = await task_manager.create_warmup_task(
        device_type=device_type,
        profile_id=profile_id,
        priority=priority,
        user_id=str(current_user.id),  # ПЕРЕДАЕМ user_id
    )

    return {
        "success": True,
        "task_id": str(task.id),
        "device_type": device_type.value,
        "profile_id": profile_id,
        "priority": priority,
        "message": "Задача на прогрев профиля создана и поставлена в очередь",
    }


# API версия для работы через API ключ
@router.post("/api/warmup", response_model=dict)
async def api_create_warmup_task(
    device_type: DeviceType = DeviceType.DESKTOP,
    profile_id: Optional[str] = Query(None, description="ID профиля"),
    priority: int = Query(2, ge=1, le=20),
    api_key: str = Query(..., description="API ключ"),
    session: AsyncSession = Depends(get_session),
):
    """Создание задачи прогрева профиля через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    task_manager = TaskManager(session)
    task = await task_manager.create_warmup_task(
        device_type=device_type, profile_id=profile_id, priority=priority
    )

    return {
        "success": True,
        "task_id": str(task.id),
        "device_type": device_type.value,
        "profile_id": profile_id,
        "message": "Warmup task created and queued",
    }


@router.post("/parse", response_model=dict)
async def create_parse_task(
    keyword: str,
    device_type: DeviceType = DeviceType.DESKTOP,
    pages: int = Query(10, ge=1, le=50),
    region_code: str = Query("213", description="Код региона"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание задачи на парсинг SERP"""

    # Проверяем и резервируем средства
    billing_service = BillingService(session)
    cost = await billing_service.calculate_check_cost(str(current_user.id), 1)

    # Проверяем достаточность средств
    from app.core.user_service import UserService

    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    available_balance = profile["current_balance"] - profile["reserved_balance"]
    if available_balance < float(cost):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно средств на балансе",
        )

    # Резервируем средства
    reserve_result = await billing_service.reserve_balance(str(current_user.id), cost)
    if not reserve_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка резервирования средств",
        )

    # Создаем задачу
    task_manager = TaskManager(session)
    task = await task_manager.create_parse_task(
        keyword=keyword,
        device_type=device_type,
        pages=pages,
        region_code=region_code,
        priority=10,  # Высокий приоритет для платных пользователей
        user_id=str(current_user.id),
        reserved_amount=float(cost),
    )

    return {
        "success": True,
        "task_id": str(task.id),
        "keyword": keyword,
        "device_type": device_type.value,
        "estimated_cost": float(cost),
        "message": "Задача создана и поставлена в очередь",
    }


@router.post("/check-positions", response_model=dict)
async def create_position_check_task(
    keyword_ids: List[str],
    device_type: DeviceType = DeviceType.DESKTOP,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание задачи на проверку позиций"""

    if not keyword_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать хотя бы одно ключевое слово",
        )

    # Проверяем принадлежность ключевых слов пользователю
    from sqlalchemy import select, and_
    from app.models import UserKeyword

    result = await session.execute(
        select(UserKeyword).where(
            and_(
                UserKeyword.id.in_(keyword_ids),
                UserKeyword.user_id == str(current_user.id),
            )
        )
    )

    user_keywords = result.scalars().all()
    if len(user_keywords) != len(keyword_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некоторые ключевые слова не найдены или не принадлежат пользователю",
        )

    # Рассчитываем стоимость
    billing_service = BillingService(session)
    cost = await billing_service.calculate_check_cost(
        str(current_user.id), len(keyword_ids)
    )

    # Проверяем и резервируем средства
    from app.core.user_service import UserService

    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    available_balance = profile["current_balance"] - profile["reserved_balance"]
    if available_balance < float(cost):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Недостаточно средств. Необходимо: {cost}, доступно: {available_balance}",
        )

    reserve_result = await billing_service.reserve_balance(str(current_user.id), cost)
    if not reserve_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка резервирования средств",
        )

    # Создаем задачу
    task_manager = TaskManager(session)
    task = await task_manager.create_position_check_task(
        keyword_ids=keyword_ids,
        device_type=device_type,
        priority=15,  # Высший приоритет для проверки позиций
        user_id=str(current_user.id),
        reserved_amount=float(cost),
    )

    return {
        "success": True,
        "task_id": str(task.id),
        "keywords_count": len(keyword_ids),
        "device_type": device_type.value,
        "total_cost": float(cost),
        "message": "Задача на проверку позиций создана",
    }


@router.get("/status/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение статуса задачи"""

    from sqlalchemy import select
    from app.models import Task

    result = await session.execute(select(Task).where(Task.id == task_id))

    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )

    # Проверяем принадлежность задачи пользователю (если есть параметр user_id)
    if task.parameters and task.parameters.get("user_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к задаче запрещен"
        )

    return {
        "task_id": str(task.id),
        "status": task.status,
        "task_type": task.task_type,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result": task.result,
        "error_message": task.error_message,
    }


@router.get("/my-tasks", response_model=List[dict])
async def get_user_tasks(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получение задач пользователя"""

    from sqlalchemy import select
    from app.models import Task

    # ТЕПЕРЬ ФИЛЬТРУЕМ ПО ПОЛЮ USER_ID
    query = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        query = query.where(Task.status == status)

    result = await session.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "task_id": str(task.id),
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "parameters": task.parameters,
            "result": task.result,
            "error_message": task.error_message,
        }
        for task in tasks
    ]


# API endpoints для работы через API ключ
@router.post("/api/parse", response_model=dict)
async def api_create_parse_task(
    keyword: str,
    device_type: DeviceType = DeviceType.DESKTOP,
    pages: int = Query(10, ge=1, le=50),
    region_code: str = Query("213"),
    api_key: str = Query(..., description="API ключ"),
    session: AsyncSession = Depends(get_session),
):
    """Создание задачи парсинга через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    # Аналогичная логика как в create_parse_task
    billing_service = BillingService(session)
    cost = await billing_service.calculate_check_cost(str(current_user.id), 1)

    from app.core.user_service import UserService

    user_service = UserService(session)
    profile = await user_service.get_user_profile(str(current_user.id))

    available_balance = profile["current_balance"] - profile["reserved_balance"]
    if available_balance < float(cost):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient balance"
        )

    reserve_result = await billing_service.reserve_balance(str(current_user.id), cost)
    if not reserve_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to reserve funds"
        )

    task_manager = TaskManager(session)
    task = await task_manager.create_parse_task(
        keyword=keyword,
        device_type=device_type,
        pages=pages,
        region_code=region_code,
        priority=10,
        user_id=str(current_user.id),
        reserved_amount=float(cost),
    )

    return {"success": True, "task_id": str(task.id), "estimated_cost": float(cost)}


@router.get("/api/status/{task_id}", response_model=dict)
async def api_get_task_status(
    task_id: str,
    api_key: str = Query(..., description="API ключ"),
    session: AsyncSession = Depends(get_session),
):
    """Получение статуса задачи через API"""
    current_user = await require_api_key(api_key=api_key, session=session)

    from sqlalchemy import select
    from app.models import Task

    result = await session.execute(select(Task).where(Task.id == task_id))

    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.parameters and task.parameters.get("user_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return {
        "task_id": str(task.id),
        "status": task.status,
        "task_type": task.task_type,
        "created_at": task.created_at.isoformat(),
        "result": task.result,
        "error_message": task.error_message,
    }
