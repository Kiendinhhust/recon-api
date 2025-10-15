@echo off
REM ========================================
REM   Start Multiple Celery Workers
REM   For parallel domain scanning
REM ========================================

echo.
echo ========================================
echo   Starting Multiple Celery Workers
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Add Go bin to PATH
set PATH=%PATH%;E:\gopath\bin

REM Check tools
echo Checking tools...
where subfinder >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] subfinder found
) else (
    echo [WARNING] subfinder not found in PATH
)

echo.
echo ========================================
echo   Worker Configuration
echo ========================================
echo.
echo This will start 3 workers:
echo   - Worker 1: recon_full (1 task per worker)
echo   - Worker 2: recon_full (1 task per worker)
echo   - Worker 3: recon_enum, recon_check, recon_screenshot, maintenance, celery (1 task per worker)
echo.
echo Note: On Windows with --pool=solo, each worker handles 1 task at a time.
echo Parallelism is achieved by running multiple worker processes.
echo.
echo Press Ctrl+C in each terminal to stop workers
echo ========================================
echo.

REM Start Worker 1 in new window (Full scans)
echo Starting Worker 1 (recon_full)...
start "Celery Worker 1 - recon_full" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full -n worker1@%%h"

timeout /t 2 /nobreak >nul

REM Start Worker 2 in new window (Full scans)
echo Starting Worker 2 (recon_full)...
start "Celery Worker 2 - recon_full" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full -n worker2@%%h"

timeout /t 2 /nobreak >nul

REM Start Worker 3 in new window (Enum/Check/Screenshot/Maintenance)
echo Starting Worker 3 (enum/check/screenshot/maintenance)...
start "Celery Worker 3 - misc" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_enum,recon_check,recon_screenshot,maintenance,celery -n worker3@%%h"

echo.
echo ========================================
echo   Workers Started!
echo ========================================
echo.
echo Check the new terminal windows for worker logs
echo.
echo To monitor all workers:
echo   celery -A app.workers.celery_app inspect active
echo.
echo To stop all workers:
echo   Close each worker terminal window
echo   OR run: celery -A app.workers.celery_app control shutdown
echo.
echo ========================================

pause

