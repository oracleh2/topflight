# backend/app/constants/strategies.py
"""
Константы для возможных значений полей стратегий.
Используются для валидации и в качестве справочника.
"""


class StrategyType:
    """Типы стратегий"""

    WARMUP = "warmup"
    POSITION_CHECK = "position_check"
    PROFILE_NURTURE = "profile_nurture"  # Новый тип - нагул профиля

    ALL = [WARMUP, POSITION_CHECK, PROFILE_NURTURE]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class DataSourceType:
    """Типы источников данных для стратегий"""

    MANUAL_LIST = "manual_list"  # Ручной ввод списка
    FILE_UPLOAD = "file_upload"  # Загрузка файла (.txt, .csv)
    URL_IMPORT = "url_import"  # Импорт по URL
    GOOGLE_SHEETS = "google_sheets"  # Импорт из Google Таблиц
    GOOGLE_DOCS = "google_docs"  # Импорт из Google Документов

    ALL = [MANUAL_LIST, FILE_UPLOAD, URL_IMPORT, GOOGLE_SHEETS, GOOGLE_DOCS]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class ExecutionStatus:
    """Статусы выполнения стратегий"""

    PENDING = "pending"  # Ожидает выполнения
    RUNNING = "running"  # Выполняется
    COMPLETED = "completed"  # Завершено успешно
    FAILED = "failed"  # Завершено с ошибкой

    ALL = [PENDING, RUNNING, COMPLETED, FAILED]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class WarmupType:
    """Типы стратегий прогрева"""

    DIRECT = "direct"  # Только прямые заходы на сайты
    SEARCH = "search"  # Только поиск в Яндексе
    MIXED = "mixed"  # Комбинированная стратегия

    ALL = [DIRECT, SEARCH, MIXED]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class ProfileNurtureType:
    """Типы стратегий нагула профиля"""

    SEARCH_BASED = "search_based"  # Через поиск в Яндексе
    DIRECT_VISITS = "direct_visits"  # Прямые заходы на сайты
    MIXED_NURTURE = "mixed_nurture"  # Комбинированный нагул

    ALL = [SEARCH_BASED, DIRECT_VISITS, MIXED_NURTURE]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class SearchEngineType:
    """Поисковые системы для нагула"""

    YANDEX_RU = "yandex.ru"
    YANDEX_BY = "yandex.by"
    YANDEX_KZ = "yandex.kz"
    YANDEX_TR = "yandex.tr"
    YANDEX_UA = "yandex.ua"
    MAIL_RU = "mail.ru"
    DZEN_RU = "dzen.ru"
    # Альтернативные домены
    YA_RU = "ya.ru"

    ALL = [
        YANDEX_RU,
        YANDEX_BY,
        YANDEX_KZ,
        YANDEX_TR,
        YANDEX_UA,
        MAIL_RU,
        DZEN_RU,
        YA_RU,
    ]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL

    @classmethod
    def get_yandex_domains(cls) -> list:
        """Получить только домены Яндекса"""
        return [
            cls.YANDEX_RU,
            cls.YANDEX_BY,
            cls.YANDEX_KZ,
            cls.YANDEX_TR,
            cls.YANDEX_UA,
            cls.YA_RU,
        ]


class QuerySourceType:
    """Типы источников запросов для нагула"""

    MANUAL_INPUT = "manual_input"  # Ручной ввод в textarea
    FILE_UPLOAD = "file_upload"  # Загрузка файла
    URL_ENDPOINT = "url_endpoint"  # URL для получения запросов
    GOOGLE_DOCS = "google_docs"  # Google документ
    GOOGLE_SHEETS = "google_sheets"  # Google таблица

    ALL = [MANUAL_INPUT, FILE_UPLOAD, URL_ENDPOINT, GOOGLE_DOCS, GOOGLE_SHEETS]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class CheckFrequency:
    """Частота проверки позиций"""

    DAILY = "daily"  # Ежедневно
    WEEKLY = "weekly"  # Еженедельно
    MONTHLY = "monthly"  # Ежемесячно
    CUSTOM = "custom"  # Пользовательское расписание (cron)

    ALL = [DAILY, WEEKLY, MONTHLY, CUSTOM]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class DeviceType:
    """Типы устройств"""

    DESKTOP = "desktop"  # Десктоп
    MOBILE = "mobile"  # Мобильное устройство

    ALL = [DESKTOP, MOBILE]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


# Примеры конфигураций по умолчанию
DEFAULT_WARMUP_CONFIG = {
    "type": WarmupType.MIXED,
    "proportions": {"direct_visits": 30, "search_visits": 70},
    "min_sites": 3,
    "max_sites": 7,
    "session_timeout": 15,
    "yandex_domain": "yandex.ru",
    "device_type": DeviceType.DESKTOP,
}

