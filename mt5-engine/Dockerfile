FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install MT5 and development dependencies
RUN apt-get update && apt-get install -y \
    wine64 winetricks \
    xvfb x11-utils \
    python3 python3-pip \
    curl wget git \
    ca-certificates openssl \
    libssl-dev libffi-dev \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Set Wine architecture
ENV WINEARCH=win64 WINEPREFIX=/root/.wine

# Download MetaTrader 5 (headless mode) - optional, can be done at runtime
RUN mkdir -p /mt5

# Install Python dependencies for health monitoring
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt 2>/dev/null || pip3 install flask requests

# Copy EA and scripts
COPY ea/ /mt5/ea/ 2>/dev/null || mkdir -p /mt5/ea
COPY scripts/ /app/scripts/ 2>/dev/null || mkdir -p /app/scripts
COPY entrypoint.sh /app/entrypoint.sh || echo "#!/bin/bash" > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
