#!/bin/bash

# ============================================================================
# DEPLOYMENT TEST SCRIPT
# ============================================================================
# Purpose: Test deployment without actually deploying
# Usage: ./test_deployment.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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

PASS_COUNT=0
FAIL_COUNT=0

# ============================================================================
# TEST 1: CHECK USER
# ============================================================================

print_header "TEST 1: CHECK USER"

if [ "$(whoami)" = "recon" ]; then
    print_success "Running as 'recon' user"
    ((PASS_COUNT++))
else
    print_error "Not running as 'recon' user (current: $(whoami))"
    ((FAIL_COUNT++))
fi

# ============================================================================
# TEST 2: CHECK DIRECTORIES
# ============================================================================

print_header "TEST 2: CHECK DIRECTORIES"

if [ -d "/home/recon/recon-api" ]; then
    print_success "Application directory exists"
    ((PASS_COUNT++))
else
    print_error "Application directory not found"
    ((FAIL_COUNT++))
fi

if [ -d "/home/recon/recon-api/venv" ]; then
    print_success "Virtual environment exists"
    ((PASS_COUNT++))
else
    print_error "Virtual environment not found"
    ((FAIL_COUNT++))
fi

if [ -d "/home/recon/backups" ]; then
    print_success "Backup directory exists"
    ((PASS_COUNT++))
else
    print_warning "Backup directory not found (will be created)"
fi

# ============================================================================
# TEST 3: CHECK GIT REPOSITORY
# ============================================================================

print_header "TEST 3: CHECK GIT REPOSITORY"

cd /home/recon/recon-api

if [ -d ".git" ]; then
    print_success "Git repository initialized"
    ((PASS_COUNT++))
    
    # Check remote
    REMOTE=$(git remote -v | grep origin | head -1 | awk '{print $2}')
    if [ -n "$REMOTE" ]; then
        print_success "Git remote configured: $REMOTE"
        ((PASS_COUNT++))
    else
        print_error "Git remote not configured"
        ((FAIL_COUNT++))
    fi
    
    # Check current branch
    BRANCH=$(git branch --show-current)
    print_info "Current branch: $BRANCH"
    
    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        print_success "No uncommitted changes"
        ((PASS_COUNT++))
    else
        print_warning "Uncommitted changes detected"
    fi
else
    print_error "Not a git repository"
    ((FAIL_COUNT++))
fi

# ============================================================================
# TEST 4: CHECK SERVICES
# ============================================================================

print_header "TEST 4: CHECK SERVICES"

if systemctl list-unit-files | grep -q "recon-api.service"; then
    print_success "recon-api service exists"
    ((PASS_COUNT++))
    
    if systemctl is-active --quiet recon-api; then
        print_success "recon-api service is running"
        ((PASS_COUNT++))
    else
        print_error "recon-api service is not running"
        ((FAIL_COUNT++))
    fi
else
    print_error "recon-api service not found"
    ((FAIL_COUNT++))
fi

if systemctl list-unit-files | grep -q "recon-celery.service"; then
    print_success "recon-celery service exists"
    ((PASS_COUNT++))
    
    if systemctl is-active --quiet recon-celery; then
        print_success "recon-celery service is running"
        ((PASS_COUNT++))
    else
        print_error "recon-celery service is not running"
        ((FAIL_COUNT++))
    fi
else
    print_error "recon-celery service not found"
    ((FAIL_COUNT++))
fi

# ============================================================================
# TEST 5: CHECK SUDO PERMISSIONS
# ============================================================================

print_header "TEST 5: CHECK SUDO PERMISSIONS"

if sudo -n systemctl status recon-api &>/dev/null; then
    print_success "Can run 'systemctl status recon-api' without password"
    ((PASS_COUNT++))
else
    print_error "Cannot run systemctl without password (check sudoers)"
    ((FAIL_COUNT++))
fi

if sudo -n systemctl restart recon-api --dry-run &>/dev/null; then
    print_success "Can run 'systemctl restart recon-api' without password"
    ((PASS_COUNT++))
else
    print_error "Cannot restart services without password (check sudoers)"
    ((FAIL_COUNT++))
fi

# ============================================================================
# TEST 6: CHECK API HEALTH
# ============================================================================

print_header "TEST 6: CHECK API HEALTH"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API health check passed (HTTP $HTTP_CODE)"
    ((PASS_COUNT++))
else
    print_error "API health check failed (HTTP $HTTP_CODE)"
    ((FAIL_COUNT++))
fi

# ============================================================================
# TEST 7: CHECK DEPLOYMENT SCRIPTS
# ============================================================================

print_header "TEST 7: CHECK DEPLOYMENT SCRIPTS"

if [ -f "/home/recon/recon-api/scripts/deploy.sh" ]; then
    print_success "deploy.sh exists"
    ((PASS_COUNT++))
    
    if [ -x "/home/recon/recon-api/scripts/deploy.sh" ]; then
        print_success "deploy.sh is executable"
        ((PASS_COUNT++))
    else
        print_warning "deploy.sh is not executable (run: chmod +x scripts/deploy.sh)"
    fi
else
    print_error "deploy.sh not found"
    ((FAIL_COUNT++))
fi

if [ -f "/home/recon/recon-api/scripts/rollback.sh" ]; then
    print_success "rollback.sh exists"
    ((PASS_COUNT++))
    
    if [ -x "/home/recon/recon-api/scripts/rollback.sh" ]; then
        print_success "rollback.sh is executable"
        ((PASS_COUNT++))
    else
        print_warning "rollback.sh is not executable (run: chmod +x scripts/rollback.sh)"
    fi
else
    print_error "rollback.sh not found"
    ((FAIL_COUNT++))
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "TEST SUMMARY"

TOTAL=$((PASS_COUNT + FAIL_COUNT))

echo ""
echo -e "${GREEN}✓ PASSED: $PASS_COUNT${NC}"
echo -e "${RED}✗ FAILED: $FAIL_COUNT${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}TOTAL TESTS: $TOTAL${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  ✓✓✓  ALL TESTS PASSED - READY FOR DEPLOYMENT!  ✓✓✓          ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  ✗✗✗  TESTS FAILED - FIX ISSUES BEFORE DEPLOYING!  ✗✗✗        ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi

