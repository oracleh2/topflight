#!/usr/bin/env python3
"""
Yandex Parser Monitor
Мониторинг состояния API и системных ресурсов
"""

import os
import sys
import time
import json
import psutil
import requests
import logging
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/www/topflight/logs/backend-monitor.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("yandex-parser-monitor")


class SystemMonitor:
    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.check_interval = int(os.getenv("MONITOR_INTERVAL", "300"))  # 5 минут
        self.stats_file = Path("/var/www/topflight/logs/monitor_stats.json")

    def check_api_health(self):
        """Проверка доступности API"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ API здоров: {response.status_code}")
                return True
            else:
                logger.warning(f"⚠️ API вернул статус: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API недоступен: {e}")
            return False

    def check_system_resources(self):
        """Проверка системных ресурсов"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Память
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)

            # Диск
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)

            # Логируем состояние
            logger.info(f"📊 Системные ресурсы:")
            logger.info(f"   CPU: {cpu_percent:.1f}%")
            logger.info(
                f"   RAM: {memory_percent:.1f}% (свободно: {memory_available_gb:.1f}GB)"
            )
            logger.info(
                f"   Диск: {disk_percent:.1f}% (свободно: {disk_free_gb:.1f}GB)"
            )

            # Предупреждения
            if cpu_percent > 80:
                logger.warning(f"⚠️ Высокая загрузка CPU: {cpu_percent:.1f}%")

            if memory_percent > 85:
                logger.warning(f"⚠️ Высокое использование памяти: {memory_percent:.1f}%")

            if disk_percent > 90:
                logger.warning(f"⚠️ Мало места на диске: {disk_percent:.1f}%")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": memory_available_gb,
                "disk_percent": disk_percent,
                "disk_free_gb": disk_free_gb,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки ресурсов: {e}")
            return None

    def check_log_files(self):
        """Проверка размеров файлов логов"""
        logs_dir = Path("/var/www/topflight/logs")
        log_info = {}

        try:
            for log_file in logs_dir.glob("backend-*.log"):
                if log_file.is_file():
                    size_mb = log_file.stat().st_size / (1024**2)
                    log_info[log_file.name] = {
                        "size_mb": round(size_mb, 2),
                        "modified": datetime.fromtimestamp(
                            log_file.stat().st_mtime
                        ).isoformat(),
                    }

                    # Предупреждение о больших файлах
                    if size_mb > 100:
                        logger.warning(
                            f"⚠️ Большой файл лога: {log_file.name} ({size_mb:.1f}MB)"
                        )

            logger.info(f"📁 Файлы логов проверены: {len(log_info)} файлов")
            return log_info

        except Exception as e:
            logger.error(f"❌ Ошибка проверки логов: {e}")
            return {}

    def check_processes(self):
        """Проверка запущенных процессов PM2"""
        try:
            # Проверяем процессы Python, связанные с нашим API
            api_processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_percent"]
            ):
                try:
                    if "python" in proc.info["name"].lower():
                        cmdline = (
                            " ".join(proc.info["cmdline"])
                            if proc.info["cmdline"]
                            else ""
                        )
                        if "run_api.py" in cmdline or "yandex-parser" in cmdline:
                            api_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cpu_percent": proc.info["cpu_percent"],
                                    "memory_percent": proc.info["memory_percent"],
                                    "cmdline": cmdline,
                                }
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.info(f"🔄 Найдено API процессов: {len(api_processes)}")
            return api_processes

        except Exception as e:
            logger.error(f"❌ Ошибка проверки процессов: {e}")
            return []

    def save_stats(self, stats):
        """Сохранение статистики в файл"""
        try:
            # Читаем существующую статистику
            if self.stats_file.exists():
                with open(self.stats_file, "r") as f:
                    all_stats = json.load(f)
            else:
                all_stats = []

            # Добавляем новую запись
            all_stats.append(stats)

            # Оставляем только последние 100 записей
            if len(all_stats) > 100:
                all_stats = all_stats[-100:]

            # Сохраняем
            with open(self.stats_file, "w") as f:
                json.dump(all_stats, f, indent=2)

            logger.info(f"💾 Статистика сохранена ({len(all_stats)} записей)")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения статистики: {e}")

    def run_check(self):
        """Выполнить один цикл проверки"""
        logger.info("🔍 Начало проверки системы...")

        stats = {
            "timestamp": datetime.now().isoformat(),
            "api_health": self.check_api_health(),
            "system_resources": self.check_system_resources(),
            "log_files": self.check_log_files(),
            "processes": self.check_processes(),
        }

        # Сохраняем статистику
        self.save_stats(stats)

        logger.info("✅ Проверка завершена")
        return stats

    def run_continuous(self):
        """Непрерывный мониторинг"""
        logger.info(f"🚀 Запуск мониторинга (интервал: {self.check_interval}с)")

        while True:
            try:
                self.run_check()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("🛑 Мониторинг остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Ждем минуту перед повтором


def main():
    """Главная функция"""
    monitor = SystemMonitor()

    # Проверяем режим работы
    mode = os.getenv("MONITOR_MODE", "single")

    if mode == "continuous":
        monitor.run_continuous()
    else:
        # Однократная проверка (для cron)
        monitor.run_check()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка монитора: {e}")
        sys.exit(1)
