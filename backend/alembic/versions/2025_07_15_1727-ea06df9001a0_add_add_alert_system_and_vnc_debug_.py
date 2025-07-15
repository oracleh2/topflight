"""add Add alert system and VNC debug support with performance indexes

Revision ID: ea06df9001a0
Revises: e1fffc129580
Create Date: 2025-07-15 17:27:34.107412

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = "ea06df9001a0"
down_revision: Union[str, None] = "e1fffc129580"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет систему алертов, VNC дебаг и индексы производительности"""

    # ========================================
    # 1. ТАБЛИЦА ПРАВИЛ АЛЕРТОВ
    # ========================================

    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Основные поля правила
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Условия срабатывания
        sa.Column("condition_type", sa.String(length=50), nullable=False),
        sa.Column(
            "condition_params", postgresql.JSON(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("threshold_value", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "comparison_operator", sa.String(length=10), nullable=True
        ),  # >, <, >=, <=, ==, !=
        # Частота проверки
        sa.Column(
            "check_interval_minutes", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column("last_check_time", sa.DateTime(), nullable=True),
        sa.Column("last_triggered_time", sa.DateTime(), nullable=True),
        # Каналы уведомлений
        sa.Column(
            "notification_channels",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "cooldown_minutes", sa.Integer(), nullable=False, server_default="30"
        ),
        # Метаданные
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "alert_level",
            sa.String(length=20),
            nullable=False,
            server_default="warning",
        ),  # info, warning, error, critical
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Ограничения
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # Индексы для alert_rules
    op.create_index("ix_alert_rules_is_active", "alert_rules", ["is_active"])
    op.create_index("ix_alert_rules_condition_type", "alert_rules", ["condition_type"])
    op.create_index("ix_alert_rules_alert_level", "alert_rules", ["alert_level"])
    op.create_index("ix_alert_rules_last_check", "alert_rules", ["last_check_time"])

    # ========================================
    # 2. ТАБЛИЦА ИСТОРИИ АЛЕРТОВ
    # ========================================

    op.create_table(
        "alert_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Связь с правилом
        sa.Column("alert_rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Данные срабатывания
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="active"
        ),  # active, resolved, acknowledged
        # Значения при срабатывании
        sa.Column("triggered_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("threshold_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column(
            "additional_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        # Уведомления
        sa.Column(
            "notifications_sent", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "acknowledged_by_user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("acknowledgement_note", sa.Text(), nullable=True),
        # Ограничения
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["alert_rule_id"], ["alert_rules.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["acknowledged_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # Индексы для alert_history
    op.create_index("ix_alert_history_rule_id", "alert_history", ["alert_rule_id"])
    op.create_index("ix_alert_history_status", "alert_history", ["status"])
    op.create_index("ix_alert_history_triggered_at", "alert_history", ["triggered_at"])

    # ========================================
    # 3. ТАБЛИЦА VNC СЕССИЙ ДЛЯ ДЕБАГА
    # ========================================

    op.create_table(
        "debug_vnc_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Связь с задачей
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # VNC параметры
        sa.Column("vnc_port", sa.Integer(), nullable=False),
        sa.Column("vnc_display", sa.String(length=10), nullable=False),  # :1, :2, etc.
        sa.Column("vnc_password", sa.String(length=255), nullable=True),
        # Дисплей параметры
        sa.Column(
            "screen_resolution", sa.String(length=20), nullable=False
        ),  # 1920x1080
        sa.Column("color_depth", sa.Integer(), nullable=False, server_default="24"),
        # Устройство для эмуляции
        sa.Column(
            "device_type", sa.String(length=20), nullable=False
        ),  # desktop, mobile, tablet
        sa.Column(
            "device_profile", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        # Статус сессии
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="initializing",
        ),  # initializing, active, stopped, error
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),
        # Процессы
        sa.Column("xvfb_pid", sa.Integer(), nullable=True),
        sa.Column("vnc_server_pid", sa.Integer(), nullable=True),
        sa.Column("browser_process_id", sa.String(length=255), nullable=True),
        # Настройки сервера
        sa.Column("server_id", sa.String(length=255), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        # Логи и ошибки
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("debug_logs", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Метаданные
        sa.Column(
            "session_timeout_minutes", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column("auto_cleanup", sa.Boolean(), nullable=False, server_default="true"),
        # Ограничения
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("vnc_port", name="uq_vnc_sessions_port"),
        sa.UniqueConstraint("vnc_display", name="uq_vnc_sessions_display"),
    )

    # Индексы для debug_vnc_sessions
    op.create_index("ix_debug_vnc_sessions_task_id", "debug_vnc_sessions", ["task_id"])
    op.create_index("ix_debug_vnc_sessions_user_id", "debug_vnc_sessions", ["user_id"])
    op.create_index("ix_debug_vnc_sessions_status", "debug_vnc_sessions", ["status"])
    op.create_index(
        "ix_debug_vnc_sessions_vnc_port", "debug_vnc_sessions", ["vnc_port"]
    )
    op.create_index(
        "ix_debug_vnc_sessions_created_at", "debug_vnc_sessions", ["created_at"]
    )

    # ========================================
    # 4. ИНДЕКСЫ ПРОИЗВОДИТЕЛЬНОСТИ
    # ========================================

    print("Creating performance indexes...")

    # Индексы для таблицы tasks
    op.create_index("ix_tasks_status_priority", "tasks", ["status", "priority"])
    op.create_index("ix_tasks_created_at_desc", "tasks", [sa.text("created_at DESC")])
    op.create_index("ix_tasks_user_status", "tasks", ["user_id", "status"])
    op.create_index("ix_tasks_task_type_status", "tasks", ["task_type", "status"])
    op.create_index("ix_tasks_completed_at", "tasks", ["completed_at"])

    # Индексы для таблицы parse_results
    op.create_index(
        "ix_parse_results_keyword_date", "parse_results", ["keyword", "parsed_at"]
    )
    op.create_index(
        "ix_parse_results_domain_date", "parse_results", ["domain", "parsed_at"]
    )
    op.create_index("ix_parse_results_position", "parse_results", ["position"])
    op.create_index(
        "ix_parse_results_task_keyword", "parse_results", ["task_id", "keyword"]
    )

    # Индексы для таблицы position_history
    op.create_index(
        "ix_position_history_domain_keyword",
        "position_history",
        ["domain_id", "keyword_id"],
    )
    op.create_index(
        "ix_position_history_check_date", "position_history", ["check_date"]
    )
    op.create_index(
        "ix_position_history_user_domain_date",
        "position_history",
        ["user_id", "domain_id", "check_date"],
    )

    # Индексы для таблицы profiles
    op.create_index("ix_profiles_status_device", "profiles", ["status", "device_type"])
    op.create_index("ix_profiles_is_warmed_up", "profiles", ["is_warmed_up"])
    op.create_index("ix_profiles_last_used", "profiles", ["last_used"])

    # Индексы для таблицы user_keywords
    op.create_index(
        "ix_user_keywords_domain_active", "user_keywords", ["domain_id", "is_active"]
    )
    op.create_index("ix_user_keywords_device_type", "user_keywords", ["device_type"])

    # Индексы для таблицы user_domains
    op.create_index(
        "ix_user_domains_user_verified", "user_domains", ["user_id", "is_verified"]
    )
    op.create_index("ix_user_domains_domain", "user_domains", ["domain"])

    # Индексы для таблицы system_logs
    op.create_index(
        "ix_system_logs_level_component", "system_logs", ["level", "component"]
    )
    op.create_index(
        "ix_system_logs_created_at_desc", "system_logs", [sa.text("created_at DESC")]
    )
    op.create_index("ix_system_logs_server_id", "system_logs", ["server_id"])

    # Индексы для таблицы performance_metrics
    op.create_index(
        "ix_performance_metrics_server_type",
        "performance_metrics",
        ["server_id", "metric_type"],
    )
    op.create_index(
        "ix_performance_metrics_measurement_time",
        "performance_metrics",
        ["measurement_time"],
    )

    # Индексы для таблицы balance_transactions
    op.create_index(
        "ix_balance_transactions_user_date",
        "balance_transactions",
        ["user_id", "created_at"],
    )
    op.create_index("ix_balance_transactions_type", "balance_transactions", ["type"])

    # ========================================
    # 5. ДОБАВЛЕНИЕ СИСТЕМНЫХ ПРАВИЛ АЛЕРТОВ
    # ========================================

    print("Adding default alert rules...")

    # Используем connection.execute с text() для корректной обработки
    connection = op.get_bind()

    # Системные алерты для администраторов
    alert_rules_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Воркер недоступен",
            "description": "Воркер не отправлял heartbeat более 5 минут",
            "condition_type": "worker_heartbeat",
            "condition_params": '{"table": "worker_nodes", "field": "last_heartbeat", "unit": "minutes"}',
            "threshold_value": 5,
            "comparison_operator": ">",
            "check_interval_minutes": 2,
            "notification_channels": '{"telegram": true, "email": true, "webhook": false}',
            "cooldown_minutes": 15,
            "alert_level": "error",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Очередь задач переполнена",
            "description": "Количество задач в очереди превышает критический размер",
            "condition_type": "queue_size",
            "condition_params": '{"table": "tasks", "status": "pending"}',
            "threshold_value": 100,
            "comparison_operator": ">",
            "check_interval_minutes": 3,
            "notification_channels": '{"telegram": true, "email": false, "webhook": true}',
            "cooldown_minutes": 30,
            "alert_level": "warning",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Низкий успех выполнения задач",
            "description": "Success rate выполнения задач ниже 85%",
            "condition_type": "success_rate",
            "condition_params": '{"calculation": "completed_tasks/total_tasks", "time_window": "1h"}',
            "threshold_value": 85,
            "comparison_operator": "<",
            "check_interval_minutes": 10,
            "notification_channels": '{"telegram": true, "email": true, "webhook": false}',
            "cooldown_minutes": 60,
            "alert_level": "warning",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Заканчиваются готовые профили",
            "description": "Количество готовых к работе профилей менее 10",
            "condition_type": "profile_count",
            "condition_params": '{"table": "profiles", "conditions": {"is_warmed_up": true, "status": "ready"}}',
            "threshold_value": 10,
            "comparison_operator": "<",
            "check_interval_minutes": 5,
            "notification_channels": '{"telegram": true, "email": false, "webhook": false}',
            "cooldown_minutes": 45,
            "alert_level": "error",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Высокая загрузка сервера",
            "description": "Сервер работает на максимуме более 10 минут",
            "condition_type": "server_load",
            "condition_params": '{"metric_type": "cpu_percent", "time_window": "10m"}',
            "threshold_value": 90,
            "comparison_operator": ">",
            "check_interval_minutes": 5,
            "notification_channels": '{"telegram": false, "email": true, "webhook": true}',
            "cooldown_minutes": 30,
            "alert_level": "warning",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ошибки backup системы",
            "description": "Backup не выполнялся успешно более 24 часов",
            "condition_type": "backup_status",
            "condition_params": '{"table": "backup_history", "status": "completed", "time_window": "24h"}',
            "threshold_value": 0,
            "comparison_operator": "==",
            "check_interval_minutes": 60,
            "notification_channels": '{"telegram": true, "email": true, "webhook": false}',
            "cooldown_minutes": 180,
            "alert_level": "critical",
            "is_active": True,
        },
    ]

    current_time = datetime.utcnow()

    for rule_data in alert_rules_data:
        insert_query = text(
            """
                            INSERT INTO alert_rules (
                                id, created_at, updated_at, name, description, condition_type,
                                condition_params, threshold_value, comparison_operator,
                                check_interval_minutes, notification_channels, cooldown_minutes,
                                alert_level, is_active
                            ) VALUES (
                                         :id, :created_at, :updated_at, :name, :description, :condition_type,
                                         :condition_params, :threshold_value, :comparison_operator,
                                         :check_interval_minutes, :notification_channels, :cooldown_minutes,
                                         :alert_level, :is_active
                                     )
                            """
        )

        connection.execute(
            insert_query,
            {**rule_data, "created_at": current_time, "updated_at": current_time},
        )

    print(
        "✅ Alert system, VNC debug support and performance indexes created successfully!"
    )


def downgrade() -> None:
    """Откатывает изменения"""

    print("Rolling back alert system and VNC debug support...")

    # Удаляем индексы производительности
    performance_indexes = [
        # tasks
        "ix_tasks_status_priority",
        "ix_tasks_created_at_desc",
        "ix_tasks_user_status",
        "ix_tasks_task_type_status",
        "ix_tasks_completed_at",
        # parse_results
        "ix_parse_results_keyword_date",
        "ix_parse_results_domain_date",
        "ix_parse_results_position",
        "ix_parse_results_task_keyword",
        # position_history
        "ix_position_history_domain_keyword",
        "ix_position_history_check_date",
        "ix_position_history_user_domain_date",
        # profiles
        "ix_profiles_status_device",
        "ix_profiles_is_warmed_up",
        "ix_profiles_last_used",
        # user_keywords
        "ix_user_keywords_domain_active",
        "ix_user_keywords_device_type",
        # user_domains
        "ix_user_domains_user_verified",
        "ix_user_domains_domain",
        # system_logs
        "ix_system_logs_level_component",
        "ix_system_logs_created_at_desc",
        "ix_system_logs_server_id",
        # performance_metrics
        "ix_performance_metrics_server_type",
        "ix_performance_metrics_measurement_time",
        # balance_transactions
        "ix_balance_transactions_user_date",
        "ix_balance_transactions_type",
    ]

    for index_name in performance_indexes:
        try:
            op.drop_index(index_name)
            print(f"Dropped index: {index_name}")
        except Exception as e:
            print(f"Warning: Could not drop index {index_name}: {e}")

    # Удаляем индексы VNC таблиц
    op.drop_index("ix_debug_vnc_sessions_created_at")
    op.drop_index("ix_debug_vnc_sessions_vnc_port")
    op.drop_index("ix_debug_vnc_sessions_status")
    op.drop_index("ix_debug_vnc_sessions_user_id")
    op.drop_index("ix_debug_vnc_sessions_task_id")

    # Удаляем индексы alert таблиц
    op.drop_index("ix_alert_history_triggered_at")
    op.drop_index("ix_alert_history_status")
    op.drop_index("ix_alert_history_rule_id")
    op.drop_index("ix_alert_rules_last_check")
    op.drop_index("ix_alert_rules_alert_level")
    op.drop_index("ix_alert_rules_condition_type")
    op.drop_index("ix_alert_rules_is_active")

    # Удаляем таблицы
    op.drop_table("debug_vnc_sessions")
    op.drop_table("alert_history")
    op.drop_table("alert_rules")

    print("🗑️ Alert system and VNC debug support rolled back successfully!")
