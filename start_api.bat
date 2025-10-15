@echo off
title Recon API - FastAPI Server
echo ========================================
echo Starting Recon API Server
echo ========================================
echo.
echo API will be available at:
echo   - http://localhost:8000
echo   - Swagger Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
