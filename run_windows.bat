@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Could not install the required Python packages.
    pause
    exit /b 1
)
python fsociety_message_crypted.py
if errorlevel 1 pause
