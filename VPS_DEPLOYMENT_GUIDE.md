# 🚀 HƯỚNG DẪN DEPLOY LÊN VPS

**VPS IP:** 124.197.22.184  
**User:** root  
**Hệ điều hành:** Linux (Ubuntu/Debian recommended)

---

## 📋 MỤC LỤC

1. [Chuẩn bị VPS](#1-chuẩn-bị-vps)
2. [Cài đặt Dependencies](#2-cài-đặt-dependencies)
3. [Upload Code lên VPS](#3-upload-code-lên-vps)
4. [Cấu hình Database](#4-cấu-hình-database)
5. [Cấu hình Redis](#5-cấu-hình-redis)
6. [Cài đặt CLI Tools](#6-cài-đặt-cli-tools)
7. [Cấu hình Environment](#7-cấu-hình-environment)
8. [Chạy Database Migration](#8-chạy-database-migration)
9. [Cấu hình Systemd Services](#9-cấu-hình-systemd-services)
10. [Cấu hình Nginx Reverse Proxy](#10-cấu-hình-nginx-reverse-proxy)
11. [Kiểm tra và Monitoring](#11-kiểm-tra-và-monitoring)

---

## 1. CHUẨN BỊ VPS

### Bước 1.1: Kết nối SSH

```bash
# Từ máy Windows, mở PowerShell
ssh root@124.197.22.184
```

### Bước 1.2: Update hệ thống

```bash
# Update package list
apt update && apt upgrade -y

# Cài đặt các tools cơ bản
apt install -y git curl wget vim htop net-tools ufw
```

### Bước 1.3: Tạo user riêng (recommended)

```bash
# Tạo user cho application
adduser recon
usermod -aG sudo recon

# Chuyển sang user recon
su - recon
```

---

## 2. CÀI ĐẶT DEPENDENCIES

### Bước 2.1: Cài đặt Python 3.13

```bash
# Thêm deadsnakes PPA (cho Ubuntu)
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Cài Python 3.13
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Cài pip
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.13

# Kiểm tra version
python3.13 --version
```

### Bước 2.2: Cài đặt PostgreSQL

```bash
# Cài PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Khởi động PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Kiểm tra status
sudo systemctl status postgresql
```

### Bước 2.3: Cài đặt Redis

```bash
# Cài Redis
sudo apt install -y redis-server

# Cấu hình Redis
sudo vim /etc/redis/redis.conf
# Tìm dòng: supervised no
# Đổi thành: supervised systemd

# Khởi động Redis
sudo systemctl restart redis
sudo systemctl enable redis

# Kiểm tra
redis-cli ping
# Kết quả: PONG
```

### Bước 2.4: Cài đặt Nginx

```bash
# Cài Nginx
sudo apt install -y nginx

# Khởi động Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Bước 2.5: Cài đặt Go (cho CLI tools)

```bash
# Download Go
cd /tmp
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Giải nén
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Thêm vào PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
source ~/.bashrc

# Kiểm tra
go version
```

---

## 3. UPLOAD CODE LÊN VPS

### Phương án 1: Sử dụng Git (Recommended)

```bash
# Trên VPS
cd /home/recon
git clone <your-repo-url> recon-api
cd recon-api
```

### Phương án 2: Sử dụng SCP từ Windows

```powershell
# Trên máy Windows (PowerShell)
# Nén project
Compress-Archive -Path C:\recon-api\* -DestinationPath C:\recon-api.zip

# Upload lên VPS
scp C:\recon-api.zip root@124.197.22.184:/home/recon/

# Trên VPS
cd /home/recon
unzip recon-api.zip -d recon-api
cd recon-api
```

### Phương án 3: Sử dụng rsync (nếu có WSL)

```bash
# Từ WSL hoặc Git Bash
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='jobs/' \
  /mnt/c/recon-api/ root@124.197.22.184:/home/recon/recon-api/
```

---

## 4. CÁU HÌNH DATABASE

### Bước 4.1: Tạo database và user

```bash
# Chuyển sang user postgres
sudo -u postgres psql

# Trong PostgreSQL shell
CREATE DATABASE recon_db;
CREATE USER recon_user WITH PASSWORD 'your_strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE recon_db TO recon_user;
\q
```

### Bước 4.2: Cho phép kết nối từ localhost

```bash
# Kiểm tra file cấu hình
sudo vim /etc/postgresql/*/main/pg_hba.conf

# Đảm bảo có dòng:
# local   all             all                                     md5
# host    all             all             127.0.0.1/32            md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## 5. CẤU HÌNH REDIS

Redis đã được cài ở bước 2.3, giờ cần kiểm tra:

```bash
# Kiểm tra Redis đang chạy
sudo systemctl status redis

# Test kết nối
redis-cli ping
# Output: PONG

# Kiểm tra port
sudo netstat -tulpn | grep redis
# Output: tcp 0 0 127.0.0.1:6379 ... LISTEN
```

---

## 6. CÀI ĐẶT CLI TOOLS

### Bước 6.1: Cài đặt subfinder

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

### Bước 6.2: Cài đặt amass

```bash
go install -v github.com/owasp-amass/amass/v4/...@master
```

### Bước 6.3: Cài đặt assetfinder

```bash
go install github.com/tomnomnom/assetfinder@latest
```

### Bước 6.4: Cài đặt httprobe

```bash
go install github.com/tomnomnom/httprobe@latest
```

### Bước 6.5: Cài đặt httpx

```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

### Bước 6.6: Cài đặt anew

```bash
go install -v github.com/tomnomnom/anew@latest
```

### Bước 6.7: Cài đặt gowitness

```bash
go install github.com/sensepost/gowitness@latest
```

### Bước 6.8: Cài đặt wafw00f

```bash
sudo pip3 install wafw00f
```

### Bước 6.9: Upload SourceLeakHacker.py

```bash
# Đảm bảo file SourceLeakHacker.py đã được upload cùng với code
# Kiểm tra
ls -la /home/recon/recon-api/SourceLeakHacker.py

# Nếu chưa có, upload từ Windows:
# scp C:\recon-api\SourceLeakHacker.py root@124.197.22.184:/home/recon/recon-api/
```

### Bước 6.10: Kiểm tra tất cả tools

```bash
# Kiểm tra từng tool
subfinder -version
amass -version
assetfinder -h
httprobe -h
httpx -version
anew -h
gowitness version
wafw00f -h
python3.13 SourceLeakHacker.py -h
```

---

## 7. CẤU HÌNH ENVIRONMENT

### Bước 7.1: Tạo Python virtual environment

```bash
cd /home/recon/recon-api

# Tạo venv
python3.13 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Bước 7.2: Cài đặt Python dependencies

```bash
# Cài đặt từ requirements.txt
pip install -r requirements.txt

# Kiểm tra
pip list
```

### Bước 7.3: Tạo file .env

```bash
# Tạo file .env
vim .env
```

**Nội dung file .env:**

```bash
# Database
DATABASE_URL=postgresql://recon_user:your_strong_password_here@localhost:5432/recon_db

# Redis
REDIS_URL=redis://localhost:6379/0

# API Settings
API_TITLE=Recon API
API_VERSION=1.0.0

# CORS (thêm IP VPS của bạn)
CORS_ORIGINS=["http://localhost:8000","http://124.197.22.184","http://124.197.22.184:8000"]

# File storage
JOBS_DIRECTORY=/home/recon/recon-api/jobs

# Tool paths (đã có trong PATH)
SUBFINDER_PATH=subfinder
AMASS_PATH=amass
ASSETFINDER_PATH=assetfinder
HTTPX_PATH=httpx
HTTPROBE_PATH=httprobe
ANEW_PATH=anew
GOWITNESS_PATH=gowitness
WAFW00F_PATH=wafw00f
SOURCELEAKHACKER_PATH=/home/recon/recon-api/SourceLeakHacker.py
PYTHON_EXECUTABLE=python3.13

# Tool timeouts (seconds)
SUBFINDER_TIMEOUT=600
AMASS_TIMEOUT=1200
ASSETFINDER_TIMEOUT=300
HTTPX_TIMEOUT=900
HTTPROBE_TIMEOUT=600
GOWITNESS_TIMEOUT=1800
WAFW00F_TIMEOUT=900
SOURCELEAKHACKER_TIMEOUT=2800
```

### Bước 7.4: Tạo thư mục jobs

```bash
mkdir -p /home/recon/recon-api/jobs
chmod 755 /home/recon/recon-api/jobs
```

---

## 8. CHẠY DATABASE MIGRATION

```bash
cd /home/recon/recon-api
source venv/bin/activate

# Chạy Alembic migration
alembic upgrade head

# Kiểm tra tables đã được tạo
sudo -u postgres psql -d recon_db -c "\dt"
```

**Kết quả mong đợi:**
```
                List of relations
 Schema |       Name        | Type  |   Owner
--------+-------------------+-------+------------
 public | alembic_version   | table | recon_user
 public | leak_detections   | table | recon_user
 public | scan_jobs         | table | recon_user
 public | screenshots       | table | recon_user
 public | subdomains        | table | recon_user
 public | waf_detections    | table | recon_user
```

---

## 9. CẤU HÌNH SYSTEMD SERVICES

### Bước 9.1: Tạo service cho FastAPI

```bash
sudo vim /etc/systemd/system/recon-api.service
```

**Nội dung:**

```ini
[Unit]
Description=Recon API FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=recon
Group=recon
WorkingDirectory=/home/recon/recon-api
Environment="PATH=/home/recon/recon-api/venv/bin:/home/recon/go/bin:/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/recon/recon-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Bước 9.2: Tạo service cho Celery Worker

```bash
sudo vim /etc/systemd/system/recon-celery.service
```

**Nội dung:**

```ini
[Unit]
Description=Recon Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=recon
Group=recon
WorkingDirectory=/home/recon/recon-api
Environment="PATH=/home/recon/recon-api/venv/bin:/home/recon/go/bin:/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/recon/recon-api/venv/bin/celery -A app.workers.celery_app worker --loglevel=info -Q recon_full,leak_check,waf_check -n worker1@%%h
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Bước 9.3: Tạo service cho Flower (optional - monitoring)

```bash
sudo vim /etc/systemd/system/recon-flower.service
```

**Nội dung:**

```ini
[Unit]
Description=Recon Flower Celery Monitoring
After=network.target redis.service

[Service]
Type=simple
User=recon
Group=recon
WorkingDirectory=/home/recon/recon-api
Environment="PATH=/home/recon/recon-api/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/recon/recon-api/venv/bin/celery -A app.workers.celery_app flower --port=5555
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Bước 9.4: Khởi động các services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (tự động chạy khi boot)
sudo systemctl enable recon-api
sudo systemctl enable recon-celery
sudo systemctl enable recon-flower

# Start services
sudo systemctl start recon-api
sudo systemctl start recon-celery
sudo systemctl start recon-flower

# Kiểm tra status
sudo systemctl status recon-api
sudo systemctl status recon-celery
sudo systemctl status recon-flower
```

---

## 10. CẤU HÌNH NGINX REVERSE PROXY

### Bước 10.1: Tạo Nginx config

```bash
sudo vim /etc/nginx/sites-available/recon-api
```

**Nội dung:**

```nginx
server {
    listen 80;
    server_name 124.197.22.184;

    client_max_body_size 100M;

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (nếu cần)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Dashboard (web interface)
    location /dashboard {
        proxy_pass http://127.0.0.1:8000/dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Jobs directory (screenshots)
    location /jobs/ {
        proxy_pass http://127.0.0.1:8000/jobs/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Root
    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Flower monitoring (optional)
    location /flower/ {
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Bước 10.2: Enable site và restart Nginx

```bash
# Tạo symbolic link
sudo ln -s /etc/nginx/sites-available/recon-api /etc/nginx/sites-enabled/

# Xóa default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 11. KIỂM TRA VÀ MONITORING

### Bước 11.1: Kiểm tra các services

```bash
# Kiểm tra tất cả services
sudo systemctl status recon-api
sudo systemctl status recon-celery
sudo systemctl status recon-flower
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Kiểm tra logs
sudo journalctl -u recon-api -f
sudo journalctl -u recon-celery -f
```

### Bước 11.2: Kiểm tra ports đang listen

```bash
sudo netstat -tulpn | grep LISTEN
```

**Kết quả mong đợi:**
```
tcp 0 0 0.0.0.0:80       0.0.0.0:*  LISTEN  (nginx)
tcp 0 0 0.0.0.0:8000     0.0.0.0:*  LISTEN  (uvicorn)
tcp 0 0 127.0.0.1:5555   0.0.0.0:*  LISTEN  (flower)
tcp 0 0 127.0.0.1:5432   0.0.0.0:*  LISTEN  (postgres)
tcp 0 0 127.0.0.1:6379   0.0.0.0:*  LISTEN  (redis)
```

### Bước 11.3: Test API từ VPS

```bash
# Test root endpoint
curl http://localhost:8000/

# Test API endpoint
curl http://localhost:8000/api/v1/scans

# Test từ bên ngoài (từ máy Windows)
# curl http://124.197.22.184/api/v1/scans
```

### Bước 11.4: Cấu hình Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (QUAN TRỌNG - làm trước khi enable UFW)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (nếu cần SSL sau này)
sudo ufw allow 443/tcp

# Kiểm tra status
sudo ufw status
```

### Bước 11.5: Truy cập từ browser

Mở browser và truy cập:

- **Dashboard:** http://124.197.22.184/
- **API Docs:** http://124.197.22.184/docs
- **Flower Monitoring:** http://124.197.22.184/flower/

---

## 12. TROUBLESHOOTING

### Lỗi: Service không start

```bash
# Xem logs chi tiết
sudo journalctl -u recon-api -n 50 --no-pager
sudo journalctl -u recon-celery -n 50 --no-pager

# Kiểm tra file config
sudo systemctl cat recon-api
```

### Lỗi: Database connection failed

```bash
# Kiểm tra PostgreSQL đang chạy
sudo systemctl status postgresql

# Test kết nối
psql -U recon_user -d recon_db -h localhost
# Nhập password

# Kiểm tra pg_hba.conf
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#"
```

### Lỗi: Redis connection failed

```bash
# Kiểm tra Redis
sudo systemctl status redis
redis-cli ping

# Kiểm tra config
sudo cat /etc/redis/redis.conf | grep -v "^#" | grep -v "^$"
```

### Lỗi: CLI tools not found

```bash
# Kiểm tra PATH
echo $PATH

# Kiểm tra Go tools
ls -la ~/go/bin/

# Thêm vào PATH nếu cần
export PATH=$PATH:$HOME/go/bin
```

### Lỗi: Permission denied

```bash
# Đảm bảo ownership đúng
sudo chown -R recon:recon /home/recon/recon-api

# Đảm bảo permissions
chmod -R 755 /home/recon/recon-api
chmod 755 /home/recon/recon-api/jobs
```

---

## 13. BẢO MẬT (SECURITY)

### Bước 13.1: Đổi password PostgreSQL

```bash
sudo -u postgres psql
ALTER USER recon_user WITH PASSWORD 'new_strong_password';
\q

# Cập nhật lại .env file
vim /home/recon/recon-api/.env
# Sửa DATABASE_URL với password mới
```

### Bước 13.2: Cấu hình SSL/HTTPS (Optional nhưng recommended)

```bash
# Cài đặt Certbot
sudo apt install -y certbot python3-certbot-nginx

# Lấy SSL certificate (cần domain name)
# sudo certbot --nginx -d yourdomain.com
```

### Bước 13.3: Giới hạn rate limiting (Optional)

Thêm vào Nginx config:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    ...
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        ...
    }
}
```

---

## 14. BACKUP VÀ MAINTENANCE

### Backup Database

```bash
# Tạo script backup
vim /home/recon/backup_db.sh
```

**Nội dung:**

```bash
#!/bin/bash
BACKUP_DIR="/home/recon/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U recon_user -h localhost recon_db > $BACKUP_DIR/recon_db_$DATE.sql

# Xóa backup cũ hơn 7 ngày
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/recon_db_$DATE.sql"
```

```bash
# Cho phép execute
chmod +x /home/recon/backup_db.sh

# Thêm vào crontab (chạy hàng ngày lúc 2AM)
crontab -e
# Thêm dòng:
0 2 * * * /home/recon/backup_db.sh
```

---

## 15. MONITORING VÀ LOGS

### Xem logs real-time

```bash
# API logs
sudo journalctl -u recon-api -f

# Celery logs
sudo journalctl -u recon-celery -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Cài đặt htop để monitor resources

```bash
sudo apt install -y htop
htop
```

---

## 🎉 HOÀN TẤT!

Hệ thống của bạn đã được deploy thành công lên VPS!

**Các URL quan trọng:**
- Dashboard: http://124.197.22.184/
- API Docs: http://124.197.22.184/docs
- Flower: http://124.197.22.184/flower/

**Các lệnh hữu ích:**

```bash
# Restart tất cả services
sudo systemctl restart recon-api recon-celery recon-flower nginx

# Xem logs
sudo journalctl -u recon-api -f

# Kiểm tra status
sudo systemctl status recon-api recon-celery

# Update code
cd /home/recon/recon-api
git pull
sudo systemctl restart recon-api recon-celery
```


