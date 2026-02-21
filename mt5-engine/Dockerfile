FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wine64 \
    xvfb \
    python3 python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install Flask requests

RUN mkdir -p /mt5 /app/scripts

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
