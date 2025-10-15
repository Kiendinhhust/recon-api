# ========================================
#   Test Bulk Domain Scanning
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Bulk Domain Scan Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:8000/api/v1"

# Test domains
$domains = @(
    "fpt.ai",
    "soict.ai",
    "hust.edu.vn"
)

Write-Host "Submitting $($domains.Count) domains for scanning..." -ForegroundColor Yellow
Write-Host ""

# Submit bulk scan
$body = @{
    domains = $domains
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/scans/bulk" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "[OK] Bulk scan submitted!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Total submitted: $($response.total_submitted)" -ForegroundColor Cyan
    Write-Host "Message: $($response.message)" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Job IDs:" -ForegroundColor Yellow
    foreach ($job in $response.jobs) {
        Write-Host "  - Domain: $($job.domain)" -ForegroundColor White
        Write-Host "    Job ID: $($job.job_id)" -ForegroundColor Gray
        Write-Host "    Status: $($job.status)" -ForegroundColor Gray
        Write-Host ""
    }
    
    # Monitor progress
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Monitoring Progress" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $job_ids = $response.jobs | ForEach-Object { $_.job_id }
    
    $completed = 0
    $max_iterations = 60  # 5 minutes max
    $iteration = 0
    
    while ($completed -lt $job_ids.Count -and $iteration -lt $max_iterations) {
        $iteration++
        Start-Sleep -Seconds 5
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking progress..." -ForegroundColor Yellow
        
        $completed = 0
        foreach ($job_id in $job_ids) {
            try {
                $progress = Invoke-RestMethod -Uri "$API_URL/scans/$job_id/progress"
                
                $status_color = switch ($progress.status) {
                    "pending" { "Gray" }
                    "running" { "Yellow" }
                    "completed" { "Green" }
                    "failed" { "Red" }
                    default { "White" }
                }
                
                Write-Host "  $($progress.job_id.Substring(0,8))... : $($progress.status)" -ForegroundColor $status_color
                
                if ($progress.status -in @("completed", "failed")) {
                    $completed++
                }
            }
            catch {
                Write-Host "  Error checking $job_id" -ForegroundColor Red
            }
        }
        
        Write-Host "  Progress: $completed / $($job_ids.Count) completed" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Get final results
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   Final Results" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($job_id in $job_ids) {
        try {
            $result = Invoke-RestMethod -Uri "$API_URL/scans/$job_id"
            
            Write-Host "Domain: $($result.domain)" -ForegroundColor Cyan
            Write-Host "  Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "completed") { "Green" } else { "Red" })
            Write-Host "  Subdomains: $($result.subdomains.Count)" -ForegroundColor White
            Write-Host "  Screenshots: $($result.screenshots.Count)" -ForegroundColor White
            
            if ($result.error_message) {
                Write-Host "  Error: $($result.error_message)" -ForegroundColor Red
            }
            
            Write-Host ""
        }
        catch {
            Write-Host "Error getting results for $job_id" -ForegroundColor Red
        }
    }
    
}
catch {
    Write-Host "[ERROR] Failed to submit bulk scan" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Test Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

