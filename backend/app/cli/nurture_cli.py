# backend/app/cli/nurture_cli.py
import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import signal

import click
import structlog
from sqlalchemy import and_

from app.core.task_manager import TaskManager
from app.database import async_session_maker
from app.services.profile_nurture_limits_service import ProfileNurtureLimitsService
from app.workers.profile_nurture_worker import ProfileNurtureWorker

logger = structlog.get_logger(__name__)


@click.group()
def cli():
    """Profile Nurture Management CLI"""
    pass


@cli.command()
@click.option("--workers", "-w", default=1, help="Number of worker processes")
@click.option(
    "--check-interval", "-i", default=5, help="Task check interval in seconds"
)
def start_worker(workers, check_interval):
    """Start profile nurture worker(s)"""

    async def run_workers():
        worker_tasks = []
        workers_list = []

        # Создаем worker'ы
        for i in range(workers):
            worker = ProfileNurtureWorker()
            worker.check_interval = check_interval
            workers_list.append(worker)

            # Запускаем каждый worker в отдельной задаче
            task = asyncio.create_task(worker.start())
            worker_tasks.append(task)

            logger.info(f"Started worker {i+1}/{workers}", worker_id=worker.worker_id)

        # Graceful shutdown handler
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping workers...")
            for worker in workers_list:
                asyncio.create_task(worker.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Ждем завершения всех worker'ов
            await asyncio.gather(*worker_tasks)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            # Останавливаем всех worker'ов
            stop_tasks = [worker.stop() for worker in workers_list]
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            logger.info("All workers stopped")

    click.echo(f"Starting {workers} profile nurture worker(s)...")
    asyncio.run(run_workers())


@cli.command()
@click.argument("strategy_id")
@click.option("--count", "-c", default=None, type=int, help="Number of tasks to create")
@click.option("--priority", "-p", default=5, help="Task priority (1-20)")
def create_tasks(strategy_id, count, priority):
    """Create nurture tasks for a strategy"""

    async def _create():
        async with async_session_maker() as session:
            limits_service = ProfileNurtureLimitsService(session)

            if count is None:
                # Автоматическое создание на основе лимитов
                result = await limits_service.spawn_nurture_tasks_if_needed(strategy_id)
            else:
                # Создание указанного количества задач
                task_manager = TaskManager(session)
                tasks_created = 0
                created_task_ids = []

                for i in range(count):
                    try:
                        task = await task_manager.create_profile_nurture_task(
                            strategy_id=strategy_id, priority=priority
                        )
                        tasks_created += 1
                        created_task_ids.append(str(task.id))
                    except Exception as e:
                        logger.error(f"Failed to create task {i+1}: {e}")
                        break

                result = {
                    "success": True,
                    "tasks_created": tasks_created,
                    "task_ids": created_task_ids,
                }

            if "message" in result:
                message = result["message"]
            else:
                message = f'Created {result["tasks_created"]} tasks'

            click.echo(f"✅ {message}")

    asyncio.run(_create())


@cli.command()
@click.argument("user_id")
def auto_maintain(user_id):
    """Auto-maintain all strategies for a user"""

    async def _maintain():
        async with async_session_maker() as session:
            limits_service = ProfileNurtureLimitsService(session)
            result = await limits_service.auto_maintain_all_strategies(user_id)

            if result["success"]:
                click.echo(
                    f"✅ Maintained {result['maintained_strategies']} strategies"
                )
                click.echo(f"📊 Total tasks created: {result['total_tasks_created']}")

                for strategy_result in result["results"]:
                    strategy_name = strategy_result["strategy_name"]
                    tasks_created = strategy_result["result"]["tasks_created"]
                    click.echo(f"   • {strategy_name}: {tasks_created} tasks")
            else:
                click.echo("❌ Failed to maintain strategies")

    asyncio.run(_maintain())


@cli.command()
@click.option("--user-id", help="Filter by user ID")
@click.option("--status", help="Filter by status")
@click.option("--limit", default=10, help="Number of strategies to show")
def list_strategies(user_id, status, limit):
    """List profile nurture strategies and their status"""

    async def _list():
        async with async_session_maker() as session:
            from sqlalchemy import select
            from app.models import UserStrategy

            # Базовый запрос
            query = (
                select(UserStrategy)
                .where(UserStrategy.strategy_type == "profile_nurture")
                .limit(limit)
            )

            if user_id:
                query = query.where(UserStrategy.user_id == user_id)

            result = await session.execute(query)
            strategies = result.scalars().all()

            if not strategies:
                click.echo("No profile nurture strategies found")
                return

            limits_service = ProfileNurtureLimitsService(session)

            click.echo(f"\n📋 Profile Nurture Strategies ({len(strategies)}):")
            click.echo("=" * 80)

            for strategy in strategies:
                try:
                    status_info = await limits_service.check_strategy_status(
                        str(strategy.id)
                    )

                    # Определяем иконку статуса
                    status_icon = {
                        "critical": "🔴",
                        "normal": "🟢",
                        "max_reached": "🔵",
                    }.get(status_info["status"], "⚪")

                    click.echo(f"\n{status_icon} {strategy.name}")
                    click.echo(f"   ID: {strategy.id}")
                    click.echo(f"   User: {strategy.user_id}")
                    click.echo(f"   Status: {status_info['status']}")
                    click.echo(
                        f"   Profiles: {status_info['current_count']}/{status_info['min_limit']}-{status_info['max_limit']}"
                    )
                    click.echo(
                        f"   Needs nurture: {'Yes' if status_info['needs_nurture'] else 'No'}"
                    )
                    click.echo(f"   Active: {'Yes' if strategy.is_active else 'No'}")

                except Exception as e:
                    click.echo(f"\n❌ {strategy.name}")
                    click.echo(f"   ID: {strategy.id}")
                    click.echo(f"   Error: {str(e)}")

    asyncio.run(_list())


@cli.command()
@click.option("--status", help="Filter by task status")
@click.option("--strategy-id", help="Filter by strategy ID")
@click.option("--limit", default=20, help="Number of tasks to show")
def list_tasks(status, strategy_id, limit):
    """List profile nurture tasks"""

    async def _list():
        async with async_session_maker() as session:
            from sqlalchemy import select, desc
            from app.models import Task

            # Базовый запрос
            query = (
                select(Task)
                .where(Task.task_type == "profile_nurture")
                .order_by(desc(Task.created_at))
                .limit(limit)
            )

            if status:
                query = query.where(Task.status == status)

            if strategy_id:
                query = query.where(
                    Task.parameters.op("->>")("strategy_id") == strategy_id
                )

            result = await session.execute(query)
            tasks = result.scalars().all()

            if not tasks:
                click.echo("No profile nurture tasks found")
                return

            click.echo(f"\n📋 Profile Nurture Tasks ({len(tasks)}):")
            click.echo("=" * 100)

            for task in tasks:
                # Определяем иконку статуса
                status_icon = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(task.status, "⚪")

                strategy_id_param = (
                    task.parameters.get("strategy_id", "unknown")
                    if task.parameters
                    else "unknown"
                )
                strategy_name = (
                    task.parameters.get("strategy_name", "Unknown")
                    if task.parameters
                    else "Unknown"
                )

                click.echo(f"\n{status_icon} Task {str(task.id)[:8]}...")
                click.echo(f"   Strategy: {strategy_name} ({strategy_id_param[:8]}...)")
                click.echo(f"   Status: {task.status}")
                click.echo(f"   Priority: {task.priority}")
                click.echo(f"   Device: {task.device_type}")
                click.echo(f"   Created: {task.created_at}")

                if task.worker_id:
                    click.echo(f"   Worker: {task.worker_id}")

                if task.error_message:
                    click.echo(f"   Error: {task.error_message}")

                if task.result and task.status == "completed":
                    cookies = task.result.get("cookies_collected", 0)
                    sites = task.result.get("sites_visited", 0)
                    click.echo(f"   Result: {cookies} cookies, {sites} sites")

    asyncio.run(_list())


@cli.command()
@click.argument("task_id")
def cancel_task(task_id):
    """Cancel a pending nurture task"""

    async def _cancel():
        async with async_session_maker() as session:
            task_manager = TaskManager(session)

            # Получаем задачу
            from sqlalchemy import select
            from app.models import Task

            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                click.echo(f"❌ Task {task_id} not found")
                return

            if task.status != "pending":
                click.echo(f"❌ Cannot cancel task in status: {task.status}")
                return

            # Отмечаем как отмененную
            success = await task_manager.mark_task_failed(task_id, "Cancelled by admin")

            if success:
                click.echo(f"✅ Task {task_id} cancelled")
            else:
                click.echo(f"❌ Failed to cancel task {task_id}")

    asyncio.run(_cancel())


@cli.command()
def health_check():
    """Check the health of the nurture system"""

    async def _check():
        async with async_session_maker() as session:
            from sqlalchemy import select, func
            from app.models import Task, UserStrategy

            click.echo("\n🏥 Profile Nurture System Health Check")
            click.echo("=" * 50)

            # Статистика задач
            tasks_stats = await session.execute(
                select(Task.status, func.count(Task.id))
                .where(Task.task_type == "profile_nurture")
                .group_by(Task.status)
            )
            tasks_by_status = dict(tasks_stats.fetchall())

            click.echo(f"\n📊 Task Statistics:")
            for status, count in tasks_by_status.items():
                icon = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                }.get(status, "⚪")
                click.echo(f"   {icon} {status.title()}: {count}")

            # Статистика стратегий
            total_strategies = await session.execute(
                select(func.count(UserStrategy.id)).where(
                    UserStrategy.strategy_type == "profile_nurture"
                )
            )
            active_strategies = await session.execute(
                select(func.count(UserStrategy.id)).where(
                    and_(
                        UserStrategy.strategy_type == "profile_nurture",
                        UserStrategy.is_active == True,
                    )
                )
            )

            click.echo(f"\n📈 Strategy Statistics:")
            click.echo(f"   📋 Total strategies: {total_strategies.scalar()}")
            click.echo(f"   ✅ Active strategies: {active_strategies.scalar()}")

            # Проверяем критические стратегии
            limits_service = ProfileNurtureLimitsService(session)

            active_strats = await session.execute(
                select(UserStrategy).where(
                    and_(
                        UserStrategy.strategy_type == "profile_nurture",
                        UserStrategy.is_active == True,
                    )
                )
            )

            critical_count = 0
            max_reached_count = 0

            for strategy in active_strats.scalars():
                try:
                    status = await limits_service.check_strategy_status(
                        str(strategy.id)
                    )
                    if status["status"] == "critical":
                        critical_count += 1
                    elif status["status"] == "max_reached":
                        max_reached_count += 1
                except:
                    pass

            click.echo(f"\n🚨 Strategy Health:")
            click.echo(f"   🔴 Critical (below minimum): {critical_count}")
            click.echo(f"   🔵 Max reached: {max_reached_count}")

            # Общий статус
            pending_tasks = tasks_by_status.get("pending", 0)
            failed_tasks = tasks_by_status.get("failed", 0)

            overall_status = "🟢 Healthy"
            if critical_count > 0:
                overall_status = "🟡 Warning (critical strategies)"
            if pending_tasks > 100:
                overall_status = "🟡 Warning (high queue)"
            if failed_tasks > 20:
                overall_status = "🔴 Unhealthy (many failures)"

            click.echo(f"\n💊 Overall Status: {overall_status}")

    asyncio.run(_check())


if __name__ == "__main__":
    cli()
