# ⚡ QUICK DEPLOY - HƯỚNG DẪN NHANH

Deploy hệ thống reconnaissance lên VPS **124.197.22.184** trong 15 phút!

---

## 🎯 CHUẨN BỊ

### Trên máy Windows:
- ✅ OpenSSH client (đã có sẵn trên Windows 10/11)
- ✅ PowerShell
- ✅ Code đã được chuẩn bị trong `C:\recon-api`

### Trên VPS (124.197.22.184):
- ✅ Ubuntu/Debian Linux
- ✅ Root access
- ✅ Kết nối internet

---

## 🚀 BƯỚC 1: UPLOAD CODE (Từ Windows)

```powershell
# Mở PowerShell trong thư mục C:\recon-api
cd C:\recon-api

# Chạy script upload
.\upload_to_vps.ps1
```

**Lưu ý:** Nếu chưa setup SSH key, bạn sẽ cần nhập password root.

---

## 🔧 BƯỚC 2: CÀI ĐẶT TRÊN VPS

### 2.1: SSH vào VPS

```bash
ssh root@124.197.22.184
```

### 2.2: Chạy script cài đặt tự động

```bash
# Chuyển đến thư mục project
cd /home/recon/recon-api

# Cài đặt dependencies cơ bản
apt update && apt upgrade -y
apt install -y python3.13 python3.13-venv python3.13-dev postgresql redis-server nginx git curl wget

# Cài đặt Go (KHUYẾN NGHỊ: Dùng snap)
# Phương án 1: Snap (Đơn giản nhất)
sudo snap install go --classic

# Phương án 2: Script tự động (nếu muốn chọn phương án)
# chmod +x install_go.sh
# ./install_go.sh

# Phương án 3: Manual (xem GO_INSTALLATION_EXPLAINED.md)
# cd /tmp
# wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
# sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
# echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc
# source ~/.bashrc

# Cài đặt CLI tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/owasp-amass/amass/v4/...@master
go install github.com/tomnomnom/assetfinder@latest
go install github.com/tomnomnom/httprobe@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/tomnomnom/anew@latest
go install github.com/sensepost/gowitness@latest
pip3 install wafw00f

# Quay lại thư mục project
cd /home/recon/recon-api

# Chạy deployment script
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

---

## 🗄️ BƯỚC 3: CẤU HÌNH DATABASE

```bash
# Tạo database và user
sudo -u postgres psql << EOF
CREATE DATABASE recon_db;
CREATE USER recon_user WITH PASSWORD 'YourStrongPassword123!';
GRANT ALL PRIVILEGES ON DATABASE recon_db TO recon_user;
\q
EOF

# Cập nhật file .env
vim .env
# Sửa dòng DATABASE_URL với password vừa tạo
```

---

## ⚙️ BƯỚC 4: CẤU HÌNH SERVICES

```bash
# Copy systemd service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable và start services
sudo systemctl enable recon-api recon-celery recon-flower
sudo systemctl start recon-api recon-celery recon-flower

# Kiểm tra status
sudo systemctl status recon-api
sudo systemctl status recon-celery
```

---

## 🌐 BƯỚC 5: CẤU HÌNH NGINX

```bash
# Copy Nginx config
sudo cp nginx/recon-api /etc/nginx/sites-available/

# Enable site
sudo ln -s /etc/nginx/sites-available/recon-api /etc/nginx/sites-enabled/

# Xóa default site
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔥 BƯỚC 6: CẤU HÌNH FIREWALL

```bash
# Enable UFW
sudo ufw enable

# Allow ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS (cho sau này)

# Kiểm tra
sudo ufw status
```

---

## ✅ BƯỚC 7: KIỂM TRA

### Kiểm tra services đang chạy:

```bash
sudo systemctl status recon-api
sudo systemctl status recon-celery
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### Kiểm tra ports:

```bash
sudo netstat -tulpn | grep LISTEN
```

Kết quả mong đợi:
```
tcp 0 0 0.0.0.0:80       0.0.0.0:*  LISTEN  (nginx)
tcp 0 0 0.0.0.0:8000     0.0.0.0:*  LISTEN  (uvicorn)
tcp 0 0 127.0.0.1:5555   0.0.0.0:*  LISTEN  (flower)
tcp 0 0 127.0.0.1:5432   0.0.0.0:*  LISTEN  (postgres)
tcp 0 0 127.0.0.1:6379   0.0.0.0:*  LISTEN  (redis)
```

### Test API:

```bash
# Từ VPS
curl http://localhost:8000/api/v1/scans

# Từ máy Windows
curl http://124.197.22.184/api/v1/scans
```

---

## 🎉 HOÀN TẤT!

Truy cập các URL sau:

- **Dashboard:** http://124.197.22.184/
- **API Docs:** http://124.197.22.184/docs
- **Flower Monitoring:** http://124.197.22.184/flower/ (admin/admin123)

---

## 🔧 TROUBLESHOOTING

### Service không start?

```bash
# Xem logs
sudo journalctl -u recon-api -n 50
sudo journalctl -u recon-celery -n 50

# Restart services
sudo systemctl restart recon-api recon-celery
```

### Database connection error?

```bash
# Kiểm tra PostgreSQL
sudo systemctl status postgresql

# Test connection
psql -U recon_user -d recon_db -h localhost
```

### Nginx error?

```bash
# Kiểm tra config
sudo nginx -t

# Xem logs
sudo tail -f /var/log/nginx/error.log
```

---

## 📚 TÀI LIỆU CHI TIẾT

Xem hướng dẫn đầy đủ trong:
- **VPS_DEPLOYMENT_GUIDE.md** - Hướng dẫn chi tiết từng bước
- **COMPREHENSIVE_CODEBASE_ANALYSIS.md** - Phân tích toàn bộ codebase

---

## 🆘 HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:

1. **Logs:** `sudo journalctl -u recon-api -f`
2. **Database:** `sudo -u postgres psql -d recon_db`
3. **Redis:** `redis-cli ping`
4. **Permissions:** `ls -la /home/recon/recon-api`

---

**Chúc mừng bạn đã deploy thành công! 🚀**

