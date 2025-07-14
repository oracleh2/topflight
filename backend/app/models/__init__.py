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

from .strategies import (
    StrategyTemplate,
    UserStrategy,
    StrategyDataSource,
    ProjectStrategy,
    StrategyExecutionLog,
)

# Экспортируем все модели
__all__ = [
    "Base",
    # User models
    "User",
    "TariffPlan",
    "UserBalance",
    "BalanceTransaction",
    "Region",
    "UserDomain",
    "UserKeyword",
    "UserDomainSettings",
    "UserServerPreferences",
    # Profile models
    "Profile",
    "ProfileFingerprint",
    "ProfileLifecycle",
    "ServerConfig",
    "WorkerNode",
    "DeviceType",
    # Task models
    "Task",
    "ParseResult",
    "PositionHistory",
    # Proxy models
    "ProjectProxy",
    "ProxyImportHistory",
    "ProfileProxyAssignment",
    "ProxyType",
    "ProxyProtocol",
    "ProxyStatus",
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
    "BackupSchedule",
    "BackupHistory",
    "CacheSettings",
    # Strategies models
    "StrategyTemplate",
    "UserStrategy",
    "StrategyDataSource",
    "ProjectStrategy",
    "StrategyExecutionLog",
]
