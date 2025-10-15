# 🔧 Fix Redis & Celery Issues

## ❌ Các lỗi bạn đang gặp

### 1. Job status "pending" mãi không chạy
```json
{
  "job_id": "a36811ce-e149-4e23-961c-ba5a18127035",
  "status": "pending"
}
```

### 2. Progress trả về "Task not found"
```json
{
  "status": "unknown",
  "message": "Task not found in active tasks"
}
```

### 3. Scan job not found
```json
{
  "detail": "Scan job not found"
}
```

### 4. Redis connection warning
```
[WARNING] Cannot connect to Redis
```

---

## 🔍 Nguyên nhân

### Vấn đề 1: Redis chạy trong WSL, không accessible từ Windows
- Redis đang chạy trong **WSL Ubuntu** (`wsl -d Ubuntu-22.04`)
- App Python chạy trên **Windows**
- → App không thể kết nối đến Redis trong WSL!

### Vấn đề 2: Celery Worker không chạy
- Không có worker để xử lý tasks
- Job tạo ra nhưng không ai xử lý → status "pending" mãi

### Vấn đề 3: URL encoding sai
- URL: `http://localhost:8000/api/v1/scans/%7Ba36811ce-e149-4e23-961c-ba5a18127035%7D`
- `%7B` = `{` và `%7D` = `}` → **KHÔNG nên có dấu ngoặc nhọn!**
- **Đúng:** `http://localhost:8000/api/v1/scans/a36811ce-e149-4e23-961c-ba5a18127035`

---

## ✅ Giải pháp

### **Bước 1: Cài Redis trên Windows**

Redis phải chạy trên **Windows**, không phải WSL!

#### **Cách A: Dùng Memurai (Khuyến nghị)**

1. Download: https://www.memurai.com/get-memurai
2. Cài đặt file `.msi`
3. Chọn "Install as Windows Service" ✅
4. Verify:
   ```powershell
   redis-cli ping
   # Output: PONG
   ```

#### **Cách B: Dùng Docker Desktop**

```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

#### **Cách C: Expose Redis từ WSL (Không khuyến nghị)**

Xem chi tiết trong file: **INSTALL_REDIS_WINDOWS.md**

---

### **Bước 2: Stop Redis trong WSL**

```powershell
# Stop Redis trong WSL
wsl -d Ubuntu-22.04 sudo systemctl stop redis-server

# Disable auto-start
wsl -d Ubuntu-22.04 sudo systemctl disable redis-server
```

---

### **Bước 3: Verify Redis trên Windows**

```powershell
# Test Redis
redis-cli ping
# Output: PONG

# Test từ Python
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
# Output: True
```

---

### **Bước 4: Kiểm tra .env file**

```powershell
notepad .env
```

**Đảm bảo:**
```env
REDIS_URL=redis://localhost:6379/0
```

**KHÔNG phải:**
```env
REDIS_URL=redis://172.x.x.x:6379/0  # ❌ WSL IP
```

---

### **Bước 5: Restart tất cả services**

```powershell
# Stop tất cả (Ctrl+C trong mỗi terminal)

# Chạy lại
.\start_all.bat
```

**Hoặc chạy từng phần:**

**Terminal 1 - API:**
```powershell
.\start_api.bat
```

**Terminal 2 - Worker (QUAN TRỌNG!):**
```powershell
.\start_worker.bat
```

**Terminal 3 - Flower:**
```powershell
.\start_flower.bat
```

---

### **Bước 6: Test API đúng cách**

#### **Cách 1: Dùng PowerShell script**

```powershell
.\scripts\test_api.ps1
```

#### **Cách 2: Thủ công**

```powershell
# Tạo scan
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"domain": "example.com"}'

# Lấy job_id
$jobId = $response.job_id
Write-Host "Job ID: $jobId"

# Check progress (KHÔNG có dấu ngoặc nhọn!)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId/progress"

