# PowerShell script to test Recon API

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Recon API - Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if API is running
Write-Host "[1/5] Checking if API is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 5
    Write-Host "[OK] API is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] API is not running!" -ForegroundColor Red
    Write-Host "Please start API first: .\start_api.bat" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check Redis connection
Write-Host "[2/5] Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Host "[OK] Redis is running" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Redis may not be running properly" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] Cannot check Redis (redis-cli not found)" -ForegroundColor Yellow
}
Write-Host ""

# Create a scan job
Write-Host "[3/5] Creating scan job..." -ForegroundColor Yellow
$domain = Read-Host "Enter domain to scan (default: example.com)"
if ([string]::IsNullOrWhiteSpace($domain)) {
    $domain = "example.com"
}

$body = @{
    domain = $domain
} | ConvertTo-Json

try {
    $createResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    $jobId = $createResponse.job_id
    Write-Host "[OK] Scan job created!" -ForegroundColor Green
    Write-Host "    Job ID: $jobId" -ForegroundColor Cyan
    Write-Host "    Domain: $($createResponse.domain)" -ForegroundColor Cyan
    Write-Host "    Status: $($createResponse.status)" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Failed to create scan job" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check progress
Write-Host "[4/5] Checking scan progress..." -ForegroundColor Yellow
Write-Host "Waiting 3 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 3

try {
    # IMPORTANT: No curly braces in URL!
    $progressUrl = "http://localhost:8000/api/v1/scans/$jobId/progress"
    Write-Host "    URL: $progressUrl" -ForegroundColor Gray
    
    $progressResponse = Invoke-RestMethod -Uri $progressUrl -Method Get
    
    Write-Host "[OK] Progress retrieved!" -ForegroundColor Green
    Write-Host "    Status: $($progressResponse.status)" -ForegroundColor Cyan
    if ($progressResponse.progress) {
        Write-Host "    Progress: $($progressResponse.progress.current)%" -ForegroundColor Cyan
        Write-Host "    Message: $($progressResponse.progress.status)" -ForegroundColor Cyan
    }
    if ($progressResponse.message) {
        Write-Host "    Message: $($progressResponse.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] Could not get progress" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

# Get scan results
Write-Host "[5/5] Getting scan results..." -ForegroundColor Yellow
try {
    # IMPORTANT: No curly braces in URL!
    $resultsUrl = "http://localhost:8000/api/v1/scans/$jobId"
    Write-Host "    URL: $resultsUrl" -ForegroundColor Gray
    
    $resultsResponse = Invoke-RestMethod -Uri $resultsUrl -Method Get
    
    Write-Host "[OK] Results retrieved!" -ForegroundColor Green
    Write-Host "    Job ID: $($resultsResponse.job_id)" -ForegroundColor Cyan
    Write-Host "    Domain: $($resultsResponse.domain)" -ForegroundColor Cyan
    Write-Host "    Status: $($resultsResponse.status)" -ForegroundColor Cyan
    Write-Host "    Subdomains: $($resultsResponse.subdomains_count)" -ForegroundColor Cyan
    Write-Host "    Screenshots: $($resultsResponse.screenshots_count)" -ForegroundColor Cyan
    
    if ($resultsResponse.subdomains -and $resultsResponse.subdomains.Count -gt 0) {
        Write-Host ""
        Write-Host "Found subdomains:" -ForegroundColor Green
        $resultsResponse.subdomains | ForEach-Object {
            Write-Host "  - $($_.subdomain) [$($_.status)]" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "[WARNING] Could not get results" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful URLs:" -ForegroundColor Yellow
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - Job Status: http://localhost:8000/api/v1/scans/$jobId" -ForegroundColor Cyan
Write-Host "  - Job Progress: http://localhost:8000/api/v1/scans/$jobId/progress" -ForegroundColor Cyan
Write-Host "  - Flower: http://localhost:5555" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to monitor progress
$monitor = Read-Host "Monitor progress? (y/N)"
if ($monitor -eq "y" -or $monitor -eq "Y") {
    Write-Host ""
    Write-Host "Monitoring progress (Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host ""
    
    while ($true) {
        try {
            $progressResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId/progress" -Method Get
            
            $timestamp = Get-Date -Format "HH:mm:ss"
            Write-Host "[$timestamp] Status: $($progressResponse.status)" -NoNewline
            
            if ($progressResponse.progress) {
                Write-Host " | Progress: $($progressResponse.progress.current)% | $($progressResponse.progress.status)" -ForegroundColor Cyan
            } else {
                Write-Host "" -ForegroundColor Cyan
            }
            
            if ($progressResponse.status -eq "completed" -or $progressResponse.status -eq "failed") {
                Write-Host ""
                Write-Host "Scan finished with status: $($progressResponse.status)" -ForegroundColor Green
                break
            }
            
            Start-Sleep -Seconds 5
        } catch {
            Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
            break
        }
    }
    
    # Get final results
    Write-Host ""
    Write-Host "Getting final results..." -ForegroundColor Yellow
    try {
        $finalResults = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId" -Method Get
        Write-Host ""
        Write-Host "Final Results:" -ForegroundColor Green
        Write-Host "  Domain: $($finalResults.domain)" -ForegroundColor Cyan
        Write-Host "  Status: $($finalResults.status)" -ForegroundColor Cyan
        Write-Host "  Subdomains found: $($finalResults.subdomains_count)" -ForegroundColor Cyan
        Write-Host "  Screenshots: $($finalResults.screenshots_count)" -ForegroundColor Cyan
        
        if ($finalResults.subdomains -and $finalResults.subdomains.Count -gt 0) {
            Write-Host ""
            Write-Host "Subdomains:" -ForegroundColor Green
            $finalResults.subdomains | ForEach-Object {
                Write-Host "  - $($_.subdomain) [$($_.status)]" -ForegroundColor Cyan
            }
        }
    } catch {
        Write-Host "[ERROR] Could not get final results" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done! 🎉" -ForegroundColor Green
