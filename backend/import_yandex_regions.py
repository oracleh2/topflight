#!/usr/bin/env python3
"""
Скрипт для импорта регионов Яндекса из GitHub gist в таблицу yandex_regions

Использование:
cd backend/
python scripts/import_yandex_regions.py

Опции:
--clear     - Очистить таблицу перед импортом
--dry-run   - Показать что будет импортировано без реальной записи
--batch-size N - Размер батча для вставки (по умолчанию 100)
--source URL - Альтернативный источник данных
"""

import asyncio
import argparse
import sys
import requests
import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models.yandex_region import YandexRegion
from sqlalchemy import select, func, delete, text


# URL источника данных
DEFAULT_GIST_URL = (
    "https://gist.githubusercontent.com/gorborukov/0722a93c35dfba96337b/raw"
)

# Известные коды регионов Яндекса для крупных городов
YANDEX_REGION_CODES = {
    "Москва": "213",
    "Санкт-Петербург": "2",
    "Екатеринбург": "54",
    "Новосибирск": "65",
    "Краснодар": "35",
    "Воронеж": "193",
    "Нижний Новгород": "47",
    "Казань": "43",
    "Челябинск": "56",
    "Омск": "66",
    "Самара": "51",
    "Ростов-на-Дону": "39",
    "Уфа": "172",
    "Красноярск": "62",
    "Пермь": "50",
    "Волгоград": "38",
    "Владивосток": "20",
    "Саратов": "194",
    "Ульяновск": "195",
    "Барнаул": "197",
    "Улан-Удэ": "198",
    "Брянск": "191",
    "Владимир": "192",
    "Белгород": "4",
    "Иваново": "5",
    "Калуга": "6",
    "Кострома": "7",
    "Курск": "8",
    "Липецк": "9",
    "Орёл": "10",
    "Рязань": "12",
    "Смоленск": "13",
    "Тамбов": "14",
    "Тверь": "15",
    "Тула": "16",
    "Ярославль": "17",
    "Чебоксары": "21",
    "Йошкар-Ола": "22",
    "Саранск": "23",
    "Ижевск": "24",
    "Сыктывкар": "25",
    "Петрозаводск": "26",
    "Архангельск": "27",
    "Вологда": "28",
    "Мурманск": "29",
    "Псков": "30",
    "Великий Новгород": "31",
    "Калининград": "32",
}


