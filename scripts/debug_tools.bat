@echo off
title Debug Recon Tools
color 0E
echo ========================================
echo   Debug Recon Tools Paths
echo ========================================
echo.

echo [1] Checking Go installation...
go version
if %errorlevel% equ 0 (
    echo [OK] Go is installed
) else (
    echo [ERROR] Go not found!
    echo Please install Go from: https://go.dev/dl/
    pause
    exit /b 1
)
echo.

echo [2] Checking GOPATH...
echo GOPATH: %GOPATH%
echo Go bin: %USERPROFILE%\go\bin
echo.

echo [3] Listing tools in Go bin...
dir "%USERPROFILE%\go\bin\*.exe"
echo.

echo [4] Testing each tool...
echo.

echo Testing subfinder...
where subfinder
subfinder -version
echo.

echo Testing amass...
where amass
amass -version
echo.

echo Testing assetfinder...
where assetfinder
assetfinder -h
echo.

echo Testing httpx...
where httpx
httpx -version
echo.

echo Testing httprobe...
where httprobe
httprobe -h
echo.

echo Testing anew...
where anew
anew -h
echo.

echo Testing gowitness...
where gowitness
gowitness version
echo.

echo ========================================
echo   Generating .env configuration
echo ========================================
echo.

echo Copy these lines to your .env file:
echo.
echo # Tool Paths (Windows - Auto-detected)

for %%T in (subfinder amass assetfinder httpx httprobe anew gowitness) do (
    for /f "delims=" %%P in ('where %%T 2^>nul') do (
        echo %%T_PATH=%%P
    )
)

echo.
echo ========================================
echo   PATH Information
echo ========================================
echo.
echo Current PATH:
echo %PATH%
echo.
echo Is Go bin in PATH?
echo %PATH% | findstr /C:"%USERPROFILE%\go\bin" >nul
if %errorlevel% equ 0 (
    echo [OK] Go bin is in PATH
) else (
    echo [WARNING] Go bin is NOT in PATH!
    echo.
    echo To add Go bin to PATH:
    echo   1. Win + R ^> sysdm.cpl
    echo   2. Advanced ^> Environment Variables
    echo   3. System Variables ^> Path ^> Edit
    echo   4. New ^> Add: %USERPROFILE%\go\bin
    echo   5. OK ^> OK ^> OK
    echo   6. Restart all terminals
)
echo.

echo ========================================
echo   Testing from Python
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Testing subprocess call...
python -c "import subprocess; result = subprocess.run(['subfinder', '-version'], capture_output=True, text=True); print('STDOUT:', result.stdout); print('STDERR:', result.stderr); print('Return code:', result.returncode)"
echo.

echo ========================================
echo   Summary
echo ========================================
echo.
echo If tools work in PowerShell but not in Celery:
echo   1. Add Go bin to SYSTEM PATH (not just User PATH)
echo   2. Or specify full paths in .env file
echo   3. Restart all terminals after changing PATH
echo.
pause
