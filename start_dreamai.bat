@echo off
title DreamAI Application
echo =========================================
echo       Starting DreamAI Project
echo =========================================
echo.

:: Check for virtual environment and activate
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No venv found. Make sure dependencies are installed!
)

:: Schedule the browser to open after 3 seconds so the server has time to start
echo [INFO] Opening browser shortly...
start /b cmd /c "timeout /t 3 >nul && start http://127.0.0.1:5000/"

:: Start the Python backend (This blocks the terminal so you can see logs and stop it with Ctrl+C)
echo [INFO] Starting Flask backend server...
python backend/app.py

echo.
pause
