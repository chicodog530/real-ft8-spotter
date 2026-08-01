#!/bin/bash
echo "=============================================="
echo "Installing Real FT8 Spotter Dependencies"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed!"
    echo "Please install Python 3.8 or newer."
    exit 1
fi

echo ""
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo ""
echo "Installing requirements from requirements.txt..."
python3 -m pip install -r requirements.txt

# On Linux, pyttsx3 might need espeak and ffmpeg, so warn the user
if [ "$(uname)" == "Linux" ]; then
    echo ""
    echo "Note for Linux Users: The Voice Alerts system (pyttsx3) requires 'espeak' and 'ffmpeg'."
    echo "If you haven't installed them, please run: sudo apt-get install espeak ffmpeg"
fi

echo ""
echo "=============================================="
echo "Installation Complete!"
echo "You can now launch the application by running:"
echo "python3 main_gui.py"
echo "=============================================="
