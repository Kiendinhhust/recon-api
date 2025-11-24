# 🚀 CI/CD SETUP GUIDE - GitHub Actions to VPS

## 📋 **OVERVIEW**

This guide will help you set up automated deployment from GitHub to your VPS (124.197.22.184) using GitHub Actions.

**What it does:**
- ✅ Automatically deploys when you push to `main` branch
- ✅ Creates backup before deployment
- ✅ Updates dependencies if requirements.txt changed
- ✅ Runs database migrations
- ✅ Restarts services with zero-downtime
- ✅ Verifies deployment success
- ✅ Automatic rollback on failure

---

## 🔧 **PREREQUISITES**

- ✅ GitHub repository with recon-api code
- ✅ VPS (124.197.22.184) with SSH access
- ✅ Application deployed at `/home/recon/recon-api`
- ✅ Systemd services: `recon-api`, `recon-celery`

---

## 📝 **SETUP STEPS**

### **STEP 1: Generate SSH Key for GitHub Actions**

On your **VPS** (as `recon` user):

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Generate SSH key (no passphrase)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# This creates:
# - Private key: ~/.ssh/github_actions_deploy
# - Public key: ~/.ssh/github_actions_deploy.pub
```

---

### **STEP 2: Add Public Key to Authorized Keys**

Still on **VPS**:

```bash
# Add public key to authorized_keys
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Verify
cat ~/.ssh/authorized_keys | grep "github-actions-deploy"
```

---

### **STEP 3: Get SSH Known Hosts**

Still on **VPS**:

```bash
# Get the SSH host key
ssh-keyscan -H 124.197.22.184 > /tmp/known_hosts

# Display it (you'll need this for GitHub Secrets)
cat /tmp/known_hosts
```

**Save this output!** You'll need it for GitHub Secrets.

---

### **STEP 4: Get Private Key**

Still on **VPS**:

```bash
# Display private key (you'll need this for GitHub Secrets)
cat ~/.ssh/github_actions_deploy
```

**Copy the ENTIRE output** (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

**⚠️ IMPORTANT:** Keep this private key secure! Never commit it to git!

---

### **STEP 5: Add GitHub Secrets**

On **GitHub** (your repository):

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Add these 2 secrets:**

#### **Secret 1: VPS_SSH_PRIVATE_KEY**

- **Name:** `VPS_SSH_PRIVATE_KEY`
- **Value:** Paste the entire private key from Step 4
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
  ... (entire key content) ...
  -----END OPENSSH PRIVATE KEY-----
  ```

#### **Secret 2: VPS_SSH_KNOWN_HOSTS**

- **Name:** `VPS_SSH_KNOWN_HOSTS`
- **Value:** Paste the output from Step 3
  ```
  |1|abc123...= ecdsa-sha2-nistp256 AAAAE2VjZHNh...
  ```

---

### **STEP 6: Upload Deployment Scripts to VPS**

From your **Windows machine** (in `C:\recon-api`):

```powershell
# Upload deployment scripts
scp scripts/deploy.sh recon@124.197.22.184:/home/recon/recon-api/scripts/
scp scripts/rollback.sh recon@124.197.22.184:/home/recon/recon-api/scripts/

# SSH to VPS and make executable
ssh recon@124.197.22.184
cd ~/recon-api/scripts
chmod +x deploy.sh rollback.sh
```

---

### **STEP 7: Create Backup Directory**

On **VPS**:

```bash
# Create backup directory
mkdir -p /home/recon/backups
chmod 755 /home/recon/backups
```

---

### **STEP 8: Configure Sudo for Service Restart**

On **VPS** (as root or with sudo):

```bash
# Edit sudoers file
sudo visudo

# Add this line at the end (allows recon user to restart services without password):
recon ALL=(ALL) NOPASSWD: /bin/systemctl restart recon-api, /bin/systemctl restart recon-celery, /bin/systemctl status recon-api, /bin/systemctl status recon-celery, /bin/systemctl is-active recon-api, /bin/systemctl is-active recon-celery

# Save and exit (Ctrl+X, then Y, then Enter)
```

**Test it:**
```bash
# As recon user
sudo systemctl status recon-api
# Should work without asking for password
```

---

### **STEP 9: Commit and Push GitHub Actions Workflow**

From your **Windows machine** (in `C:\recon-api`):

```bash
# Add workflow file
git add .github/workflows/deploy.yml

# Add deployment scripts
git add scripts/deploy.sh scripts/rollback.sh

# Commit
git commit -m "Add CI/CD pipeline with GitHub Actions"

# Push to GitHub
git push origin main
```

---

### **STEP 10: Verify GitHub Actions Workflow**

On **GitHub**:

1. Go to your repository
2. Click **Actions** tab
3. You should see a workflow run for "Deploy to VPS"
4. Click on it to see the progress

**Expected output:**
```
✓ Checkout code
✓ Setup SSH
✓ Create backup on VPS
✓ Pull latest code on VPS
✓ Check for dependency changes
✓ Update Python dependencies (if needed)
✓ Run database migrations
✓ Restart services
✓ Verify deployment
✓ Cleanup
```

---

## 🧪 **TESTING THE CI/CD PIPELINE**

