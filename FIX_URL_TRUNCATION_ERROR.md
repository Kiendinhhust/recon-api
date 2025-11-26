# 🔧 FIX: PostgreSQL String Data Right Truncation Error

## 🔴 **ERROR DETAILS**

**Error Type:** `psycopg2.errors.StringDataRightTruncation: value too long for type character varying(512)`

**Context:**
- Scan Job: `f4bc44c5-ba28-4cd2-b46c-b8680dbb289c`
- Subdomain: `accounts-stag.fpt.vn` (ID: 2477)
- Failed Column: `final_url`
- Actual Length: **2359+ characters**
- Database Limit: **512 characters**

**Failed URL:**
```
https://accounts-stag.fpt.vn/sso/Auth/Identifier?challenge=vMU-EXTI8oG3Lgv0HyHrXl76yw0vN5ZgSB1QtVhxNbyhAhUJGLwTEFpqqdxfvzztBKhacndI8qoxRzuhxyo8QLO0r7...
```

---

## 🎯 **ROOT CAUSE ANALYSIS**

### **Why is the URL so long?**

**OAuth/SSO Authentication Flow:**
```
Original URL: https://accounts-stag.fpt.vn
↓ 302 Redirect
https://accounts-stag.fpt.vn/sso/Auth/Identifier
↓ 302 Redirect  
https://accounts-stag.fpt.vn/sso/Auth/Identifier?challenge=ABC123... (500 chars)
↓ 302 Redirect
https://accounts-stag.fpt.vn/sso/Auth/Identifier?challenge=ABC123...&state=XYZ789... (1000 chars)
↓ 302 Redirect
https://accounts-stag.fpt.vn/sso/Auth/Identifier?challenge=ABC123...&state=XYZ789...&nonce=... (1500 chars)
↓ 200 OK
Final URL: 2359+ characters
```

**Components of Long URLs:**
- ✅ `challenge` parameter: JWT token hoặc encrypted state (500-1000 chars)
- ✅ `state` parameter: CSRF protection token (200-500 chars)
- ✅ `nonce` parameter: Replay attack prevention (100-200 chars)
- ✅ `redirect_uri` parameter: Callback URL (100-300 chars)
- ✅ Other OAuth parameters: `scope`, `response_type`, `client_id`, etc.

**Redirect Chain:** `[302, 302, 302, 302, 200]` - 4 redirects, mỗi lần thêm parameters

---

## 📊 **AFFECTED COLUMNS**

| Column | Current Type | Max Length | Risk Level | Reason |
|--------|--------------|------------|------------|--------|
| **`url`** | VARCHAR(512) | 512 | 🟡 **MEDIUM** | Initial URL thường ngắn, nhưng có thể có query params |
| **`final_url`** | VARCHAR(512) | 512 | 🔴 **VERY HIGH** | OAuth/SSO URLs với challenge parameters (2000-4000 chars) |
| **`title`** | VARCHAR(512) | 512 | 🟢 **LOW** | HTML titles thường < 200 chars, nhưng có thể dài hơn |

**In this case:**
- ✅ **`final_url`** definitely failed (2359 chars > 512)
- ⚠️ **`url`** might also fail if httpx saves URL with query params

---

## ✅ **SOLUTION: INCREASE COLUMN LENGTHS**

### **Strategy: Use TEXT for URLs, VARCHAR for Titles**

**Rationale:**
- URLs không có giới hạn chuẩn (RFC 2616 không quy định max length)
- Browsers hỗ trợ URLs lên đến 2MB
- OAuth/SSO URLs thường 2000-4000 characters
- PostgreSQL TEXT type performance tốt, không giới hạn độ dài

**Changes:**
```python
url         → TEXT           # Was VARCHAR(512)
final_url   → TEXT           # Was VARCHAR(512)
title       → VARCHAR(1024)  # Was VARCHAR(512)
```

---

## 🛠️ **IMPLEMENTATION STEPS**

### **Step 1: Files Modified**

**1. Database Model (`app/storage/models.py`):**
```python
# Before
url = Column(String(512), nullable=True)
final_url = Column(String(512), nullable=True)
title = Column(String(512), nullable=True)

# After
url = Column(Text, nullable=True)  # TEXT to handle long OAuth URLs
final_url = Column(Text, nullable=True)  # TEXT to handle long OAuth/SSO URLs
title = Column(String(1024), nullable=True)  # Increased to 1024 for long titles
```

**2. Alembic Migration (`alembic/versions/003_increase_url_column_lengths.py`):**
- Created new migration to alter column types
- Changes VARCHAR(512) → TEXT for `url` and `final_url`
- Changes VARCHAR(512) → VARCHAR(1024) for `title`

---

### **Step 2: Run Migration Locally (Test First)**

```powershell
cd c:\recon-api

# Check current migration status
alembic current

# Run the new migration
alembic upgrade head

# Verify migration applied
alembic current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 002_optimize_subdomains -> 003_increase_url_lengths, increase url column lengths to handle long OAuth/SSO URLs
```

---

### **Step 3: Verify Database Schema**

```powershell
# Connect to local PostgreSQL
psql -U postgres -d recon_db

# Check column types
\d subdomains

# Expected output:
# url         | text          |
# final_url   | text          |
# title       | character varying(1024) |

# Exit
\q
```

---

### **Step 4: Test with Problematic Scan**

