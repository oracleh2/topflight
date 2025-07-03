import asyncio
import click
from app.core.task_manager import TaskManager, TaskType
from app.models import DeviceType
from app.database import async_session_maker


@click.group()
def cli():
    """Task Management CLI"""
    pass


@cli.command()
@click.option('--keyword', required=True, help='Search keyword')
@click.option('--device', type=click.Choice(['desktop', 'mobile']), default='desktop')
@click.option('--pages', default=10, help='Number of pages to parse')
@click.option('--region', default='213', help='Region code')
def parse_serp(keyword, device, pages, region):
    """Create SERP parsing task"""

    async def _parse():
        async with async_session_maker() as session:
            manager = TaskManager(session)
            task = await manager.create_parse_task(
                keyword=keyword,
                device_type=DeviceType(device),
                pages=pages,
                region_code=region
            )
            click.echo(f"Task created: {task.id}")

    asyncio.run(_parse())


@cli.command()
@click.option('--device', type=click.Choice(['desktop', 'mobile']), default='desktop')
def warmup_profile(device):
    """Create profile warmup task"""

    async def _warmup():
        async with async_session_maker() as session:
            manager = TaskManager(session)
            task = await manager.create_warmup_task(
                device_type=DeviceType(device)
            )
            click.echo(f"Warmup task created: {task.id}")

    asyncio.run(_warmup())


@cli.command()
def start_worker():
    """Start task worker"""

    async def _start():
        async with async_session_maker() as session:
            manager = TaskManager(session)
            click.echo("Starting task worker...")
            await manager.start()

    asyncio.run(_start())


if __name__ == '__main__':
    cli()