# 🚀 Hướng dẫn Setup và Sử dụng Recon API

## 📋 Mục lục
1. [Cài đặt Tools](#1-cài-đặt-tools)
2. [Setup Database và Redis](#2-setup-database-và-redis)
3. [Cài đặt Python Dependencies](#3-cài-đặt-python-dependencies)
4. [Chạy hệ thống](#4-chạy-hệ-thống)
5. [Sử dụng API](#5-sử-dụng-api)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Cài đặt Tools

### Cài đặt Go (nếu chưa có)
```bash
# Download và cài đặt Go
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz

# Thêm vào ~/.bashrc hoặc ~/.zshrc
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Reload shell
source ~/.bashrc
```

### Cài đặt Recon Tools
```bash
# Subfinder - Subdomain discovery
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Httpx - HTTP toolkit
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Assetfinder - Find domains and subdomains
go install -v github.com/tomnomnom/assetfinder@latest

# Httprobe - Take a list of domains and probe for working HTTP/HTTPS servers
go install -v github.com/tomnomnom/httprobe@latest

# Anew - Append lines from stdin to a file, but only if they don't already appear
go install -v github.com/tomnomnom/anew@latest

# Gowitness - Web screenshot utility
go install -v github.com/sensepost/gowitness@latest

# Amass - In-depth attack surface mapping
# Download binary
wget https://github.com/owasp-amass/amass/releases/download/v4.2.0/amass_Linux_amd64.zip
unzip amass_Linux_amd64.zip
sudo mv amass_Linux_amd64/amass /usr/local/bin/
rm -rf amass_Linux_amd64*
```

### Verify Tools Installation
```bash
# Check tất cả tools đã cài đặt
subfinder -version
amass -version
assetfinder -h
httprobe -h
httpx -version
anew -h
gowitness version
```

---

## 2. Setup Database và Redis

### Cài đặt PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Tạo database
sudo -u postgres psql
```

Trong PostgreSQL shell:
```sql
CREATE DATABASE recon_db;
CREATE USER recon_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE recon_db TO recon_user;
\q
```

### Cài đặt Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping
# Should return: PONG
```

---

## 3. Cài đặt Python Dependencies

```bash
# Clone repository
cd recon-api

# Tạo virtual environment (khuyến nghị)
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Copy và cấu hình .env
cp .env.example .env
```

### Cấu hình .env file
```bash
nano .env
```

Nội dung:
```env
# Database Configuration
DATABASE_URL=postgresql://recon_user:your_password@localhost:5432/recon_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_TITLE=Recon API
API_VERSION=1.0.0

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]

# File Storage
JOBS_DIRECTORY=./jobs

# Tool Paths
SUBFINDER_PATH=subfinder
AMASS_PATH=amass
ASSETFINDER_PATH=assetfinder
HTTPX_PATH=httpx
HTTPROBE_PATH=httprobe
ANEW_PATH=anew
GOWITNESS_PATH=gowitness
```

### Khởi tạo Database
```bash
# Tạo tables
python scripts/init_db.py

# Hoặc dùng Alembic
alembic upgrade head
```

---

## 4. Chạy hệ thống

### Option 1: Chạy thủ công (Development)

**Terminal 1 - API Server:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

**Terminal 3 - Celery Flower (Optional - Monitoring):**
```bash
source venv/bin/activate
celery -A app.workers.celery_app flower
```

### Option 2: Sử dụng Makefile

```bash
# Terminal 1 - API
make dev

# Terminal 2 - Worker
make worker

# Hoặc chạy multiple workers
make worker-multi
```

### Option 3: Docker (Production)

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Initialize database
docker-compose exec api alembic upgrade head
```

---

## 5. Sử dụng API

### Truy cập Web Interface
Mở browser: `http://localhost:8000`

### Truy cập API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Sử dụng API qua cURL

**1. Tạo Scan Job:**
```bash
curl -X POST "http://localhost:8000/api/v1/scans" \
     -H "Content-Type: application/json" \
     -d '{"domain": "fpt.ai"}'
```

Response:
```json
{
  "job_id": "abc123-def456-ghi789",
  "domain": "fpt.ai",
  "status": "pending",
  "message": "Scan job created successfully. Task ID: ..."
}
```

**2. Check Progress:**
```bash
curl "http://localhost:8000/api/v1/scans/{job_id}/progress"
```

Response:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "running",
  "progress": {
    "current": 65,
    "total": 100,
    "status": "Running httpx for detailed analysis..."
  }
}
```

**3. Get Results:**
```bash
curl "http://localhost:8000/api/v1/scans/{job_id}"
```

Response:
```json
{
  "job_id": "abc123-def456-ghi789",
  "domain": "fpt.ai",
  "status": "completed",
  "subdomains": [
    {
      "id": 1,
      "subdomain": "bot.fpt.ai",
      "status": "live",
      "is_live": true,
      "http_status": 200
    },
    ...
  ],
  "screenshots": [
    {
      "id": 1,
      "url": "https://bot.fpt.ai",
      "filename": "bot_fpt_ai.png",
      "file_path": "jobs/abc123/shots/bot_fpt_ai.png"
    },
    ...
  ]
}
```

**4. List All Scans:**
```bash
curl "http://localhost:8000/api/v1/scans?limit=10"
```

**5. Delete Scan:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/scans/{job_id}"
```

### Sử dụng Python Client

```python
import requests

# Tạo scan
response = requests.post(
    "http://localhost:8000/api/v1/scans",
    json={"domain": "fpt.ai"}
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Check progress
import time
while True:
    progress = requests.get(f"http://localhost:8000/api/v1/scans/{job_id}/progress")
    data = progress.json()
    print(f"Progress: {data}")
    
    if data.get("status") in ["completed", "failed"]:
        break
    
    time.sleep(5)

# Get results
results = requests.get(f"http://localhost:8000/api/v1/scans/{job_id}")
print(results.json())
```

---

## 6. Troubleshooting

### Lỗi: Tools not found
```bash
# Kiểm tra PATH
echo $PATH | grep go

# Verify tools
which subfinder
which amass
which httpx
```

### Lỗi: Database connection
```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Test connection
psql -U recon_user -d recon_db -h localhost
```

### Lỗi: Redis connection
```bash
# Check Redis running
sudo systemctl status redis

# Test connection
redis-cli ping
```

### Lỗi: Celery worker not processing
```bash
# Check Redis connection
redis-cli ping

# Check Celery logs
celery -A app.workers.celery_app inspect active

# Restart worker
pkill -f celery
make worker
```

### View Logs
```bash
# API logs
tail -f logs/api.log

# Worker logs
tail -f logs/worker.log

# Docker logs
docker-compose logs -f api
docker-compose logs -f worker
```

---

## 📊 Monitoring

### Celery Flower
Access: `http://localhost:5555`

Features:
- View active tasks
- Monitor worker status
- Task history
- Performance metrics

### Check Job Files
```bash
# List all jobs
ls -la jobs/

# View specific job
ls -la jobs/{job_id}/

# View subdomains found
cat jobs/{job_id}/subs.txt

# View live hosts
cat jobs/{job_id}/live.txt

# View screenshots
ls -la jobs/{job_id}/shots/
```

---

## 🎯 Tips & Best Practices

1. **Performance**: Sử dụng `make worker-multi` để chạy multiple workers
2. **Monitoring**: Luôn chạy Flower để monitor tasks
3. **Cleanup**: Định kỳ cleanup old jobs để tiết kiệm disk space
4. **Security**: Chỉ scan domains bạn có quyền
5. **Rate Limiting**: Cân nhắc thêm rate limiting cho production

---

## 🆘 Support

Nếu gặp vấn đề:
1. Check logs
2. Verify tools installation
3. Check database/Redis connection
4. Review configuration in .env file
