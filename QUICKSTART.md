# ⚡ Quick Start Guide

## 🚀 Cách chạy nhanh nhất (5 phút)

### 1. Chạy Quick Start Script
```bash
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh
```

Script sẽ tự động:
- ✅ Check prerequisites
- ✅ Setup virtual environment
- ✅ Install dependencies
- ✅ Create configuration files
- ✅ Initialize database

### 2. Start Services

**Terminal 1 - API Server:**
```bash
source venv/bin/activate
make dev
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
make worker
```

### 3. Test API

**Mở browser:**
```
http://localhost:8000
```

**Hoặc dùng cURL:**
```bash
# Tạo scan
curl -X POST "http://localhost:8000/api/v1/scans" \
     -H "Content-Type: application/json" \
     -d '{"domain": "fpt.ai"}'

# Lấy job_id từ response, sau đó check kết quả:
curl "http://localhost:8000/api/v1/scans/{job_id}"
```

---

## 🐳 Hoặc dùng Docker (Đơn giản hơn)

```bash
# Build và start
docker-compose up -d

# Init database
docker-compose exec api alembic upgrade head

# Check logs
docker-compose logs -f

# Access
# Web: http://localhost:8000
# Flower: http://localhost:5555
```

---

## 📋 Về Amass Output Filtering

### Vấn đề
Amass output có nhiều thông tin không cần thiết:
```
bot.fpt.ai (FQDN) --> a_record --> 124.197.26.207 (IPAddress)
172.64.0.0/18 (Netblock) --> contains --> 172.64.33.114 (IPAddress)
13335 (ASN) --> announces --> 172.64.0.0/18 (Netblock)
```

### Giải pháp
Hệ thống tự động lọc chỉ lấy FQDN:
```python
# Code tự động filter trong app/services/pipeline.py
async def _filter_amass_output(self, raw_file: Path):
    """Filter amass output to extract only FQDNs"""
    fqdns = set()
    
    with open(raw_file, 'r') as f:
        for line in f:
            if '-->' in line:
                # Extract FQDN from: "domain.com (FQDN) --> ..."
                match = re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\s+\(FQDN\)', line)
                if match:
                    domain = line.split('(FQDN)')[0].strip().lower()
                    if domain.endswith(self.domain):
                        fqdns.add(domain)
    
    # Save filtered results
    with open(self.amass_file, 'w') as f:
        for fqdn in sorted(fqdns):
            f.write(f"{fqdn}\n")
```

### Test Filtering
```bash
# Test script để verify filtering
python scripts/test_amass_filter.py
```

Output:
```
🔍 Testing Amass Output Filtering
==============================================================

🎯 Target Domain: fpt.ai
📄 Processing 57 lines of Amass output...

✅ Found 7 unique subdomains:
------------------------------------------------------------
 1. agribank-export-service.fpt.ai
 2. bot.fpt.ai
 3. cdn-static-v3.fpt.ai
 4. ivechat.fpt.ai
 5. livesupport.tcb.fpt.ai
 6. staging-callcenter.fpt.ai
 7. tpb-rating.fpt.ai
 8. www.fpt.ai

==============================================================
📊 Summary:
   Total lines processed: 57
   Unique FQDNs extracted: 8
   Filtered out: 49 lines
```

---

## 🔧 Pipeline Flow

```
1. Subdomain Enumeration
   ├─ subfinder -d domain.com -silent -o subs.txt
   ├─ amass enum -passive -d domain.com -o amass_raw.txt
   │  └─ Filter only FQDNs → amass.txt
   │  └─ cat amass.txt | anew subs.txt
   └─ assetfinder --subs-only domain.com | anew subs.txt

2. Live Host Detection
   ├─ cat subs.txt | httprobe > httprobe.txt (quick check)
   └─ cat subs.txt | httpx -silent -mc 200,301,302 -title -tech-detect -json > live.txt

3. Screenshot Capture
   └─ gowitness scan file -f live.txt --threads 4 --screenshot-path shots/
```

---

## 📊 Monitoring Progress

### Via API
```bash
# Check progress
curl "http://localhost:8000/api/v1/scans/{job_id}/progress"
```

Response:
```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": {
    "current": 65,
    "total": 100,
    "status": "Running httpx for detailed analysis..."
  }
}
```

### Via Celery Flower
```
http://localhost:5555
```

### Via Files
```bash
# View discovered subdomains
cat jobs/{job_id}/subs.txt

# View live hosts
cat jobs/{job_id}/live.txt

# View screenshots
ls jobs/{job_id}/shots/
```

---

## 🎯 Example Usage

### Python Client
```python
import requests
import time

# Create scan
response = requests.post(
    "http://localhost:8000/api/v1/scans",
    json={"domain": "fpt.ai"}
)
job_id = response.json()["job_id"]

# Monitor progress
while True:
    progress = requests.get(
        f"http://localhost:8000/api/v1/scans/{job_id}/progress"
    ).json()
    
    print(f"Progress: {progress['progress']['current']}% - {progress['progress']['status']}")
    
    if progress['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# Get results
results = requests.get(f"http://localhost:8000/api/v1/scans/{job_id}").json()
print(f"Found {len(results['subdomains'])} subdomains")
print(f"Found {len(results['screenshots'])} screenshots")
```

---

## 🆘 Troubleshooting

### Tools not found
```bash
# Add Go bin to PATH
export PATH=$PATH:$HOME/go/bin

# Verify
which subfinder
which amass
```

### Database connection error
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Create database
sudo -u postgres createdb recon_db
```

### Redis connection error
```bash
# Check Redis
sudo systemctl status redis

# Start Redis
sudo systemctl start redis
```

### Celery worker not processing
```bash
# Check Redis connection
redis-cli ping

# Restart worker
pkill -f celery
make worker
```

---

## 📚 Full Documentation

- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API Documentation**: http://localhost:8000/docs
- **README**: [README.md](README.md)

---

## 💡 Tips

1. **Multiple Workers**: Use `make worker-multi` for better performance
2. **Monitoring**: Always run Flower to monitor tasks
3. **Testing**: Test Amass filtering with `python scripts/test_amass_filter.py`
4. **Cleanup**: Regularly cleanup old jobs to save disk space

---

## 🎉 You're Ready!

Hệ thống đã sẵn sàng để scan subdomains với:
- ✅ Automatic Amass output filtering
- ✅ Multi-tool subdomain discovery
- ✅ Live host detection
- ✅ Screenshot capture
- ✅ Progress tracking
- ✅ Retry logic

Happy Hunting! 🎯
