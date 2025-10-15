# 🪟 Hướng dẫn Setup và Chạy trên Windows

## 📋 Yêu cầu đã cài đặt

- ✅ Python 3.8+ 
- ✅ PostgreSQL
- ✅ Redis
- ✅ Go (để cài các recon tools)
- ✅ Các recon tools: subfinder, amass, assetfinder, httpx, httprobe, anew, gowitness

---

## 🚀 Các bước Setup

### **Bước 1: Tạo file .env**

```powershell
# Mở PowerShell trong thư mục recon-api
cd C:\recon-api

# Copy file .env.example thành .env
copy .env.example .env

# Mở và chỉnh sửa file .env
notepad .env
```

**Chỉnh sửa file .env:**
```env
# Thay your_password_here bằng password PostgreSQL của bạn
DATABASE_URL=postgresql://postgres:your_password_here@localhost:5432/recon_db

# Redis (giữ nguyên nếu Redis chạy mặc định)
REDIS_URL=redis://localhost:6379/0

# Các cấu hình khác giữ nguyên
```

**Lưu file và đóng notepad.**

---

### **Bước 2: Tạo Database PostgreSQL**

#### **Cách 1: Dùng Command Line (psql)**

```powershell
# Mở PowerShell hoặc Command Prompt

# Nếu psql đã có trong PATH:
psql -U postgres

# Nếu chưa có trong PATH, cd vào thư mục PostgreSQL:
cd "C:\Program Files\PostgreSQL\15\bin"
.\psql -U postgres
```

**Trong psql shell:**
```sql
-- Tạo database
CREATE DATABASE recon_db;

-- Kiểm tra database đã tạo
\l

-- Thoát
\q
```

#### **Cách 2: Dùng pgAdmin (GUI - Dễ hơn)**

1. Mở **pgAdmin 4** (tìm trong Start Menu)
2. Nhập master password nếu được hỏi
3. Expand **Servers** → **PostgreSQL 15** (hoặc version bạn cài)
4. Right-click **Databases** → **Create** → **Database...**
5. Trong tab **General**:
   - **Database**: `recon_db`
   - **Owner**: `postgres`
6. Click **Save**

✅ **Database đã được tạo!**

---

### **Bước 3: Kiểm tra Redis**

```powershell
# Kiểm tra Redis đang chạy
redis-cli ping
```

**Nếu trả về `PONG`** → Redis OK ✅

**Nếu lỗi:**
1. Mở **Services** (Win + R → gõ `services.msc` → Enter)
2. Tìm **Redis** trong danh sách
3. Right-click → **Start**
4. Kiểm tra lại: `redis-cli ping`

---

### **Bước 4: Setup Python Virtual Environment**

```powershell
# Mở PowerShell trong thư mục recon-api
cd C:\recon-api

# Tạo virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**Nếu gặp lỗi "execution policy":**
```powershell
# Chạy lệnh này (chỉ cần 1 lần)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Sau đó activate lại
.\venv\Scripts\Activate.ps1
```

**Khi thành công, bạn sẽ thấy `(venv)` ở đầu dòng:**
```
(venv) PS C:\recon-api>
```

---

### **Bước 5: Cài đặt Python Dependencies**

```powershell
# Đảm bảo venv đã activate
(venv) PS C:\recon-api>

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Cài đặt dependencies
pip install -r requirements.txt
```

**⚠️ Lưu ý cho Python 3.13:**
- Nếu bạn dùng **Python 3.13** và gặp lỗi về `pydantic` hoặc `Rust compiler`, xem file **PYTHON_313_FIX.md**
- File `requirements.txt` đã được cập nhật để tương thích Python 3.13
- Nếu vẫn lỗi, chạy: `pip install --prefer-binary -r requirements.txt`

**Đợi khoảng 2-5 phút để cài đặt xong.**

---

### **Bước 6: Khởi tạo Database Tables**

```powershell
# Cách 1: Dùng script Windows
.\scripts\init_db_windows.bat

# Cách 2: Chạy trực tiếp
python scripts\init_db.py
```

**Output mong đợi:**
```
Connecting to database: postgresql://postgres:***@localhost:5432/recon_db
Creating database tables...
Database initialized successfully!
Tables created:
  - scan_jobs
  - subdomains
  - screenshots
```

✅ **Database đã sẵn sàng!**

---

## 🎯 Cách Chạy Hệ Thống

### **Cách 1: Dùng Batch Scripts (Khuyến nghị - Dễ nhất)**

**Mở 3 cửa sổ PowerShell/CMD riêng biệt:**

#### **Cửa sổ 1 - API Server:**
```powershell
# Double-click file hoặc chạy:
.\start_api.bat
```

#### **Cửa sổ 2 - Celery Worker:**
```powershell
# Double-click file hoặc chạy:
.\start_worker.bat
```

#### **Cửa sổ 3 - Flower (Optional - Monitoring):**
```powershell
# Double-click file hoặc chạy:
.\start_flower.bat
```

### **Cách 2: Chạy thủ công**

#### **Terminal 1 - API Server:**
```powershell
cd C:\recon-api
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Terminal 2 - Celery Worker:**
```powershell
cd C:\recon-api
.\venv\Scripts\Activate.ps1
celery -A app.workers.celery_app worker --loglevel=info --pool=solo --concurrency=2
```

**⚠️ Lưu ý:** Trên Windows, Celery cần dùng `--pool=solo` hoặc `--pool=gevent`

#### **Terminal 3 - Flower (Optional):**
```powershell
cd C:\recon-api
.\venv\Scripts\Activate.ps1
celery -A app.workers.celery_app flower
```

---

## 🌐 Truy cập Ứng dụng

Sau khi chạy xong, mở browser:

- **Web Interface**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Celery Flower (Monitoring)**: http://localhost:5555

