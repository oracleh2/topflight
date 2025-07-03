import asyncio
import random
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import structlog

from app.models import Profile, ParseResult, Task, UserKeyword, DeviceType
from app.database import async_session_maker
from .browser_manager import BrowserManager

logger = structlog.get_logger(__name__)


class YandexParser:
    """Парсер поисковой выдачи Яндекса с поддержкой разных типов устройств"""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.browser_manager = BrowserManager(db_session)

        # URL для разных типов устройств
        self.search_urls = {
            DeviceType.DESKTOP: "https://yandex.ru/search/",
            DeviceType.MOBILE: "https://yandex.ru/search/touch/"
        }

        # Селекторы для разных типов устройств
        self.selectors = {
            DeviceType.DESKTOP: {
                "search_input": "input[name='text']",
                "search_button": "button[type='submit']",
                "results_container": ".serp-list",
                "result_item": ".serp-item",
                "result_link": "h2 a, .organic__url a",
                "result_title": "h2, .organic__title-wrapper",
                "result_snippet": ".text-container, .organic__text",
                "next_page": ".pager__item_kind_next",
                "captcha": ".captcha, .checkbox__box",
                "no_results": ".misspell, .not-found"
            },
            DeviceType.MOBILE: {
                "search_input": "input[name='text']",
                "search_button": "button[type='submit']",
                "results_container": ".serp-list, .content__left",
                "result_item": ".serp-item, .organic",
                "result_link": ".organic__url a, .path__item a",
                "result_title": ".organic__title-wrapper, .serp-item__title",
                "result_snippet": ".organic__text, .serp-item__text",
                "next_page": ".pager__item_kind_next, .button2_theme_next",
                "captcha": ".captcha, .checkbox__box",
                "no_results": ".misspell, .not-found"
            }
        }

    async def get_session(self) -> AsyncSession:
        """Получает сессию БД"""
        if self.db:
            return self.db
        else:
            async with async_session_maker() as session:
                return session

    async def parse_serp(self, keyword: str, profile: Profile, pages: int = 10,
                         region_code: str = "213") -> List[ParseResult]:
        """Парсинг поисковой выдачи Яндекса"""
        session = await self.get_session()
        results = []

        try:
            device_type = profile.device_type
            selectors = self.selectors[device_type]
            search_url = self.search_urls[device_type]

            logger.info("Starting SERP parsing",
                        keyword=keyword,
                        profile_id=str(profile.id),
                        device_type=device_type.value,
                        region=region_code)

            async with async_playwright() as p:
                browser = await self.browser_manager._launch_browser(p, profile)
                context = await self.browser_manager._create_context(browser, profile)
                page = await context.new_page()

                try:
                    # Устанавливаем регион в куки
                    await self._set_region(page, region_code)

                    # Переходим на страницу поиска
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)

                    # Проверяем на блокировки
                    if await self._check_for_blocks(page, selectors):
                        await self.browser_manager.mark_profile_corrupted(
                            profile, "Captcha or blocking detected during search"
                        )
                        return []

                    # Вводим поисковый запрос
                    await self._perform_search(page, keyword, selectors, device_type)

                    # Парсим результаты по страницам
                    for page_num in range(1, pages + 1):
                        try:
                            logger.info("Parsing page",
                                        keyword=keyword,
                                        page_number=page_num,
                                        device_type=device_type.value)

                            # Ждем загрузки результатов
                            await page.wait_for_selector(selectors["results_container"],
                                                         timeout=15000)

                            # Проверяем на блокировки на странице результатов
                            if await self._check_for_blocks(page, selectors):
                                logger.warning("Blocking detected on results page",
                                               page_number=page_num)
                                break

                            # Парсим результаты текущей страницы
                            page_results = await self._parse_page_results(
                                page, selectors, keyword, page_num, device_type
                            )
                            results.extend(page_results)

                            # Переходим на следующую страницу
                            if page_num < pages:
                                if not await self._go_to_next_page(page, selectors, device_type):
                                    logger.info("No more pages available", page_number=page_num)
                                    break

                        except Exception as e:
                            logger.error("Error parsing page",
                                         page_number=page_num, error=str(e))
                            continue

                    # Обновляем статистику использования профиля
                    await self._update_profile_usage(profile, True)

                except Exception as e:
                    await self._update_profile_usage(profile, False)
                    logger.error("Error during SERP parsing", error=str(e))
                    raise

                finally:
                    await browser.close()

            logger.info("SERP parsing completed",
                        keyword=keyword,
                        results_count=len(results),
                        device_type=device_type.value)

            return results

        except Exception as e:
            logger.error("Failed to parse SERP",
                         keyword=keyword,
                         error=str(e))
            raise

    async def _set_region(self, page: Page, region_code: str):
        """Устанавливает регион поиска"""
        try:
            # Устанавливаем куки региона для Яндекса
            await page.context.add_cookies([
                {
                    "name": "yp",
                    "value": f"{int(datetime.now().timestamp()) + 31536000}.gpauto.55_755065:37_618050:100:1:1640995200",
                    "domain": ".yandex.ru",
                    "path": "/"
                },
                {
                    "name": "yandex_gid",
                    "value": region_code,
                    "domain": ".yandex.ru",
                    "path": "/"
                },
                {
                    "name": "L",
                    "value": f"YXJ1PTE2NDEwMzc5MDA=.czE9ZXdvZ2gyOGw=.{region_code}",
                    "domain": ".yandex.ru",
                    "path": "/"
                }
            ])

            logger.debug("Region set", region_code=region_code)

        except Exception as e:
            logger.warning("Failed to set region", region_code=region_code, error=str(e))

    async def _check_for_blocks(self, page: Page, selectors: Dict[str, str]) -> bool:
        """Проверяет наличие капчи или блокировок"""
        try:
            # Проверяем наличие капчи
            captcha_element = await page.query_selector(selectors["captcha"])
            if captcha_element:
                logger.warning("Captcha detected")
                return True

            # Проверяем URL на признаки блокировки
            current_url = page.url
            if any(keyword in current_url.lower() for keyword in
                   ["captcha", "blocked", "robot", "verify"]):
                logger.warning("Blocking URL detected", url=current_url)
                return True

            # Проверяем заголовок страницы
            title = await page.title()
            if any(keyword in title.lower() for keyword in
                   ["captcha", "blocked", "robot", "verify", "ошибка"]):
                logger.warning("Blocking title detected", title=title)
                return True

            return False

        except Exception as e:
            logger.error("Error checking for blocks", error=str(e))
            return False

    async def _perform_search(self, page: Page, keyword: str, selectors: Dict[str, str],
                              device_type: DeviceType):
        """Выполняет поисковый запрос"""
        try:
            # Находим поле поиска
            search_input = await page.wait_for_selector(selectors["search_input"],
                                                        timeout=10000)

            # Очищаем поле и вводим запрос по частям (имитация печати)
            await search_input.click()
            await search_input.fill("")

            # Печатаем запрос с человеческими задержками
            for char in keyword:
                await search_input.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # Небольшая пауза перед отправкой
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Отправляем запрос (Enter или кнопка)
            if device_type == DeviceType.MOBILE or random.random() < 0.3:
                # На мобильных или иногда на десктопе нажимаем кнопку
                search_button = await page.query_selector(selectors["search_button"])
                if search_button:
                    await search_button.click()
                else:
                    await search_input.press("Enter")
            else:
                await search_input.press("Enter")

            # Ждем загрузки результатов
            await page.wait_for_load_state("networkidle")

            logger.debug("Search performed", keyword=keyword)

        except Exception as e:
            logger.error("Failed to perform search", keyword=keyword, error=str(e))
            raise

    async def _parse_page_results(self, page: Page, selectors: Dict[str, str],
                                  keyword: str, page_number: int,
                                  device_type: DeviceType) -> List[ParseResult]:
        """Парсит результаты с текущей страницы"""
        results = []

        try:
            # Ждем появления результатов
            await asyncio.sleep(random.uniform(1, 3))

            # Получаем все элементы результатов
            result_elements = await page.query_selector_all(selectors["result_item"])

            if not result_elements:
                logger.warning("No result elements found",
                               page_number=page_number,
                               device_type=device_type.value)
                return results

            for idx, element in enumerate(result_elements):
                try:
                    # Извлекаем данные из элемента результата
                    result_data = await self._extract_result_data(
                        element, selectors, keyword, page_number, idx + 1, device_type
                    )

                    if result_data:
                        results.append(result_data)

                except Exception as e:
                    logger.warning("Failed to extract result data",
                                   index=idx, error=str(e))
                    continue

            logger.debug("Page results parsed",
                         page_number=page_number,
                         results_count=len(results))

            return results

        except Exception as e:
            logger.error("Failed to parse page results",
                         page_number=page_number, error=str(e))
            return results

    async def _extract_result_data(self, element, selectors: Dict[str, str],
                                   keyword: str, page_number: int, position_on_page: int,
                                   device_type: DeviceType) -> Optional[ParseResult]:
        """Извлекает данные из элемента результата поиска"""
        try:
            # Извлекаем ссылку
            link_element = await element.query_selector(selectors["result_link"])
            url = ""
            if link_element:
                url = await link_element.get_attribute("href")
                if url and not url.startswith("http"):
                    url = urljoin("https://yandex.ru", url)

            # Пропускаем рекламные и служебные результаты
            if not url or self._is_advertisement_or_service(url):
                return None

            # Извлекаем заголовок
            title_element = await element.query_selector(selectors["result_title"])
            title = ""
            if title_element:
                title = await title_element.inner_text()
                title = title.strip()

            # Извлекаем сниппет
            snippet_element = await element.query_selector(selectors["result_snippet"])
            snippet = ""
            if snippet_element:
                snippet = await snippet_element.inner_text()
                snippet = snippet.strip()

            # Извлекаем домен
            domain = ""
            if url:
                try:
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc.lower()
                    # Убираем www
                    if domain.startswith("www."):
                        domain = domain[4:]
                except:
                    pass

            # Вычисляем позицию
            position = (page_number - 1) * 10 + position_on_page

            # Создаем результат
            result = ParseResult(
                keyword=keyword,
                position=position,
                url=url,
                title=title,
                snippet=snippet,
                domain=domain,
                page_number=page_number,
                parsed_at=datetime.utcnow()
            )

            logger.debug("Result extracted",
                         position=position,
                         domain=domain,
                         device_type=device_type.value)

            return result

        except Exception as e:
            logger.warning("Failed to extract result data", error=str(e))
            return None

    def _is_advertisement_or_service(self, url: str) -> bool:
        """Проверяет является ли URL рекламой или служебным результатом"""
        if not url:
            return True

        # Исключаем рекламные домены и служебные страницы Яндекса
        exclude_patterns = [
            "an.yandex.ru",
            "yabs.yandex.ru",
            "direct.yandex.ru",
            "market-click.yandex.ru",
            "clck.yandex.ru",
            "/redir/",
            "/track/",
            "yandex.ru/search",
            "yandex.ru/images",
            "yandex.ru/video",
            "yandex.ru/maps"
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in exclude_patterns)

    async def _go_to_next_page(self, page: Page, selectors: Dict[str, str],
                               device_type: DeviceType) -> bool:
        """Переходит на следующую страницу результатов"""
        try:
            # Ищем ссылку на следующую страницу
            next_link = await page.query_selector(selectors["next_page"])

            if not next_link:
                return False

            # Проверяем что ссылка активна
            is_disabled = await next_link.get_attribute("aria-disabled")
            if is_disabled == "true":
                return False

            # Скроллим к ссылке для мобильных устройств
            if device_type == DeviceType.MOBILE:
                await next_link.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.5, 1))

            # Кликаем по ссылке
            await next_link.click()

            # Ждем загрузки новой страницы
            await page.wait_for_load_state("networkidle")

            # Дополнительная пауза
            await asyncio.sleep(random.uniform(2, 4))

            logger.debug("Navigated to next page", device_type=device_type.value)
            return True

        except Exception as e:
            logger.warning("Failed to navigate to next page",
                           device_type=device_type.value, error=str(e))
            return False

    async def _update_profile_usage(self, profile: Profile, success: bool):
        """Обновляет статистику использования профиля"""
        session = await self.get_session()

        try:
            profile.total_usage_count += 1
            profile.last_used = datetime.utcnow()

            # Обновляем success rate
            if profile.total_usage_count > 0:
                if success:
                    current_success = profile.success_rate * (profile.total_usage_count - 1)
                    profile.success_rate = (current_success + 1) / profile.total_usage_count
                else:
                    current_success = profile.success_rate * (profile.total_usage_count - 1)
                    profile.success_rate = current_success / profile.total_usage_count

            await session.commit()

        except Exception as e:
            logger.error("Failed to update profile usage",
                         profile_id=str(profile.id), error=str(e))

    async def check_position(self, keyword: str, target_domain: str, profile: Profile,
                             region_code: str = "213", max_pages: int = 10) -> Optional[int]:
        """Проверяет позицию конкретного домена по ключевому слову"""
        try:
            results = await self.parse_serp(keyword, profile, max_pages, region_code)

            # Ищем домен в результатах
            for result in results:
                if result.domain and target_domain.lower() in result.domain.lower():
                    logger.info("Position found",
                                keyword=keyword,
                                domain=target_domain,
                                position=result.position)
                    return result.position

            logger.info("Domain not found in results",
                        keyword=keyword,
                        domain=target_domain,
                        max_pages=max_pages)
            return None

        except Exception as e:
            logger.error("Failed to check position",
                         keyword=keyword,
                         domain=target_domain,
                         error=str(e))
            return None