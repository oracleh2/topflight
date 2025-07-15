# docker/websockify/Dockerfile
# WebSockify прокси
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Клонируем websockify
RUN git clone https://github.com/novnc/websockify.git /app/websockify
WORKDIR /app/websockify

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директории
RUN mkdir -p /app/tokens /app/logs

# Скрипт запуска
COPY websockify_start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 6081

CMD ["/app/start.sh"]

