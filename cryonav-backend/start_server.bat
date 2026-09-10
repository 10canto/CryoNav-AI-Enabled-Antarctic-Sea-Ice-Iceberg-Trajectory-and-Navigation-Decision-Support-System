@echo off
REM CryoNav AI - Quick Start Script for Windows
echo ========================================
echo   CryoNav AI - Backend Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Start the server
echo ========================================
echo   Starting FastAPI Server
echo ========================================
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

uvicorn app.main:app --reload

pause
