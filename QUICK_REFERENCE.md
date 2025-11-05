# 🚀 Quick Reference Guide - Redis Cleanup

## TL;DR (Too Long; Didn't Read)

**Problem:** Celery task crashed and stored corrupted data in Redis  
**Solution:** Run cleanup script to delete corrupted data  
**Command:** `python clear_redis_corrupted_data.py`  
**Choose:** Option 1 (Clear only task results)  

---

## What to Do Right Now

### Step 1: Run the Cleanup Script

```bash
python clear_redis_corrupted_data.py
```

### Step 2: Choose Option 1

```
Choose an option:
  1. Clear only Celery task results (recommended)
  2. Clear ALL Redis data (use with caution!)
  3. Cancel

Enter choice (1/2/3): 1  ← Type this
```

### Step 3: Confirm Deletion

```
⚠️  Delete X Celery task result keys? (yes/no): yes  ← Type this
```

### Step 4: Restart Celery Workers

```bash
# Kill old workers
taskkill /F /IM celery.exe

# Start fresh worker
celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,waf_check,leak_check
```

### Step 5: Test Selective Scanning

1. Open http://localhost:8000
2. Click on a completed scan
3. Use "🎯 Selective Leak Scanning"
4. Verify it works without errors

---

## FAQ (Frequently Asked Questions)

### Q1: What does Option 1 delete?

**A:** Only the task result keys (`celery-task-meta-*`). These store the results of completed/failed tasks.

**Example keys deleted:**
```
celery-task-meta-269ac526-2ab5-4db9-b57b-2a8ca67d69a4
celery-task-meta-7c7f686b-a5f7-4d6f-8b5e-3c2d1a9e8f7b
```

**What it keeps:**
- Pending tasks in queues
- Worker state
- Other Redis data

### Q2: What does Option 2 delete?

**A:** EVERYTHING in Redis! Use only if Option 1 doesn't work.

**Deletes:**
- All task results
- All pending tasks
- All worker state
- All other Redis data

### Q3: Will I lose my scan data?

**A:** No! Your scan data is stored in PostgreSQL, not Redis.

**What's in PostgreSQL (SAFE):**
- Scan jobs
- Subdomains
- Screenshots
- WAF detections
- Leak detections

**What's in Redis (TEMPORARY):**
- Task queue messages
- Task results/state
- Worker state

### Q4: Can I run the script while Celery is running?

**A:** Yes, but it's better to stop Celery first to avoid conflicts.

**Recommended order:**
1. Stop Celery workers
2. Run cleanup script
3. Restart Celery workers

### Q5: What if Option 1 doesn't fix the error?

**A:** Try Option 2 (clear all Redis data), then restart Celery.

### Q6: How do I know if it worked?

**A:** After cleanup and restart:
1. Run a selective scan
2. Check Celery logs - should see:
   ```
   [INFO] Task received
   [INFO] Parsed X leaks from CSV
   [INFO] Task succeeded
   ```
3. No more "ValueError: Exception information must include the exception type"

---

## Redis Keys Explained

### Task Result Keys (Deleted by Option 1)

```
celery-task-meta-<task_id>
```

**What they store:**
- Task state (PENDING, PROGRESS, SUCCESS, FAILURE)
- Task result data
- Exception information (if task failed)
- Progress updates

**Example data:**
```json
{
    "status": "SUCCESS",
    "result": {
        "job_id": "job-123",
        "leaks_found": 26
    },
    "date_done": "2025-10-31T08:08:22.500000"
}
```

### Queue Keys (Kept by Option 1, Deleted by Option 2)

```
celery:leak_check
celery:waf_check
celery:recon_full
```

**What they store:**
- Pending task messages
- Tasks waiting to be executed

**Example data:**
```json
{
    "task": "app.workers.tasks.run_sourceleakhacker_check",
    "id": "269ac526...",
    "args": ["job-123", ["https://fpt.ai"], "tiny"]
}
```

---

## Troubleshooting

### Error: "Failed to connect to Redis"

**Solution:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis
redis-server
```

### Error: "No module named 'app.deps'"

**Solution:**
```bash
# Activate virtual environment first
venv\Scripts\activate

