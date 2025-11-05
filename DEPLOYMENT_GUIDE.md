# Deployment Guide: Three Critical Issues Fixed

## Quick Start

### Step 1: Update Configuration (.env)

Add these new settings to your `.env` file:

```env
# WAF Detection Tool
WAFW00F_PATH=wafw00f
WAFW00F_TIMEOUT=900

# Source Leak Detection (optional - set to false to disable)
ENABLE_SOURCELEAKHACKER=false
SOURCELEAKHACKER_PATH=E:\SourceLeakHacker\SourceLeakHacker.py
SOURCELEAKHACKER_MODE=tiny
SOURCELEAKHACKER_TIMEOUT=1800
SOURCELEAKHACKER_THREADS=8
PYTHON_EXECUTABLE=python
```

**Note**: Adjust paths based on your system. If tools are in PATH, you can use just the command name.

### Step 2: Run Database Migration

```powershell
# Navigate to project root
cd c:\recon-api

# Run migration script
python scripts/add_waf_and_leak_tables.py
```

Expected output:
```
Will create table: waf_detections
Will create table: leak_detections

Creating 2 table(s)...
✓ Migration completed successfully!
```

### Step 3: Restart Services

```powershell
# Stop existing services (if running)
# Ctrl+C in each terminal

# Restart API server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, restart Celery workers
celery -A app.workers.celery_app worker --loglevel=info -Q scans -c 3
```

### Step 4: Verify Deployment

1. Open dashboard: http://localhost:8000
2. Create a test scan
3. Wait for completion
4. Verify in scan details:
   - ✓ All scans visible in list (Issue 1)
   - ✓ Dead subdomains show HTTP status codes (Issue 2)
   - ✓ WAF Detections table appears (Issue 3)
   - ✓ Leak Findings table appears if enabled (Issue 3)

---

## Configuration Details

### WAFW00F Settings
- **WAFW00F_PATH**: Path to wafw00f executable
  - Default: `wafw00f` (assumes in PATH)
  - Windows: `E:\Wafw00f\wafw00f.exe` (if not in PATH)
- **WAFW00F_TIMEOUT**: Timeout in seconds (default: 900 = 15 minutes)

### SourceLeakHacker Settings
- **ENABLE_SOURCELEAKHACKER**: Enable/disable leak scanning
  - `true`: Run leak detection on non-WAF URLs
  - `false`: Skip leak detection (faster scans)
- **SOURCELEAKHACKER_PATH**: Path to SourceLeakHacker.py
  - Windows: `E:\SourceLeakHacker\SourceLeakHacker.py`
- **SOURCELEAKHACKER_MODE**: Scanning mode
  - `tiny`: Fast, basic scanning (recommended)
  - `full`: Comprehensive scanning (slower)
- **SOURCELEAKHACKER_TIMEOUT**: Timeout in seconds (default: 1800 = 30 minutes)
- **SOURCELEAKHACKER_THREADS**: Number of threads (default: 8)
- **PYTHON_EXECUTABLE**: Python command (default: `python`)

---

## Troubleshooting

### Issue: "wafw00f not found"
**Solution**: 
- Install wafw00f: `pip install wafw00f`
- Or set full path in .env: `WAFW00F_PATH=E:\path\to\wafw00f.exe`

### Issue: "SourceLeakHacker not found"
**Solution**:
- Set full path in .env: `SOURCELEAKHACKER_PATH=E:\SourceLeakHacker\SourceLeakHacker.py`
- Or disable it: `ENABLE_SOURCELEAKHACKER=false`

### Issue: Migration script fails
**Solution**:
- Ensure DATABASE_URL is correct in .env
- Check PostgreSQL is running
- Verify database exists and is accessible

### Issue: WAF detections not appearing
**Solution**:
- Check wafw00f is installed and working
- Verify WAFW00F_PATH is correct
- Check logs for errors: `jobs/{job_id}/` directory

### Issue: Scans taking too long
**Solution**:
- Disable SourceLeakHacker: `ENABLE_SOURCELEAKHACKER=false`
- Reduce SOURCELEAKHACKER_THREADS
- Increase timeouts if needed

---

## Monitoring

### Check Pipeline Progress
1. Open dashboard
2. Click "Monitor" button on running scans
3. Watch progress percentage and status messages

### Check Logs
```powershell
# API logs (in terminal where API is running)
# Look for [job_id] entries

# Worker logs (in terminal where workers are running)
# Look for task execution messages
```

### Database Verification
```sql
-- Check WAF detections
SELECT COUNT(*) FROM waf_detections;

-- Check leak detections
SELECT COUNT(*) FROM leak_detections;

-- Check scan jobs
SELECT job_id, domain, status FROM scan_jobs ORDER BY created_at DESC LIMIT 10;
```

---

## Performance Tuning

### For Faster Scans
1. Disable SourceLeakHacker: `ENABLE_SOURCELEAKHACKER=false`
2. Reduce WAFW00F_TIMEOUT: `WAFW00F_TIMEOUT=300` (5 minutes)
3. Increase worker threads: `celery -A app.workers.celery_app worker -c 5`

### For More Comprehensive Scans
1. Enable SourceLeakHacker: `ENABLE_SOURCELEAKHACKER=true`
2. Set mode to full: `SOURCELEAKHACKER_MODE=full`
3. Increase timeouts as needed

---

## Rollback (if needed)

If you need to revert changes:

```powershell
# Stop services
# Ctrl+C in each terminal

# Restore from backup (if available)
# Or manually delete new tables:
# DROP TABLE waf_detections;
# DROP TABLE leak_detections;

# Restart services with old code
```

---

## Next Steps

1. ✅ Update .env configuration
2. ✅ Run migration script
3. ✅ Restart services
4. ✅ Test with sample domains
5. ✅ Monitor logs for any issues
6. ✅ Adjust timeouts/settings as needed

---

## Support

For issues or questions:
1. Check logs in `jobs/{job_id}/` directory
2. Review IMPLEMENTATION_SUMMARY.md for technical details
3. Verify all tools are installed and accessible
4. Check database connectivity

