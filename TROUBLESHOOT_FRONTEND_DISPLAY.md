# 🔧 TROUBLESHOOTING: Frontend Not Displaying Httpx Fields

## 📋 **PROBLEM**

**Symptom:** API returns correct httpx field data, but dashboard shows "-" or wrong values.

**Example:**
- API returns: `"webserver": "LiteSpeed"`
- Dashboard shows: `"enhanced_pipeline"` or `"-"`

---

## 🎯 **ROOT CAUSE**

**Browser Cache** - The browser is serving an **old version** of `app.js` that doesn't have the updated `displaySubdomains()` function.

---

## ✅ **SOLUTION**

### **Step 1: Restart FastAPI Server**

```powershell
# Stop the server
Ctrl+C

# Restart
cd c:\recon-api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for:**
```
INFO:     Application startup complete.
```

---

### **Step 2: Hard Refresh Browser**

#### **Method A: Keyboard Shortcut (Fastest)**

```
1. Go to: http://127.0.0.1:8000/dashboard
2. Press: Ctrl + Shift + R  (Hard refresh)
   OR
   Press: Ctrl + F5  (Force reload)
3. Wait for page to fully reload
```

#### **Method B: DevTools (Most Reliable)**

```
1. Open: http://127.0.0.1:8000/dashboard
2. Press F12 (DevTools)
3. Right-click the refresh button (next to address bar)
4. Select "Empty Cache and Hard Reload"
5. Wait for page to reload
```

#### **Method C: Disable Cache (For Testing)**

```
1. Open: http://127.0.0.1:8000/dashboard
2. Press F12 (DevTools)
3. Go to "Network" tab
4. Check: "Disable cache"
5. Keep DevTools open
6. Refresh page (F5)
```

---

### **Step 3: Verify Fix**

```
1. Login to dashboard
2. Click on "example2.com" scan
3. Check subdomain table:
   - Webserver column should show "LiteSpeed"
   - Technologies column should show "LiteSpeed, LiteSpeed Cache"
   - Response Time column should show "691.3686ms"
```

**Expected Result:**

| Subdomain | Webserver | Technologies | Response Time |
|-----------|-----------|--------------|---------------|
| autodiscover.example2.com | **LiteSpeed** | **LiteSpeed, LiteSpeed Cache** | **691.3686ms** |
| mail.example2.com | **LiteSpeed** | **LiteSpeed, LiteSpeed Cache** | **722.1395ms** |

---

## 🐛 **DEBUGGING STEPS**

### **Step 1: Check Browser Console**

```
1. Press F12 → "Console" tab
2. Click on the scan
3. Look for debug messages:
   - "First subdomain data: {...}"
   - "Webserver: LiteSpeed"
   - "Technologies: [{...}]"
4. Look for RED error messages
```

**Expected Console Output:**
```
First subdomain data: {id: 99447, subdomain: "autodiscover.example2.com", webserver: "LiteSpeed", ...}
Webserver: LiteSpeed
Technologies: [{id: 289, name: "LiteSpeed"}, {id: 290, name: "LiteSpeed Cache"}, ...]
```

**If you see this:** The JavaScript is receiving the data correctly.

**If you DON'T see this:** The JavaScript file is still cached - try Method B or C above.

---

### **Step 2: Verify API Response**

```
1. Press F12 → "Network" tab
2. Click on the scan
3. Find request: /api/v1/scans/dab12b27-ce2f-4cdb-b297-4d8636e6c8f7
4. Click on it → "Response" tab
5. Verify response includes:
   - "webserver": "LiteSpeed"
   - "technologies": [...]
   - "url": "https://..."
```

**If API response is correct but console shows wrong data:**
- The browser is still using cached JavaScript
- Try clearing all browser data (Ctrl + Shift + Delete)

---

### **Step 3: Verify JavaScript File Version**

```
1. Press F12 → "Network" tab
2. Refresh page (F5)
3. Find request: /static/app.js?v=3
4. Click on it → "Response" tab
5. Search for: "First subdomain data"
6. Verify the debug logging code is present
```

**If you DON'T see the debug code:**
- The server is serving an old version
- Restart the FastAPI server
- Hard refresh again

---

## 🔍 **COMMON ISSUES**

### **Issue 1: Shows "enhanced_pipeline" in Multiple Columns**

**Cause:** Browser is using old JavaScript that has wrong column mapping.

**Solution:**
1. Hard refresh (Ctrl + Shift + R)
2. Clear cache and hard reload (DevTools method)
3. Restart server and refresh

---

### **Issue 2: Shows "-" for All Httpx Fields**

**Cause:** Either browser cache OR old scan data.

**Solution:**
1. Check if scan was created AFTER migration
2. If old scan: Create NEW scan
3. If new scan: Hard refresh browser

---

### **Issue 3: Console Shows Errors**

**Common Errors:**

**Error:** `Cannot read property 'name' of undefined`
**Cause:** Technologies array is null/undefined
**Solution:** Already fixed in code with `sub.technologies && sub.technologies.length > 0`

**Error:** `Failed to fetch`
**Cause:** Server not running or wrong URL
**Solution:** Restart FastAPI server

---

## 📝 **VERIFICATION CHECKLIST**

### **Before Testing:**
- [ ] Restart FastAPI server
- [ ] Hard refresh browser (Ctrl + Shift + R)
- [ ] Clear browser cache
- [ ] Check console for errors

### **During Testing:**
- [ ] API response includes httpx fields
- [ ] Console shows debug messages
- [ ] No RED errors in console
- [ ] JavaScript file version is ?v=3

### **After Testing:**
- [ ] Webserver column shows actual data
- [ ] Technologies column shows actual data
- [ ] Response Time column shows actual data
- [ ] Details modal shows all httpx fields

---

## 🚀 **DEPLOYMENT TO VPS**

After verifying locally, deploy to VPS:

```powershell
cd c:\recon-api
git add web/index.html web/app.js
git commit -m "fix: Add cache-busting and debug logging for httpx fields display"
git push origin main
```

**Then:**
1. Monitor GitHub Actions
2. Wait for deployment (~2-3 minutes)
3. Open VPS dashboard: http://124.197.22.184:8000/dashboard
4. Hard refresh (Ctrl + Shift + R)
5. Verify httpx fields display correctly

---

## 📊 **SUMMARY**

**Problem:** Browser cache serving old JavaScript

**Solution:**
1. ✅ Restart FastAPI server
2. ✅ Hard refresh browser (Ctrl + Shift + R)
3. ✅ Added cache-busting parameter (?v=3)
4. ✅ Added debug logging to console

**Files Modified:**
- `web/index.html` - Added cache-busting parameter
- `web/app.js` - Added debug logging

**Result:**
- ✅ Browser loads fresh JavaScript
- ✅ Dashboard displays httpx fields correctly
- ✅ Console shows debug information

---

**Follow the steps above and the dashboard should display the httpx fields correctly! 🎉**

