@echo off
:: Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.10 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if dependencies are installed
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

:: Run the application
echo Starting RSA Spectrum Analyzer GUI...
python rsa_gui.py

:: Keep window open after application closes
echo.
echo Application has exited.
pause
