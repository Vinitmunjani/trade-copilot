FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV WINEARCH=win64

RUN apt-get update && apt-get install -y \
    wine64 \
    wine-binfmt \
    xvfb \
    python3 python3-pip \
    curl wget \
    ca-certificates \
    xdotool \
    wmctrl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create Wine prefix
RUN mkdir -p /root/.wine/drive_c/Program\ Files/MetaTrader\ 5

WORKDIR /app

RUN pip3 install Flask requests pyautogui

RUN mkdir -p /mt5 /app/scripts /var/log/supervisor

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy MT5 installer (if provided) or download
COPY terminal.exe /app/terminal.exe 2>/dev/null || echo "Terminal installer not provided"

COPY TradeMonitor.mq5 /app/TradeMonitor.mq5
COPY api_server.py /app/api_server.py
COPY health_monitor.py /app/health_monitor.py

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
