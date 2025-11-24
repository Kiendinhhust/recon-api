#!/bin/bash

# ============================================================================
# DEPLOYMENT SCRIPT FOR RECON-API
# ============================================================================
# Purpose: Deploy recon-api application on VPS
# Usage: ./deploy.sh [--skip-backup] [--skip-deps] [--skip-migrations]
# ============================================================================

set -e  # Exit on error

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
VENV_PATH="${APP_PATH}/venv"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
SKIP_BACKUP=false
SKIP_DEPS=false
SKIP_MIGRATIONS=false

for arg in "$@"; do
    case $arg in
        --skip-backup)
            SKIP_BACKUP=true
            ;;
        --skip-deps)
            SKIP_DEPS=true
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            ;;
    esac
done

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
# STEP 1: PRE-DEPLOYMENT CHECKS
# ============================================================================

print_header "STEP 1: PRE-DEPLOYMENT CHECKS"

# Check if running as recon user
if [ "$(whoami)" != "recon" ]; then
    print_error "This script must be run as 'recon' user"
    exit 1
fi

# Check if app directory exists
if [ ! -d "$APP_PATH" ]; then
    print_error "Application directory not found: $APP_PATH"
    exit 1
fi

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found: $VENV_PATH"
    exit 1
fi

print_success "Pre-deployment checks passed"

# ============================================================================
# STEP 2: CREATE BACKUP
# ============================================================================

if [ "$SKIP_BACKUP" = false ]; then
    print_header "STEP 2: CREATE BACKUP"
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_PATH="${BACKUP_DIR}/recon-api_${TIMESTAMP}"
    
    print_info "Creating backup at: $BACKUP_PATH"
    
    # Backup application code (exclude venv, jobs, __pycache__)
    rsync -a --exclude='venv' --exclude='jobs' --exclude='__pycache__' \
        --exclude='*.pyc' --exclude='.git' \
        "$APP_PATH/" "$BACKUP_PATH/"
    
    # Save current git commit hash
    cd "$APP_PATH"
    if [ -d ".git" ]; then
        git rev-parse HEAD > "$BACKUP_PATH/COMMIT_HASH" 2>/dev/null || echo "unknown" > "$BACKUP_PATH/COMMIT_HASH"
    fi
    
    print_success "Backup created: $BACKUP_PATH"
    
    # Keep only last 5 backups
    cd "$BACKUP_DIR"
    ls -t | tail -n +6 | xargs -r rm -rf
    print_info "Old backups cleaned up (kept last 5)"
else
    print_warning "Skipping backup (--skip-backup flag)"
fi

# ============================================================================
# STEP 3: PULL LATEST CODE
# ============================================================================

print_header "STEP 3: PULL LATEST CODE"

cd "$APP_PATH"

if [ -d ".git" ]; then
    print_info "Pulling latest code from GitHub..."
    
    # Save current commit for comparison
    OLD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    # Pull latest code
    git fetch origin
    git reset --hard origin/main
    
    NEW_COMMIT=$(git rev-parse HEAD)
    
    print_success "Code updated"
    print_info "Old commit: $OLD_COMMIT"
    print_info "New commit: $NEW_COMMIT"
    
    # Check if requirements.txt changed
    if git diff "$OLD_COMMIT" "$NEW_COMMIT" --name-only | grep -q "requirements.txt"; then
        print_warning "requirements.txt changed - dependencies will be updated"
        DEPS_CHANGED=true
    else
        print_info "requirements.txt unchanged"
        DEPS_CHANGED=false
    fi
else
    print_warning "Not a git repository - skipping git pull"
    DEPS_CHANGED=false
fi

# ============================================================================
# STEP 4: UPDATE DEPENDENCIES
# ============================================================================

if [ "$SKIP_DEPS" = false ] && [ "$DEPS_CHANGED" = true ]; then
    print_header "STEP 4: UPDATE DEPENDENCIES"
    
    print_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    print_info "Updating pip..."
    pip install --upgrade pip --quiet
    
    print_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt --quiet
    
    print_success "Dependencies updated"
elif [ "$SKIP_DEPS" = true ]; then
    print_warning "Skipping dependency update (--skip-deps flag)"
else
    print_info "Skipping dependency update (no changes detected)"
fi

# ============================================================================
# STEP 5: RUN DATABASE MIGRATIONS
# ============================================================================

if [ "$SKIP_MIGRATIONS" = false ]; then
    print_header "STEP 5: RUN DATABASE MIGRATIONS"

    source "$VENV_PATH/bin/activate"

    # Load environment variables from .env file
    if [ -f "${APP_PATH}/.env" ]; then
        print_info "Loading environment variables from .env..."

        # Load .env file line by line to handle special characters properly
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ -n "$line" ]]; then
                # Export the variable
                export "$line"
            fi
        done < "${APP_PATH}/.env"

        # Verify DATABASE_URL is set
        if [ -n "$DATABASE_URL" ]; then
            MASKED_URL=$(echo "$DATABASE_URL" | sed 's/:[^:@]*@/:***@/')
            print_success "DATABASE_URL loaded: $MASKED_URL"
        else
            print_error "DATABASE_URL not found in .env file"
            exit 1
        fi
    else
        print_error ".env file not found at ${APP_PATH}/.env"
        print_warning "Please create .env file with DATABASE_URL before deploying"
        exit 1
    fi

    print_info "Checking for pending migrations..."

    # Run migrations
    alembic upgrade head

    print_success "Database migrations completed"
else
    print_warning "Skipping database migrations (--skip-migrations flag)"
fi

# ============================================================================
# STEP 6: RESTART SERVICES
# ============================================================================

print_header "STEP 6: RESTART SERVICES"

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
# STEP 7: VERIFY DEPLOYMENT
# ============================================================================

print_header "STEP 7: VERIFY DEPLOYMENT"

print_info "Waiting for API to be ready..."
sleep 5

# Check API is responding (using /docs endpoint)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API is responding (HTTP $HTTP_CODE on /docs)"
else
    print_error "API is not responding (HTTP $HTTP_CODE on /docs)"
    print_error "Deployment verification failed!"
    exit 1
fi

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

print_header "DEPLOYMENT COMPLETE"

print_success "Deployment completed successfully!"
print_info "Timestamp: $TIMESTAMP"
print_info "Backup: $BACKUP_PATH"
print_info "Commit: $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
echo ""
print_info "Services status:"
systemctl status recon-api --no-pager -l | head -5
systemctl status recon-celery --no-pager -l | head -5
echo ""
print_info "Access dashboard: http://124.197.22.184:8000"

