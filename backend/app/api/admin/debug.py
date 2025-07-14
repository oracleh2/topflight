# backend/app/api/admin/debug.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import structlog
import io

from app.database import get_session
from app.models import Task, User, DeviceType  # Исправляем импорты
from app.core.vnc_manager import vnc_manager
from app.core.browser_manager import BrowserManager
from app.api.auth import (
    get_current_admin_user,
    log_admin_action,
)  # Импортируем админ проверку

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug VNC"])


@router.post("/start/{task_id}")
async def start_task_debugging(
    task_id: str,
    device_type: DeviceType = Query(
        DeviceType.DESKTOP, description="Тип устройства для эмуляции"
    ),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Запускает режим дебага для задачи"""
    try:
        # Проверяем существование задачи
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Проверяем, что задача в подходящем статусе
        if task.status not in ["pending", "running", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot debug task with status: {task.status}",
            )

        # Добавляем флаг дебага в параметры задачи
        if not task.parameters:
            task.parameters = {}

        task.parameters["debug_enabled"] = True
        task.parameters["debug_device_type"] = device_type.value
        task.parameters["debug_started_by"] = str(current_admin.id)
        task.parameters["debug_started_at"] = datetime.now(timezone.utc).isoformat()

        # Сохраняем изменения
        await session.commit()

        # Создаем VNC сессию и запускаем браузер
        browser_manager = BrowserManager(session)
        debug_info = await browser_manager.launch_debug_browser(task_id, device_type)

        logger.info(
            "Task debugging started",
            task_id=task_id,
            device_type=device_type.value,
            admin_id=str(current_admin.id),
            vnc_port=debug_info.get("vnc_port"),
        )

        return {
            "success": True,
            "task_id": task_id,
            "debug_info": debug_info,
            "message": "Debug session created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start task debugging", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start debugging: {str(e)}",
        )


@router.post("/stop/{task_id}")
async def stop_task_debugging(
    task_id: str,
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Останавливает режим дебага для задачи"""
    try:
        # Проверяем существование задачи
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Останавливаем VNC сессию
        success = await vnc_manager.stop_debug_session(task_id)

        # Убираем флаг дебага из параметров задачи
        if task.parameters and "debug_enabled" in task.parameters:
            task.parameters["debug_enabled"] = False
            task.parameters["debug_stopped_by"] = str(current_admin.id)
            task.parameters["debug_stopped_at"] = datetime.now(timezone.utc).isoformat()
            await session.commit()

        logger.info(
            "Task debugging stopped",
            task_id=task_id,
            success=success,
            admin_id=str(current_admin.id),
        )

        return {
            "success": success,
            "task_id": task_id,
            "message": (
                "Debug session stopped" if success else "Debug session stop failed"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop task debugging", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop debugging: {str(e)}",
        )


@router.get("/sessions")
async def get_active_debug_sessions(
    current_admin: User = Depends(get_current_admin_user),
) -> List[Dict[str, Any]]:
    """Получает список активных debug сессий"""
    try:
        sessions = await vnc_manager.get_active_sessions()

        # Очищаем неактивные сессии
        await vnc_manager.cleanup_inactive_sessions()

        # Получаем обновленный список
        sessions = await vnc_manager.get_active_sessions()

        logger.info("Retrieved active debug sessions", count=len(sessions))

        return sessions

    except Exception as e:
        logger.error("Failed to get active debug sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get debug sessions: {str(e)}",
        )


@router.get("/session/{task_id}")
async def get_debug_session_info(
    task_id: str, current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Получает информацию о конкретной debug сессии"""
    try:
        browser_manager = BrowserManager()
        session_info = await browser_manager.get_debug_session_info(task_id)

        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found"
            )

        return session_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get debug session info", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session info: {str(e)}",
        )


@router.get("/screenshot/{task_id}")
async def get_task_screenshot(
    task_id: str, current_admin: User = Depends(get_current_admin_user)
) -> StreamingResponse:
    """Получает скриншот debug сессии"""
    try:
        browser_manager = BrowserManager()
        screenshot_data = await browser_manager.take_debug_screenshot(task_id)

        if not screenshot_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screenshot not available or debug session not found",
            )

        # Возвращаем скриншот как PNG
        screenshot_io = io.BytesIO(screenshot_data)

        return StreamingResponse(
            screenshot_io,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=debug_screenshot_{task_id}.png"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task screenshot", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get screenshot: {str(e)}",
        )


@router.post("/restart/{task_id}")
async def restart_task_with_debug(
    task_id: str,
    device_type: DeviceType = Query(
        DeviceType.DESKTOP, description="Тип устройства для эмуляции"
    ),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Перезапускает задачу в режиме дебага"""
    try:
        # Проверяем существование задачи
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Перезапускаем с дебагом
        browser_manager = BrowserManager(session)
        debug_info = await browser_manager.restart_task_with_debug(task_id, device_type)

        # Обновляем параметры задачи
        if not task.parameters:
            task.parameters = {}

        task.parameters["debug_enabled"] = True
        task.parameters["debug_device_type"] = device_type.value
        task.parameters["debug_restarted_by"] = str(current_admin.id)
        task.parameters["debug_restarted_at"] = datetime.now(timezone.utc).isoformat()

        await session.commit()

        logger.info(
            "Task restarted with debug",
            task_id=task_id,
            device_type=device_type.value,
            admin_id=str(current_admin.id),
        )

        return {
            "success": True,
            "task_id": task_id,
            "debug_info": debug_info,
            "message": "Task restarted in debug mode",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to restart task with debug", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart with debug: {str(e)}",
        )


@router.get("/vnc-instructions/{task_id}")
async def get_vnc_connection_instructions(
    task_id: str, current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Получает инструкции по подключению к VNC"""
    try:
        session_info = await vnc_manager.get_active_sessions()
        task_session = next((s for s in session_info if s["task_id"] == task_id), None)

        if not task_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found"
            )

        vnc_port = task_session["vnc_port"]
        vnc_host = task_session["vnc_host"]

        instructions = {
            "task_id": task_id,
            "vnc_connection": {
                "host": vnc_host,
                "port": vnc_port,
                "url": f"vnc://{vnc_host}:{vnc_port}",
            },
            "client_commands": {
                "vnc_viewer": f"vncviewer {vnc_host}:{vnc_port}",
                "ssh_tunnel": f"ssh -L {vnc_port}:localhost:{vnc_port} user@your-server",
                "browser_vnc": f"http://localhost:6080/vnc.html?host={vnc_host}&port={vnc_port}",
            },
            "recommended_clients": [
                {
                    "name": "RealVNC Viewer",
                    "platform": "Windows/Mac/Linux",
                    "download": "https://www.realvnc.com/en/connect/download/viewer/",
                },
                {
                    "name": "TightVNC Viewer",
                    "platform": "Windows",
                    "download": "https://www.tightvnc.com/download.php",
                },
                {
                    "name": "noVNC (Web)",
                    "platform": "Browser",
                    "description": "Web-based VNC client, no installation required",
                },
            ],
            "security_notes": [
                "VNC connection is localhost-only for security",
                "Use SSH tunnel for remote access",
                "No password required (localhost connections only)",
                "Session will be automatically terminated after 1 hour of inactivity",
            ],
        }

        return instructions

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get VNC instructions", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VNC instructions: {str(e)}",
        )


# Подключаем роутер к главному приложению в backend/app/main.py:
# from app.api.admin.debug import router as debug_router
# app.include_router(debug_router, prefix="/api/v1/admin")
