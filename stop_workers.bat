@echo off
REM ========================================
REM   Stop All Celery Workers
REM ========================================

echo.
echo ========================================
echo   Stopping All Celery Workers
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Shutdown all workers gracefully
echo Sending shutdown signal to all workers...
celery -A app.workers.celery_app control shutdown

echo.
echo Waiting for workers to shutdown...
timeout /t 3 /nobreak >nul

REM Force kill any remaining celery processes
echo.
echo Checking for remaining celery processes...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Celery*" 2>nul | find /I "python.exe" >nul
if %errorlevel% equ 0 (
    echo Found remaining processes, force killing...
    taskkill /F /FI "WINDOWTITLE eq Celery*" 2>nul
) else (
    echo No remaining processes found
)

echo.
echo ========================================
echo   All Workers Stopped
echo ========================================
echo.

pause

