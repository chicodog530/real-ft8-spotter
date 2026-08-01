@echo off
echo ==============================================
echo Installing Real FT8 Spotter Dependencies
echo ==============================================

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in your PATH!
    echo Please install Python 3.8 or newer from https://www.python.org/downloads/
    pause
    exit /b
)

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing requirements from requirements.txt...
python -m pip install -r requirements.txt

echo.
echo ==============================================
echo Installation Complete!
echo You can now launch the application by running:
echo python main_gui.py
echo ==============================================
pause
