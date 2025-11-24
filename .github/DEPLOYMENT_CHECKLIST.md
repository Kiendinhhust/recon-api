# ✅ CI/CD DEPLOYMENT CHECKLIST

Use this checklist to set up and verify your CI/CD pipeline.

---

## 📋 **INITIAL SETUP (One-time)**

### **Phase 1: Prepare VPS**

- [ ] SSH access to VPS (124.197.22.184) as `recon` user
- [ ] Application deployed at `/home/recon/recon-api`
- [ ] Services running: `recon-api`, `recon-celery`
- [ ] Git repository initialized in `/home/recon/recon-api`
- [ ] Git remote configured (GitHub)

---

### **Phase 2: Upload Scripts**

From Windows (`C:\recon-api`):

```powershell
# Option 1: Automated (Recommended)
.\scripts\setup_cicd.ps1

# Option 2: Manual
scp scripts/deploy.sh recon@124.197.22.184:/home/recon/recon-api/scripts/
scp scripts/rollback.sh recon@124.197.22.184:/home/recon/recon-api/scripts/
scp scripts/test_deployment.sh recon@124.197.22.184:/home/recon/recon-api/scripts/
```

- [ ] Scripts uploaded to VPS
- [ ] Scripts made executable (`chmod +x scripts/*.sh`)

---

### **Phase 3: Generate SSH Keys**

On VPS:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ''
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

- [ ] SSH key generated
- [ ] Public key added to authorized_keys
- [ ] Permissions set correctly

---

### **Phase 4: Get Secrets for GitHub**

On VPS:

```bash
# Get private key
cat ~/.ssh/github_actions_deploy

# Get known_hosts
ssh-keyscan -H 124.197.22.184
```

- [ ] Private key copied (for `VPS_SSH_PRIVATE_KEY`)
- [ ] Known hosts copied (for `VPS_SSH_KNOWN_HOSTS`)

---

### **Phase 5: Configure GitHub Secrets**

On GitHub (Repository → Settings → Secrets and variables → Actions):

- [ ] Added secret: `VPS_SSH_PRIVATE_KEY`
- [ ] Added secret: `VPS_SSH_KNOWN_HOSTS`

---

### **Phase 6: Configure Sudoers**

On VPS:

```bash
sudo visudo
```

Add this line:
```
recon ALL=(ALL) NOPASSWD: /bin/systemctl restart recon-api, /bin/systemctl restart recon-celery, /bin/systemctl status recon-api, /bin/systemctl status recon-celery, /bin/systemctl is-active recon-api, /bin/systemctl is-active recon-celery
```

- [ ] Sudoers configured
- [ ] Tested: `sudo systemctl status recon-api` (no password prompt)

---

### **Phase 7: Create Backup Directory**

On VPS:

```bash
mkdir -p /home/recon/backups
chmod 755 /home/recon/backups
```

- [ ] Backup directory created

---

### **Phase 8: Push Workflow to GitHub**

From Windows:

```bash
git add .github/workflows/deploy.yml
git add scripts/
git add CICD_*.md
git commit -m "Add CI/CD pipeline with GitHub Actions"
git push origin main
```

- [ ] Workflow file committed
- [ ] Pushed to GitHub
- [ ] GitHub Actions workflow visible in Actions tab

---

## 🧪 **TESTING (Before First Real Deployment)**

### **Test 1: Deployment Readiness**

On VPS:

```bash
cd ~/recon-api/scripts
./test_deployment.sh
```

- [ ] All tests passed
- [ ] Services running
- [ ] API health check passed

---

### **Test 2: Manual Deployment**

On VPS:

```bash
cd ~/recon-api/scripts
./deploy.sh --skip-backup
```

- [ ] Deployment completed successfully
- [ ] Services restarted
- [ ] API responding

---

### **Test 3: Rollback**

On VPS:

```bash
cd ~/recon-api/scripts
./rollback.sh
```

- [ ] Rollback completed successfully
- [ ] Services restarted
- [ ] API responding

---

### **Test 4: GitHub Actions Deployment**

From Windows:

```bash
# Make a small change
echo "# CI/CD test" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main
```

On GitHub:
- [ ] Workflow triggered automatically
- [ ] All steps completed successfully
- [ ] Deployment verified

On VPS:
- [ ] Latest code deployed
- [ ] Services running
- [ ] API responding

---

## 🔄 **REGULAR DEPLOYMENT WORKFLOW**

### **Before Pushing:**

- [ ] Code tested locally
- [ ] All tests passing
- [ ] No uncommitted changes
- [ ] Requirements.txt updated (if dependencies changed)

---

### **Push to GitHub:**

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

- [ ] Code pushed to GitHub

---

### **Monitor Deployment:**

On GitHub (Actions tab):
- [ ] Workflow started
- [ ] All steps green
- [ ] Deployment completed

---

### **Verify on VPS:**

```bash
# Check services
sudo systemctl status recon-api recon-celery

# Check API
curl http://localhost:8000/api/v1/health

# Check logs
sudo journalctl -u recon-api -n 20
```

- [ ] Services running
- [ ] API responding
- [ ] No errors in logs

---

## 🐛 **TROUBLESHOOTING CHECKLIST**

### **If Deployment Fails:**

- [ ] Check GitHub Actions logs
- [ ] SSH to VPS and check service status
- [ ] Check VPS logs: `sudo journalctl -u recon-api -n 50`
- [ ] Verify API health: `curl http://localhost:8000/api/v1/health`
- [ ] If needed, rollback: `./scripts/rollback.sh`

---

### **If SSH Connection Fails:**

- [ ] Check authorized_keys: `cat ~/.ssh/authorized_keys | grep github-actions`
- [ ] Check permissions: `ls -la ~/.ssh/`
- [ ] Verify GitHub secrets are correct
- [ ] Test SSH manually: `ssh -i ~/.ssh/github_actions_deploy recon@124.197.22.184`

---

### **If Services Won't Restart:**

- [ ] Check sudo permissions: `sudo -n systemctl status recon-api`
- [ ] Check sudoers file: `sudo visudo`
- [ ] Check service files: `systemctl cat recon-api`
- [ ] Check logs: `sudo journalctl -u recon-api -n 50`

---

## 📊 **MAINTENANCE CHECKLIST**

### **Weekly:**

- [ ] Review deployment logs on GitHub Actions
- [ ] Check VPS disk space: `df -h`
- [ ] Check backup count: `ls -lt /home/recon/backups | wc -l`
- [ ] Verify services running: `sudo systemctl status recon-api recon-celery`

---

### **Monthly:**

- [ ] Test rollback procedure
- [ ] Review and clean old backups (automatic, but verify)
- [ ] Update dependencies if needed
- [ ] Review GitHub Actions usage

---

## 🎯 **SUCCESS CRITERIA**

Your CI/CD pipeline is working correctly if:

- ✅ Push to main triggers automatic deployment
- ✅ Deployment completes in 1-2 minutes
- ✅ Services restart without errors
- ✅ API health check passes
- ✅ Backup created before deployment
- ✅ Automatic rollback on failure
- ✅ No manual SSH required

---

## 📞 **EMERGENCY CONTACTS**

If something goes wrong:

1. **Check GitHub Actions logs** (most detailed)
2. **Check VPS logs:** `sudo journalctl -u recon-api -n 100`
3. **Rollback immediately:** `./scripts/rollback.sh`
4. **Verify services:** `sudo systemctl status recon-api recon-celery`
5. **Check API:** `curl http://localhost:8000/api/v1/health`

---

**Checklist Complete! 🎉**

Your CI/CD pipeline is ready for production use!

