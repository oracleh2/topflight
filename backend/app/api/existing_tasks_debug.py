# backend/app/api/existing_tasks_debug.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.database import async_session_maker
from app.models import Task, DeviceType
from app.core.task_manager import TaskManager
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks-debug"])


async def get_db_session():
    """Dependency для получения сессии БД"""
    async with async_session_maker() as session:
        yield session


@router.get("/list")
async def list_tasks(
    status: Optional[str] = Query(
        None, description="Фильтр по статусу: pending, running, failed, completed"
    ),
    task_type: Optional[str] = Query(None, description="Фильтр по типу задачи"),
    limit: int = Query(20, description="Количество задач", ge=1, le=100),
    offset: int = Query(0, description="Смещение", ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Получить список существующих задач для дебага"""
    try:
        query = select(Task).order_by(Task.created_at.desc())

        # Применяем фильтры
        if status:
            query = query.where(Task.status == status)
        if task_type:
            query = query.where(Task.task_type == task_type)

        # Пагинация
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # Формируем ответ
        tasks_data = []
        for task in tasks:
            task_data = {
                "id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "device_type": task.device_type,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                "debug_enabled": task.debug_enabled,
                "can_be_debugged": task.can_be_debugged(),
                "parameters": task.parameters,
                "profile_id": str(task.profile_id) if task.profile_id else None,
                "worker_id": task.worker_id,
                "error_message": task.error_message,
            }

            # Добавляем debug информацию если есть
            if task.debug_enabled:
                task_data["debug_info"] = task.debug_info

            tasks_data.append(task_data)

        # Получаем общее количество
        count_query = select(Task)
        if status:
            count_query = count_query.where(Task.status == status)
        if task_type:
            count_query = count_query.where(Task.task_type == task_type)

        total_result = await db.execute(count_query)
        total_count = len(total_result.scalars().all())

        return {
            "success": True,
            "tasks": tasks_data,
            "total_count": total_count,
            "page_info": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
            },
        }

    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.post("/{task_id}/enable-debug")
async def enable_task_debug(
    task_id: str,
    device_type: str = "desktop",
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Включить debug режим для существующей задачи"""
    try:
        # Преобразуем device_type
        try:
            device_type_enum = DeviceType(device_type.lower())
        except ValueError:
            device_type_enum = DeviceType.DESKTOP

        # Получаем задачу
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        if not task.can_be_debugged():
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} cannot be debugged. Status: {task.status}",
            )

        # Включаем debug режим через TaskManager
        task_manager = TaskManager(db)
        success = await task_manager.enable_task_debug(
            task_id=task_id, device_type=device_type_enum
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to enable debug mode")

        # Перезагружаем задачу
        await db.refresh(task)

        logger.info(
            "Debug mode enabled for existing task",
            task_id=task_id,
            task_type=task.task_type,
            device_type=device_type_enum.value,
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": "Debug mode enabled successfully",
            "task_info": {
                "id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "device_type": task.device_type,
                "debug_enabled": task.debug_enabled,
                "debug_device_type": device_type_enum.value,
            },
            "instructions": [
                "1. Task is now marked for debug mode",
                "2. Worker will pick it up within 5 seconds",
                "3. VNC session will be created automatically",
                "4. Check logs or /tasks/{task_id}/debug-info for VNC details",
                "5. Connect with 'vncviewer localhost:PORT'",
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to enable debug for task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to enable debug: {str(e)}")


@router.delete("/{task_id}/disable-debug")
async def disable_task_debug(
    task_id: str, db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Отключить debug режим для задачи"""
    try:
        # Получаем задачу
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Отключаем debug режим
        task_manager = TaskManager(db)
        success = await task_manager.disable_task_debug(task_id=task_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to disable debug mode")

        # Останавливаем VNC сессию если есть
        try:
            from app.core.enhanced_vnc_manager import enhanced_vnc_manager

            await enhanced_vnc_manager.stop_debug_session(task_id)
        except Exception as e:
            logger.warning("Failed to stop VNC session", task_id=task_id, error=str(e))

        return {
            "success": True,
            "task_id": task_id,
            "message": "Debug mode disabled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to disable debug for task", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to disable debug: {str(e)}"
        )


@router.get("/{task_id}/debug-info")
async def get_task_debug_info(
    task_id: str, db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Получить информацию о debug сессии задачи"""
    try:
        # Получаем задачу
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Базовая информация о задаче
        task_info = {
            "task_id": task_id,
            "task_type": task.task_type,
            "status": task.status,
            "device_type": task.device_type,
            "debug_enabled": task.debug_enabled,
            "debug_info": task.debug_info,
            "can_be_debugged": task.can_be_debugged(),
        }

        # Получаем информацию о VNC сессии если есть
        vnc_info = None
        try:
            from app.core.enhanced_vnc_manager import enhanced_vnc_manager

            vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)
            if vnc_session:
                vnc_info = vnc_session.to_dict()
                vnc_info["connection_command"] = (
                    f"vncviewer localhost:{vnc_session.vnc_port}"
                )
        except Exception as e:
            logger.warning(
                "Failed to get VNC session info", task_id=task_id, error=str(e)
            )

        return {
            "success": True,
            "task_info": task_info,
            "vnc_info": vnc_info,
            "has_active_vnc": vnc_info is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get debug info", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get debug info: {str(e)}"
        )


@router.post("/{task_id}/restart-debug")
async def restart_task_debug(
    task_id: str,
    device_type: str = "desktop",
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Перезапустить задачу в debug режиме (сбросить статус на pending)"""
    try:
        # Преобразуем device_type
        try:
            device_type_enum = DeviceType(device_type.lower())
        except ValueError:
            device_type_enum = DeviceType.DESKTOP

        # Получаем задачу
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Останавливаем существующую VNC сессию
        try:
            from app.core.enhanced_vnc_manager import enhanced_vnc_manager

            await enhanced_vnc_manager.stop_debug_session(task_id)
        except Exception as e:
            logger.warning(
                "Failed to stop existing VNC session", task_id=task_id, error=str(e)
            )

        # Сбрасываем статус задачи и включаем debug
        task.status = "pending"
        task.started_at = None
        task.completed_at = None
        task.worker_id = None
        task.error_message = None
        task.result = None

        # Обновляем debug параметры
        if not task.parameters:
            task.parameters = {}

        task.parameters.update(
            {
                "debug_enabled": True,
                "debug_device_type": device_type_enum.value,
                "debug_restarted_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        await db.commit()

        logger.info(
            "Task restarted in debug mode",
            task_id=task_id,
            task_type=task.task_type,
            device_type=device_type_enum.value,
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task restarted in debug mode",
            "task_info": {
                "id": str(task.id),
                "task_type": task.task_type,
                "status": task.status,
                "device_type": task.device_type,
                "debug_enabled": task.debug_enabled,
                "debug_device_type": device_type_enum.value,
            },
            "instructions": [
                "1. Task status reset to 'pending'",
                "2. Debug mode enabled",
                "3. Worker will pick it up within 5 seconds",
                "4. VNC session will be created automatically",
                "5. Monitor logs for VNC connection details",
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to restart task in debug", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to restart task: {str(e)}")


@router.get("/debug-sessions")
async def get_all_debug_sessions() -> Dict[str, Any]:
    """Получить все активные debug сессии"""
    try:
        from app.core.enhanced_vnc_manager import enhanced_vnc_manager

        sessions = await enhanced_vnc_manager.get_active_sessions()

        return {
            "success": True,
            "active_sessions": sessions,
            "total_sessions": len(sessions),
            "instructions": {
                "connect_via_vnc": "vncviewer localhost:PORT",
                "available_ports": [session.get("vnc_port") for session in sessions],
            },
        }

    except Exception as e:
        logger.error("Failed to get debug sessions", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "active_sessions": [],
            "total_sessions": 0,
        }


# Добавьте этот роутер в main.py:
# from app.api.v1.existing_tasks_debug import router as existing_tasks_debug_router
# app.include_router(existing_tasks_debug_router, prefix="/api/v1")
