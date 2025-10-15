# 🚀 Startup Guide - Recon API

## Quick Start (Recommended)

### **Option 1: Automatic Start (Easiest)**

```powershell
.\start_all.ps1
```

This will:
1. ✅ Check PostgreSQL and Redis
2. ✅ Run database migration
3. ✅ Start FastAPI server (new window)
4. ✅ Start Celery workers (3 new windows)
5. ✅ Verify everything is running

**Then test:**
```powershell
.\scripts\test_api.ps1
.\scripts\test_bulk_scan.ps1
```

**To stop everything:**
```powershell
.\stop_all.ps1
```

---

## Manual Start (Step by Step)

### **Prerequisites Check**

**1. Check PostgreSQL:**
```powershell
Get-Service -Name postgresql*
# Should show: Status = Running
```

If not running:
```powershell
Start-Service postgresql-x64-16  # Replace with your service name
```

**2. Check Redis:**
```powershell
Get-Process -Name redis-server
```

If not running:
```powershell
# Start Redis in a new terminal
redis-server
```

**3. Check Virtual Environment:**
```powershell
.\venv\Scripts\Activate.ps1
python --version
# Should show: Python 3.13.x
```

---

### **Step 1: Database Migration**

**Terminal 1:**
```powershell
.\venv\Scripts\Activate.ps1
python scripts\add_task_id_column.py
```

**Expected output:**
```
✓ Added 'task_id' column to scan_jobs table
```

Or:
```
✓ Column 'task_id' already exists
```

---

### **Step 2: Start FastAPI Server**

**Terminal 1 (or new terminal):**
```powershell
.\start_api.bat
```

**Expected output:**
```
========================================
   Starting FastAPI Server
========================================

Starting uvicorn server on http://localhost:8000

API Docs will be available at: http://localhost:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Keep this terminal OPEN!**

---

### **Step 3: Verify API is Running**

**Terminal 2 (new terminal):**
```powershell
# Test API
Invoke-RestMethod -Uri "http://localhost:8000/"
```

**Expected output:**
```json
{
  "message": "Recon API is running",
  "version": "1.0.0"
}
```

**Or open browser:**
```
http://localhost:8000/docs
```

You should see Swagger UI! 🎉

---

### **Step 4: Start Celery Workers**

**Terminal 3 (new terminal):**

**Option A: Multiple workers (recommended for production):**
```powershell
.\start_workers.bat
```

This opens 3 new windows with workers.

**Option B: Single worker (for testing):**
```powershell
.\start_worker.bat
```

**Expected output:**
```
Checking tools...
[OK] subfinder found

 -------------- celery@WINDOWS-PC v5.4.0 (opalescent)
--- ***** -----
-- ******* ---- Windows-10-10.0.19045-SP0 2025-10-06 17:30:00
...
[queues]
  .> recon_full       exchange=recon_full(direct) key=recon_full
  .> recon_enum       exchange=recon_enum(direct) key=recon_enum
  .> recon_check      exchange=recon_check(direct) key=recon_check
  .> recon_screenshot exchange=recon_screenshot(direct) key=recon_screenshot
  .> maintenance      exchange=maintenance(direct) key=maintenance
  .> celery           exchange=celery(direct) key=celery

[tasks]
  . app.workers.tasks.cleanup_old_jobs
  . app.workers.tasks.run_live_host_check
  . app.workers.tasks.run_recon_scan
  . app.workers.tasks.run_screenshot_capture
  . app.workers.tasks.run_subdomain_enumeration

celery@WINDOWS-PC ready.
```

**✅ Keep worker terminal(s) OPEN!**

---

### **Step 5: Test the System**

**Terminal 2:**

**Test 1: Regular scan**
```powershell
.\scripts\test_api.ps1
```

**Test 2: Bulk scan**
```powershell
.\scripts\test_bulk_scan.ps1
```

**Test 3: Manual API call**
```powershell
# Create scan
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"domain":"fpt.ai"}'

$job_id = $response.job_id
Write-Host "Job ID: $job_id"

# Check progress
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$job_id/progress"

