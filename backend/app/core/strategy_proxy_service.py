# backend/app/core/strategy_proxy_service.py
from typing import List, Dict, Optional, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
import json
import random
from datetime import datetime, timedelta

from ..models.strategies import UserStrategy
from ..models.strategy_proxy import (
    StrategyProxySource,
    StrategyProxyAssignment,
    StrategyProxyRotation,
)
from ..models.proxy import ProjectProxy
from ..models.profile import Profile
from ..core.proxy_service import ProxyParser
from ..schemas.strategy_proxy import (
    StrategyProxyImportResponse,
    StrategyProxyStatsResponse,
)


class StrategyProxyService:
    """Сервис для управления прокси стратегий"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def import_proxy_for_strategy(
        self,
        strategy_id: str,
        source_type: str,
        proxy_data: Optional[str] = None,
        source_url: Optional[str] = None,
        file_content: Optional[str] = None,
    ) -> StrategyProxyImportResponse:
        """Импорт прокси для стратегии"""

        try:
            # Получаем стратегию
            strategy_result = await self.session.execute(
                select(UserStrategy).where(UserStrategy.id == strategy_id)
            )
            strategy = strategy_result.scalar_one_or_none()

            if not strategy:
                return StrategyProxyImportResponse(
                    success=False, errors=["Стратегия не найдена"]
                )

            # Определяем источник данных
            if source_type == "manual_list":
                raw_data = proxy_data
            elif source_type == "file_upload":
                raw_data = file_content
            elif source_type == "url_import":
                raw_data = await self._fetch_data_from_url(source_url)
            elif source_type == "google_docs":
                raw_data = await self._fetch_google_docs_data(source_url)
            elif source_type == "google_sheets":
                raw_data = await self._fetch_google_sheets_data(source_url)
            else:
                return StrategyProxyImportResponse(
                    success=False, errors=["Неподдерживаемый тип источника"]
                )

            if not raw_data:
                return StrategyProxyImportResponse(
                    success=False, errors=["Не удалось получить данные прокси"]
                )

            # Парсим прокси
            parsed_proxies = ProxyParser.parse_proxy_list(raw_data)

            if not parsed_proxies:
                return StrategyProxyImportResponse(
                    success=False, errors=["Не удалось распарсить ни одной прокси"]
                )

            # Создаем источник прокси
            proxy_source = StrategyProxySource(
                strategy_id=strategy_id,
                source_type=source_type,
                source_url=source_url,
                proxy_data=raw_data,
            )

            self.session.add(proxy_source)

            # Импортируем прокси в основную таблицу
            domain_id = await self._get_strategy_domain_id(strategy_id)
            user_id = strategy.user_id

            successfully_imported = 0
            errors = []

            for proxy_data in parsed_proxies:
                try:
                    # Проверяем, существует ли уже такая прокси
                    existing_proxy = await self.session.execute(
                        select(ProjectProxy).where(
                            and_(
                                ProjectProxy.user_id == user_id,
                                ProjectProxy.domain_id == domain_id,
                                ProjectProxy.host == proxy_data["host"],
                                ProjectProxy.port == proxy_data["port"],
                            )
                        )
                    )

                    if existing_proxy.scalar_one_or_none():
                        continue  # Прокси уже существует

                    # Создаем новую прокси
                    new_proxy = ProjectProxy(
                        user_id=user_id,
                        domain_id=domain_id,
                        proxy_type="warmup",  # По умолчанию для стратегий
                        host=proxy_data["host"],
                        port=proxy_data["port"],
                        username=proxy_data.get("username"),
                        password=proxy_data.get("password"),
                        protocol=proxy_data.get("protocol", "http"),
                        status="active",
                    )

                    self.session.add(new_proxy)
                    successfully_imported += 1

                except Exception as e:
                    errors.append(
                        f"Ошибка импорта прокси {proxy_data.get('host', 'unknown')}: {str(e)}"
                    )

            await self.session.commit()

            return StrategyProxyImportResponse(
                success=True,
                total_parsed=len(parsed_proxies),
                successfully_imported=successfully_imported,
                failed_imports=len(parsed_proxies) - successfully_imported,
                errors=errors,
                source_id=str(proxy_source.id),
            )

        except Exception as e:
            await self.session.rollback()
            return StrategyProxyImportResponse(
                success=False, errors=[f"Ошибка импорта: {str(e)}"]
            )

    async def get_strategy_proxies(self, strategy_id: str) -> List[Dict[str, Any]]:
        """Получение прокси для стратегии"""

        # Получаем домен стратегии
        domain_id = await self._get_strategy_domain_id(strategy_id)

        # Получаем стратегию
        strategy_result = await self.session.execute(
            select(UserStrategy).where(UserStrategy.id == strategy_id)
        )
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            return []

        # Получаем прокси домена
        proxies_result = await self.session.execute(
            select(ProjectProxy).where(
                and_(
                    ProjectProxy.user_id == strategy.user_id,
                    ProjectProxy.domain_id == domain_id,
                )
            )
        )
        proxies = proxies_result.scalars().all()

        return [
            {
                "id": str(proxy.id),
                "host": proxy.host,
                "port": proxy.port,
                "protocol": proxy.protocol,
                "status": proxy.status,
                "success_rate": proxy.success_rate,
                "total_uses": proxy.total_uses,
                "last_check": (
                    proxy.last_check.isoformat() if proxy.last_check else None
                ),
            }
            for proxy in proxies
        ]

    async def assign_proxy_to_profile(
        self, profile_id: str, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Назначение прокси профилю для стратегии"""

        # Получаем доступные прокси для стратегии
        available_proxies = await self.get_strategy_proxies(strategy_id)

        if not available_proxies:
            return None

        # Выбираем случайную активную прокси
        active_proxies = [p for p in available_proxies if p["status"] == "active"]
        if not active_proxies:
            return None

        selected_proxy = random.choice(active_proxies)

        # Обновляем профиль
        await self.session.execute(select(Profile).where(Profile.id == profile_id))

        # Создаем назначение
        assignment = StrategyProxyAssignment(
            profile_id=profile_id,
            strategy_id=strategy_id,
            proxy_id=selected_proxy["id"],
        )

        self.session.add(assignment)
        await self.session.commit()

        return selected_proxy

    async def get_strategy_proxy_stats(
        self, strategy_id: str
    ) -> StrategyProxyStatsResponse:
        """Получение статистики прокси стратегии"""

        proxies = await self.get_strategy_proxies(strategy_id)

        if not proxies:
            return StrategyProxyStatsResponse(
                total_proxies=0,
                active_proxies=0,
                failed_proxies=0,
                last_check=None,
                average_response_time=None,
                success_rate=None,
            )

        total_proxies = len(proxies)
        active_proxies = len([p for p in proxies if p["status"] == "active"])
        failed_proxies = len(
            [p for p in proxies if p["status"] in ["inactive", "banned"]]
        )

        # Рассчитываем средний success_rate
        success_rates = [
            p["success_rate"] for p in proxies if p["success_rate"] is not None
        ]
        avg_success_rate = (
            sum(success_rates) / len(success_rates) if success_rates else None
        )

        return StrategyProxyStatsResponse(
            total_proxies=total_proxies,
            active_proxies=active_proxies,
            failed_proxies=failed_proxies,
            last_check=None,  # Можно добавить логику получения последней проверки
            average_response_time=None,
            success_rate=avg_success_rate,
        )

    async def rotate_proxy_for_strategy(
        self, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Ротация прокси для стратегии"""

        # Получаем текущую настройку ротации
        rotation_result = await self.session.execute(
            select(StrategyProxyRotation).where(
                StrategyProxyRotation.strategy_id == strategy_id
            )
        )
        rotation = rotation_result.scalar_one_or_none()

        if not rotation:
            # Создаем новую настройку ротации
            rotation = StrategyProxyRotation(
                strategy_id=strategy_id, rotation_interval=10, current_usage_count=0
            )
            self.session.add(rotation)

        # Получаем следующую прокси
        available_proxies = await self.get_strategy_proxies(strategy_id)
        active_proxies = [p for p in available_proxies if p["status"] == "active"]

        if not active_proxies:
            return None

        # Выбираем следующую прокси (исключаем текущую)
        if rotation.current_proxy_id:
            next_proxies = [
                p for p in active_proxies if p["id"] != str(rotation.current_proxy_id)
            ]
        else:
            next_proxies = active_proxies

        if not next_proxies:
            next_proxies = active_proxies

        selected_proxy = random.choice(next_proxies)

        # Обновляем ротацию
        rotation.current_proxy_id = selected_proxy["id"]
        rotation.current_usage_count = 0

        await self.session.commit()

        return selected_proxy

    async def _fetch_data_from_url(self, url: str) -> Optional[str]:
        """Получение данных по URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            print(f"Error fetching data from URL: {e}")
        return None

    async def _fetch_google_docs_data(self, url: str) -> Optional[str]:
        """Получение данных из Google Docs"""
        if "/edit" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
            export_url = (
                f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            )
            return await self._fetch_data_from_url(export_url)
        return None

    async def _fetch_google_sheets_data(self, url: str) -> Optional[str]:
        """Получение данных из Google Sheets"""
        if "/edit" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
            export_url = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            )
            return await self._fetch_data_from_url(export_url)
        return None

    async def _get_strategy_domain_id(self, strategy_id: str) -> Optional[str]:
        """Получение domain_id для стратегии"""
        # Это может потребовать дополнительной логики в зависимости от архитектуры
        # Пока возвращаем None, но нужно будет реализовать
        return None