---

## 🧪 Test Hệ Thống

### **Test 1: Qua Web Interface**

1. Mở http://localhost:8000
2. Nhập domain: `example.com`
3. Click **Start Scan**
4. Lưu lại **Job ID**
5. Nhập Job ID vào ô **Check Scan Status**
6. Click **Check Status** để xem kết quả

### **Test 2: Qua API (PowerShell)**

```powershell
# Tạo scan job
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"domain": "example.com"}'

# Lấy job_id
$jobId = $response.job_id
Write-Host "Job ID: $jobId"

# Check progress
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId/progress"

# Get results
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$jobId"
```

### **Test 3: Qua cURL (nếu có cài)**

```bash
# Tạo scan
curl -X POST "http://localhost:8000/api/v1/scans" ^
     -H "Content-Type: application/json" ^
     -d "{\"domain\": \"example.com\"}"

# Check results (thay {job_id} bằng ID thực tế)
curl "http://localhost:8000/api/v1/scans/{job_id}"
```

---

## 📊 Xem Kết Quả

### **Qua Web Interface:**
- Vào http://localhost:8000
- Nhập Job ID và click Check Status

### **Qua Files:**
```powershell
# Xem subdomains tìm được
type jobs\{job_id}\subs.txt

# Xem live hosts
type jobs\{job_id}\live.txt

# Xem screenshots
dir jobs\{job_id}\shots\
```

### **Qua Flower:**
- Vào http://localhost:5555
- Xem tasks đang chạy
- Xem task history

---

## 🐛 Troubleshooting

### **Lỗi: "psql is not recognized"**
```powershell
# Thêm PostgreSQL vào PATH
# Mở System Environment Variables:
# Win + R → sysdm.cpl → Advanced → Environment Variables
# Thêm vào Path: C:\Program Files\PostgreSQL\15\bin
```

### **Lỗi: "redis-cli is not recognized"**
```powershell
# Thêm Redis vào PATH
# Thêm vào Path: C:\Program Files\Redis
```

### **Lỗi: "execution policy" khi activate venv**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Lỗi: Celery không chạy trên Windows**
```powershell
# Phải dùng --pool=solo
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### **Lỗi: Database connection failed**
```powershell
# Kiểm tra PostgreSQL đang chạy
# Services → PostgreSQL → Start

# Kiểm tra password trong .env file
notepad .env
```

### **Lỗi: Redis connection failed**
```powershell
# Kiểm tra Redis đang chạy
redis-cli ping

# Nếu không chạy:
# Services → Redis → Start
```

### **Lỗi: Tools not found**
```powershell
# Kiểm tra tools đã cài
subfinder -version
amass -version
httpx -version

# Nếu không tìm thấy, kiểm tra Go bin trong PATH
# Thêm vào Path: %USERPROFILE%\go\bin
```

---

## 📝 Các Lệnh Hữu Ích

### **Kiểm tra Services:**
```powershell
# PostgreSQL
Get-Service -Name postgresql*

# Redis
Get-Service -Name Redis
```

### **Xem Logs:**
```powershell
# API logs (nếu có)
type logs\api.log

# Worker logs (nếu có)
type logs\worker.log
```

### **Stop Services:**
```powershell
# Stop API: Ctrl + C trong terminal đang chạy API
# Stop Worker: Ctrl + C trong terminal đang chạy Worker
# Stop Flower: Ctrl + C trong terminal đang chạy Flower
```

### **Deactivate Virtual Environment:**
```powershell
deactivate
```

---

## 🎯 Quick Reference

### **Start Everything:**
1. Double-click `start_api.bat`
2. Double-click `start_worker.bat`
3. Double-click `start_flower.bat` (optional)

### **Access:**
- Web: http://localhost:8000
- Docs: http://localhost:8000/docs
- Flower: http://localhost:5555

### **Stop Everything:**
- Press `Ctrl + C` in each terminal window

---

## 💡 Tips cho Windows

1. **Tạo Desktop Shortcuts:**
   - Right-click `start_api.bat` → Send to → Desktop (create shortcut)
   - Làm tương tự cho `start_worker.bat`

2. **Chạy tự động khi khởi động:**
   - Win + R → `shell:startup`
   - Copy shortcuts vào folder này

3. **Sử dụng Windows Terminal:**
   - Cài Windows Terminal từ Microsoft Store
   - Có thể mở nhiều tabs trong 1 cửa sổ

4. **Kiểm tra Port đang dùng:**
   ```powershell
   netstat -ano | findstr :8000
   netstat -ano | findstr :6379
   netstat -ano | findstr :5432
   ```

---

## 🆘 Cần Giúp Đỡ?

1. Kiểm tra logs trong terminal
2. Kiểm tra file .env
3. Kiểm tra PostgreSQL và Redis đang chạy
4. Kiểm tra tools đã cài đúng chưa
5. Xem SETUP_GUIDE.md để biết thêm chi tiết

---

## ✅ Checklist

- [ ] PostgreSQL đã cài và đang chạy
- [ ] Redis đã cài và đang chạy
- [ ] Python 3.8+ đã cài
- [ ] Go đã cài
- [ ] Các recon tools đã cài (subfinder, amass, httpx, etc.)
- [ ] File .env đã tạo và cấu hình đúng
- [ ] Database `recon_db` đã tạo
- [ ] Virtual environment đã tạo và activate
- [ ] Dependencies đã cài (pip install -r requirements.txt)
- [ ] Database tables đã khởi tạo (python scripts\init_db.py)
- [ ] API server đang chạy (start_api.bat)
- [ ] Celery worker đang chạy (start_worker.bat)
- [ ] Có thể truy cập http://localhost:8000

**Nếu tất cả đều ✅ → Hệ thống đã sẵn sàng! 🎉**
