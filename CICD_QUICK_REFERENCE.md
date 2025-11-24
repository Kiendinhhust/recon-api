# 🚀 CI/CD QUICK REFERENCE

## 📋 **QUICK SETUP CHECKLIST**

```
□ Generate SSH key on VPS
□ Add public key to authorized_keys
□ Get SSH known_hosts
□ Add VPS_SSH_PRIVATE_KEY to GitHub Secrets
□ Add VPS_SSH_KNOWN_HOSTS to GitHub Secrets
□ Upload deployment scripts to VPS
□ Configure sudoers for service restart
□ Create backup directory
□ Push workflow to GitHub
□ Test deployment
```

---

## 🔑 **GITHUB SECRETS REQUIRED**

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `VPS_SSH_PRIVATE_KEY` | SSH private key for VPS access | `cat ~/.ssh/github_actions_deploy` |
| `VPS_SSH_KNOWN_HOSTS` | SSH host key fingerprint | `ssh-keyscan -H 124.197.22.184` |

---

## 📁 **FILES CREATED**

| File | Purpose | Location |
|------|---------|----------|
| `.github/workflows/deploy.yml` | GitHub Actions workflow | Repository root |
| `scripts/deploy.sh` | Deployment script | VPS: `/home/recon/recon-api/scripts/` |
| `scripts/rollback.sh` | Rollback script | VPS: `/home/recon/recon-api/scripts/` |
| `scripts/test_deployment.sh` | Pre-deployment test | VPS: `/home/recon/recon-api/scripts/` |

---

## 🎯 **COMMON COMMANDS**

### **On Windows (Local Development)**

```bash
# Make changes
git add .
git commit -m "Your commit message"
git push origin main

# Watch deployment on GitHub
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

---

### **On VPS (Manual Operations)**

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Test deployment readiness
cd ~/recon-api/scripts
./test_deployment.sh

# Manual deployment
./deploy.sh

# Manual deployment (skip backup)
./deploy.sh --skip-backup

# Manual deployment (skip dependencies)
./deploy.sh --skip-deps

# Rollback to previous version
./rollback.sh

# Rollback to specific backup
./rollback.sh recon-api_20241124_153000

# List backups
ls -lt /home/recon/backups

# Check service status
sudo systemctl status recon-api recon-celery

# View logs
sudo journalctl -u recon-api -n 50
sudo journalctl -u recon-celery -n 50

# Restart services manually
sudo systemctl restart recon-celery
sudo systemctl restart recon-api

# Check API health
curl http://localhost:8000/api/v1/health
```

---

## 🔍 **MONITORING DEPLOYMENTS**

### **GitHub Actions**

```
1. Go to repository on GitHub
2. Click "Actions" tab
3. Click on latest workflow run
4. Click "Deploy to Production VPS"
5. Expand steps to see logs
```

---

### **VPS Logs**

```bash
# Real-time logs
sudo journalctl -u recon-api -f

# Last 100 lines
sudo journalctl -u recon-api -n 100

# Logs from last hour
sudo journalctl -u recon-api --since "1 hour ago"

# Logs with errors
sudo journalctl -u recon-api | grep -i "error\|failed"
```

---

## 🐛 **TROUBLESHOOTING**

### **Deployment Failed**

```bash
# Check GitHub Actions logs first
# Then SSH to VPS and check:

# Service status
sudo systemctl status recon-api recon-celery

# Recent logs
sudo journalctl -u recon-api -n 50

# API health
curl http://localhost:8000/api/v1/health

# If needed, rollback
cd ~/recon-api/scripts
./rollback.sh
```

---

### **SSH Connection Failed**

```bash
# On VPS, check authorized_keys
cat ~/.ssh/authorized_keys | grep "github-actions-deploy"

# Check permissions
ls -la ~/.ssh/
# Should be: drwx------ (700) for .ssh
# Should be: -rw------- (600) for authorized_keys

# Fix permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

### **Service Won't Restart**

```bash
# Check sudo permissions
sudo -n systemctl status recon-api

# If password required, edit sudoers
sudo visudo

# Add this line:
recon ALL=(ALL) NOPASSWD: /bin/systemctl restart recon-api, /bin/systemctl restart recon-celery, /bin/systemctl status recon-api, /bin/systemctl status recon-celery, /bin/systemctl is-active recon-api, /bin/systemctl is-active recon-celery
```

---

## 📊 **DEPLOYMENT WORKFLOW**

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Developer pushes to main branch                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. GitHub Actions triggered automatically                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Workflow connects to VPS via SSH                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Creates backup of current code                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Pulls latest code from GitHub                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Updates dependencies (if requirements.txt changed)         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Runs database migrations                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. Restarts services (Celery → API)                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. Verifies deployment (health check)                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  10. Success! ✓ (or rollback on failure)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏱️ **TYPICAL DEPLOYMENT TIMELINE**

| Step | Duration |
|------|----------|
| Checkout code | 5-10s |
| Setup SSH | 2-5s |
| Create backup | 5-10s |
| Pull latest code | 5-10s |
| Update dependencies | 30-60s (if changed) |
| Run migrations | 5-10s |
| Restart services | 10-15s |
| Verify deployment | 5-10s |
| **Total** | **1-2 minutes** |

---

## 🎯 **BEST PRACTICES**

1. ✅ **Test locally** before pushing to main
2. ✅ **Use feature branches** for development
3. ✅ **Monitor GitHub Actions** after each push
4. ✅ **Check VPS logs** if deployment fails
5. ✅ **Test rollback** procedure periodically
6. ✅ **Keep backups** (automatic cleanup keeps last 5)
7. ✅ **Review deployment logs** regularly

---

## 📞 **EMERGENCY PROCEDURES**

### **If Deployment Breaks Production**

```bash
# 1. SSH to VPS immediately
ssh recon@124.197.22.184

# 2. Rollback to previous version
cd ~/recon-api/scripts
./rollback.sh

# 3. Verify services are running
sudo systemctl status recon-api recon-celery

# 4. Check API health
curl http://localhost:8000/api/v1/health

# 5. Investigate what went wrong
sudo journalctl -u recon-api -n 100
```

---

### **If Services Won't Start After Rollback**

```bash
# 1. Check logs for errors
sudo journalctl -u recon-api -n 50
sudo journalctl -u recon-celery -n 50

# 2. Try manual restart
sudo systemctl restart recon-celery
sudo systemctl restart recon-api

# 3. Check if ports are in use
sudo netstat -tlnp | grep 8000
sudo netstat -tlnp | grep 6379

# 4. If needed, kill processes and restart
sudo pkill -f "uvicorn"
sudo pkill -f "celery"
sudo systemctl restart recon-celery
sudo systemctl restart recon-api
```

---

## 📝 **USEFUL LINKS**

- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **GitHub Secrets:** https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **SSH Key Generation:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

**Quick Reference Complete! 🎉**

