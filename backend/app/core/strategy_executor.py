# backend/app/core/strategy_executor.py
import random
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page
import structlog

from app.core.browser_manager import BrowserManager
from app.models import Profile, Task
from app.models.profile import DeviceType

logger = structlog.get_logger()


class StrategyExecutor:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def execute_warmup_strategy(self, task: Task, session) -> Dict[str, Any]:
        """Выполнение стратегии прогрева профилей"""

        execution_data = task.parameters.get("execution_data", {})
        actions = execution_data.get("actions", [])
        config = execution_data.get("config", {})

        # Получаем или создаем профиль - исправляем метод
        device_type_str = task.parameters.get("device_type", "desktop")
        device_type = DeviceType(device_type_str)

        profile = await self.browser_manager.get_ready_profile(device_type=device_type)

        if not profile:
            profile = await self.browser_manager.create_profile(device_type=device_type)

        results = {
            "profile_id": str(profile.id),
            "actions_completed": 0,
            "actions_failed": 0,
            "total_actions": len(actions),
            "details": [],
        }

        try:
            async with async_playwright() as p:
                # Запускаем браузер с профилем
                browser = await self._launch_browser_with_profile(p, profile)
                context = (
                    browser.contexts[0]
                    if browser.contexts
                    else await browser.new_context()
                )
                page = await context.new_page()

                # Выполняем действия согласно стратегии
                for i, action in enumerate(actions):
                    try:
                        action_result = await self._execute_warmup_action(
                            page, action, config
                        )

                        results["details"].append(
                            {
                                "action_index": i,
                                "action_type": action["type"],
                                "target": action.get("target", action.get("keyword")),
                                "success": action_result["success"],
                                "details": action_result.get("details", ""),
                            }
                        )

                        if action_result["success"]:
                            results["actions_completed"] += 1
                        else:
                            results["actions_failed"] += 1

                        # Пауза между действиями
                        delay_config = config.get("general", {}).get(
                            "delay_between_actions", {"min": 2, "max": 8}
                        )
                        await asyncio.sleep(
                            random.uniform(delay_config["min"], delay_config["max"])
                        )

                    except Exception as e:
                        logger.error(
                            "Failed to execute warmup action",
                            action_index=i,
                            action=action,
                            error=str(e),
                        )
                        results["actions_failed"] += 1
                        results["details"].append(
                            {
                                "action_index": i,
                                "action_type": action["type"],
                                "success": False,
                                "error": str(e),
                            }
                        )

                # Сохраняем обновленные cookies
                cookies = await context.cookies()
                profile.cookies = cookies
                profile.last_used = datetime.now(timezone.utc)
                profile.warmup_sites_visited += results["actions_completed"]

                await browser.close()
                await session.commit()

        except Exception as e:
            logger.error(
                "Strategy warmup execution failed",
                profile_id=str(profile.id),
                error=str(e),
            )
            results["error"] = str(e)
            raise

        return results

    async def _execute_warmup_action(
        self, page: Page, action: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Выполнение одного действия прогрева"""

        action_type = action["type"]

        if action_type == "direct_visit":
            return await self._execute_direct_visit(page, action, config)
        elif action_type == "search_visit":
            return await self._execute_search_visit(page, action, config)
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    async def _execute_direct_visit(
        self, page: Page, action: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Прямое посещение сайта"""

        target_url = action["target"]
        direct_config = config.get("direct_config", {})

        try:
            # Переходим на сайт
            await page.goto(target_url, wait_until="networkidle", timeout=30000)

            # Имитируем человеческое поведение
            behavior_result = await self._simulate_human_behavior_on_site(
                page, direct_config
            )

            return {
                "success": True,
                "details": f"Visited {target_url}",
                "behavior": behavior_result,
            }

        except Exception as e:
            logger.warning("Direct visit failed", url=target_url, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "details": f"Failed to visit {target_url}",
            }

    async def _execute_search_visit(
        self, page: Page, action: Dict, config: Dict
    ) -> Dict[str, Any]:
        """Поиск в Яндексе и переход на результат"""

        keyword = action["keyword"]
        yandex_domain = action.get("yandex_domain", "yandex.ru")
        search_config = config.get("search_config", {})

        try:
            # Переходим в Яндекс
            search_url = f"https://{yandex_domain}/search/?text={keyword}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)

            # Проверяем наличие капчи
            captcha_present = await page.query_selector(".captcha") is not None
            if captcha_present:
                return {
                    "success": False,
                    "error": "Captcha detected",
                    "details": f"Search for '{keyword}' blocked by captcha",
                }

            # Скроллим страницу результатов
            await self._scroll_serp_naturally(page)

            # Решаем, кликать ли на результат
            click_probability = search_config.get("click_probability", 0.7)
            if random.random() < click_probability:
                click_result = await self._click_search_result(page, search_config)
                return {
                    "success": True,
                    "details": f"Searched '{keyword}' and clicked result",
                    "click_result": click_result,
                }
            else:
                return {
                    "success": True,
                    "details": f"Searched '{keyword}' without clicking",
                }

        except Exception as e:
            logger.warning("Search visit failed", keyword=keyword, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "details": f"Failed to search for '{keyword}'",
            }

    async def _simulate_human_behavior_on_site(
        self, page: Page, config: Dict
    ) -> Dict[str, Any]:
        """Имитация человеческого поведения на сайте"""

        behavior_results = {"time_spent": 0, "scrolled": False, "clicked": False}

        # Время на сайте
        time_config = config.get("time_per_site", {"min": 10, "max": 45})
        time_to_spend = random.uniform(time_config["min"], time_config["max"])

        # Скроллинг
        scroll_probability = config.get("scroll_probability", 0.8)
        if random.random() < scroll_probability:
            await self._scroll_page_naturally(page)
            behavior_results["scrolled"] = True

        # Случайные клики
        click_probability = config.get("click_probability", 0.3)
        if random.random() < click_probability:
            clicked = await self._random_click(page)
            behavior_results["clicked"] = clicked

        # Ждем
        await asyncio.sleep(time_to_spend)
        # Исправляем тип - конвертируем в int
        behavior_results["time_spent"] = int(time_to_spend)

        return behavior_results

    async def _scroll_serp_naturally(self, page: Page):
        """Естественный скроллинг страницы результатов поиска"""

        # Получаем высоту страницы
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")

        if page_height <= viewport_height:
            return

        # Скроллим по частям
        scroll_steps = random.randint(3, 8)
        step_size = page_height // scroll_steps

        for i in range(scroll_steps):
            scroll_to = min(step_size * (i + 1), page_height)
            await page.evaluate(f"window.scrollTo(0, {scroll_to})")
            await asyncio.sleep(random.uniform(0.5, 2.0))

    async def _scroll_page_naturally(self, page: Page):
        """Естественный скроллинг обычной страницы"""

        # Несколько случайных скроллов
        scroll_count = random.randint(2, 5)

        for _ in range(scroll_count):
            # Скроллим на случайное расстояние
            scroll_distance = random.randint(200, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(1, 3))

    async def _click_search_result(self, page: Page, config: Dict) -> Dict[str, Any]:
        """Клик по результату поиска"""

        try:
            # Ищем ссылки результатов поиска
            result_links = await page.query_selector_all(".organic__url")

            if not result_links:
                # Альтернативный селектор
                result_links = await page.query_selector_all(".Path-Item")

            if result_links:
                # Выбираем случайный результат (предпочитаем первые)
                weights = [max(1, 10 - i) for i in range(len(result_links))]
                selected_link = random.choices(result_links, weights=weights)[0]

                # Кликаем
                await selected_link.click()
                await page.wait_for_load_state("networkidle", timeout=15000)

                # Проводим время на сайте
                time_on_site = random.uniform(5, 20)
                await asyncio.sleep(time_on_site)

                return {
                    "success": True,
                    "time_spent": int(time_on_site),
                    "url": page.url,
                }
            else:
                return {"success": False, "error": "No search results found to click"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _random_click(self, page: Page) -> bool:
        """Случайный клик по элементу на странице"""

        try:
            # Ищем кликабельные элементы
            clickable_elements = await page.query_selector_all("a, button, [onclick]")

            if clickable_elements:
                # Фильтруем элементы, исключая навигацию и формы
                safe_elements = []
                for element in clickable_elements:
                    try:
                        element_text = await element.inner_text()
                        element_class = await element.get_attribute("class") or ""

                        # Пропускаем элементы навигации, форм и важные кнопки
                        if not any(
                            word in element_text.lower()
                            for word in [
                                "купить",
                                "заказать",
                                "отправить",
                                "submit",
                                "delete",
                                "удалить",
                            ]
                        ):
                            if not any(
                                cls in element_class.lower()
                                for cls in ["nav", "menu", "form", "submit"]
                            ):
                                safe_elements.append(element)
                    except:
                        # Пропускаем элементы, которые нельзя обработать
                        continue

                if safe_elements:
                    selected_element = random.choice(safe_elements)
                    await selected_element.click()
                    await asyncio.sleep(random.uniform(1, 3))
                    return True

            return False

        except Exception:
            return False

    async def _launch_browser_with_profile(self, playwright, profile: Profile):
        """Запуск браузера с настройками профиля"""

        browser_config = {
            "headless": False,
            "args": [
                "--no-first-run",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
            ],
        }

        # Применяем настройки профиля
        if profile.browser_settings:
            browser_config.update(profile.browser_settings)

        browser = await playwright.chromium.launch(**browser_config)

        # Создаем контекст с cookies
        context_config = {
            "user_agent": profile.user_agent,
            "viewport": {"width": 1366, "height": 768},
        }

        if profile.cookies:
            context = await browser.new_context(**context_config)
            await context.add_cookies(profile.cookies)
        else:
            context = await browser.new_context(**context_config)

        return browser