### **Test 1: Make a Small Change**

```bash
# On Windows (in C:\recon-api)

# Make a small change (e.g., add a comment)
echo "# CI/CD test" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main
```

**Watch GitHub Actions:**
- Go to **Actions** tab on GitHub
- Watch the deployment progress
- Should complete in ~2-3 minutes

---

### **Test 2: Verify Deployment on VPS**

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Check services
sudo systemctl status recon-api recon-celery

# Check API
curl http://localhost:8000/api/v1/health

# Check latest commit
cd ~/recon-api
git log -1
```

---

### **Test 3: Test Rollback**

```bash
# SSH to VPS
ssh recon@124.197.22.184

# List backups
ls -lt /home/recon/backups

# Rollback to previous version
cd ~/recon-api/scripts
./rollback.sh

# Follow prompts to confirm rollback
```

---

## 🔍 **MONITORING DEPLOYMENTS**

### **View GitHub Actions Logs**

1. Go to **Actions** tab on GitHub
2. Click on the workflow run
3. Click on "Deploy to Production VPS" job
4. Expand each step to see detailed logs

---

### **View VPS Logs**

```bash
# SSH to VPS
ssh recon@124.197.22.184

# View service logs
sudo journalctl -u recon-api -n 50
sudo journalctl -u recon-celery -n 50

# View deployment logs (if using systemd)
sudo journalctl -u recon-api --since "10 minutes ago"
```

---

## 🐛 **TROUBLESHOOTING**

### **Issue: SSH Connection Failed**

**Error:** `Permission denied (publickey)`

**Fix:**
```bash
# On VPS, check authorized_keys
cat ~/.ssh/authorized_keys | grep "github-actions-deploy"

# Check permissions
ls -la ~/.ssh/
# Should be: drwx------ (700) for .ssh
# Should be: -rw------- (600) for authorized_keys

# Fix permissions if needed
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

### **Issue: Service Restart Failed**

**Error:** `sudo: a password is required`

**Fix:**
```bash
# On VPS, edit sudoers
sudo visudo

# Make sure this line exists:
recon ALL=(ALL) NOPASSWD: /bin/systemctl restart recon-api, /bin/systemctl restart recon-celery, /bin/systemctl status recon-api, /bin/systemctl status recon-celery, /bin/systemctl is-active recon-api, /bin/systemctl is-active recon-celery
```

---

### **Issue: Deployment Verification Failed**

**Error:** `API health check failed (HTTP 000)`

**Fix:**
```bash
# On VPS, check service status
sudo systemctl status recon-api

# Check logs
sudo journalctl -u recon-api -n 50

# Check if port is listening
sudo netstat -tlnp | grep 8000

# Manually restart
sudo systemctl restart recon-api
```

---

### **Issue: Git Pull Failed**

**Error:** `error: Your local changes to the following files would be overwritten by merge`

**Fix:**
```bash
# On VPS
cd ~/recon-api

# Stash local changes
git stash

# Or reset to remote
git reset --hard origin/main
```

---

## 📊 **DEPLOYMENT WORKFLOW DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────┐
│  DEVELOPER                                                      │
│  ├─ Make code changes                                          │
│  ├─ git commit -m "Update feature"                             │
│  └─ git push origin main                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS (Automated)                                     │
│  ├─ Checkout code                                              │
│  ├─ Setup SSH connection to VPS                                │
│  ├─ Create backup on VPS                                       │
│  ├─ Pull latest code from GitHub                               │
│  ├─ Check if requirements.txt changed                          │
│  ├─ Update dependencies (if needed)                            │
│  ├─ Run database migrations                                    │
│  ├─ Restart services (Celery → API)                            │
│  ├─ Verify deployment (health check)                           │
│  └─ Rollback if failed                                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  VPS (124.197.22.184)                                           │
│  ├─ /home/recon/recon-api (updated code)                       │
│  ├─ /home/recon/backups (backup created)                       │
│  ├─ recon-api service (restarted)                              │
│  ├─ recon-celery service (restarted)                           │
│  └─ API responding at :8000                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 **BEST PRACTICES**

1. **Always test locally first** before pushing to main
2. **Use feature branches** for development, merge to main when ready
3. **Monitor GitHub Actions** after each push
4. **Check VPS logs** if deployment fails
5. **Keep backups** - automatic cleanup keeps last 5
6. **Test rollback** procedure periodically
7. **Update secrets** if SSH keys change

---

## 📝 **MANUAL DEPLOYMENT (Alternative)**

If you need to deploy manually without GitHub Actions:

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Run deployment script
cd ~/recon-api/scripts
./deploy.sh

# Or with options
./deploy.sh --skip-backup
./deploy.sh --skip-deps
./deploy.sh --skip-migrations
```

---

## 🔄 **ROLLBACK PROCEDURE**

If deployment fails or causes issues:

```bash
# SSH to VPS
ssh recon@124.197.22.184

# Run rollback script
cd ~/recon-api/scripts
./rollback.sh

# Or specify backup
./rollback.sh recon-api_20241124_153000
```

---

**Setup Complete! 🎉**

Your CI/CD pipeline is now ready. Every push to `main` will automatically deploy to your VPS!

