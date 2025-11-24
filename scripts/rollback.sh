#!/bin/bash

# ============================================================================
# ROLLBACK SCRIPT FOR RECON-API
# ============================================================================
# Purpose: Rollback to previous deployment
# Usage: ./rollback.sh [backup_name]
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
APP_PATH="/home/recon/recon-api"
BACKUP_DIR="/home/recon/backups"

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# ============================================================================
# STEP 1: SELECT BACKUP
# ============================================================================

print_header "ROLLBACK TO PREVIOUS DEPLOYMENT"

if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

cd "$BACKUP_DIR"

# List available backups
echo "Available backups:"
echo ""
ls -lt | grep "^d" | awk '{print NR". "$9" ("$6" "$7" "$8")"}'
echo ""

# Select backup
if [ -n "$1" ]; then
    BACKUP_NAME="$1"
    print_info "Using specified backup: $BACKUP_NAME"
else
    # Use most recent backup
    BACKUP_NAME=$(ls -t | head -1)
    print_warning "No backup specified, using most recent: $BACKUP_NAME"
    
    echo ""
    read -p "Continue with this backup? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Rollback cancelled"
        exit 0
    fi
fi

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

if [ ! -d "$BACKUP_PATH" ]; then
    print_error "Backup not found: $BACKUP_PATH"
    exit 1
fi

print_success "Selected backup: $BACKUP_PATH"

# Show backup info
if [ -f "$BACKUP_PATH/COMMIT_HASH" ]; then
    BACKUP_COMMIT=$(cat "$BACKUP_PATH/COMMIT_HASH")
    print_info "Backup commit: $BACKUP_COMMIT"
fi

# ============================================================================
# STEP 2: CONFIRM ROLLBACK
# ============================================================================

print_warning "This will restore the application to the selected backup"
print_warning "Current code will be overwritten!"
echo ""
read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Rollback cancelled"
    exit 0
fi

# ============================================================================
# STEP 3: RESTORE CODE
# ============================================================================

print_header "STEP 1: RESTORE CODE"

print_info "Restoring code from backup..."

# Restore code (exclude venv, jobs, __pycache__)
rsync -a --exclude='venv' --exclude='jobs' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' \
    "$BACKUP_PATH/" "$APP_PATH/"

print_success "Code restored from backup"

# ============================================================================
# STEP 4: RESTART SERVICES
# ============================================================================

print_header "STEP 2: RESTART SERVICES"

print_info "Restarting recon-celery service..."
sudo systemctl restart recon-celery
sleep 3

if systemctl is-active --quiet recon-celery; then
    print_success "recon-celery restarted successfully"
else
    print_error "recon-celery failed to start!"
    sudo journalctl -u recon-celery -n 20 --no-pager
    exit 1
fi

print_info "Restarting recon-api service..."
sudo systemctl restart recon-api
sleep 5

if systemctl is-active --quiet recon-api; then
    print_success "recon-api restarted successfully"
else
    print_error "recon-api failed to start!"
    sudo journalctl -u recon-api -n 20 --no-pager
    exit 1
fi

# ============================================================================
# STEP 5: VERIFY ROLLBACK
# ============================================================================

print_header "STEP 3: VERIFY ROLLBACK"

print_info "Waiting for API to be ready..."
sleep 5

# Check API is responding (using /docs endpoint)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API is responding (HTTP $HTTP_CODE on /docs)"
else
    print_error "API is not responding (HTTP $HTTP_CODE on /docs)"
    print_error "Rollback verification failed!"
    exit 1
fi

# ============================================================================
# ROLLBACK COMPLETE
# ============================================================================

print_header "ROLLBACK COMPLETE"

print_success "Rollback completed successfully!"
print_info "Restored from: $BACKUP_PATH"
if [ -f "$BACKUP_PATH/COMMIT_HASH" ]; then
    print_info "Commit: $(cat $BACKUP_PATH/COMMIT_HASH)"
fi
echo ""
print_info "Services status:"
systemctl status recon-api --no-pager -l | head -5
systemctl status recon-celery --no-pager -l | head -5
echo ""
print_warning "Note: Database migrations were NOT rolled back"
print_warning "If needed, manually rollback database using: alembic downgrade <revision>"

