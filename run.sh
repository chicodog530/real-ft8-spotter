#!/bin/bash
if [ ! -d "venv" ]; then
    echo "Virtual environment not found! Please run bash install.sh first."
    exit 1
fi

source venv/bin/activate
python3 main_gui.py