class RegionImporter:
    """Класс для импорта регионов из GitHub gist"""

    def __init__(self, source_url: str = DEFAULT_GIST_URL):
        self.source_url = source_url
        self.used_codes: Set[str] = set()
        self.stats = {
            "total_processed": 0,
            "successful_imports": 0,
            "errors": 0,
            "duplicates": 0,
        }

    def fetch_data(self) -> List[Dict]:
        """Загружает данные из GitHub gist"""
        print(f"🔄 Загрузка данных из {self.source_url}")

        try:
            response = requests.get(self.source_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            print(f"✅ Загружено {len(data)} записей")
            return data

        except requests.RequestException as e:
            print(f"❌ Ошибка загрузки: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return []

    def generate_region_code(self, city_name: str, region_name: str) -> str:
        """Генерирует уникальный код региона"""
        # Сначала проверяем известные коды
        if city_name in YANDEX_REGION_CODES:
            code = YANDEX_REGION_CODES[city_name]
            if code not in self.used_codes:
                return code

        # Генерируем код на основе хеша
        city_hash = abs(hash(city_name + region_name)) % 9999
        code = str(city_hash)

        # Убеждаемся что код уникален
        counter = 1
        original_code = code
        while code in self.used_codes:
            code = f"{original_code}_{counter}"
            counter += 1

        return code

    def determine_region_type(self, region_name: str) -> str:
        """Определяет тип региона"""
        region_lower = region_name.lower()

        if any(word in region_lower for word in ["обл.", "область"]):
            return "region"
        elif any(word in region_lower for word in ["край"]):
            return "region"
        elif any(word in region_lower for word in ["ао", "автономный"]):
            return "region"
        elif any(word in region_lower for word in ["респ.", "республика"]):
            return "region"
        elif region_lower in ["россия", "russia"]:
            return "country"
        else:
            return "city"

    def create_region_object(self, item: Dict) -> YandexRegion:
        """Создает объект YandexRegion из данных"""
        city = item.get("city", "").strip()
        region = item.get("region", "").strip()

        if not city or not region:
            raise ValueError("Пустые данные города или региона")

        # Генерируем уникальный код
        region_code = self.generate_region_code(city, region)
        self.used_codes.add(region_code)

        # Определяем тип региона
        region_type = self.determine_region_type(region)

        # Создаем поисковые строки
        search_name = f"{city} {region}".replace("обл.", "область").replace(
            "респ.", "республика"
        )

        return YandexRegion(
            region_code=region_code,
            region_name=city,
            country_code="RU",
            region_type=region_type,
            is_active=True,
            display_name=city,
            search_name=search_name,
        )

    async def clear_table(self):
        """Очищает таблицу перед импортом"""
        async with async_session_maker() as session:
            try:
                # Подсчитываем количество записей используя ORM
                count_query = await session.execute(select(func.count(YandexRegion.id)))
                total = count_query.scalar()

                if total > 0:
                    print(f"🗑️  Удаление {total} существующих записей...")
                    await session.execute(delete(YandexRegion))
                    await session.commit()
                    print("✅ Таблица очищена")
                else:
                    print("📝 Таблица уже пуста")

            except Exception as e:
                print(f"❌ Ошибка очистки таблицы: {e}")
                await session.rollback()
                raise

    async def import_regions(
        self, regions_data: List[Dict], batch_size: int = 100, dry_run: bool = False
    ):
        """Импортирует регионы в базу данных"""

        if dry_run:
            print("🔍 Режим dry-run: анализ данных без записи в БД")

        async with async_session_maker() as session:
            batch = []

            for item in regions_data:
                try:
                    self.stats["total_processed"] += 1

                    # Создаем объект региона
                    region = self.create_region_object(item)

                    if dry_run:
                        print(
                            f"  {region.region_code}: {region.region_name} ({region.region_type})"
                        )
                        continue

                    # Проверяем на дубликат используя ORM
                    existing_query = await session.execute(
                        select(YandexRegion.id).where(
                            YandexRegion.region_code == region.region_code
                        )
                    )
                    existing = existing_query.first()

                    if existing:
                        self.stats["duplicates"] += 1
                        print(
                            f"⚠️  Дубликат кода {region.region_code}: {region.region_name}"
                        )
                        continue

                    batch.append(region)

                    # Обрабатываем батч
                    if len(batch) >= batch_size:
                        await self._process_batch(session, batch)
                        batch = []

                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"❌ Ошибка обработки {item}: {e}")
                    continue

            # Обрабатываем оставшиеся записи
            if batch and not dry_run:
                await self._process_batch(session, batch)

    async def _process_batch(self, session, batch: List[YandexRegion]):
        """Обрабатывает батч записей"""
        try:
            session.add_all(batch)
            await session.commit()

            self.stats["successful_imports"] += len(batch)
            print(
                f"✅ Импортировано {len(batch)} записей (всего: {self.stats['successful_imports']})"
            )

        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка вставки батча: {e}")
            raise

    def print_stats(self):
        """Выводит статистику импорта"""
        print("\n" + "=" * 50)
        print("📊 СТАТИСТИКА ИМПОРТА")
        print("=" * 50)
        print(f"Всего обработано:     {self.stats['total_processed']}")
        print(f"Успешно импортировано: {self.stats['successful_imports']}")
        print(f"Дубликатов:           {self.stats['duplicates']}")
        print(f"Ошибок:               {self.stats['errors']}")
        print("=" * 50)


async def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="Импорт регионов Яндекса из GitHub gist"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Очистить таблицу перед импортом"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Показать что будет импортировано"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Размер батча для вставки"
    )
    parser.add_argument(
        "--source", type=str, default=DEFAULT_GIST_URL, help="URL источника данных"
    )

    args = parser.parse_args()

    print("🚀 Запуск импорта регионов Яндекса")
    print(f"Источник: {args.source}")
    print(f"Размер батча: {args.batch_size}")
    print(f"Режим dry-run: {args.dry_run}")
    print("")

    # Создаем импортер
    importer = RegionImporter(args.source)

    try:
        # Загружаем данные
        regions_data = importer.fetch_data()

        if not regions_data:
            print("❌ Нет данных для импорта")
            return 1

        # Очищаем таблицу если нужно
        if args.clear and not args.dry_run:
            await importer.clear_table()

        # Импортируем данные
        await importer.import_regions(
            regions_data, batch_size=args.batch_size, dry_run=args.dry_run
        )

        # Выводим статистику
        importer.print_stats()

        if not args.dry_run:
            print("\n🎉 Импорт завершен успешно!")
            print("\nДля проверки выполните:")
            print("  SELECT COUNT(*) FROM yandex_regions;")
            print(
                "  SELECT region_code, region_name, region_type FROM yandex_regions LIMIT 10;"
            )

        return 0

    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