DEFAULT_POSITION_CHECK_CONFIG = {
    "check_frequency": CheckFrequency.DAILY,
    "yandex_domain": "yandex.ru",
    "device_type": DeviceType.DESKTOP,
    "max_pages": 10,
    "custom_schedule": None,
    "behavior": {
        "random_delays": True,
        "scroll_pages": True,
        "human_like_clicks": True,
    },
}

DEFAULT_PROFILE_NURTURE_CONFIG = {
    "nurture_type": ProfileNurtureType.SEARCH_BASED,
    "target_cookies": {"min": 50, "max": 100},
    "session_config": {
        "timeout_per_site": 15,  # секунды
        "min_timeout": 10,
        "max_timeout": 30,
    },
    "search_engines": [SearchEngineType.YANDEX_RU],
    "queries_source": {
        "type": QuerySourceType.MANUAL_INPUT,
        "refresh_on_each_cycle": False,  # Для URL источников
    },
    "behavior": {
        "return_to_search": True,  # Возвращаться в поиск после сайта
        "close_browser_after_cycle": False,  # Закрывать браузер после цикла
        "emulate_human_actions": True,  # Эмулировать действия человека
        "scroll_pages": True,
        "random_clicks": True,
    },
    "proportions": {"search_visits": 70, "direct_visits": 30},  # Для смешанного типа
}


# Валидация конфигураций
def validate_warmup_config(config: dict) -> dict:
    """Валидация конфигурации прогрева"""
    validated = {**DEFAULT_WARMUP_CONFIG, **config}

    if not WarmupType.is_valid(validated.get("type")):
        raise ValueError(f"Invalid warmup type. Must be one of: {WarmupType.ALL}")

    proportions = validated.get("proportions", {})
    if validated["type"] == WarmupType.MIXED:
        if not proportions.get("direct_visits") or not proportions.get("search_visits"):
            raise ValueError(
                "Mixed strategy requires both direct_visits and search_visits proportions"
            )

    return validated


def validate_position_check_config(config: dict) -> dict:
    """Валидация конфигурации проверки позиций"""
    validated = {**DEFAULT_POSITION_CHECK_CONFIG, **config}

    if not CheckFrequency.is_valid(validated.get("check_frequency")):
        raise ValueError(
            f"Invalid check frequency. Must be one of: {CheckFrequency.ALL}"
        )

    if validated["check_frequency"] == CheckFrequency.CUSTOM and not validated.get(
        "custom_schedule"
    ):
        raise ValueError("Custom frequency requires custom_schedule (cron expression)")

    return validated


def validate_profile_nurture_config(config: dict) -> dict:
    """Валидация конфигурации нагула профиля"""
    validated = {**DEFAULT_PROFILE_NURTURE_CONFIG, **config}

    # Проверяем тип нагула
    if not ProfileNurtureType.is_valid(validated.get("nurture_type")):
        raise ValueError(
            f"Invalid nurture type. Must be one of: {ProfileNurtureType.ALL}"
        )

    # Проверяем целевое количество куков
    target_cookies = validated.get("target_cookies", {})
    min_cookies = target_cookies.get("min", 50)
    max_cookies = target_cookies.get("max", 100)

    if min_cookies <= 0 or max_cookies <= 0:
        raise ValueError("Target cookies must be positive numbers")

    if min_cookies > max_cookies:
        raise ValueError("Min cookies cannot be greater than max cookies")

    # Проверяем поисковые системы
    search_engines = validated.get("search_engines", [])
    if validated["nurture_type"] in [
        ProfileNurtureType.SEARCH_BASED,
        ProfileNurtureType.MIXED_NURTURE,
    ]:
        if not search_engines:
            raise ValueError("Search engines required for search-based nurturing")

        for engine in search_engines:
            if not SearchEngineType.is_valid(engine):
                raise ValueError(f"Invalid search engine: {engine}")

    # Проверяем источник запросов
    queries_source = validated.get("queries_source", {})
    source_type = queries_source.get("type")

    if validated["nurture_type"] in [
        ProfileNurtureType.SEARCH_BASED,
        ProfileNurtureType.MIXED_NURTURE,
    ]:
        if not QuerySourceType.is_valid(source_type):
            raise ValueError(
                f"Invalid query source type. Must be one of: {QuerySourceType.ALL}"
            )

    # Проверяем пропорции для смешанного типа
    if validated["nurture_type"] == ProfileNurtureType.MIXED_NURTURE:
        proportions = validated.get("proportions", {})
        if not proportions.get("search_visits") or not proportions.get("direct_visits"):
            raise ValueError(
                "Mixed nurture requires both search_visits and direct_visits proportions"
            )

    # Проверяем конфигурацию сессии
    session_config = validated.get("session_config", {})
    timeout = session_config.get("timeout_per_site", 15)
    min_timeout = session_config.get("min_timeout", 10)
    max_timeout = session_config.get("max_timeout", 30)

    if timeout <= 0 or min_timeout <= 0 or max_timeout <= 0:
        raise ValueError("Session timeouts must be positive numbers")

    if min_timeout > max_timeout:
        raise ValueError("Min timeout cannot be greater than max timeout")

    return validated
