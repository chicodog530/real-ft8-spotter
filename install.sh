#!/bin/bash
echo "=============================================="
echo "Installing Real FT8 Spotter Dependencies"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed! Please install Python 3.8 or newer."
    exit 1
fi

echo "Creating a safe Virtual Environment..."
# Ensure the python3-venv package is installed (sometimes missing on Ubuntu/Debian)
if ! python3 -m venv venv; then
    echo ""
    echo "ERROR: Failed to create virtual environment."
    echo "If you are on Debian/Ubuntu, you may need to install the venv package first:"
    echo "sudo apt-get install python3-venv"
    exit 1
fi

echo "Activating Virtual Environment..."
source venv/bin/activate

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing requirements from requirements.txt..."
python3 -m pip install -r requirements.txt

# Linux specific warning for pyttsx3
if [ "$(uname)" == "Linux" ]; then
    echo ""
    echo "Note: The Voice Alerts system (pyttsx3) requires 'espeak' and 'ffmpeg'."
    echo "If you haven't installed them, please run: sudo apt-get install espeak ffmpeg"
fi

echo ""
echo "=============================================="
echo "Installation Complete!"
echo "You can now launch the application at any time by running:"
echo "bash run.sh"
echo "=============================================="
