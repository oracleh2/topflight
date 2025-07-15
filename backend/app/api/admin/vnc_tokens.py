# backend/app/api/admin/vnc_tokens.py - обновленная версия
"""
Управление токенами для noVNC с правильными путями
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional
import structlog

logger = structlog.get_logger(__name__)

# Пути проекта
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/var/www/topflight"))
VNC_TOKENS_DIR = PROJECT_ROOT / "data" / "vnc_tokens"


class VNCTokenManager:
    """Менеджер токенов для noVNC с обновленными путями"""

    def __init__(self):
        self.token_file = VNC_TOKENS_DIR / "vnc_tokens.conf"
        self.tokens: Dict[str, Dict] = {}

        # Создаем директорию если не существует
        VNC_TOKENS_DIR.mkdir(parents=True, exist_ok=True)

        # Создаем файл токенов если не существует
        if not self.token_file.exists():
            self.token_file.touch()

        logger.info(
            "VNC Token Manager initialized",
            token_file=str(self.token_file),
            project_root=str(PROJECT_ROOT),
        )

    def generate_token(self, task_id: str, vnc_host: str, vnc_port: int) -> str:
        """Генерирует токен для VNC сессии"""
        token_data = f"{task_id}:{vnc_host}:{vnc_port}:{int(time.time())}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:16]

        self.tokens[token] = {
            "task_id": task_id,
            "vnc_host": vnc_host,
            "vnc_port": vnc_port,
            "created_at": time.time(),
            "project_root": str(PROJECT_ROOT),
        }

        self._update_token_file()

        logger.info(
            "VNC token generated", task_id=task_id, token=token, vnc_port=vnc_port
        )
        return token

    def revoke_token(self, task_id: str) -> bool:
        """Отзывает токен для задачи"""
        tokens_to_remove = [
            token for token, data in self.tokens.items() if data["task_id"] == task_id
        ]

        for token in tokens_to_remove:
            del self.tokens[token]

        if tokens_to_remove:
            self._update_token_file()
            logger.info(
                "VNC tokens revoked", task_id=task_id, count=len(tokens_to_remove)
            )
            return True

        return False

    def get_vnc_url(self, token: str) -> Optional[str]:
        """Получает URL для noVNC по токену"""
        if token in self.tokens:
            data = self.tokens[token]
            base_url = f"http://localhost:6080"
            return (
                f"{base_url}/vnc_lite.html?token={token}&autoconnect=true&resize=remote"
            )
        return None

    def _update_token_file(self):
        """Обновляет файл токенов для websockify"""
        try:
            # Создаем временный файл
            temp_file = self.token_file.with_suffix(".tmp")

            with open(temp_file, "w") as f:
                for token, data in self.tokens.items():
                    f.write(f"{token}: {data['vnc_host']}:{data['vnc_port']}\n")

            # Атомарно заменяем основной файл
            temp_file.replace(self.token_file)

            # Устанавливаем права доступа
            try:
                os.chmod(self.token_file, 0o644)
                if os.getuid() == 0:  # Если запущено от root
                    import pwd

                    try:
                        topflight_uid = pwd.getpwnam("topflight").pw_uid
                        topflight_gid = pwd.getpwnam("topflight").pw_gid
                        os.chown(self.token_file, topflight_uid, topflight_gid)
                    except KeyError:
                        pass
            except Exception as e:
                logger.warning("Failed to set token file permissions", error=str(e))

            logger.debug(
                "VNC token file updated",
                token_count=len(self.tokens),
                token_file=str(self.token_file),
            )

        except Exception as e:
            logger.error(
                "Failed to update token file",
                token_file=str(self.token_file),
                error=str(e),
            )

    def cleanup_expired_tokens(self, max_age: int = 7200):  # 2 часа
        """Очищает устаревшие токены"""
        current_time = time.time()
        expired_tokens = [
            token
            for token, data in self.tokens.items()
            if current_time - data["created_at"] > max_age
        ]

        for token in expired_tokens:
            del self.tokens[token]

        if expired_tokens:
            self._update_token_file()
            logger.info(
                "Expired VNC tokens cleaned", count=len(expired_tokens), max_age=max_age
            )


# Глобальный менеджер токенов
vnc_token_manager = VNCTokenManager()
