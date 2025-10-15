@echo off
title Recon API - Starting All Services
color 0B
echo ========================================
echo   Recon API - Starting All Services
echo ========================================
echo.
echo This will open 3 separate windows:
echo   1. API Server (Port 8000)
echo   2. Celery Worker
echo   3. Celery Flower (Port 5555)
echo.
echo Press any key to continue...
pause >nul

echo.
echo Starting services...
echo.

REM Start API Server in new window
echo [1/3] Starting API Server...
start "Recon API - Server" cmd /k "start_api.bat"
timeout /t 2 >nul

REM Start Celery Worker in new window
echo [2/3] Starting Celery Worker...
start "Recon API - Worker" cmd /k "start_worker.bat"
timeout /t 2 >nul

REM Start Flower in new window
echo [3/3] Starting Celery Flower...
start "Recon API - Flower" cmd /k "start_flower.bat"
timeout /t 2 >nul

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo Access the application:
echo   - Web Interface: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Flower Monitor: http://localhost:5555
echo.
echo To stop all services:
echo   - Close all opened windows
echo   - Or press Ctrl+C in each window
echo.
echo Opening web browser...
timeout /t 3 >nul
start http://localhost:8000

echo.
echo Press any key to exit this window...
pause >nul
