#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Virtual muhit yaratilmoqda..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

echo "🎬 Kino bot ishga tushirilmoqda..."
./venv/bin/python3 main.py

