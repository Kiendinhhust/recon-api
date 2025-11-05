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
echo This will start 3 parallel workers for load balancing:
echo   - Worker 1: Listening to ALL queues (recon_full, waf_check, leak_check)
echo   - Worker 2: Listening to ALL queues (recon_full, waf_check, leak_check)
echo   - Worker 3: Listening to ALL queues (recon_full, waf_check, leak_check)
echo.
echo Note: On Windows with --pool=solo, each worker handles 1 task at a time.
echo Parallelism is achieved by running multiple worker processes.
echo All workers can pick up tasks from any queue for better load balancing.
echo.
echo Press Ctrl+C in each terminal to stop workers
echo ========================================
echo.

REM Start Worker 1 in new window (All queues)
echo Starting Worker 1 (All Queues)...
start "Celery Worker 1 - All Queues" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,waf_check,leak_check -n worker1@%%h"

timeout /t 2 /nobreak >nul

REM Start Worker 2 in new window (All queues)
echo Starting Worker 2 (All Queues)...
start "Celery Worker 2 - All Queues" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,waf_check,leak_check -n worker2@%%h"

timeout /t 2 /nobreak >nul

REM Start Worker 3 in new window (All queues)
echo Starting Worker 3 (All Queues)...
start "Celery Worker 3 - All Queues" cmd /k "venv\Scripts\activate.bat && celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,waf_check,leak_check -n worker3@%%h"

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

