# backend/app/constants/strategies.py
"""
Константы для возможных значений полей стратегий.
Используются для валидации и в качестве справочника.
"""

class StrategyType:
    """Типы стратегий"""
    WARMUP = "warmup"
    POSITION_CHECK = "position_check"

    ALL = [WARMUP, POSITION_CHECK]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class DataSourceType:
    """Типы источников данных для стратегий"""
    MANUAL_LIST = "manual_list"        # Ручной ввод списка
    FILE_UPLOAD = "file_upload"        # Загрузка файла (.txt, .csv)
    URL_IMPORT = "url_import"          # Импорт по URL
    GOOGLE_SHEETS = "google_sheets"    # Импорт из Google Таблиц
    GOOGLE_DOCS = "google_docs"        # Импорт из Google Документов

    ALL = [MANUAL_LIST, FILE_UPLOAD, URL_IMPORT, GOOGLE_SHEETS, GOOGLE_DOCS]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class ExecutionStatus:
    """Статусы выполнения стратегий"""
    PENDING = "pending"      # Ожидает выполнения
    RUNNING = "running"      # Выполняется
    COMPLETED = "completed"  # Завершено успешно
    FAILED = "failed"        # Завершено с ошибкой

    ALL = [PENDING, RUNNING, COMPLETED, FAILED]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class WarmupType:
    """Типы стратегий прогрева"""
    DIRECT = "direct"        # Только прямые заходы на сайты
    SEARCH = "search"        # Только поиск в Яндексе
    MIXED = "mixed"          # Комбинированная стратегия

    ALL = [DIRECT, SEARCH, MIXED]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class CheckFrequency:
    """Частота проверки позиций"""
    DAILY = "daily"          # Ежедневно
    WEEKLY = "weekly"        # Еженедельно
    MONTHLY = "monthly"      # Ежемесячно
    CUSTOM = "custom"        # Пользовательское расписание (cron)

    ALL = [DAILY, WEEKLY, MONTHLY, CUSTOM]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class YandexDomain:
    """Домены Яндекса для поиска"""
    RU = "yandex.ru"         # Россия
    BY = "yandex.by"         # Беларусь
    KZ = "yandex.kz"         # Казахстан
    UA = "yandex.ua"         # Украина

    ALL = [RU, BY, KZ, UA]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

class DeviceType:
    """Типы устройств"""
    DESKTOP = "desktop"      # Десктоп
    MOBILE = "mobile"        # Мобильное устройство

    ALL = [DESKTOP, MOBILE]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

# Примеры конфигураций по умолчанию
DEFAULT_WARMUP_CONFIG = {
    "type": WarmupType.MIXED,
    "proportions": {
        "direct_visits": 5,
        "search_visits": 1
    },
    "search_config": {
        "yandex_domains": [YandexDomain.RU],
        "keywords_per_session": {"min": 1, "max": 3},
        "click_probability": 0.7,
        "random_result_click": True
    },
    "direct_config": {
        "sites_per_session": {"min": 3, "max": 7},
        "time_per_site": {"min": 10, "max": 45},
        "scroll_probability": 0.8,
        "click_probability": 0.3
    },
    "general": {
        "delay_between_actions": {"min": 2, "max": 8},
        "user_agent_rotation": True,
        "cookie_retention": True
    }
}

DEFAULT_POSITION_CHECK_CONFIG = {
    "check_frequency": CheckFrequency.DAILY,
    "search_config": {
        "pages_to_check": 10,
        "yandex_domain": YandexDomain.RU,
        "device_types": [DeviceType.DESKTOP],
        "regions": ["213"]  # Moscow
    },
    "behavior": {
        "scroll_serp": True,
        "click_competitors": 0.1,
        "time_on_serp": {"min": 5, "max": 15}
    }
}

# Валидационные функции
def validate_warmup_config(config: dict) -> dict:
    """Валидация и нормализация конфигурации прогрева"""
    if not config.get("type"):
        raise ValueError("Поле 'type' обязательно для стратегии прогрева")

    if not WarmupType.is_valid(config["type"]):
        raise ValueError(f"Неверный тип стратегии прогрева. Допустимые: {', '.join(WarmupType.ALL)}")

    # Валидируем пропорции для mixed стратегии
    if config["type"] == WarmupType.MIXED:
        proportions = config.get("proportions", {})
        if not proportions.get("direct_visits") or not proportions.get("search_visits"):
            raise ValueError("Для mixed стратегии необходимо указать пропорции direct_visits и search_visits")

    # Добавляем значения по умолчанию
    result_config = DEFAULT_WARMUP_CONFIG.copy()
    result_config.update(config)

    return result_config

def validate_position_check_config(config: dict) -> dict:
    """Валидация и нормализация конфигурации проверки позиций"""
    # Проверяем частоту если указана
    if config.get("check_frequency") and not CheckFrequency.is_valid(config["check_frequency"]):
        raise ValueError(f"Неверная частота проверки. Допустимые: {', '.join(CheckFrequency.ALL)}")

    # Проверяем домен Яндекса если указан
    search_config = config.get("search_config", {})
    if search_config.get("yandex_domain") and not YandexDomain.is_valid(search_config["yandex_domain"]):
        raise ValueError(f"Неверный домен Яндекса. Допустимые: {', '.join(YandexDomain.ALL)}")

    # Проверяем типы устройств если указаны
    if search_config.get("device_types"):
        for device_type in search_config["device_types"]:
            if not DeviceType.is_valid(device_type):
                raise ValueError(f"Неверный тип устройства: {device_type}. Допустимые: {', '.join(DeviceType.ALL)}")

    # Добавляем значения по умолчанию
    result_config = DEFAULT_POSITION_CHECK_CONFIG.copy()

    # Рекурсивно объединяем вложенные словари
    def deep_merge(base: dict, update: dict) -> dict:
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    result_config = deep_merge(result_config, config)

    return result_config
