FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV WINEARCH=win64
ENV WINEPREFIX=/root/.wine

# Install dependencies - avoid wine conflicts with smaller install
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xdotool \
    python3 python3-pip \
    curl wget \
    ca-certificates \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Install Wine separately with --fix-missing
RUN apt-get update && apt-get install -y --fix-missing \
    wine64 \
    wine-binfmt \
    && rm -rf /var/lib/apt/lists/* || true

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy scripts
COPY download_mt5.sh /app/download_mt5.sh
COPY setup_mt5.sh /app/setup_mt5.sh
COPY entrypoint.sh /app/entrypoint.sh
COPY api_server.py /app/api_server.py
COPY ea/TradeMonitor.mq5 /app/TradeMonitor.mq5

# Copy MT5 terminal executable
COPY terminal64.exe /app/terminal/terminal64.exe

RUN chmod +x /app/download_mt5.sh /app/setup_mt5.sh /app/entrypoint.sh

# Create Wine and terminal directories
RUN mkdir -p /root/.wine/drive_c/Program\ Files/MT5 /app/terminal /tmp

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
