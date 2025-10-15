# ========================================
#   Monitor Celery Workers
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Celery Workers Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

Write-Host "Checking active workers..." -ForegroundColor Yellow
Write-Host ""

# Get active workers
celery -A app.workers.celery_app inspect active

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Worker Stats" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get worker stats
celery -A app.workers.celery_app inspect stats

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Registered Tasks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get registered tasks
celery -A app.workers.celery_app inspect registered

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Active Queues" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get active queues
celery -A app.workers.celery_app inspect active_queues

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

