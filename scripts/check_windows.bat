@echo off
title Recon API - Windows System Check
color 0A
echo ========================================
echo   Recon API - Windows System Check
echo ========================================
echo.

echo [1/10] Checking Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python installed
    python --version
) else (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/
)
echo.

echo [2/10] Checking PostgreSQL...
psql --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL installed
    psql --version
) else (
    echo [WARNING] psql not found in PATH
    echo PostgreSQL may be installed but not in PATH
)
echo.

echo [3/10] Checking Redis...
redis-cli --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis installed
    redis-cli --version
) else (
    echo [WARNING] redis-cli not found in PATH
    echo Redis may be installed but not in PATH
)
echo.

echo [4/10] Checking Go...
go version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Go installed
    go version
) else (
    echo [WARNING] Go not found
    echo You need Go to install recon tools
)
echo.

echo [5/10] Checking Recon Tools...
echo.

echo   - Checking subfinder...
subfinder -version >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] subfinder installed
) else (
    echo     [X] subfinder not found
)

echo   - Checking amass...
amass -version >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] amass installed
) else (
    echo     [X] amass not found
)

echo   - Checking assetfinder...
assetfinder -h >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] assetfinder installed
) else (
    echo     [X] assetfinder not found
)

echo   - Checking httpx...
httpx -version >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] httpx installed
) else (
    echo     [X] httpx not found
)

echo   - Checking httprobe...
httprobe -h >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] httprobe installed
) else (
    echo     [X] httprobe not found
)

echo   - Checking anew...
anew -h >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] anew installed
) else (
    echo     [X] anew not found
)

echo   - Checking gowitness...
gowitness version >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] gowitness installed
) else (
    echo     [X] gowitness not found
)
echo.

echo [6/10] Checking Virtual Environment...
if exist "venv\" (
    echo [OK] Virtual environment exists
) else (
    echo [WARNING] Virtual environment not found
    echo Run: python -m venv venv
)
echo.

echo [7/10] Checking .env file...
if exist ".env" (
    echo [OK] .env file exists
) else (
    echo [WARNING] .env file not found
    echo Run: copy .env.example .env
)
echo.

echo [8/10] Checking jobs directory...
if exist "jobs\" (
    echo [OK] jobs directory exists
) else (
    echo [INFO] Creating jobs directory...
    mkdir jobs
    echo [OK] jobs directory created
)
echo.

echo [9/10] Checking Redis connection...

 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis is running
) else (
    echo [WARNING] Cannot connect to Redis
    echo Make sure Redis service is running
)
echo.

echo [10/10] Checking PostgreSQL connection...
echo This requires .env file to be configured
echo.

echo ========================================
echo   System Check Complete
echo ========================================
echo.
echo Next steps:
echo   1. If any tools are missing, install them
echo   2. Create .env file: copy .env.example .env
echo   3. Edit .env with your database password
echo   4. Create database: See WINDOWS_SETUP.md
echo   5. Initialize database: .\scripts\init_db_windows.bat
echo   6. Start API: .\start_api.bat
echo   7. Start Worker: .\start_worker.bat
echo.
echo For detailed instructions, see WINDOWS_SETUP.md
echo.
pause
