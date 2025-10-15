# ========================================
#   Start All Services
#   (API Server + Celery Workers)
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting Recon API System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check PostgreSQL
try {
    $pgService = Get-Service -Name "postgresql*" -ErrorAction Stop | Where-Object {$_.Status -eq "Running"} | Select-Object -First 1
    if ($pgService) {
        Write-Host "[OK] PostgreSQL is running" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] PostgreSQL service found but not running" -ForegroundColor Yellow
        Write-Host "  Please start PostgreSQL manually" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] PostgreSQL service not found" -ForegroundColor Yellow
    Write-Host "  Make sure PostgreSQL is installed and running" -ForegroundColor Yellow
}

# Check Redis
$redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redisProcess) {
    Write-Host "[OK] Redis is running" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Redis is not running" -ForegroundColor Yellow
    Write-Host "  Please start Redis manually: redis-server" -ForegroundColor Yellow
}

Write-Host ""

# Run database migration
Write-Host "Running database migration..." -ForegroundColor Yellow
& "venv\Scripts\python.exe" "scripts\add_task_id_column.py"
Write-Host ""

# Start API Server in new window
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; Write-Host 'Starting FastAPI Server...' -ForegroundColor Cyan; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "[OK] API server starting in new window" -ForegroundColor Green
Write-Host ""

# Wait for API to be ready
Write-Host "Waiting for API to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$apiReady = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "[OK] API is ready!" -ForegroundColor Green
        $apiReady = $true
        break
    } catch {
        Write-Host "  Attempt $i/10: Waiting..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $apiReady) {
    Write-Host "[ERROR] API failed to start" -ForegroundColor Red
    Write-Host "  Check the API server window for errors" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Start Celery Workers
Write-Host "Starting Celery workers..." -ForegroundColor Yellow
& ".\start_workers.bat"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   All Services Started!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Server:  http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Workers:     3 workers running (check separate windows)" -ForegroundColor Green
Write-Host ""
Write-Host "To test:" -ForegroundColor Yellow
Write-Host "  .\scripts\test_api.ps1" -ForegroundColor White
Write-Host "  .\scripts\test_bulk_scan.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  .\stop_all.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

