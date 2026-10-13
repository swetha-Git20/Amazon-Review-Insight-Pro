@echo off
echo ===================================================
echo Amazon Review Insight Pro Analyzer - Starting
echo ===================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment active.
    echo.
) else (
    echo Virtual environment not found. Using system Python.
    echo.
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found in PATH. Please install Python 3.10+ and add it to PATH.
    echo.
    pause
    exit /b 1
)

REM Start Amazon Review Insight Pro Analyzer
echo Launching Amazon Review Insight Pro Analyzer...
echo The application will open automatically in your browser.
echo.
streamlit run app.py

if errorlevel 1 (
    echo.
    echo An unexpected error occurred while running the application.
    pause
)