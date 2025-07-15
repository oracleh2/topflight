# backend/app/core/vnc_metrics.py
from prometheus_client import Counter, Gauge, Histogram
import time
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)

# Prometheus метрики для VNC системы
vnc_active_sessions_total = Gauge(
    "vnc_active_sessions_total", "Total number of active VNC debug sessions"
)

vnc_session_duration_seconds = Histogram(
    "vnc_session_duration_seconds",
    "Duration of VNC debug sessions in seconds",
    buckets=[30, 60, 300, 600, 1800, 3600, 7200],  # 30s, 1m, 5m, 10m, 30m, 1h, 2h
)

debug_tasks_total = Counter(
    "debug_tasks_total",
    "Total number of debug tasks created",
    ["device_type", "status"],  # labels: desktop/mobile, success/failed
)

vnc_connection_errors_total = Counter(
    "vnc_connection_errors_total",
    "Total number of VNC connection errors",
    ["error_type"],  # labels: xvfb_failed, vnc_failed, browser_failed
)

vnc_sessions_created_total = Counter(
    "vnc_sessions_created_total",
    "Total number of VNC sessions created",
    ["device_type"],
)

vnc_sessions_terminated_total = Counter(
    "vnc_sessions_terminated_total",
    "Total number of VNC sessions terminated",
    ["reason"],  # manual, timeout, error, cleanup
)


class VNCMetricsCollector:
    """Сборщик метрик для VNC системы"""

    def __init__(self):
        self.session_start_times: Dict[str, float] = {}

    def record_session_created(self, task_id: str, device_type: str):
        """Записывает создание новой VNC сессии"""
        try:
            self.session_start_times[task_id] = time.time()
            vnc_sessions_created_total.labels(device_type=device_type).inc()
            debug_tasks_total.labels(device_type=device_type, status="success").inc()
            logger.info(
                "VNC session metrics recorded", task_id=task_id, device_type=device_type
            )
        except Exception as e:
            logger.error("Failed to record session creation metrics", error=str(e))

    def record_session_terminated(self, task_id: str, reason: str = "manual"):
        """Записывает завершение VNC сессии"""
        try:
            if task_id in self.session_start_times:
                duration = time.time() - self.session_start_times[task_id]
                vnc_session_duration_seconds.observe(duration)
                del self.session_start_times[task_id]
                logger.info(
                    "VNC session duration recorded", task_id=task_id, duration=duration
                )

            vnc_sessions_terminated_total.labels(reason=reason).inc()
            logger.info(
                "VNC session termination recorded", task_id=task_id, reason=reason
            )
        except Exception as e:
            logger.error("Failed to record session termination metrics", error=str(e))

    def record_connection_error(self, error_type: str, task_id: str = None):
        """Записывает ошибку подключения VNC"""
        try:
            vnc_connection_errors_total.labels(error_type=error_type).inc()
            debug_tasks_total.labels(device_type="unknown", status="failed").inc()
            logger.error(
                "VNC connection error recorded", error_type=error_type, task_id=task_id
            )
        except Exception as e:
            logger.error("Failed to record connection error metrics", error=str(e))

    def update_active_sessions_count(self, count: int):
        """Обновляет количество активных сессий"""
        try:
            vnc_active_sessions_total.set(count)
        except Exception as e:
            logger.error("Failed to update active sessions count", error=str(e))

    def record_debug_task_failed(self, device_type: str, task_id: str):
        """Записывает неудачный запуск debug задачи"""
        try:
            debug_tasks_total.labels(device_type=device_type, status="failed").inc()
            logger.error(
                "Debug task failed recorded", device_type=device_type, task_id=task_id
            )
        except Exception as e:
            logger.error("Failed to record debug task failure", error=str(e))


# Глобальный сборщик метрик
metrics_collector = VNCMetricsCollector()
