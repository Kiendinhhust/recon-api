@echo off
title Recon API - Celery Flower
echo ========================================
echo Starting Celery Flower (Monitoring)
echo ========================================
echo.
echo Flower will be available at:
echo   - http://localhost:5555
echo.
echo Press Ctrl+C to stop Flower
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Flower
celery -A app.workers.celery_app flower
