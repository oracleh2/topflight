import asyncio
from app.core.yandex_parser import YandexParser
from app.core.browser_manager import BrowserManager
from app.models import DeviceType
from app.database import async_session_maker


async def test_parser():
    """Тестирование парсера"""

    async with async_session_maker() as session:
        browser_manager = BrowserManager(session)
        parser = YandexParser(session)

        # Создаем тестовые профили
        desktop_profile = await browser_manager.create_profile(
            name="Test_Desktop",
            device_type=DeviceType.DESKTOP
        )

        mobile_profile = await browser_manager.create_profile(
            name="Test_Mobile",
            device_type=DeviceType.MOBILE
        )

        # Прогреваем профили
        print("Warming up desktop profile...")
        await browser_manager.warmup_profile(desktop_profile)

        print("Warming up mobile profile...")
        await browser_manager.warmup_profile(mobile_profile)

        # Тестируем парсинг
        test_keyword = "купить телефон"

        print(f"\nTesting desktop parsing for: {test_keyword}")
        desktop_results = await parser.parse_serp(
            keyword=test_keyword,
            profile=desktop_profile,
            pages=2,
            region_code="213"
        )

        print(f"Desktop results: {len(desktop_results)}")
        for i, result in enumerate(desktop_results[:5]):
            print(f"  {i + 1}. {result.domain} - {result.title[:60]}...")

        print(f"\nTesting mobile parsing for: {test_keyword}")
        mobile_results = await parser.parse_serp(
            keyword=test_keyword,
            profile=mobile_profile,
            pages=2,
            region_code="213"
        )

        print(f"Mobile results: {len(mobile_results)}")
        for i, result in enumerate(mobile_results[:5]):
            print(f"  {i + 1}. {result.domain} - {result.title[:60]}...")

        # Тестируем проверку позиций
        test_domain = "ozon.ru"
        print(f"\nChecking position for {test_domain}...")

        desktop_position = await parser.check_position(
            keyword=test_keyword,
            target_domain=test_domain,
            profile=desktop_profile,
            region_code="213"
        )

        mobile_position = await parser.check_position(
            keyword=test_keyword,
            target_domain=test_domain,
            profile=mobile_profile,
            region_code="213"
        )

        print(f"Desktop position for {test_domain}: {desktop_position}")
        print(f"Mobile position for {test_domain}: {mobile_position}")


if __name__ == "__main__":
    asyncio.run(test_parser())