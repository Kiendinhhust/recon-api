# ========================================
#   Check Celery Workers Status
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Celery Workers Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

Write-Host "1. Checking registered workers..." -ForegroundColor Yellow
Write-Host ""
celery -A app.workers.celery_app inspect registered
Write-Host ""

Write-Host "2. Checking active tasks..." -ForegroundColor Yellow
Write-Host ""
celery -A app.workers.celery_app inspect active
Write-Host ""

Write-Host "3. Checking reserved tasks..." -ForegroundColor Yellow
Write-Host ""
celery -A app.workers.celery_app inspect reserved
Write-Host ""

Write-Host "4. Checking worker stats..." -ForegroundColor Yellow
Write-Host ""
celery -A app.workers.celery_app inspect stats
Write-Host ""

Write-Host "5. Checking scheduled tasks..." -ForegroundColor Yellow
Write-Host ""
celery -A app.workers.celery_app inspect scheduled
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Status Check Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you see 'Error: No nodes replied', workers are NOT running!" -ForegroundColor Red
Write-Host "Start workers with: .\start_workers.bat" -ForegroundColor Yellow
Write-Host ""

