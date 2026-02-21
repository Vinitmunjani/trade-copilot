FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Wine, Xvfb, MT5 dependencies
RUN apt-get update && apt-get install -y \
    wine wine32 wine64 winetricks \
    xvfb x11-utils \
    python3 python3-pip \
    curl wget git \
    ca-certificates openssl \
    libssl-dev libffi-dev \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Set Wine architecture
ENV WINEARCH=win64 WINEPREFIX=/root/.wine

# Download MetaTrader 5 (headless mode)
RUN mkdir -p /mt5 && \
    cd /mt5 && \
    wget -q https://download.mql5.com/mt5/mt5setup.exe -O mt5setup.exe && \
    echo "MT5 installer downloaded"

# Install Python dependencies for health monitoring
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy EA and scripts
COPY ea/ /mt5/ea/
COPY scripts/ /app/scripts/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 /app/scripts/health_monitor.py || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
