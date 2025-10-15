@echo off
title Recon API - Celery Worker
echo ========================================
echo Starting Celery Worker
echo ========================================
echo.
echo Worker is processing background tasks
echo Press Ctrl+C to stop the worker
echo ========================================
echo.

REM Add Go bin to PATH
set PATH=%PATH%;%USERPROFILE%\go\bin

REM Verify tools are accessible
echo Checking tools...
where subfinder >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] subfinder found
) else (
    echo [WARNING] subfinder not found in PATH
)
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Celery worker with all queues
celery -A app.workers.celery_app worker --loglevel=info --pool=solo --concurrency=2 -Q recon_full,recon_enum,recon_check,recon_screenshot,maintenance,celery
