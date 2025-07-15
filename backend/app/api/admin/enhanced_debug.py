# backend/app/api/admin/enhanced_debug.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import structlog
import io
import asyncio

from app.database import get_session
from app.models import Task, User, DeviceType
from app.core.enhanced_vnc_manager import enhanced_vnc_manager
from app.core.browser_manager import BrowserManager
from app.core.vnc_cleanup import cleanup_service
from app.core.vnc_metrics import metrics_collector
from app.api.admin.vnc_tokens import vnc_token_manager
from app.api.auth import get_current_admin_user, log_admin_action

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Enhanced VNC Debug"])


@router.post("/start/{task_id}")
async def start_task_debugging(
    task_id: str,
    background_tasks: BackgroundTasks,
    device_type: DeviceType = Query(
        DeviceType.DESKTOP, description="Тип устройства для эмуляции"
    ),
    auto_screenshot: bool = Query(True, description="Автоматические скриншоты"),
    session_timeout: int = Query(
        3600, ge=300, le=7200, description="Таймаут сессии в секундах"
    ),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Запускает режим дебага с улучшенными возможностями"""
    try:
        # Проверяем существование и статус задачи
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status not in ["pending", "running", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot debug task with status: {task.status}",
            )

        # Проверяем, что сессия не существует
        existing_session = enhanced_vnc_manager.get_session_by_task(task_id)
        if existing_session:
            logger.warning("VNC session already exists", task_id=task_id)
            # Возвращаем существующую сессию
            vnc_token = vnc_token_manager.generate_token(
                task_id, existing_session.vnc_host, existing_session.vnc_port
            )
            session_data = existing_session.to_dict()
            session_data["vnc_token"] = vnc_token
            session_data["web_vnc_url"] = vnc_token_manager.get_vnc_url(vnc_token)
            return {
                "success": True,
                "task_id": task_id,
                "debug_info": session_data,
                "message": "Using existing debug session",
            }

        # Добавляем расширенные параметры дебага
        if not task.parameters:
            task.parameters = {}

        task.parameters.update(
            {
                "debug_enabled": True,
                "debug_device_type": device_type.value,
                "debug_started_by": str(current_admin.id),
                "debug_started_at": datetime.now(timezone.utc).isoformat(),
                "debug_auto_screenshot": auto_screenshot,
                "debug_session_timeout": session_timeout,
            }
        )

        await session.commit()

        # Создаем VNC сессию
        debug_info = await enhanced_vnc_manager.create_debug_session(
            task_id, device_type
        )

        # Генерируем токен для noVNC
        vnc_token = vnc_token_manager.generate_token(
            task_id, debug_info["vnc_host"], debug_info["vnc_port"]
        )

        # Добавляем токен и web URL в ответ
        debug_info["vnc_token"] = vnc_token
        debug_info["web_vnc_url"] = vnc_token_manager.get_vnc_url(vnc_token)

        # Запускаем браузер в debug режиме
        browser_manager = BrowserManager(session)
        browser_info = await browser_manager.launch_debug_browser(task_id, device_type)
        debug_info.update(browser_info)

        # Логируем действие администратора
        await log_admin_action(
            session,
            current_admin.id,
            "debug_session_started",
            {
                "task_id": task_id,
                "device_type": device_type.value,
                "vnc_port": debug_info["vnc_port"],
            },
        )

        # Планируем автоматические скриншоты если включены
        if auto_screenshot:
            background_tasks.add_task(
                schedule_auto_screenshots, task_id, 30
            )  # каждые 30 сек

        logger.info(
            "Task debugging started",
            task_id=task_id,
            device_type=device_type.value,
            admin_id=str(current_admin.id),
            vnc_port=debug_info.get("vnc_port"),
            vnc_token=vnc_token,
        )

        return {
            "success": True,
            "task_id": task_id,
            "debug_info": debug_info,
            "message": "Debug session created successfully",
            "instructions": {
                "native_vnc": f"vncviewer {debug_info['vnc_host']}:{debug_info['vnc_port']}",
                "web_vnc": debug_info["web_vnc_url"],
                "ssh_tunnel": f"ssh -L {debug_info['vnc_port']}:localhost:{debug_info['vnc_port']} user@server",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start task debugging", task_id=task_id, error=str(e))
        metrics_collector.record_debug_task_failed(device_type.value, task_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start debugging: {str(e)}",
        )


@router.post("/stop/{task_id}")
async def stop_task_debugging(
    task_id: str,
    force: bool = Query(False, description="Принудительная остановка"),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Останавливает режим дебага с улучшенной очисткой"""
    try:
        # Проверяем существование задачи
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Останавливаем VNC сессию
        success = await enhanced_vnc_manager.stop_debug_session(task_id)

        # Отзываем токены
        vnc_token_manager.revoke_token(task_id)

        # Убираем флаг дебага из параметров задачи
        if task.parameters and "debug_enabled" in task.parameters:
            task.parameters["debug_enabled"] = False
            task.parameters["debug_stopped_by"] = str(current_admin.id)
            task.parameters["debug_stopped_at"] = datetime.now(timezone.utc).isoformat()
            task.parameters["debug_force_stopped"] = force
            await session.commit()

        # Логируем действие
        await log_admin_action(
            session,
            current_admin.id,
            "debug_session_stopped",
            {"task_id": task_id, "force": force, "success": success},
        )

        logger.info(
            "Task debugging stopped",
            task_id=task_id,
            success=success,
            force=force,
            admin_id=str(current_admin.id),
        )

        return {
            "success": success,
            "task_id": task_id,
            "force_stopped": force,
            "message": (
                "Debug session stopped successfully"
                if success
                else "Debug session stop failed"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop task debugging", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop debugging: {str(e)}",
        )


@router.get("/sessions")
async def get_active_debug_sessions(
    include_metrics: bool = Query(True, description="Включить метрики"),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Получает список активных debug сессий с метриками"""
    try:
        # Очищаем неактивные сессии
        await enhanced_vnc_manager.cleanup_inactive_sessions()

        # Получаем активные сессии
        sessions = await enhanced_vnc_manager.get_active_sessions()

        # Добавляем токены для каждой сессии
        for session_data in sessions:
            task_id = session_data["task_id"]
            vnc_host = session_data["vnc_host"]
            vnc_port = session_data["vnc_port"]

            # Генерируем или получаем существующий токен
            token = vnc_token_manager.generate_token(task_id, vnc_host, vnc_port)
            session_data["vnc_token"] = token
            session_data["web_vnc_url"] = vnc_token_manager.get_vnc_url(token)

        result = {
            "sessions": sessions,
            "total_count": len(sessions),
        }

        # Добавляем системные метрики если запрошены
        if include_metrics:
            result["metrics"] = {
                "max_sessions": enhanced_vnc_manager.max_sessions,
                "available_sessions": enhanced_vnc_manager.max_sessions - len(sessions),
                "used_displays": list(enhanced_vnc_manager.used_displays),
                "session_timeout": enhanced_vnc_manager.session_timeout,
            }

        logger.info(
            "Retrieved active debug sessions",
            count=len(sessions),
            admin_id=str(current_admin.id),
        )

        return result

    except Exception as e:
        logger.error("Failed to get active debug sessions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get debug sessions: {str(e)}",
        )


@router.get("/session/{task_id}")
async def get_debug_session_info(
    task_id: str, current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """Получает подробную информацию о debug сессии"""
    try:
        vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)

        if not vnc_session:
            raise HTTPException(status_code=404, detail="Debug session not found")

        session_info = vnc_session.to_dict()

        # Добавляем токен и web URL
        token = vnc_token_manager.generate_token(
            task_id, vnc_session.vnc_host, vnc_session.vnc_port
        )
        session_info["vnc_token"] = token
        session_info["web_vnc_url"] = vnc_token_manager.get_vnc_url(token)

        return session_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get debug session info", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}",
        )


@router.get("/screenshot/{task_id}")
async def get_task_screenshot(
    task_id: str,
    format: str = Query("png", regex="^(png|jpg|jpeg)$"),
    current_admin: User = Depends(get_current_admin_user),
) -> StreamingResponse:
    """Получает скриншот debug сессии"""
    try:
        vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)

        if not vnc_session:
            raise HTTPException(status_code=404, detail="Debug session not found")

        # Делаем скриншот через DISPLAY
        screenshot_data = await take_display_screenshot(vnc_session.display_num, format)

        if not screenshot_data:
            raise HTTPException(status_code=404, detail="Screenshot not available")

        return StreamingResponse(
            io.BytesIO(screenshot_data),
            media_type=f"image/{format}",
            headers={
                "Content-Disposition": f"inline; filename=screenshot_{task_id}.{format}",
                "Cache-Control": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get screenshot", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get screenshot: {str(e)}",
        )


@router.get("/web-vnc/{task_id}")
async def redirect_to_web_vnc(
    task_id: str, current_admin: User = Depends(get_current_admin_user)
) -> RedirectResponse:
    """Перенаправляет на web VNC интерфейс"""
    try:
        vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)

        if not vnc_session:
            raise HTTPException(status_code=404, detail="Debug session not found")

        # Генерируем токен и получаем URL
        token = vnc_token_manager.generate_token(
            task_id, vnc_session.vnc_host, vnc_session.vnc_port
        )
        web_vnc_url = vnc_token_manager.get_vnc_url(token)

        if not web_vnc_url:
            raise HTTPException(
                status_code=500, detail="Failed to generate web VNC URL"
            )

        return RedirectResponse(url=web_vnc_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to redirect to web VNC", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to redirect to web VNC: {str(e)}",
        )


@router.post("/cleanup")
async def force_cleanup_sessions(
    reason: str = Query("manual_cleanup", description="Причина очистки"),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Принудительная очистка всех debug сессий"""
    try:
        # Получаем список сессий перед очисткой
        sessions_before = await enhanced_vnc_manager.get_active_sessions()
        session_count = len(sessions_before)

        # Выполняем очистку
        await cleanup_service.cleanup_all_sessions(reason)

        # Очищаем все токены
        vnc_token_manager.tokens.clear()
        vnc_token_manager._update_token_file()

        # Логируем действие
        await log_admin_action(
            session,
            current_admin.id,
            "debug_sessions_cleanup",
            {"session_count": session_count, "reason": reason},
        )

        logger.info(
            "Force cleanup completed",
            session_count=session_count,
            reason=reason,
            admin_id=str(current_admin.id),
        )

        return {
            "success": True,
            "sessions_cleaned": session_count,
            "reason": reason,
            "message": f"Cleaned up {session_count} debug sessions",
        }

    except Exception as e:
        logger.error("Failed to cleanup sessions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup sessions: {str(e)}",
        )


@router.get("/metrics")
async def get_vnc_metrics(
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Получает метрики VNC системы"""
    try:
        # Обновляем счетчик активных сессий
        active_sessions = await enhanced_vnc_manager.get_active_sessions()
        metrics_collector.update_active_sessions_count(len(active_sessions))

        return {
            "active_sessions": len(active_sessions),
            "max_sessions": enhanced_vnc_manager.max_sessions,
            "available_sessions": enhanced_vnc_manager.max_sessions
            - len(active_sessions),
            "used_displays": list(enhanced_vnc_manager.used_displays),
            "session_timeout": enhanced_vnc_manager.session_timeout,
            "cleanup_service_running": cleanup_service.is_running,
            "metrics_available": True,
        }

    except Exception as e:
        logger.error("Failed to get VNC metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}",
        )


# Вспомогательные функции
async def take_display_screenshot(
    display_num: int, format: str = "png"
) -> Optional[bytes]:
    """Делает скриншот виртуального дисплея"""
    try:
        cmd = [
            "import",
            "-display",
            f":{display_num}",
            "-window",
            "root",
            f"{format}:-",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout
        else:
            logger.error(
                "Screenshot failed", display_num=display_num, stderr=stderr.decode()
            )
            return None

    except Exception as e:
        logger.error("Error taking screenshot", display_num=display_num, error=str(e))
        return None


async def schedule_auto_screenshots(task_id: str, interval: int):
    """Планирует автоматические скриншоты"""
    try:
        while True:
            await asyncio.sleep(interval)

            # Проверяем, что сессия еще активна
            vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)
            if not vnc_session:
                logger.info("Auto-screenshot stopped: session ended", task_id=task_id)
                break

            # Делаем скриншот
            screenshot_data = await take_display_screenshot(vnc_session.display_num)
            if screenshot_data:
                # Сохраняем скриншот (можно добавить сохранение в файл/БД)
                logger.debug(
                    "Auto-screenshot taken", task_id=task_id, size=len(screenshot_data)
                )

    except asyncio.CancelledError:
        logger.info("Auto-screenshot cancelled", task_id=task_id)
    except Exception as e:
        logger.error("Auto-screenshot error", task_id=task_id, error=str(e))
