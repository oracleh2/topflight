# backend/app/api/admin/vnc_tokens.py
# Управление токенами для noVNC
import os
import hashlib
import time
from typing import Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class VNCTokenManager:
    """Менеджер токенов для noVNC"""

    def __init__(self):
        self.token_file = "/tmp/vnc_tokens.conf"
        self.tokens: Dict[str, Dict] = {}

    def generate_token(self, task_id: str, vnc_host: str, vnc_port: int) -> str:
        """Генерирует токен для VNC сессии"""
        # Создаем уникальный токен на основе task_id и времени
        token_data = f"{task_id}:{vnc_host}:{vnc_port}:{int(time.time())}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:16]

        # Сохраняем токен
        self.tokens[token] = {
            "task_id": task_id,
            "vnc_host": vnc_host,
            "vnc_port": vnc_port,
            "created_at": time.time(),
        }

        # Обновляем файл токенов
        self._update_token_file()

        logger.info("VNC token generated", task_id=task_id, token=token)
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
            return f"http://localhost:6080/vnc_lite.html?token={token}&autoconnect=true&resize=remote"
        return None

    def _update_token_file(self):
        """Обновляет файл токенов для websockify"""
        try:
            with open(self.token_file, "w") as f:
                for token, data in self.tokens.items():
                    f.write(f"{token}: {data['vnc_host']}:{data['vnc_port']}\n")

            logger.debug("VNC token file updated", token_count=len(self.tokens))

        except Exception as e:
            logger.error("Failed to update token file", error=str(e))

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
            logger.info("Expired VNC tokens cleaned", count=len(expired_tokens))


# Глобальный менеджер токенов
vnc_token_manager = VNCTokenManager()
