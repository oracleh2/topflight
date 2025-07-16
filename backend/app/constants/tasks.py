# Обновите constants в backend/app/constants/tasks.py


class TaskType:
    """Типы задач"""

    WARMUP_PROFILE = "warmup_profile"
    PARSE_SERP = "parse_serp"
    CHECK_POSITIONS = "check_positions"
    PROFILE_NURTURE = "profile_nurture"  # Добавляем новый тип

    ALL = [WARMUP_PROFILE, PARSE_SERP, CHECK_POSITIONS, PROFILE_NURTURE]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class TaskStatus:
    """Статусы задач"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    ALL = [PENDING, RUNNING, COMPLETED, FAILED]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


class TaskPriority:
    """Приоритеты задач"""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 15
    CRITICAL = 20

    @classmethod
    def is_valid(cls, value: int) -> bool:
        return 1 <= value <= 20


# Добавляем маппинг типов задач для лучшей читаемости
TASK_TYPE_DESCRIPTIONS = {
    TaskType.WARMUP_PROFILE: "Прогрев профиля",
    TaskType.PARSE_SERP: "Парсинг SERP",
    TaskType.CHECK_POSITIONS: "Проверка позиций",
    TaskType.PROFILE_NURTURE: "Нагул профиля",
}

TASK_STATUS_DESCRIPTIONS = {
    TaskStatus.PENDING: "Ожидает выполнения",
    TaskStatus.RUNNING: "Выполняется",
    TaskStatus.COMPLETED: "Завершена",
    TaskStatus.FAILED: "Ошибка",
}

# Приоритеты по типам задач
DEFAULT_TASK_PRIORITIES = {
    TaskType.WARMUP_PROFILE: TaskPriority.NORMAL,
    TaskType.PARSE_SERP: TaskPriority.NORMAL,
    TaskType.CHECK_POSITIONS: TaskPriority.HIGH,
    TaskType.PROFILE_NURTURE: TaskPriority.NORMAL,
}
