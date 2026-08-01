@echo off
IF NOT EXIST venv (
    echo Virtual environment not found! Please run install.bat first.
    pause
    exit /b
)

call venv\Scripts\activate
python main_gui.py
pause
