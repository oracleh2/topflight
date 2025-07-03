import asyncio
import random
from typing import Dict, List, Any
from playwright.async_api import Page
import structlog

logger = structlog.get_logger(__name__)


class YandexDetectionUtils:
    """Утилиты для детекции и обхода блокировок Яндекса"""

    @staticmethod
    async def detect_blocking_signals(page: Page) -> Dict[str, Any]:
        """Детектирует различные сигналы блокировки"""
        signals = {
            "captcha_present": False,
            "robot_check": False,
            "ip_blocked": False,
            "rate_limited": False,
            "unusual_activity": False,
            "details": []
        }

        try:
            # Проверяем наличие капчи
            captcha_selectors = [
                ".captcha",
                ".checkbox__box",
                "[data-bem*='captcha']",
                ".form__captcha",
                "#captcha"
            ]

            for selector in captcha_selectors:
                if await page.query_selector(selector):
                    signals["captcha_present"] = True
                    signals["details"].append(f"Captcha found: {selector}")
                    break

            # Проверяем текст страницы на признаки блокировки
            page_text = await page.text_content("body") or ""
            page_text_lower = page_text.lower()

            blocking_phrases = [
                "подозрительная активность",
                "unusual activity",
                "robot",
                "bot",
                "автоматические запросы",
                "automated requests",
                "доступ ограничен",
                "access denied",
                "заблокирован",
                "blocked"
            ]

            for phrase in blocking_phrases:
                if phrase in page_text_lower:
                    if "robot" in phrase or "bot" in phrase:
                        signals["robot_check"] = True
                    elif "ограничен" in phrase or "denied" in phrase or "blocked" in phrase:
                        signals["ip_blocked"] = True
                    else:
                        signals["unusual_activity"] = True

                    signals["details"].append(f"Blocking phrase found: {phrase}")

            # Проверяем HTTP статус
            response = await page.evaluate("() => window.performance.getEntries().pop()?.responseStatus")
            if response in [429, 403, 503]:
                signals["rate_limited"] = True
                signals["details"].append(f"HTTP {response} status")

            # Проверяем URL на признаки редиректа на страницу блокировки
            current_url = page.url.lower()
            blocking_url_parts = ["captcha", "blocked", "robot", "verify", "check"]

            for part in blocking_url_parts:
                if part in current_url:
                    signals["robot_check"] = True
                    signals["details"].append(f"Blocking URL pattern: {part}")
                    break

            return signals

        except Exception as e:
            logger.error("Error detecting blocking signals", error=str(e))
            return signals

    @staticmethod
    async def inject_stealth_scripts(page: Page):
        """Внедряет скрипты для обхода детекции"""

        stealth_script = """
        // Удаляем webdriver traces
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Перезаписываем navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            ],
        });

        // Убираем автоматизацию Chrome
        if (window.chrome) {
            Object.defineProperty(window.chrome, 'runtime', {
                get: () => ({
                    onConnect: undefined,
                    onMessage: undefined,
                })
            });
        }

        // Перезаписываем permissions query
        const originalPermissionsQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalPermissionsQuery(parameters)
        );

        // Убираем automation флаги
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });

        // Перезаписываем languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru', 'en-US', 'en'],
        });

        // Скрываем headless признаки
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });

        // Эмулируем batteryAPI для мобильных
        if (navigator.userAgent.includes('Mobile')) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: Math.random() * 0.3 + 0.7  // 70-100%
            });
        }

        // Убираем следы Playwright
        delete window.__playwright;
        delete window.__pw_manual;
        delete window.__PW_inspect;

        // Эмулируем реальные события мыши
        let lastMouseMove = Date.now();
        document.addEventListener('mousemove', () => {
            lastMouseMove = Date.now();
        });

        // Добавляем случайные вариации в Date.now
        const originalDateNow = Date.now;
        Date.now = () => originalDateNow() + Math.floor(Math.random() * 2 - 1);
        """

        await page.add_init_script(stealth_script)

    @staticmethod
    async def simulate_human_reading(page: Page, device_type: str):
        """Имитирует человеческое чтение страницы"""
        try:
            # Получаем высоту страницы
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")

            if page_height <= viewport_height:
                # Страница помещается в viewport
                await asyncio.sleep(random.uniform(2, 5))
                return

            # Имитируем чтение с прокруткой
            scroll_positions = []
            current_position = 0

            # Генерируем позиции для прокрутки
            while current_position < page_height - viewport_height:
                scroll_distance = random.randint(200, 600)
                current_position += scroll_distance
                scroll_positions.append(min(current_position, page_height - viewport_height))

            # Прокручиваем страницу с паузами
            for position in scroll_positions:
                await page.evaluate(f"window.scrollTo(0, {position})")

                # Пауза для "чтения"
                reading_time = random.uniform(1, 4)
                if device_type == "mobile":
                    reading_time *= 0.7  # На мобильных читают быстрее

                await asyncio.sleep(reading_time)

                # Иногда возвращаемся назад (человеческое поведение)
                if random.random() < 0.1:
                    back_scroll = random.randint(50, 200)
                    await page.evaluate(f"window.scrollBy(0, -{back_scroll})")
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await page.evaluate(f"window.scrollBy(0, {back_scroll})")

        except Exception as e:
            logger.warning("Error simulating human reading", error=str(e))