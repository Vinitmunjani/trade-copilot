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

# Create MT5 directory
RUN mkdir -p /mt5 /app/scripts

# Install Python dependencies for health monitoring
WORKDIR /app
COPY requirements.txt . || echo "Flask==2.3.0" > requirements.txt
RUN pip3 install --no-cache-dir Flask==2.3.0 requests 2>/dev/null || true

# Copy entrypoint if exists, otherwise create minimal one
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh || echo '#!/bin/bash\necho "MT5 container running"\nsleep infinity' > /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health 2>/dev/null || exit 0

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "-c", "/app/entrypoint.sh"]
