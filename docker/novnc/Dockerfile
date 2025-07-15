# docker/novnc/Dockerfile
# Docker контейнер для noVNC web-интерфейса
FROM node:18-alpine AS builder

# Устанавливаем git для клонирования noVNC
RUN apk add --no-cache git

# Клонируем noVNC
WORKDIR /app
RUN git clone https://github.com/novnc/noVNC.git .
RUN git checkout v1.4.0

# Собираем noVNC
RUN npm install
RUN ./utils/make_lite.sh

# Создаем production образ
FROM nginx:alpine

# Копируем собранный noVNC
COPY --from=builder /app /usr/share/nginx/html

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Создаем конфигурационный файл для noVNC
RUN echo '{"vnc_host": "127.0.0.1", "vnc_port": 5900, "password": ""}' > /usr/share/nginx/html/vnc_config.json

EXPOSE 6080

CMD ["nginx", "-g", "daemon off;"]
