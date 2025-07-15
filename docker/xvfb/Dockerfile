# docker/xvfb/Dockerfile
# Xvfb контейнер
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя
RUN useradd -m -s /bin/bash xvfb

# Устанавливаем права на X11 сокеты
RUN mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix

USER xvfb

EXPOSE 6000-6010

CMD ["Xvfb", ":99", "-screen", "0", "1920x1080x24", "-ac", "-nolisten", "tcp", "+extension", "GLX", "+extension", "RANDR", "-dpi", "96"]
