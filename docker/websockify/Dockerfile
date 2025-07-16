# docker/websockify/Dockerfile
# WebSockify прокси
FROM python:3.11-slim

# Установка переменной окружения
ENV PROJECT_ROOT=/var/www/topflight

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Клонируем websockify
#RUN git clone https://github.com/novnc/websockify.git /app/websockify
#WORKDIR /app/websockify
# Клонирование проекта в ${PROJECT_ROOT}/websockify
RUN git clone https://github.com/novnc/websockify ${PROJECT_ROOT}/websockify
WORKDIR ${PROJECT_ROOT}/websockify


# Устанавливаем зависимости
RUN #pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r test-requirements.txt

# Создаем директории
RUN #mkdir -p /app/tokens /app/logs
RUN mkdir -p ${PROJECT_ROOT}/tokens ${PROJECT_ROOT}/logs

# Скрипт запуска
#COPY websockify_start.sh /app/start.sh
COPY websockify_start.sh ${PROJECT_ROOT}/start.sh
RUN #chmod +x /app/start.sh
RUN chmod +x ${PROJECT_ROOT}/start.sh

EXPOSE 6081

#CMD ["/app/start.sh"]
CMD ["sh", "-c", "$PROJECT_ROOT/start.sh"]

