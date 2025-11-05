# Recon API - Start All Services with Multiple Workers (Windows Compatible)
# This script starts API, 4 Celery workers (solo pool), and Flower

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Recon API - Starting All Services" -ForegroundColor Green
Write-Host "  (Multiple Celery Workers - Solo Pool)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if venv exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "Services to start:" -ForegroundColor Cyan
Write-Host "  1. API Server (Port 8000)" -ForegroundColor White
Write-Host "  2. Celery Worker 1 (Solo Pool)" -ForegroundColor White
Write-Host "  3. Celery Worker 2 (Solo Pool)" -ForegroundColor White
Write-Host "  4. Celery Worker 3 (Solo Pool)" -ForegroundColor White
Write-Host "  5. Celery Worker 4 (Solo Pool)" -ForegroundColor White
Write-Host "  6. Celery Flower (Port 5555)" -ForegroundColor White
Write-Host ""
Write-Host "Total: 4 workers (each processes tasks sequentially)" -ForegroundColor Yellow
Write-Host "Note: Using Solo Pool to avoid Windows shared memory issues" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Press Enter to continue or 'q' to quit"
if ($response -eq 'q') {
    exit 0
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Function to start a process in a new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [int]$Index,
        [int]$Total
    )
    
    Write-Host "[$Index/$Total] Starting $Title..." -ForegroundColor Yellow
    
    $scriptBlock = {
        param($cmd, $title)
        $host.UI.RawUI.WindowTitle = $title
        Invoke-Expression $cmd
    }
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock, "-ArgumentList", "`"$Command`", `"$Title`"" -WindowStyle Normal
    Start-Sleep -Seconds 2
}

# Start API Server
Start-ServiceWindow -Title "Recon API - Server" -Command ".\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -Index 1 -Total 6

# Start Celery Workers with Solo Pool
Start-ServiceWindow -Title "Recon API - Worker 1" -Command ".\venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info -Q scans --pool=solo -n worker1@`$env:COMPUTERNAME" -Index 2 -Total 6

Start-ServiceWindow -Title "Recon API - Worker 2" -Command ".\venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info -Q scans --pool=solo -n worker2@`$env:COMPUTERNAME" -Index 3 -Total 6

Start-ServiceWindow -Title "Recon API - Worker 3" -Command ".\venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info -Q scans --pool=solo -n worker3@`$env:COMPUTERNAME" -Index 4 -Total 6

Start-ServiceWindow -Title "Recon API - Worker 4" -Command ".\venv\Scripts\celery -A app.workers.celery_app worker --loglevel=info -Q scans --pool=solo -n worker4@`$env:COMPUTERNAME" -Index 5 -Total 6

# Start Flower
Start-ServiceWindow -Title "Recon API - Flower" -Command ".\venv\Scripts\celery -A app.workers.celery_app flower --port=5555" -Index 6 -Total 6

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Access the application:" -ForegroundColor Cyan
Write-Host "  - Web Interface: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Flower Monitor: http://localhost:5555" -ForegroundColor White
Write-Host ""

Write-Host "Services Running:" -ForegroundColor Cyan
Write-Host "  - API Server: Running" -ForegroundColor Green
Write-Host "  - 4 Celery Workers (Solo Pool): Running" -ForegroundColor Green
Write-Host "  - Flower Monitor: Running" -ForegroundColor Green
Write-Host ""

Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  - Close all opened windows" -ForegroundColor White
Write-Host "  - Or press Ctrl+C in each window" -ForegroundColor White
Write-Host ""

Write-Host "Opening web browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All services are running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "This window will close in 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