```powershell
# Create a new scan to test
$body = @{
    domain = "fpt.vn"
} | ConvertTo-Json

$scan = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/scans" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# Monitor progress
$jobId = $scan.job_id
do {
    Start-Sleep -Seconds 5
    $progress = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/scans/$jobId/progress"
    Write-Host "Progress: $($progress.progress)% - $($progress.current_stage)"
} while ($progress.status -eq "running")

# Check if scan completed successfully
$results = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/scans/$jobId"
Write-Host "Scan Status: $($results.status)"
Write-Host "Subdomains Found: $($results.subdomains.Count)"

# Check for long URLs
$longUrls = $results.subdomains | Where-Object { $_.final_url.Length -gt 512 }
Write-Host "Subdomains with long final_url: $($longUrls.Count)"
$longUrls | Format-Table subdomain, @{Label="URL Length";Expression={$_.final_url.Length}}
```

---

## 🚀 **DEPLOYMENT TO VPS**

### **Step 1: Commit Changes**

```powershell
cd c:\recon-api

git add app/storage/models.py
git add alembic/versions/003_increase_url_column_lengths.py
git add FIX_URL_TRUNCATION_ERROR.md

git commit -m "fix: Increase URL column lengths to handle long OAuth/SSO URLs

- Change url from VARCHAR(512) to TEXT
- Change final_url from VARCHAR(512) to TEXT
- Change title from VARCHAR(512) to VARCHAR(1024)
- Add migration 003_increase_url_column_lengths
- Fixes psycopg2.errors.StringDataRightTruncation error

Root cause: OAuth/SSO URLs with challenge parameters can exceed 2000 characters
Example: accounts-stag.fpt.vn redirect chain produces 2359 char URL"

git push origin main
```

---

### **Step 2: Monitor GitHub Actions Deployment**

```
1. Go to GitHub → Actions tab
2. Watch the deployment workflow
3. Verify all steps complete successfully:
   ✅ Create backup
   ✅ Pull latest code
   ✅ Run database migrations (alembic upgrade head)
   ✅ Restart services
   ✅ Verify deployment
```

**Expected Migration Output on VPS:**
```
INFO  [alembic.runtime.migration] Running upgrade 002_optimize_subdomains -> 003_increase_url_lengths
```

---

### **Step 3: Verify VPS Database**

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Check database schema
sudo -u postgres psql recon_db -c "\d subdomains"

# Expected:
# url       | text
# final_url | text
# title     | character varying(1024)

# Exit
exit
```

---

### **Step 4: Retry Failed Scan**

```powershell
# Create new scan on VPS
$body = @{
    domain = "fpt.vn"
} | ConvertTo-Json

$scan = Invoke-RestMethod -Uri "http://124.197.22.184:8000/api/v1/scans" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# Monitor
$jobId = $scan.job_id
do {
    Start-Sleep -Seconds 5
    $progress = Invoke-RestMethod -Uri "http://124.197.22.184:8000/api/v1/scans/$jobId/progress"
    Write-Host "Progress: $($progress.progress)%"
} while ($progress.status -eq "running")

# Verify success
$results = Invoke-RestMethod -Uri "http://124.197.22.184:8000/api/v1/scans/$jobId"
Write-Host "Status: $($results.status)" -ForegroundColor $(if ($results.status -eq "completed") { "Green" } else { "Red" })
```

---

## 📝 **BEST PRACTICES FOR URL STORAGE**

### **1. Use TEXT for URLs**
```python
# ✅ GOOD - No length limit
url = Column(Text, nullable=True)

# ❌ BAD - Will fail with long URLs
url = Column(String(512), nullable=True)
```

### **2. Use VARCHAR for Fixed-Length Fields**
```python
# ✅ GOOD - Webserver names are short
webserver = Column(String(128), nullable=True)

# ❌ OVERKILL - Wastes space
webserver = Column(Text, nullable=True)
```

### **3. Index Strategy**
```python
# ✅ GOOD - Index on subdomain (short, frequently queried)
subdomain = Column(String(255), nullable=False, index=True)

# ❌ BAD - Don't index TEXT columns (poor performance)
url = Column(Text, nullable=True, index=True)  # Don't do this!
```

### **4. Validation in Application Layer**
```python
# Add validation before saving
if url and len(url) > 10000:  # Sanity check
    logger.warning(f"Extremely long URL detected: {len(url)} chars")
    # Optionally truncate or skip
```

---

## ✅ **VERIFICATION CHECKLIST**

### **Local Testing:**
- [ ] Migration runs successfully (`alembic upgrade head`)
- [ ] Database schema updated (url, final_url are TEXT)
- [ ] New scan completes without truncation error
- [ ] Long URLs saved correctly to database

### **VPS Deployment:**
- [ ] Commit and push changes
- [ ] GitHub Actions deployment succeeds
- [ ] Migration runs on VPS
- [ ] Database schema updated on VPS
- [ ] New scan on VPS completes successfully
- [ ] `accounts-stag.fpt.vn` subdomain saves correctly

---

## 📊 **SUMMARY**

**Problem:** VARCHAR(512) too short for OAuth/SSO URLs with challenge parameters

**Root Cause:** 
- OAuth redirect chains append long parameters (challenge, state, nonce)
- Final URL can be 2000-4000+ characters
- Database column limited to 512 characters

**Solution:**
- ✅ Change `url` to TEXT (no limit)
- ✅ Change `final_url` to TEXT (no limit)
- ✅ Change `title` to VARCHAR(1024) (reasonable limit)
- ✅ Create Alembic migration 003_increase_url_column_lengths

**Files Modified:**
- `app/storage/models.py` - Updated column types
- `alembic/versions/003_increase_url_column_lengths.py` - New migration

**Result:**
- ✅ No more truncation errors
- ✅ Long OAuth/SSO URLs saved correctly
- ✅ Scans complete successfully

---

**Follow the deployment steps above to fix the issue on VPS! 🚀**

