# backend/Dockerfile - Минимальный Dockerfile для TopFlight

FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    xvfb \
    x11vnc \
    x11-utils \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя
RUN useradd -m -s /bin/bash topflight

# Устанавливаем рабочую директорию
WORKDIR /var/www/topflight/backend

RUN ls

# Копируем requirements и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Устанавливаем права
RUN chown -R topflight:topflight /var/www/topflight

# Переключаемся на пользователя topflight
USER topflight

# Устанавливаем переменные окружения
ENV DISPLAY=:99
ENV PROJECT_ROOT=/var/www/topflight
ENV PYTHONPATH=/var/www/topflight/backend

# Порт для API
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "run_api.py"]



# docker/xvfb/Dockerfile - Dockerfile для Xvfb контейнера

#FROM ubuntu:22.04
#
## Устанавливаем Xvfb и утилиты
#RUN apt-get update && apt-get install -y \
#    xvfb \
#    x11-utils \
#    && rm -rf /var/lib/apt/lists/*
#
## Создаем пользователя
#RUN useradd -m -s /bin/bash topflight
#
## Создаем директории
#RUN mkdir -p /tmp/.X11-unix && \
#    chmod 1777 /tmp/.X11-unix
#
#USER topflight
#
#EXPOSE 6000-6010
#
#CMD ["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-ac", "-nolisten", "tcp", "+extension", "GLX", "+extension", "RANDR", "-dpi", "96"]



# docker/novnc/Dockerfile - Dockerfile для noVNC

#FROM node:18-alpine AS builder
#
#RUN apk add --no-cache git
#
#WORKDIR /app
#RUN git clone https://github.com/novnc/noVNC.git .
#RUN git checkout v1.4.0
#
#FROM nginx:alpine
#
#COPY --from=builder /app /usr/share/nginx/html
#
#COPY nginx.conf /etc/nginx/conf.d/default.conf
#
#EXPOSE 6080
#
#CMD ["nginx", "-g", "daemon off;"]



# docker/novnc/nginx.conf - Конфигурация nginx для noVNC

#server {
#    listen 6080;
#    server_name localhost;
#
#    root /usr/share/nginx/html;
#    index vnc_lite.html;
#
#    location / {
#        try_files $uri $uri/ /vnc_lite.html;
#    }
#
#    location /websockify {
#        proxy_pass http://backend:8000;
#        proxy_http_version 1.1;
#        proxy_set_header Upgrade $http_upgrade;
#        proxy_set_header Connection $connection_upgrade;
#        proxy_set_header Host $host;
#        proxy_read_timeout 3600s;
#        proxy_send_timeout 3600s;
#    }
#}
#
#map $http_upgrade $connection_upgrade {
#    default upgrade;
#    '' close;
#}

