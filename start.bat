@echo off
echo ========================================
echo Amazon Review Insight Pro - Starting
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
) else (
    echo Virtual environment not found. Using system Python.
    echo.
    echo Note: It is recommended to create a virtual environment first.
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    echo.
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not found in PATH. Please install Python 3.10+ and add it to PATH.
    echo.
    echo Press any key to close...
    pause >nul
    exit /b 1
)

REM Check if Streamlit is installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlit is not installed. Installing dependencies...
    python -m pip install -r requirements.txt
    echo.
)

REM Start Streamlit app
echo Starting Streamlit application...
echo.
echo The application will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.
echo ========================================

REM Try to open Chrome in full-screen mode if available
set "CHROME_PATH="
for %%p in (
    "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
    "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    "%LocalAppData%\Google\Chrome\Application\chrome.exe"
) do (
    if exist %%p (
        set "CHROME_PATH=%%p"
        goto :chrome_found
    )
)

:chrome_found
if defined CHROME_PATH (
    echo Opening Chrome in full-screen mode...
    start "" "%CHROME_PATH%" --start-fullscreen "http://localhost:8501"
) else (
    echo Chrome not found. Streamlit will open in default browser...
)

REM Start Streamlit (this keeps the terminal open)
streamlit run app.py

REM If Streamlit exits, keep terminal open for error viewing
if errorlevel 1 (
    echo.
    echo ========================================
    echo Error occurred. Press any key to close...
    echo ========================================
    pause >nul
)