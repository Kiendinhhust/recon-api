# ========================================
#   Stop All Services
#   (API Server + Celery Workers)
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Stopping All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop Celery workers
Write-Host "Stopping Celery workers..." -ForegroundColor Yellow
& ".\stop_workers.bat"
Write-Host ""

# Stop API server (uvicorn)
Write-Host "Stopping API server..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*app.main:app*"
}

if ($uvicornProcesses) {
    foreach ($process in $uvicornProcesses) {
        Write-Host "  Stopping process $($process.Id)..." -ForegroundColor Gray
        Stop-Process -Id $process.Id -Force
    }
    Write-Host "[OK] API server stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] No API server process found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   All Services Stopped" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

