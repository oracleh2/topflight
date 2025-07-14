# backend/app/core/proxy_service.py

import random
import re
from typing import List, Dict, Any, Optional

import aiohttp
import structlog
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.profile import Profile
from ..models.proxy import (
    ProjectProxy,
    ProxyImportHistory,
    ProxyType,
    ProxyProtocol,
    ProxyStatus,
)

logger = structlog.get_logger(__name__)


class ProxyParser:
    """Парсер различных форматов прокси"""

    # Популярные форматы прокси
    PROXY_PATTERNS = [
        # http://user:pass@host:port
        r"^(https?)://([^:]+):([^@]+)@([^:]+):(\d+)$",
        # http://host:port@user:pass
        r"^(https?)://([^:]+):(\d+)@([^:]+):([^@]+)$",
        # user:pass@host:port
        r"^([^:]+):([^@]+)@([^:]+):(\d+)$",
        # host:port:user:pass
        r"^([^:]+):(\d+):([^:]+):(.+)$",
        # host:port@user:pass
        r"^([^:]+):(\d+)@([^:]+):(.+)$",
        # host:port (без авторизации)
        r"^([^:]+):(\d+)$",
        # socks5://user:pass@host:port
        r"^(socks[45])://([^:]+):([^@]+)@([^:]+):(\d+)$",
        # socks5://host:port
        r"^(socks[45])://([^:]+):(\d+)$",
    ]

    @classmethod
    def parse_proxy(cls, proxy_string: str) -> Optional[Dict[str, Any]]:
        """Парсит строку прокси в структурированный формат"""
        proxy_string = proxy_string.strip()

        for pattern in cls.PROXY_PATTERNS:
            match = re.match(pattern, proxy_string, re.IGNORECASE)
            if match:
                groups = match.groups()

                # Определяем протокол
                protocol = "http"  # по умолчанию
                if len(groups) >= 1 and groups[0]:
                    if groups[0].lower() in ["socks4", "socks5"]:
                        protocol = groups[0].lower()
                    elif groups[0].lower() == "https":
                        protocol = "https"

                # Различные варианты парсинга в зависимости от формата
                if (
                    len(groups) == 5
                    and groups[0]
                    and groups[0].lower() in ["http", "https", "socks4", "socks5"]
                ):
                    # Формат: protocol://user:pass@host:port
                    return {
                        "protocol": protocol,
                        "host": groups[3],
                        "port": int(groups[4]),
                        "username": groups[1],
                        "password": groups[2],
                    }
                elif len(groups) == 4 and ":" in proxy_string and "@" in proxy_string:
                    # Формат: user:pass@host:port
                    return {
                        "protocol": protocol,
                        "host": groups[2],
                        "port": int(groups[3]),
                        "username": groups[0],
                        "password": groups[1],
                    }
                elif len(groups) == 4:
                    # Формат: host:port:user:pass
                    return {
                        "protocol": protocol,
                        "host": groups[0],
                        "port": int(groups[1]),
                        "username": groups[2],
                        "password": groups[3],
                    }
                elif len(groups) == 2:
                    # Формат: host:port (без авторизации)
                    return {
                        "protocol": protocol,
                        "host": groups[0],
                        "port": int(groups[1]),
                        "username": None,
                        "password": None,
                    }

        return None

    @classmethod
    def parse_proxy_list(cls, proxy_text: str) -> List[Dict[str, Any]]:
        """Парсит список прокси из текста"""
        lines = proxy_text.strip().split("\n")
        parsed_proxies = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parsed = cls.parse_proxy(line)
            if parsed:
                parsed["original_string"] = line
                parsed_proxies.append(parsed)

        return parsed_proxies