# Get results (KHÔNG có dấu ngoặc nhọn!)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId"
```

#### **Cách 3: Dùng browser**

1. Mở: http://localhost:8000/docs
2. Expand **POST /api/v1/scans**
3. Click **Try it out**
4. Nhập:
   ```json
   {
     "domain": "example.com"
   }
   ```
5. Click **Execute**
6. Copy `job_id` từ response
7. Expand **GET /api/v1/scans/{job_id}**
8. Paste `job_id` (KHÔNG có dấu ngoặc nhọn!)
9. Click **Execute**

---

## ✅ Verify hệ thống hoạt động

### **Check 1: Redis**
```powershell
redis-cli ping
# Output: PONG
```

### **Check 2: API**
```powershell
curl http://localhost:8000/docs
# Nên mở được Swagger UI
```

### **Check 3: Worker**
Trong terminal chạy `start_worker.bat`, bạn nên thấy:
```
[tasks]
  . app.workers.tasks.run_recon_scan
  . app.workers.tasks.run_subdomain_enumeration
  . app.workers.tasks.run_live_host_check
  . app.workers.tasks.run_screenshot_capture

[2025-10-05 17:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-10-05 17:00:00,000: INFO/MainProcess] celery@HOSTNAME ready.
```

### **Check 4: Flower**
```powershell
# Mở browser
start http://localhost:5555
```

### **Check 5: Create và monitor scan**
```powershell
.\scripts\test_api.ps1
```

---

## 📊 Luồng hoạt động đúng

```
1. User tạo scan → POST /api/v1/scans
   ↓
2. API tạo job trong database (status: pending)
   ↓
3. API gửi task đến Redis queue
   ↓
4. Celery Worker lấy task từ Redis
   ↓
5. Worker chạy pipeline (subfinder → amass → httpx → gowitness)
   ↓
6. Worker cập nhật progress vào Redis
   ↓
7. Worker lưu kết quả vào database (status: completed)
   ↓
8. User check progress → GET /api/v1/scans/{job_id}/progress
   ↓
9. User get results → GET /api/v1/scans/{job_id}
```

---

## 🐛 Troubleshooting

### Lỗi: "Cannot connect to Redis"

**Kiểm tra:**
```powershell
# Redis có chạy không?
redis-cli ping

# Service có start không?
Get-Service -Name *redis* | Select-Object Name, Status

# Port có mở không?
netstat -ano | findstr :6379
```

**Fix:**
```powershell
# Win + R → services.msc
# Tìm Redis → Right-click → Start
```

### Lỗi: "Task not found in active tasks"

**Nguyên nhân:** Celery Worker không chạy

**Fix:**
```powershell
# Chạy worker
.\start_worker.bat
```

### Lỗi: "Scan job not found"

**Nguyên nhân:** URL sai (có dấu ngoặc nhọn)

**Sai:**
```
http://localhost:8000/api/v1/scans/{a36811ce-e149-4e23-961c-ba5a18127035}
```

**Đúng:**
```
http://localhost:8000/api/v1/scans/a36811ce-e149-4e23-961c-ba5a18127035
```

### Job status "pending" mãi

**Nguyên nhân:**
1. Worker không chạy
2. Redis không kết nối được
3. Worker bị lỗi

**Fix:**
```powershell
# Check worker logs
# Xem terminal đang chạy start_worker.bat

# Restart worker
# Ctrl+C → .\start_worker.bat
```

---

## 📝 Checklist

- [ ] Redis chạy trên **Windows** (không phải WSL)
- [ ] `redis-cli ping` trả về `PONG`
- [ ] File `.env` có `REDIS_URL=redis://localhost:6379/0`
- [ ] API server đang chạy (`start_api.bat`)
- [ ] **Celery Worker đang chạy** (`start_worker.bat`) ← QUAN TRỌNG!
- [ ] Worker logs hiện "celery@HOSTNAME ready"
- [ ] Flower accessible tại http://localhost:5555
- [ ] Test API không có dấu ngoặc nhọn trong URL

---

## 🎉 Kết quả mong đợi

Sau khi fix:

1. ✅ Tạo scan → Status "pending"
2. ✅ Worker nhận task → Status "running"
3. ✅ Progress updates real-time
4. ✅ Scan hoàn thành → Status "completed"
5. ✅ Có kết quả subdomains và screenshots

---

**Hãy làm theo từng bước và test lại! 🚀**
