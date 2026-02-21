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

EXPOSE 5000

CMD ["python3", "-c", "from flask import Flask; app = Flask(__name__); @app.route('/health'); def health(): return {'status': 'ok'}; app.run(host='0.0.0.0', port=5000)"]
