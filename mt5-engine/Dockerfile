FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV WINEARCH=win64
ENV WINEPREFIX=/root/.wine

# Install dependencies (wine64 only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wine64 \
    wine-binfmt \
    xvfb \
    xdotool \
    dbus \
    dbus-user-session \
    python3 python3-pip \
    curl wget \
    ca-certificates \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

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

RUN chmod +x /app/download_mt5.sh /app/setup_mt5.sh /app/entrypoint.sh

# Create Wine and terminal directories
RUN mkdir -p /root/.wine/drive_c/Program\ Files/MT5 /app/terminal /tmp

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
