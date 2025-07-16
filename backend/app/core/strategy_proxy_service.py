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
    StrategyProxy,
)
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

            # Создаем источник прокси
            proxy_source = StrategyProxySource(
                strategy_id=strategy_id,
                source_type=source_type,
                source_url=source_url,
                proxy_data=proxy_data or file_content,
            )

            self.session.add(proxy_source)
            await self.session.flush()  # Получаем ID источника

            # Для динамических источников (URL, Google Docs/Sheets) НЕ импортируем прокси сразу
            if source_type in ["url_import", "google_docs", "google_sheets"]:
                await self.session.commit()

                # Тестируем доступность источника
                test_data = await self._fetch_data_by_source_type(
                    source_type, source_url
                )
                if not test_data:
                    return StrategyProxyImportResponse(
                        success=False,
                        errors=["Не удалось получить данные из источника"],
                    )

                # Парсим для подсчета количества прокси
                parsed_proxies = ProxyParser.parse_proxy_list(test_data)

                return StrategyProxyImportResponse(
                    success=True,
                    total_parsed=len(parsed_proxies),
                    successfully_imported=0,  # Не импортируем статично
                    failed_imports=0,
                    errors=[],
                    source_id=str(proxy_source.id),
                    message=f"Динамический источник сохранен. Найдено {len(parsed_proxies)} прокси.",
                )

            # Для статических источников (manual_list, file_upload) импортируем прокси
            else:
                raw_data = proxy_data or file_content

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

                # Импортируем прокси в таблицу StrategyProxy
                successfully_imported = 0
                errors = []

                for proxy_data in parsed_proxies:
                    try:
                        # Проверяем, существует ли уже такая прокси
                        existing_proxy = await self.session.execute(
                            select(StrategyProxy).where(
                                and_(
                                    StrategyProxy.strategy_id == strategy_id,
                                    StrategyProxy.host == proxy_data["host"],
                                    StrategyProxy.port == proxy_data["port"],
                                )
                            )
                        )

                        if existing_proxy.scalar_one_or_none():
                            continue  # Прокси уже существует

                        # Создаем новую прокси
                        new_proxy = StrategyProxy(
                            strategy_id=strategy_id,
                            source_id=proxy_source.id,
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

    async def get_random_proxy_from_strategy(
        self, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получение случайной прокси из всех источников стратегии"""

        # Получаем все источники прокси для стратегии
        sources_result = await self.session.execute(
            select(StrategyProxySource).where(
                and_(
                    StrategyProxySource.strategy_id == strategy_id,
                    StrategyProxySource.is_active == True,
                )
            )
        )
        sources = sources_result.scalars().all()

        all_proxies = []

        for source in sources:
            if source.source_type in ["url_import", "google_docs", "google_sheets"]:
                # Для динамических источников загружаем данные по URL
                fresh_data = await self._fetch_data_by_source_type(
                    source.source_type, source.source_url
                )
                if fresh_data:
                    parsed_proxies = ProxyParser.parse_proxy_list(fresh_data)
                    all_proxies.extend(parsed_proxies)

            elif source.source_type in ["manual_list", "file_upload"]:
                # Для статических источников получаем прокси из таблицы StrategyProxy
                static_proxies = await self.get_strategy_proxies(strategy_id)
                all_proxies.extend(
                    [
                        {
                            "host": proxy["host"],
                            "port": proxy["port"],
                            "username": proxy["username"],
                            "password": proxy["password"],
                            "protocol": proxy["protocol"],
                        }
                        for proxy in static_proxies
                        if proxy["status"] == "active"
                    ]
                )

        if not all_proxies:
            return None

        # Возвращаем случайную прокси
        return random.choice(all_proxies)

    async def _fetch_data_by_source_type(
        self, source_type: str, source_url: str
    ) -> Optional[str]:
        """Получение данных в зависимости от типа источника"""

        if source_type == "url_import":
            return await self._fetch_data_from_url(source_url)
        elif source_type == "google_docs":
            return await self._fetch_google_docs_data(source_url)
        elif source_type == "google_sheets":
            return await self._fetch_google_sheets_data(source_url)

        return None

    async def get_strategy_proxy_stats(
        self, strategy_id: str
    ) -> StrategyProxyStatsResponse:
        """Получение статистики прокси стратегии"""

        # Получаем статические прокси из таблицы StrategyProxy
        static_proxies = await self.get_strategy_proxies(strategy_id)

        # Получаем динамические источники
        sources_result = await self.session.execute(
            select(StrategyProxySource).where(
                and_(
                    StrategyProxySource.strategy_id == strategy_id,
                    StrategyProxySource.is_active == True,
                    StrategyProxySource.source_type.in_(
                        ["url_import", "google_docs", "google_sheets"]
                    ),
                )
            )
        )
        dynamic_sources = sources_result.scalars().all()

        total_dynamic_proxies = 0

        # Подсчитываем прокси из динамических источников
        for source in dynamic_sources:
            fresh_data = await self._fetch_data_by_source_type(
                source.source_type, source.source_url
            )
            if fresh_data:
                parsed_proxies = ProxyParser.parse_proxy_list(fresh_data)
                total_dynamic_proxies += len(parsed_proxies)

        total_proxies = len(static_proxies) + total_dynamic_proxies
        active_static = len([p for p in static_proxies if p["status"] == "active"])

        # Для динамических источников считаем все прокси активными
        active_proxies = active_static + total_dynamic_proxies

        failed_proxies = len(
            [p for p in static_proxies if p["status"] in ["inactive", "banned"]]
        )

        # Рассчитываем средний success_rate только для статических
        success_rates = [
            p["success_rate"] for p in static_proxies if p["success_rate"] is not None
        ]
        avg_success_rate = (
            sum(success_rates) / len(success_rates) if success_rates else 100.0
        )

        return StrategyProxyStatsResponse(
            total_proxies=total_proxies,
            active_proxies=active_proxies,
            failed_proxies=failed_proxies,
            last_check=None,
            average_response_time=None,
            success_rate=avg_success_rate,
        )

    async def get_strategy_proxies(self, strategy_id: str) -> List[Dict[str, Any]]:
        """Получение прокси для стратегии из таблицы StrategyProxy"""

        # Получаем прокси стратегии
        proxies_result = await self.session.execute(
            select(StrategyProxy).where(StrategyProxy.strategy_id == strategy_id)
        )
        proxies = proxies_result.scalars().all()

        return [
            {
                "id": str(proxy.id),
                "host": proxy.host,
                "port": proxy.port,
                "username": proxy.username,
                "password": proxy.password,
                "protocol": proxy.protocol,
                "status": proxy.status,
                "success_rate": proxy.success_rate,
                "total_uses": proxy.total_uses,
                "successful_uses": proxy.successful_uses,
                "failed_uses": proxy.failed_uses,
                "response_time": proxy.response_time,
                "last_used_at": (
                    proxy.last_used_at.isoformat() if proxy.last_used_at else None
                ),
                "created_at": proxy.created_at.isoformat(),
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

        # Проверяем, существует ли профиль
        profile_result = await self.session.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            return None

        # Создаем назначение
        assignment = StrategyProxyAssignment(
            profile_id=profile_id,
            strategy_id=strategy_id,
            proxy_id=selected_proxy["id"],
        )

        self.session.add(assignment)
        await self.session.commit()

        return selected_proxy

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

        # Получаем доступные прокси стратегии
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

    async def get_proxy_for_profile_execution(
        self, strategy_id: str, profile_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получение прокси для выполнения профиля"""

        # Получаем случайную прокси из всех источников
        proxy = await self.get_random_proxy_from_strategy(strategy_id)

        if proxy:
            # Добавляем логирование использования
            await self._log_proxy_usage(strategy_id, profile_id, proxy)

        return proxy

    async def _log_proxy_usage(
        self, strategy_id: str, profile_id: str, proxy_data: Dict[str, Any]
    ):
        """Логирование использования прокси"""

        # Находим StrategyProxy для обновления статистики
        proxy_result = await self.session.execute(
            select(StrategyProxy).where(
                and_(
                    StrategyProxy.strategy_id == strategy_id,
                    StrategyProxy.host == proxy_data["host"],
                    StrategyProxy.port == proxy_data["port"],
                )
            )
        )
        proxy = proxy_result.scalar_one_or_none()

        if proxy:
            # Обновляем статистику использования
            proxy.total_uses += 1
            proxy.last_used_at = datetime.utcnow()
            await self.session.commit()

    async def get_source_preview(
        self, strategy_id: str, source_id: str
    ) -> Dict[str, Any]:
        """Получение превью прокси из динамического источника"""

        try:
            # Получаем источник
            source_result = await self.session.execute(
                select(StrategyProxySource).where(
                    and_(
                        StrategyProxySource.id == source_id,
                        StrategyProxySource.strategy_id == strategy_id,
                        StrategyProxySource.is_active == True,
                    )
                )
            )
            source = source_result.scalar_one_or_none()

            if not source:
                return {"success": False, "error": "Источник не найден"}

            # Проверяем, что это динамический источник
            if source.source_type not in ["url_import", "google_docs", "google_sheets"]:
                return {"success": False, "error": "Источник не является динамическим"}

            # Получаем свежие данные
            fresh_data = await self._fetch_data_by_source_type(
                source.source_type, source.source_url
            )

            if not fresh_data:
                return {
                    "success": False,
                    "error": "Не удалось получить данные из источника",
                }

            # Парсим прокси
            parsed_proxies = ProxyParser.parse_proxy_list(fresh_data)

            return {
                "success": True,
                "source_id": source_id,
                "source_type": source.source_type,
                "source_url": source.source_url,
                "total_count": len(parsed_proxies),
                "proxies": parsed_proxies,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": f"Ошибка получения превью: {str(e)}"}

    async def update_proxy_status(
        self,
        strategy_id: str,
        proxy_id: str,
        status: str,
        response_time: Optional[int] = None,
    ) -> bool:
        """Обновление статуса прокси"""

        try:
            # Получаем прокси
            proxy_result = await self.session.execute(
                select(StrategyProxy).where(
                    and_(
                        StrategyProxy.id == proxy_id,
                        StrategyProxy.strategy_id == strategy_id,
                    )
                )
            )
            proxy = proxy_result.scalar_one_or_none()

            if not proxy:
                return False

            # Обновляем статус
            proxy.status = status
            if response_time is not None:
                proxy.response_time = response_time

            await self.session.commit()
            return True

        except Exception as e:
            await self.session.rollback()
            print(f"Error updating proxy status: {e}")
            return False

    async def update_proxy_success_rate(
        self, strategy_id: str, proxy_id: str, success: bool
    ) -> bool:
        """Обновление статистики успешности прокси"""

        try:
            # Получаем прокси
            proxy_result = await self.session.execute(
                select(StrategyProxy).where(
                    and_(
                        StrategyProxy.id == proxy_id,
                        StrategyProxy.strategy_id == strategy_id,
                    )
                )
            )
            proxy = proxy_result.scalar_one_or_none()

            if not proxy:
                return False

            # Обновляем статистику
            if success:
                proxy.successful_uses += 1
            else:
                proxy.failed_uses += 1

            # Пересчитываем success_rate
            total_attempts = proxy.successful_uses + proxy.failed_uses
            if total_attempts > 0:
                proxy.success_rate = int((proxy.successful_uses / total_attempts) * 100)

            await self.session.commit()
            return True

        except Exception as e:
            await self.session.rollback()
            print(f"Error updating proxy success rate: {e}")
            return False

    async def delete_proxy(self, strategy_id: str, proxy_id: str) -> bool:
        """Удаление прокси из стратегии"""

        try:
            # Получаем прокси
            proxy_result = await self.session.execute(
                select(StrategyProxy).where(
                    and_(
                        StrategyProxy.id == proxy_id,
                        StrategyProxy.strategy_id == strategy_id,
                    )
                )
            )
            proxy = proxy_result.scalar_one_or_none()

            if not proxy:
                return False

            # Удаляем прокси
            await self.session.delete(proxy)
            await self.session.commit()
            return True

        except Exception as e:
            await self.session.rollback()
            print(f"Error deleting proxy: {e}")
            return False

    async def get_proxy_by_id(
        self, strategy_id: str, proxy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Получение прокси по ID"""

        try:
            proxy_result = await self.session.execute(
                select(StrategyProxy).where(
                    and_(
                        StrategyProxy.id == proxy_id,
                        StrategyProxy.strategy_id == strategy_id,
                    )
                )
            )
            proxy = proxy_result.scalar_one_or_none()

            if not proxy:
                return None

            return {
                "id": str(proxy.id),
                "host": proxy.host,
                "port": proxy.port,
                "username": proxy.username,
                "password": proxy.password,
                "protocol": proxy.protocol,
                "status": proxy.status,
                "success_rate": proxy.success_rate,
                "total_uses": proxy.total_uses,
                "successful_uses": proxy.successful_uses,
                "failed_uses": proxy.failed_uses,
                "response_time": proxy.response_time,
                "last_used_at": (
                    proxy.last_used_at.isoformat() if proxy.last_used_at else None
                ),
                "created_at": proxy.created_at.isoformat(),
            }

        except Exception as e:
            print(f"Error getting proxy by ID: {e}")
            return None
