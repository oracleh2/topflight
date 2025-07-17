#!/usr/bin/env python3
# scripts/debug_tasks.py - CLI скрипт для управления debug режимом

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

# Добавляем путь к backend для импорта
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import async_session_maker
from app.models import Task, DeviceType
from app.core.task_manager import TaskManager
from app.core.enhanced_vnc_manager import enhanced_vnc_manager
import structlog

logger = structlog.get_logger(__name__)


class DebugTasksCLI:
    """CLI для управления debug режимом задач"""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self.session = async_session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def list_tasks(self, status: Optional[str] = None, limit: int = 20):
        """Показать список задач"""
        query = select(Task).order_by(Task.created_at.desc()).limit(limit)

        if status:
            query = query.where(Task.status == status)

        result = await self.session.execute(query)
        tasks = result.scalars().all()

        print(f"\n📋 Найдено {len(tasks)} задач:")
        print("=" * 120)
        print(f"{'ID':<36} {'Тип':<20} {'Статус':<12} {'Устройство':<10} {'Debug':<8} {'Создана':<19}")
        print("=" * 120)

        for task in tasks:
            debug_status = "✅ Да" if task.debug_enabled else "❌ Нет"
            created_str = task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "N/A"

            print(f"{str(task.id):<36} {task.task_type:<20} {task.status:<12} {task.device_type:<10} {debug_status:<8} {created_str}")

        print("=" * 120)

        # Показываем задачи, которые можно отлаживать
        debuggable = [t for t in tasks if t.can_be_debugged()]
        if debuggable:
            print(f"\n🔍 Задач доступных для дебага: {len(debuggable)}")
            for task in debuggable[:5]:  # Показываем первые 5
                print(f"   • {task.id} - {task.task_type} ({task.status})")

    async def enable_debug(self, task_id: str, device_type: str = "desktop"):
        """Включить debug режим для задачи"""
        try:
            device_type_enum = DeviceType(device_type.lower())
        except ValueError:
            device_type_enum = DeviceType.DESKTOP

        task_manager = TaskManager(self.session)
        success = await task_manager.enable_task_debug(
            task_id=task_id,
            device_type=device_type_enum
        )

        if success:
            print(f"✅ Debug режим включен для задачи {task_id}")
            print(f"🖥️  Тип устройства: {device_type_enum.value}")
            print("📝 Задача будет обработана воркером в debug режиме")
            print("🔍 Следите за логами для получения VNC подключения")
        else:
            print(f"❌ Не удалось включить debug режим для задачи {task_id}")

    async def disable_debug(self, task_id: str):
        """Отключить debug режим для задачи"""
        task_manager = TaskManager(self.session)
        success = await task_manager.disable_task_debug(task_id=task_id)

        # Также останавливаем VNC сессию
        try:
            await enhanced_vnc_manager.stop_debug_session(task_id)
            print(f"🔌 VNC сессия остановлена для задачи {task_id}")
        except Exception as e:
            print(f"⚠️  Не удалось остановить VNC сессию: {e}")

        if success:
            print(f"✅ Debug режим отключен для задачи {task_id}")
        else:
            print(f"❌ Не удалось отключить debug режим для задачи {task_id}")

    async def restart_task(self, task_id: str, device_type: str = "desktop"):
        """Перезапустить задачу в debug режиме"""
        try:
            device_type_enum = DeviceType(device_type.lower())
        except ValueError:
            device_type_enum = DeviceType.DESKTOP

        # Получаем задачу
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            print(f"❌ Задача {task_id} не найдена")
            return

        # Останавливаем VNC сессию если есть
        try:
            await enhanced_vnc_manager.stop_debug_session(task_id)
        except Exception:
            pass

        # Сбрасываем статус и включаем debug
        task.status = "pending"
        task.started_at = None
        task.completed_at = None
        task.worker_id = None
        task.error_message = None
        task.result = None

        if not task.parameters:
            task.parameters = {}

        task.parameters.update({
            "debug_enabled": True,
            "debug_device_type": device_type_enum.value,
        })

        await self.session.commit()

        print(f"🔄 Задача {task_id} перезапущена в debug режиме")
        print(f"📋 Тип: {task.task_type}")
        print(f"🖥️  Устройство: {device_type_enum.value}")
        print("⏳ Воркер подхватит задачу в течение 5 секунд")

    async def show_vnc_sessions(self):
        """Показать активные VNC сессии"""
        try:
            sessions = await enhanced_vnc_manager.get_active_sessions()

            if not sessions:
                print("📺 Нет активных VNC сессий")
                return

            print(f"\n📺 Активных VNC сессий: {len(sessions)}")
            print("=" * 100)
            print(f"{'Task ID':<36} {'VNC Port':<10} {'Display':<10} {'Resolution':<12} {'Device':<10} {'Status':<10}")
            print("=" * 100)

            for session in sessions:
                task_id = session.get("task_id", "N/A")
                vnc_port = session.get("vnc_port", "N/A")
                display_num = session.get("display_num", "N/A")
                resolution = session.get("resolution", "N/A")
                device_type = session.get("device_type", "N/A")
                status = session.get("status", "N/A")

                print(f"{task_id:<36} {vnc_port:<10} :{display_num:<9} {resolution:<12} {device_type:<10} {status:<10}")

            print("=" * 100)
            print("\n🔌 Команды для подключения:")
            for session in sessions:
                task_id = session.get("task_id", "Unknown")[:8]
                vnc_port = session.get("vnc_port")
                print(f"   • vncviewer localhost:{vnc_port}  # Task: {task_id}...")

        except Exception as e:
            print(f"❌ Ошибка получения VNC сессий: {e}")

    async def show_task_info(self, task_id: str):
        """Показать подробную информацию о задаче"""
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            print(f"❌ Задача {task_id} не найдена")
            return

        print(f"\n📋 Информация о задаче {task_id}")
        print("=" * 80)
        print(f"🏷️  Тип: {task.task_type}")
        print(f"📊 Статус: {task.status}")
        print(f"🖥️  Устройство: {task.device_type}")
        print(f"🔍 Debug режим: {'✅ Включен' if task.debug_enabled else '❌ Отключен'}")
        print(f"🔄 Можно отладить: {'✅ Да' if task.can_be_debugged() else '❌ Нет'}")

        if task.created_at:
            print(f"📅 Создана: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if task.started_at:
            print(f"▶️  Запущена: {task.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if task.completed_at:
            print(f"✅ Завершена: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if task.worker_id:
            print(f"👷 Воркер: {task.worker_id}")

        if task.error_message:
            print(f"❌ Ошибка: {task.error_message}")

        # Debug информация
        if task.debug_enabled and task.debug_info:
            print(f"\n🔍 Debug информация:")
            debug_info = task.debug_info
            for key, value in debug_info.items():
                if value:
                    print(f"   • {key}: {value}")

        # VNC сессия
        try:
            vnc_session = enhanced_vnc_manager.get_session_by_task(task_id)
            if vnc_session:
                print(f"\n📺 VNC сессия:")
                print(f"   • Порт: {vnc_session.vnc_port}")
                print(f"   • Дисплей: :{vnc_session.display_num}")
                print(f"   • Разрешение: {vnc_session.resolution}")
                print(f"   • Команда: vncviewer localhost:{vnc_session.vnc_port}")
        except Exception:
            pass

        # Параметры задачи
        if task.parameters:
            print(f"\n⚙️  Параметры:")
            print(json.dumps(task.parameters, indent=2, ensure_ascii=False))


async def main():
    """Главная функция CLI"""
    if len(sys.argv) < 2:
        print("""
🔍 Debug Tasks CLI - Управление debug режимом задач

Использование:
    python scripts/debug_tasks.py <команда> [аргументы]

Команды:
    list [status] [limit]         - Список задач (опционально по статусу)
    enable <task_id> [device]     - Включить debug для задачи
    disable <task_id>             - Отключить debug для задачи
    restart <task_id> [device]    - Перезапустить задачу в debug режиме
    vnc                           - Показать активные VNC сессии
    info <task_id>                - Подробная информация о задаче

Примеры:
    python scripts/debug_tasks.py list pending 10
    python scripts/debug_tasks.py enable 123e4567-e89b-12d3-a456-426614174000 desktop
    python scripts/debug_tasks.py restart 123e4567-e89b-12d3-a456-426614174000
    python scripts/debug_tasks.py vnc
    python scripts/debug_tasks.py info 123e4567-e89b-12d3-a456-426614174000
        """)
        return

    command = sys.argv[1]

    async with DebugTasksCLI() as cli:
        try:
            if command == "list":
                status = sys.argv[2] if len(sys.argv) > 2 else None
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
                await cli.list_tasks(status, limit)

            elif command == "enable":
                if len(sys.argv) < 3:
                    print("❌ Укажите task_id: python scripts/debug_tasks.py enable <task_id>")
                    return
                task_id = sys.argv[2]
                device_type = sys.argv[3] if len(sys.argv) > 3 else "desktop"
                await cli.enable_debug(task_id, device_type)

            elif command == "disable":
                if len(sys.argv) < 3:
                    print("❌ Укажите task_id: python scripts/debug_tasks.py disable <task_id>")
                    return
                task_id = sys.argv[2]
                await cli.disable_debug(task_id)

            elif command == "restart":
                if len(sys.argv) < 3:
                    print("❌ Укажите task_id: python scripts/debug_tasks.py restart <task_id>")
                    return
                task_id = sys.argv[2]
                device_type = sys.argv[3] if len(sys.argv) > 3 else "desktop"
                await cli.restart_task(task_id, device_type)

            elif command == "vnc":
                await cli.show_vnc_sessions()

            elif command == "info":
                if len(sys.argv) < 3:
                    print("❌ Укажите task_id: python scripts/debug_tasks.py info <task_id>")
                    return
                task_id = sys.argv[2]
                await cli.show_task_info(task_id)

            else:
                print(f"❌ Неизвестная команда: {command}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
