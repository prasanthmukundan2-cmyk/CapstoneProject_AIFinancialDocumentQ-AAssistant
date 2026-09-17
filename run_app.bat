@echo off
echo.
echo ============================================================
echo Starting Financial RAG Assistant
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit is not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Run the app
echo Starting application...
echo Open http://localhost:8501 in your browser
echo.
python -m streamlit run app.py

pause
