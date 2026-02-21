#!/bin/bash
python3 << 'PYTHON'
from flask import Flask
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok', 'broker': os.getenv('BROKER', 'unknown')}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PYTHON
