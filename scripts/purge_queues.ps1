# ========================================
#   Purge Celery Queues (Redis broker)
#   WARNING: This removes ALL pending tasks in the selected queues
# ========================================

param (
    [string[]]$Queues = @("recon_full","recon_enum","recon_check","recon_screenshot","maintenance","celery"),
    [switch]$Force
)

Write-Host "" 
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Purging Celery Queues" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

foreach ($q in $Queues) {
    Write-Host "Purging queue: $q" -ForegroundColor Yellow
    if ($Force) {
        celery -A app.workers.celery_app purge -Q $q -f
    } else {
        celery -A app.workers.celery_app purge -Q $q
    }
}

Write-Host "" 
Write-Host "Verifying queues are empty (reserved tasks)..." -ForegroundColor Yellow
celery -A app.workers.celery_app inspect reserved

Write-Host "" 
Write-Host "You can also check Redis queue lengths (requires redis-cli):" -ForegroundColor Yellow
Write-Host "  redis-cli -n 0 LLEN recon_full" -ForegroundColor Gray
Write-Host "  redis-cli -n 0 LLEN recon_enum" -ForegroundColor Gray
Write-Host "  redis-cli -n 0 LLEN recon_check" -ForegroundColor Gray
Write-Host "  redis-cli -n 0 LLEN recon_screenshot" -ForegroundColor Gray
Write-Host "  redis-cli -n 0 LLEN maintenance" -ForegroundColor Gray
Write-Host "  redis-cli -n 0 LLEN celery" -ForegroundColor Gray

Write-Host "" 
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Purge Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