# Get results
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$job_id"
```

---

## Terminal Summary

| Terminal | Purpose | Command | Status |
|----------|---------|---------|--------|
| **Terminal 1** | FastAPI Server | `.\start_api.bat` | **Must stay open** |
| **Terminal 2** | Testing/Commands | `.\scripts\test_api.ps1` | Run as needed |
| **Terminal 3+** | Celery Workers | `.\start_workers.bat` | **Must stay open** |

---

## Troubleshooting

### ❌ Error: "Unable to connect to the remote server"

**Cause:** API server is not running

**Fix:**
```powershell
# Terminal 1
.\start_api.bat
```

**Verify:**
```powershell
# Terminal 2
curl http://localhost:8000/
```

---

### ❌ Error: "API is not running!"

**Cause:** Same as above

**Fix:**
```powershell
# Check if uvicorn is running
Get-Process -Name python | Where-Object {$_.CommandLine -like "*uvicorn*"}
```

If no output → API not running → Start it:
```powershell
.\start_api.bat
```

---

### ❌ Error: Database connection failed

**Cause:** PostgreSQL is not running

**Fix:**
```powershell
# Check service
Get-Service -Name postgresql*

# Start if stopped
Start-Service postgresql-x64-16  # Replace with actual service name
```

---

### ❌ Error: Redis connection failed

**Cause:** Redis is not running

**Fix:**
```powershell
# Check if running
Get-Process -Name redis-server

# Start if not running (new terminal)
redis-server
```

---

### ❌ Error: Workers not receiving tasks

**Cause:** Workers not running or Redis connection issue

**Fix:**
```powershell
# Stop workers
.\stop_workers.bat

# Restart workers
.\start_workers.bat

# Verify workers are registered
celery -A app.workers.celery_app inspect registered
```

---

### ❌ Error: "No module named 'app'"

**Cause:** Virtual environment not activated

**Fix:**
```powershell
.\venv\Scripts\Activate.ps1
```

---

## Verification Checklist

Before running tests, verify:

- [ ] PostgreSQL service is running
- [ ] Redis is running
- [ ] Virtual environment is activated
- [ ] Database migration completed
- [ ] API server is running (http://localhost:8000)
- [ ] Celery workers are running
- [ ] Tools are accessible (subfinder, amass, etc.)

**Quick check:**
```powershell
# Check all at once
Get-Service postgresql* | Select-Object Status
Get-Process redis-server | Select-Object Id
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Select-Object Id
Get-Process python | Where-Object {$_.CommandLine -like "*celery*"} | Select-Object Id
```

---

## Common Workflows

### **Daily Development:**
```powershell
# Morning: Start everything
.\start_all.ps1

# Work...
.\scripts\test_api.ps1

# Evening: Stop everything
.\stop_all.ps1
```

### **Testing Changes:**
```powershell
# 1. Stop workers
.\stop_workers.bat

# 2. Make code changes...

# 3. Restart workers
.\start_workers.bat

# 4. Test
.\scripts\test_api.ps1
```

### **Database Changes:**
```powershell
# 1. Stop everything
.\stop_all.ps1

# 2. Make database changes...

# 3. Run migration
python scripts\add_task_id_column.py

# 4. Start everything
.\start_all.ps1
```

---

## URLs Reference

| Service | URL | Description |
|---------|-----|-------------|
| API Root | http://localhost:8000 | API health check |
| Swagger UI | http://localhost:8000/docs | Interactive API docs |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Flower (optional) | http://localhost:5555 | Celery monitoring |

---

## Next Steps

After everything is running:

1. **Test single scan:**
   ```powershell
   .\scripts\test_api.ps1
   ```

2. **Test bulk scan:**
   ```powershell
   .\scripts\test_bulk_scan.ps1
   ```

3. **Monitor workers:**
   ```powershell
   .\scripts\monitor_workers.ps1
   ```

4. **View results:**
   - Check `jobs/{job_id}/` directories
   - View screenshots in `jobs/{job_id}/screenshots/`
   - Query database for results

---

## 🎯 Quick Reference

**Start everything:**
```powershell
.\start_all.ps1
```

**Stop everything:**
```powershell
.\stop_all.ps1
```

**Test:**
```powershell
.\scripts\test_api.ps1
.\scripts\test_bulk_scan.ps1
```

**Monitor:**
```powershell
.\scripts\monitor_workers.ps1
```

---

**Happy Scanning! 🚀**

