@echo off
title Recon API - Starting All Services with Specialized Workers
color 0B
echo ========================================
echo   Recon API - Starting All Services
echo   (Specialized Celery Workers)
echo ========================================
echo.
echo This will open 6 separate windows:
echo   1. API Server (Port 8000)
echo   2. Celery Workers (3 specialized workers)
echo   3. Celery Flower (Port 5555)
echo   4. This control window
echo.
echo Total Workers: 3 specialized workers
echo Note: Using Solo Pool to avoid Windows shared memory issues
echo Each worker is dedicated to a specific task type for optimal resource management
echo.
echo Press any key to continue...
pause >nul

echo.
echo Starting services...
echo.

REM Start API Server in new window
echo [1/4] Starting API Server (Port 8000)...
start "Recon API - Server" cmd /k "start_api.bat"
timeout /t 3 >nul

REM Start Celery Workers in new window
REM This calls start_workers.bat which starts 3 specialized workers
echo [2/4] Starting Celery Workers (recon_full, waf_check, leak_check)...
start "Recon API - Workers" cmd /k "start_workers.bat"
timeout /t 5 >nul

REM Start Flower in new window
echo [3/4] Starting Celery Flower (Port 5555)...
start "Recon API - Flower" cmd /k "start_flower.bat"
timeout /t 2 >nul

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo Services Running:
echo   - API Server: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Flower Monitor: http://localhost:5555
echo   - 3 Specialized Celery Workers:
echo     * Worker 1: recon_full (Full reconnaissance scans)
echo     * Worker 2: waf_check (WAF detection)
echo     * Worker 3: leak_check (SourceLeakHacker leak detection)
echo.
echo To stop all services:
echo   - Close all opened windows
echo   - Or press Ctrl+C in each window
echo.
echo Opening web browser...
timeout /t 3 >nul
start http://localhost:8000

echo.
echo ========================================
echo   Control Window - Keep this open
echo ========================================
echo.
echo All services are running. Close this window to stop monitoring.
echo.
echo For detailed worker information, check Flower at http://localhost:5555
echo.
pause