class ProxyService:
    """Сервис для управления прокси"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def import_proxies_manual(
        self, user_id: str, domain_id: str, proxy_type: ProxyType, proxy_text: str
    ) -> Dict[str, Any]:
        """Импорт прокси из текста"""
        try:
            # Парсим прокси
            parsed_proxies = ProxyParser.parse_proxy_list(proxy_text)

            if not parsed_proxies:
                return {
                    "success": False,
                    "error": "Не удалось распознать ни одной прокси",
                }

            # Сохраняем историю импорта
            import_record = ProxyImportHistory(
                user_id=user_id,
                domain_id=domain_id,
                proxy_type=proxy_type.value,
                import_method="manual",
                total_imported=len(parsed_proxies),
            )
            self.session.add(import_record)

            # Добавляем прокси
            successful = 0
            failed = 0
            errors = []

            for proxy_data in parsed_proxies:
                try:
                    # Проверяем, не существует ли уже такая прокси
                    existing = await self.session.execute(
                        select(ProjectProxy).where(
                            and_(
                                ProjectProxy.user_id == user_id,
                                ProjectProxy.domain_id == domain_id,
                                ProjectProxy.proxy_type == proxy_type.value,
                                ProjectProxy.host == proxy_data["host"],
                                ProjectProxy.port == proxy_data["port"],
                            )
                        )
                    )

                    if existing.scalar_one_or_none():
                        failed += 1
                        errors.append(
                            f"Прокси {proxy_data['host']}:{proxy_data['port']} уже существует"
                        )
                        continue

                    proxy = ProjectProxy(
                        user_id=user_id,
                        domain_id=domain_id,
                        proxy_type=proxy_type.value,
                        host=proxy_data["host"],
                        port=proxy_data["port"],
                        username=proxy_data.get("username"),
                        password=proxy_data.get("password"),
                        protocol=proxy_data["protocol"],
                    )

                    self.session.add(proxy)
                    successful += 1

                except Exception as e:
                    failed += 1
                    errors.append(
                        f"Ошибка добавления {proxy_data.get('original_string', '')}: {str(e)}"
                    )

            # Обновляем статистику импорта
            import_record.successful_imported = successful
            import_record.failed_imported = failed
            import_record.error_details = {"errors": errors}

            await self.session.commit()

            return {
                "success": True,
                "total": len(parsed_proxies),
                "successful": successful,
                "failed": failed,
                "errors": errors,
            }

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to import proxies", error=str(e))
            return {"success": False, "error": f"Ошибка импорта: {str(e)}"}

    async def import_proxies_from_url(
        self, user_id: str, domain_id: str, proxy_type: ProxyType, url: str
    ) -> Dict[str, Any]:
        """Импорт прокси по URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Ошибка загрузки URL: HTTP {response.status}",
                        }

                    content = await response.text()

            # Сохраняем источник
            import_record = ProxyImportHistory(
                user_id=user_id,
                domain_id=domain_id,
                proxy_type=proxy_type.value,
                import_method="url",
                source_url=url,
            )
            self.session.add(import_record)

            # Импортируем как текст
            result = await self.import_proxies_manual(
                user_id, domain_id, proxy_type, content
            )

            # Обновляем источник в истории
            import_record.total_imported = result.get("total", 0)
            import_record.successful_imported = result.get("successful", 0)
            import_record.failed_imported = result.get("failed", 0)

            await self.session.commit()

            return result

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to import proxies from URL", url=url, error=str(e))
            return {"success": False, "error": f"Ошибка загрузки URL: {str(e)}"}

    async def get_random_proxy(
        self, user_id: str, domain_id: str, proxy_type: ProxyType
    ) -> Optional[ProjectProxy]:
        """Получает случайную рабочую прокси"""
        try:
            result = await self.session.execute(
                select(ProjectProxy).where(
                    and_(
                        ProjectProxy.user_id == user_id,
                        ProjectProxy.domain_id == domain_id,
                        ProjectProxy.proxy_type == proxy_type.value,
                        ProjectProxy.status == "active",
                    )
                )
            )

            proxies = result.scalars().all()

            if not proxies:
                return None

            # Выбираем случайную прокси с учетом статистики
            # Приоритет прокси с лучшим success_rate
            weighted_proxies = []
            for proxy in proxies:
                weight = max(1, proxy.success_rate)  # Минимальный вес 1
                weighted_proxies.extend([proxy] * weight)

            return random.choice(weighted_proxies) if weighted_proxies else None

        except Exception as e:
            logger.error("Failed to get random proxy", error=str(e))
            return None

    async def assign_warmup_proxy(
        self, profile_id: str, user_id: str, domain_id: str
    ) -> Optional[ProjectProxy]:
        """Назначает прокси для нагула профиля"""
        try:
            # Получаем случайную прокси для нагула
            proxy = await self.get_random_proxy(user_id, domain_id, ProxyType.WARMUP)

            if not proxy:
                return None

            # Обновляем профиль
            await self.session.execute(
                update(Profile)
                .where(Profile.id == profile_id)
                .values(assigned_warmup_proxy_id=proxy.id)
            )

            await self.session.commit()

            logger.info(
                "Assigned warmup proxy to profile",
                profile_id=profile_id,
                proxy_id=str(proxy.id),
            )

            return proxy

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to assign warmup proxy", error=str(e))
            return None

    async def get_parsing_proxy(
        self,
        profile_id: str,
        user_id: str,
        domain_id: str,
        use_warmup_proxy: bool = True,
    ) -> Optional[ProjectProxy]:
        """Получает прокси для замера позиций"""
        try:
            if use_warmup_proxy:
                # Пытаемся использовать прокси из профиля
                result = await self.session.execute(
                    select(Profile)
                    .options(selectinload(Profile.assigned_warmup_proxy))
                    .where(Profile.id == profile_id)
                )

                profile = result.scalar_one_or_none()
                if profile and profile.assigned_warmup_proxy:
                    # Проверяем, что прокси рабочая
                    if profile.assigned_warmup_proxy.status == "active":
                        return profile.assigned_warmup_proxy

            # Если прокси профиля недоступна, берем случайную для парсинга
            return await self.get_random_proxy(user_id, domain_id, ProxyType.PARSING)

        except Exception as e:
            logger.error("Failed to get parsing proxy", error=str(e))
            return None

    async def update_proxy_stats(
        self, proxy_id: str, success: bool, response_time: int = None
    ):
        """Обновляет статистику использования прокси"""
        try:
            proxy = await self.session.get(ProjectProxy, proxy_id)
            if not proxy:
                return

            proxy.total_uses += 1

            if success:
                proxy.successful_uses = getattr(proxy, "successful_uses", 0) + 1
            else:
                proxy.failed_uses += 1

            # Обновляем success_rate
            total = proxy.total_uses
            successful = getattr(proxy, "successful_uses", total - proxy.failed_uses)
            proxy.success_rate = int((successful / total) * 100) if total > 0 else 100

            if response_time:
                proxy.response_time = response_time

            # Если success_rate слишком низкий, помечаем как неактивную
            if proxy.success_rate < 50 and proxy.total_uses > 10:
                proxy.status = "inactive"

            await self.session.commit()

        except Exception as e:
            logger.error(
                "Failed to update proxy stats", proxy_id=proxy_id, error=str(e)
            )

    async def get_domain_proxies(
        self, user_id: str, domain_id: str
    ) -> List[Dict[str, Any]]:
        """Получает все прокси домена"""
        try:
            result = await self.session.execute(
                select(ProjectProxy)
                .where(
                    and_(
                        ProjectProxy.user_id == user_id,
                        ProjectProxy.domain_id == domain_id,
                    )
                )
                .order_by(ProjectProxy.created_at.desc())
            )

            proxies = result.scalars().all()

            proxy_list = []
            for proxy in proxies:
                proxy_data = {
                    "id": str(proxy.id),
                    "host": proxy.host,
                    "port": proxy.port,
                    "proxy_type": proxy.proxy_type,
                    "protocol": proxy.protocol,
                    "status": proxy.status,
                    "success_rate": proxy.success_rate,
                    "total_uses": proxy.total_uses,
                    "response_time": proxy.response_time,
                    "country": proxy.country,
                    "last_check": (
                        proxy.last_check.isoformat() if proxy.last_check else None
                    ),
                    "created_at": proxy.created_at.isoformat(),
                }
                proxy_list.append(proxy_data)

            return proxy_list

        except Exception as e:
            logger.error("Failed to get domain proxies", error=str(e))
            return []

    async def delete_proxy(self, user_id: str, proxy_id: str) -> bool:
        """Удаляет прокси"""
        try:
            result = await self.session.execute(
                select(ProjectProxy).where(
                    and_(ProjectProxy.id == proxy_id, ProjectProxy.user_id == user_id)
                )
            )

            proxy = result.scalar_one_or_none()
            if not proxy:
                return False

            await self.session.delete(proxy)
            await self.session.commit()

            return True

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to delete proxy", proxy_id=proxy_id, error=str(e))
            return False
