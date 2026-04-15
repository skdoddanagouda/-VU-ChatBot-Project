@echo off
TITLE VURA Chatbot - Debug Mode (Port 5050)
echo ========================================
echo   VURA Chatbot Diagnostic Starter
echo ========================================
echo.

:: Ensure we are in the project root
cd /d "%~dp0"

echo [STEP 1] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    pause
    exit /b
)
echo [OK] Python found.

echo [STEP 2] Checking for backend folder...
if not exist "backend\server.py" (
    echo [ERROR] Could not find backend\server.py. 
    echo Current folder: %CD%
    dir
    pause
    exit /b
)
echo [OK] Backend files found.

echo [STEP 3] Checking if port 5050 is busy...
netstat -ano | findstr :5050 >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 5050 is ALREADY in use. 
    echo.
    echo Opening the browser for you now...
    start http://127.0.0.1:5050
    pause
    exit /b
)

echo [STEP 4] Installing dependencies...
python -m pip install -r requirements.txt --quiet
echo [OK] Dependencies checked.

echo [STEP 5] Starting the Browser...
start http://127.0.0.1:5050

echo [STEP 6] Starting VURA Server on Port 5050...
echo.
.\venv\Scripts\python backend/server.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The server stopped unexpectedly.
)

pause
