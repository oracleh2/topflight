# backend/app/models/__init__.py

from .analytics import (
    SystemConfig,
    SystemLog,
    AuditTrail,
    ConfigChangesLog,
    FinancialTransactionsLog,
    PerformanceMetrics,
    BusinessMetrics,
    UserActivityStats,
    TaskAnalytics,
    ParsingAnalytics,
    BackupSchedule,
    BackupHistory,
    CacheSettings,
)
from .base import Base
from .profile import (
    Profile,
    ProfileFingerprint,
    ProfileLifecycle,
    ServerConfig,
    WorkerNode,
    DeviceType,
)
from .proxy import (
    ProjectProxy,
    ProxyImportHistory,
    ProfileProxyAssignment,
    ProxyType,
    ProxyProtocol,
    ProxyStatus,
)
from .task import Task, ParseResult, PositionHistory
from .user import (
    User,
    TariffPlan,
    UserBalance,
    BalanceTransaction,
    Region,
    UserDomain,
    UserKeyword,
    UserDomainSettings,
    UserServerPreferences,
)

from .yandex_region import YandexRegion

from .strategies import (
    StrategyTemplate,
    UserStrategy,
    StrategyDataSource,
    ProjectStrategy,
    StrategyExecutionLog,
)

from .strategy_proxy import (
    StrategyProxySource,
    StrategyProxyAssignment,
    StrategyProxyRotation,
)

from .alerts import AlertRule, AlertHistory, DebugVNCSession

from .strategy_proxy import StrategyProxySource, StrategyProxy


# Экспортируем все модели
__all__ = [
    "Base",
    # User models
    "User",
    "UserBalance",
    "BalanceTransaction",
    "UserDomain",
    "UserKeyword",
    "UserDomainSettings",
    "UserServerPreferences",
    "YandexRegion",
    # Profile models
    "Profile",
    "ProfileFingerprint",
    "ProfileLifecycle",
    # Task models
    "Task",
    "ParseResult",
    "PositionHistory",
    # Analytics models
    "SystemConfig",
    "SystemLog",
    "AuditTrail",
    "ConfigChangesLog",
    "FinancialTransactionsLog",
    "PerformanceMetrics",
    "BusinessMetrics",
    "UserActivityStats",
    "TaskAnalytics",
    "ParsingAnalytics",
    # Infrastructure models
    "BackupSchedule",
    "BackupHistory",
    "CacheSettings",
    "ServerConfig",
    "WorkerNode",
    "TariffPlan",
    # Proxy models
    "ProjectProxy",
    "ProxyImportHistory",
    "ProfileProxyAssignment",
    # Strategy models
    "StrategyTemplate",
    "UserStrategy",
    "StrategyDataSource",
    "ProjectStrategy",
    "StrategyExecutionLog",
    # Alert and Debug models
    "AlertRule",
    "AlertHistory",
    "DebugVNCSession",
    # Strategy proxy models
    "StrategyProxySource",
    "StrategyProxyAssignment",
    "StrategyProxyRotation",
    "StrategyProxy",
]

# __all__ = [
#     "Base",
#     # User models
#     "User",
#     "TariffPlan",
#     "UserBalance",
#     "BalanceTransaction",
#     # Закомментировал старую модель Region
#     # "Region",
#     "YandexRegion",
#     "UserDomain",
#     "UserKeyword",
#     "UserDomainSettings",
#     "UserServerPreferences",
#     # Profile models
#     "Profile",
#     "ProfileFingerprint",
#     "ProfileLifecycle",
#     "ServerConfig",
#     "WorkerNode",
#     "DeviceType",
#     # Task models
#     "Task",
#     "ParseResult",
#     "PositionHistory",
#     # Proxy models
#     "ProjectProxy",
#     "ProxyImportHistory",
#     "ProfileProxyAssignment",
#     "ProxyType",
#     "ProxyProtocol",
#     "ProxyStatus",
#     # Analytics models
#     "SystemConfig",
#     "SystemLog",
#     "AuditTrail",
#     "ConfigChangesLog",
#     "FinancialTransactionsLog",
#     "PerformanceMetrics",
#     "BusinessMetrics",
#     "UserActivityStats",
#     "TaskAnalytics",
#     "ParsingAnalytics",
#     "BackupSchedule",
#     "BackupHistory",
#     "CacheSettings",
#     # Strategies models
#     "StrategyTemplate",
#     "UserStrategy",
#     "StrategyDataSource",
#     "ProjectStrategy",
#     "StrategyExecutionLog",
# ]