# Then run script
python clear_redis_corrupted_data.py
```

### Script shows "0 Celery task result keys found"

**Meaning:** Redis is already clean! No corrupted data to delete.

**What to do:** Just restart Celery workers and test.

### After cleanup, selective scan still fails

**Possible causes:**
1. Celery worker not restarted (still running old code)
2. Different error (not related to Redis)

**Solution:**
1. Make sure you killed ALL Celery workers:
   ```bash
   taskkill /F /IM celery.exe
   ```
2. Start fresh worker
3. Check Celery logs for the actual error

---

## Visual Summary

### Option 1: Surgical Cleanup (Recommended) ✅

```
Before:                          After:
┌─────────────────────┐         ┌─────────────────────┐
│ Redis Database      │         │ Redis Database      │
├─────────────────────┤         ├─────────────────────┤
│ ❌ task-meta-123    │  ────▶  │                     │
│ ❌ task-meta-456    │  DELETE │                     │
│ ❌ task-meta-789    │  ────▶  │                     │
│ ✅ celery:queue     │  ────▶  │ ✅ celery:queue     │
│ ✅ worker:state     │  KEEP   │ ✅ worker:state     │
└─────────────────────┘         └─────────────────────┘
```

### Option 2: Nuclear Cleanup (Use with Caution) ⚠️

```
Before:                          After:
┌─────────────────────┐         ┌─────────────────────┐
│ Redis Database      │         │ Redis Database      │
├─────────────────────┤         ├─────────────────────┤
│ ❌ task-meta-123    │  ────▶  │                     │
│ ❌ task-meta-456    │  DELETE │                     │
│ ❌ task-meta-789    │  ALL    │     (EMPTY)         │
│ ❌ celery:queue     │  ────▶  │                     │
│ ❌ worker:state     │         │                     │
└─────────────────────┘         └─────────────────────┘
```

---

## Command Cheat Sheet

```bash
# 1. Run cleanup script
python clear_redis_corrupted_data.py

# 2. Choose Option 1
# Type: 1

# 3. Confirm deletion
# Type: yes

# 4. Kill Celery workers
taskkill /F /IM celery.exe

# 5. Start fresh Celery worker
celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,waf_check,leak_check

# 6. Test selective scanning
# Open http://localhost:8000 in browser
```

---

## When to Use Each Option

### Use Option 1 When:
- ✅ First time running cleanup
- ✅ You have pending tasks you don't want to lose
- ✅ You just want to fix the corrupted task results error
- ✅ You're not sure which option to choose

### Use Option 2 When:
- ⚠️ Option 1 didn't fix the issue
- ⚠️ You want a complete fresh start
- ⚠️ You don't have any important pending tasks
- ⚠️ Redis has other corrupted data (not just task results)

---

## Expected Output

### Successful Cleanup (Option 1)

```
============================================================
Redis Cleanup Tool
============================================================

Choose an option:
  1. Clear only Celery task results (recommended)
  2. Clear ALL Redis data (use with caution!)
  3. Cancel

Enter choice (1/2/3): 1

============================================================
Clearing Celery task results...
============================================================

Connecting to Redis: redis://localhost:6379/0
✅ Connected to Redis successfully
Found 15 total keys in Redis
Found 3 Celery task result keys

Celery task result keys:
  - celery-task-meta-269ac526-2ab5-4db9-b57b-2a8ca67d69a4
  - celery-task-meta-7c7f686b-a5f7-4d6f-8b5e-3c2d1a9e8f7b
  - celery-task-meta-abc123-def456-789012-345678-901234

⚠️  Delete 3 Celery task result keys? (yes/no): yes
✅ Deleted 3 Celery task result keys

📊 Remaining keys in Redis: 12

Key distribution by prefix:
  celery: 8 keys
  _kombu: 4 keys

✅ Redis cleanup complete!
```

### Already Clean

```
Connecting to Redis: redis://localhost:6379/0
✅ Connected to Redis successfully
Found 12 total keys in Redis
Found 0 Celery task result keys
✅ No Celery task result keys found - Redis is clean

📊 Remaining keys in Redis: 12
✅ Redis cleanup complete!
```

---

## Summary

| Action | Command | When to Use |
|--------|---------|-------------|
| Run cleanup | `python clear_redis_corrupted_data.py` | After fixing code |
| Choose Option 1 | Type `1` | First attempt (recommended) |
| Choose Option 2 | Type `2` | If Option 1 fails |
| Restart Celery | `taskkill /F /IM celery.exe` then start worker | After cleanup |
| Test | Open http://localhost:8000 | After restart |

**Remember:** Your scan data in PostgreSQL is safe! Redis only stores temporary task state.

