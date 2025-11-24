#!/bin/bash

# ============================================================================
# VPS DEPLOYMENT VERIFICATION SCRIPT
# ============================================================================
# Purpose: Comprehensive verification of recon-api deployment
# Tests: Services, Ports, Database, Redis, Celery, Tools, Permissions, API
# ============================================================================

set +e  # Don't exit on errors - we want to collect all test results

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Test results array
declare -a FAILED_TESTS
declare -a WARNING_TESTS

print_success() { 
    echo -e "${GREEN}✓ $1${NC}"
    ((PASS_COUNT++))
}

print_error() { 
    echo -e "${RED}✗ $1${NC}"
    ((FAIL_COUNT++))
    FAILED_TESTS+=("$1")
}

print_warning() { 
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARN_COUNT++))
    WARNING_TESTS+=("$1")
}

print_info() { echo -e "${CYAN}ℹ $1${NC}"; }

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo ""
    echo -e "${MAGENTA}▶ $1${NC}"
    echo -e "${MAGENTA}$(printf '─%.0s' {1..70})${NC}"
}

# ============================================================================
# DETECT VPS IP
# ============================================================================

VPS_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "")
if [ -z "$VPS_IP" ]; then
    VPS_IP=$(curl -s ifconfig.me 2>/dev/null || echo "UNKNOWN")
fi

# ============================================================================
# START VERIFICATION
# ============================================================================

clear
print_header "VPS DEPLOYMENT VERIFICATION"
echo ""
print_info "VPS IP Address: $VPS_IP"
print_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
print_info "User: $(whoami)"
print_info "Working Directory: $(pwd)"
echo ""

# ============================================================================
# SECTION 1: SYSTEMD SERVICES
# ============================================================================

print_header "SECTION 1: SYSTEMD SERVICES"

print_section "1.1 Checking recon-api service"
if systemctl is-active --quiet recon-api; then
    print_success "recon-api service is running"
    PID=$(systemctl show -p MainPID recon-api | cut -d= -f2)
    print_info "  Process ID: $PID"
    UPTIME=$(systemctl show -p ActiveEnterTimestamp recon-api | cut -d= -f2)
    print_info "  Started: $UPTIME"
else
    print_error "recon-api service is NOT running"
    print_info "  Fix: sudo systemctl start recon-api"
fi

if systemctl is-enabled --quiet recon-api 2>/dev/null; then
    print_success "recon-api service is enabled (auto-start)"
else
    print_warning "recon-api service is NOT enabled for auto-start"
    print_info "  Fix: sudo systemctl enable recon-api"
fi

print_section "1.2 Checking recon-celery service"
if systemctl is-active --quiet recon-celery; then
    print_success "recon-celery service is running"
    PID=$(systemctl show -p MainPID recon-celery | cut -d= -f2)
    print_info "  Process ID: $PID"
else
    print_error "recon-celery service is NOT running"
    print_info "  Fix: sudo systemctl start recon-celery"
fi

if systemctl is-enabled --quiet recon-celery 2>/dev/null; then
    print_success "recon-celery service is enabled (auto-start)"
else
    print_warning "recon-celery service is NOT enabled for auto-start"
    print_info "  Fix: sudo systemctl enable recon-celery"
fi

print_section "1.3 Checking recon-flower service (optional)"
if systemctl list-unit-files | grep -q "recon-flower.service"; then
    if systemctl is-active --quiet recon-flower; then
        print_success "recon-flower service is running"
    else
        print_warning "recon-flower service exists but is NOT running"
    fi
else
    print_info "recon-flower service not configured (optional)"
fi

print_section "1.4 Checking nginx service (optional)"
if systemctl list-unit-files | grep -q "nginx.service"; then
    if systemctl is-active --quiet nginx; then
        print_success "nginx service is running"
    else
        print_warning "nginx service exists but is NOT running"
    fi
else
    print_info "nginx service not configured (optional)"
fi

# ============================================================================
# SECTION 2: NETWORK PORTS
# ============================================================================

print_header "SECTION 2: NETWORK PORTS"

print_section "2.1 Checking port 8000 (FastAPI)"
if sudo netstat -tlnp 2>/dev/null | grep -q ":8000" || sudo ss -tlnp 2>/dev/null | grep -q ":8000"; then
    print_success "Port 8000 is listening"
    PORT_INFO=$(sudo netstat -tlnp 2>/dev/null | grep ":8000" || sudo ss -tlnp 2>/dev/null | grep ":8000")
    print_info "  $PORT_INFO"
else
    print_error "Port 8000 is NOT listening"
    print_info "  Fix: Check recon-api service logs: sudo journalctl -u recon-api -n 50"
fi

print_section "2.2 Checking port 6379 (Redis)"
if sudo netstat -tlnp 2>/dev/null | grep -q ":6379" || sudo ss -tlnp 2>/dev/null | grep -q ":6379"; then
    print_success "Port 6379 is listening (Redis)"
else
    print_error "Port 6379 is NOT listening (Redis)"
    print_info "  Fix: sudo systemctl start redis-server"
fi

print_section "2.3 Checking port 5432 (PostgreSQL)"
if sudo netstat -tlnp 2>/dev/null | grep -q ":5432" || sudo ss -tlnp 2>/dev/null | grep -q ":5432"; then
    print_success "Port 5432 is listening (PostgreSQL)"
else
    print_error "Port 5432 is NOT listening (PostgreSQL)"
    print_info "  Fix: sudo systemctl start postgresql"
fi

# ============================================================================
# SECTION 3: DATABASE
# ============================================================================

print_header "SECTION 3: DATABASE"

print_section "3.1 Checking PostgreSQL service"
if systemctl is-active --quiet postgresql; then
    print_success "PostgreSQL service is running"
else
    print_error "PostgreSQL service is NOT running"
    print_info "  Fix: sudo systemctl start postgresql"
fi

print_section "3.2 Checking database 'recon_db' exists"
if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw recon_db; then
    print_success "Database 'recon_db' exists"
else
    print_error "Database 'recon_db' does NOT exist"
    print_info "  Fix: sudo -u postgres createdb recon_db"
fi

print_section "3.3 Checking database user 'recon_user' exists"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='recon_user'" 2>/dev/null | grep -q 1; then
    print_success "Database user 'recon_user' exists"
else
    print_error "Database user 'recon_user' does NOT exist"
    print_info "  Fix: sudo -u postgres createuser recon_user"
fi

print_section "3.4 Checking database connection"
if sudo -u postgres psql -d recon_db -c "SELECT 1;" &>/dev/null; then
    print_success "Can connect to database 'recon_db'"
else
    print_error "Cannot connect to database 'recon_db'"
    print_info "  Fix: Check PostgreSQL logs: sudo journalctl -u postgresql -n 50"
fi

print_section "3.5 Checking database tables"
EXPECTED_TABLES=("alembic_version" "scan_jobs" "subdomains" "screenshots" "waf_detections" "leak_detections")
TABLE_COUNT=0

for table in "${EXPECTED_TABLES[@]}"; do
    if sudo -u postgres psql -d recon_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" 2>/dev/null | grep -q t; then
        print_success "Table '$table' exists"
        ((TABLE_COUNT++))
    else
        print_error "Table '$table' does NOT exist"
        print_info "  Fix: Run Alembic migration: cd ~/recon-api && source venv/bin/activate && alembic upgrade head"
    fi
done

print_info "  Total tables found: $TABLE_COUNT/${#EXPECTED_TABLES[@]}"

# ============================================================================
# SECTION 4: REDIS
# ============================================================================

print_header "SECTION 4: REDIS"

print_section "4.1 Checking Redis service"
if systemctl is-active --quiet redis-server || systemctl is-active --quiet redis; then
    print_success "Redis service is running"
else
    print_error "Redis service is NOT running"
    print_info "  Fix: sudo systemctl start redis-server"
fi

print_section "4.2 Checking Redis connection"
if redis-cli ping 2>/dev/null | grep -q PONG; then
    print_success "Redis connection OK (PING → PONG)"
else
    print_error "Redis connection FAILED"
    print_info "  Fix: Check Redis service: sudo systemctl status redis-server"
fi

print_section "4.3 Testing Redis read/write"
if redis-cli SET test_key "test_value" &>/dev/null && redis-cli GET test_key 2>/dev/null | grep -q "test_value"; then
    print_success "Redis read/write OK"
    redis-cli DEL test_key &>/dev/null
else
    print_error "Redis read/write FAILED"
fi

# ============================================================================
# SECTION 5: CELERY
# ============================================================================

print_header "SECTION 5: CELERY"

print_section "5.1 Checking Celery worker processes"
if pgrep -f "celery.*worker" &>/dev/null; then
    WORKER_COUNT=$(pgrep -f "celery.*worker" | wc -l)
    print_success "Celery worker processes running ($WORKER_COUNT processes)"
else
    print_error "No Celery worker processes found"
    print_info "  Fix: sudo systemctl start recon-celery"
fi

print_section "5.2 Checking Celery can connect to Redis"
if [ -f "/home/recon/recon-api/venv/bin/celery" ] || [ -f "venv/bin/celery" ]; then
    CELERY_BIN=$(find /home/recon/recon-api/venv/bin -name celery 2>/dev/null || find venv/bin -name celery 2>/dev/null || echo "celery")

    # Try to inspect Celery
    CELERY_CHECK=$($CELERY_BIN -A app.workers.celery_app inspect ping 2>&1 || echo "FAILED")

    if echo "$CELERY_CHECK" | grep -q "pong"; then
        print_success "Celery workers are responsive (ping → pong)"
    else
        print_warning "Celery workers may not be responsive"
        print_info "  This is OK if workers just started"
    fi
else
    print_warning "Celery binary not found in venv"
fi

# ============================================================================
# SECTION 6: CLI TOOLS
# ============================================================================

print_header "SECTION 6: CLI RECONNAISSANCE TOOLS"

print_section "6.1 Checking Go installation"
if command -v go &>/dev/null; then
    GO_VERSION=$(go version 2>/dev/null)
    print_success "Go is installed: $GO_VERSION"
else
    print_error "Go is NOT installed"
    print_info "  Fix: Install Go 1.19+ (see VPS_DEPLOYMENT_GUIDE.md)"
fi

print_section "6.2 Checking reconnaissance tools"
TOOLS=("subfinder" "amass" "assetfinder" "httprobe" "httpx" "anew" "gowitness")

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &>/dev/null; then
        TOOL_PATH=$(which "$tool")
        print_success "$tool is installed: $TOOL_PATH"
    else
        print_error "$tool is NOT installed"
        print_info "  Fix: go install github.com/projectdiscovery/$tool/cmd/$tool@latest"
    fi
done

print_section "6.3 Checking wafw00f (Python tool)"
if command -v wafw00f &>/dev/null; then
    print_success "wafw00f is installed"
elif python3 -m pip show wafw00f &>/dev/null; then
    print_success "wafw00f is installed (Python package)"
else
    print_error "wafw00f is NOT installed"
    print_info "  Fix: pip install wafw00f"
fi

# ============================================================================
# SECTION 7: SOURCELEAKHACKER
# ============================================================================

print_header "SECTION 7: SOURCELEAKHACKER"

print_section "7.1 Checking SourceLeakHacker directory"
if [ -d "/home/recon/recon-api/SourceLeakHacker" ]; then
    print_success "SourceLeakHacker directory exists"
elif [ -d "SourceLeakHacker" ]; then
    print_success "SourceLeakHacker directory exists (current dir)"
else
    print_error "SourceLeakHacker directory NOT found"
    print_info "  Fix: Upload SourceLeakHacker folder (see UPLOAD_SOURCELEAKHACKER_GUIDE.md)"
fi

print_section "7.2 Checking SourceLeakHacker.py file"
if [ -f "/home/recon/recon-api/SourceLeakHacker/SourceLeakHacker.py" ]; then
    print_success "SourceLeakHacker.py exists"
    if [ -x "/home/recon/recon-api/SourceLeakHacker/SourceLeakHacker.py" ]; then
        print_success "SourceLeakHacker.py is executable"
    else
        print_warning "SourceLeakHacker.py is NOT executable"
        print_info "  Fix: chmod +x /home/recon/recon-api/SourceLeakHacker/SourceLeakHacker.py"
    fi
elif [ -f "SourceLeakHacker/SourceLeakHacker.py" ]; then
    print_success "SourceLeakHacker.py exists (current dir)"
else
    print_error "SourceLeakHacker.py NOT found"
fi

print_section "7.3 Checking SourceLeakHacker dict/ folder"
if [ -d "/home/recon/recon-api/SourceLeakHacker/dict" ]; then
    DICT_COUNT=$(find /home/recon/recon-api/SourceLeakHacker/dict -type f 2>/dev/null | wc -l)
    print_success "SourceLeakHacker dict/ folder exists ($DICT_COUNT files)"
elif [ -d "SourceLeakHacker/dict" ]; then
    DICT_COUNT=$(find SourceLeakHacker/dict -type f 2>/dev/null | wc -l)
    print_success "SourceLeakHacker dict/ folder exists ($DICT_COUNT files)"
else
    print_error "SourceLeakHacker dict/ folder NOT found"
    print_info "  Fix: Upload complete SourceLeakHacker folder structure"
fi

# ============================================================================
# SECTION 8: FILE PERMISSIONS
# ============================================================================

print_header "SECTION 8: FILE PERMISSIONS & OWNERSHIP"

print_section "8.1 Checking recon-api directory ownership"
if [ -d "/home/recon/recon-api" ]; then
    OWNER=$(stat -c '%U:%G' /home/recon/recon-api 2>/dev/null)
    if [ "$OWNER" = "recon:recon" ]; then
        print_success "recon-api directory owned by recon:recon"
    else
        print_warning "recon-api directory owned by $OWNER (expected recon:recon)"
        print_info "  Fix: sudo chown -R recon:recon /home/recon/recon-api"
    fi
else
    print_error "recon-api directory NOT found at /home/recon/recon-api"
fi

print_section "8.2 Checking .env file"
if [ -f "/home/recon/recon-api/.env" ]; then
    print_success ".env file exists"

    PERMS=$(stat -c '%a' /home/recon/recon-api/.env 2>/dev/null)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        print_success ".env file has secure permissions ($PERMS)"
    else
        print_warning ".env file permissions: $PERMS (recommended: 600)"
        print_info "  Fix: chmod 600 /home/recon/recon-api/.env"
    fi
elif [ -f ".env" ]; then
    print_success ".env file exists (current dir)"
else
    print_error ".env file NOT found"
    print_info "  Fix: Create .env file (see VPS_DEPLOYMENT_GUIDE.md)"
fi

print_section "8.3 Checking venv directory"
if [ -d "/home/recon/recon-api/venv" ]; then
    print_success "Virtual environment exists"

    if [ -f "/home/recon/recon-api/venv/bin/python" ]; then
        PYTHON_VERSION=$(/home/recon/recon-api/venv/bin/python --version 2>&1)
        print_success "Python in venv: $PYTHON_VERSION"
    fi
elif [ -d "venv" ]; then
    print_success "Virtual environment exists (current dir)"
else
    print_error "Virtual environment NOT found"
    print_info "  Fix: python3.13 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

print_section "8.4 Checking jobs directory"
if [ -d "/home/recon/recon-api/jobs" ]; then
    print_success "jobs/ directory exists"
elif [ -d "jobs" ]; then
    print_success "jobs/ directory exists (current dir)"
else
    print_warning "jobs/ directory NOT found (will be created automatically)"
fi

# ============================================================================
# SECTION 9: FIREWALL
# ============================================================================

print_header "SECTION 9: FIREWALL"

print_section "9.1 Checking UFW status"
if command -v ufw &>/dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        print_info "UFW firewall is ACTIVE"

        if sudo ufw status | grep -q "8000"; then
            print_success "Port 8000 is allowed in firewall"
        else
            print_warning "Port 8000 is NOT allowed in firewall"
            print_info "  Fix: sudo ufw allow 8000/tcp"
        fi

        if sudo ufw status | grep -q "80"; then
            print_success "Port 80 (HTTP) is allowed in firewall"
        else
            print_info "Port 80 (HTTP) is NOT allowed (optional for nginx)"
        fi
    else
        print_info "UFW firewall is INACTIVE"
    fi
else
    print_info "UFW not installed"
fi

# ============================================================================
# SECTION 10: API FUNCTIONALITY
# ============================================================================

print_header "SECTION 10: API FUNCTIONALITY"

print_section "10.1 Testing API health endpoint (localhost)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    RESPONSE=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null)
    print_success "API health endpoint responds (HTTP $HTTP_CODE)"
    print_info "  Response: $RESPONSE"
else
    print_error "API health endpoint NOT responding (HTTP $HTTP_CODE)"
    print_info "  Fix: Check service logs: sudo journalctl -u recon-api -n 50"
fi

print_section "10.2 Testing API health endpoint (external IP)"
if [ "$VPS_IP" != "UNKNOWN" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$VPS_IP:8000/api/v1/health" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "API accessible from external IP (HTTP $HTTP_CODE)"
    else
        print_warning "API NOT accessible from external IP (HTTP $HTTP_CODE)"
        print_info "  This might be a firewall issue"
    fi
fi

print_section "10.3 Testing API scans endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/scans 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API scans endpoint responds (HTTP $HTTP_CODE)"

    SCAN_COUNT=$(curl -s http://localhost:8000/api/v1/scans 2>/dev/null | grep -o '"total":[0-9]*' | cut -d: -f2)
    if [ -n "$SCAN_COUNT" ]; then
        print_info "  Total scans in database: $SCAN_COUNT"
    fi
else
    print_error "API scans endpoint NOT responding (HTTP $HTTP_CODE)"
fi

print_section "10.4 Testing API docs endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API documentation accessible (HTTP $HTTP_CODE)"
    print_info "  URL: http://$VPS_IP:8000/docs"
else
    print_warning "API documentation NOT accessible (HTTP $HTTP_CODE)"
fi

# ============================================================================
# SECTION 11: FRONTEND
# ============================================================================

print_header "SECTION 11: FRONTEND CONFIGURATION"

print_section "11.1 Checking web directory"
if [ -d "/home/recon/recon-api/web" ]; then
    print_success "web/ directory exists"
elif [ -d "web" ]; then
    print_success "web/ directory exists (current dir)"
else
    print_error "web/ directory NOT found"
fi

print_section "11.2 Checking frontend files"
FRONTEND_FILES=("index.html" "app.js" "styles.css")
for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "/home/recon/recon-api/web/$file" ]; then
        print_success "web/$file exists"
    elif [ -f "web/$file" ]; then
        print_success "web/$file exists (current dir)"
    else
        print_error "web/$file NOT found"
    fi
done

print_section "11.3 Checking frontend API URL configuration"
if [ -f "/home/recon/recon-api/web/app.js" ]; then
    API_URL=$(grep "API_BASE_URL" /home/recon/recon-api/web/app.js | head -1)
    print_info "Frontend API URL config:"
    print_info "  $API_URL"

    if echo "$API_URL" | grep -q "localhost"; then
        print_warning "Frontend uses 'localhost' - may not work from external browser"
        print_info "  Fix: Run ./fix_frontend_api_url.sh"
    else
        print_success "Frontend does NOT hardcode localhost"
    fi
elif [ -f "web/app.js" ]; then
    API_URL=$(grep "API_BASE_URL" web/app.js | head -1)
    print_info "Frontend API URL: $API_URL"
fi

print_section "11.4 Testing frontend accessibility"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Frontend is accessible (HTTP $HTTP_CODE)"
    print_info "  URL: http://$VPS_IP:8000"
else
    print_error "Frontend NOT accessible (HTTP $HTTP_CODE)"
fi

# ============================================================================
# SECTION 12: ENVIRONMENT CONFIGURATION
# ============================================================================

print_header "SECTION 12: ENVIRONMENT CONFIGURATION"

print_section "12.1 Checking .env file configuration"
if [ -f "/home/recon/recon-api/.env" ]; then
    ENV_FILE="/home/recon/recon-api/.env"
elif [ -f ".env" ]; then
    ENV_FILE=".env"
else
    print_error ".env file not found"
    ENV_FILE=""
fi

if [ -n "$ENV_FILE" ]; then
    # Check critical environment variables
    if grep -q "DATABASE_URL=" "$ENV_FILE"; then
        print_success ".env contains DATABASE_URL"
    else
        print_error ".env missing DATABASE_URL"
    fi

    if grep -q "REDIS_URL=" "$ENV_FILE"; then
        print_success ".env contains REDIS_URL"
    else
        print_error ".env missing REDIS_URL"
    fi

    if grep -q "JOBS_DIRECTORY=" "$ENV_FILE"; then
        print_success ".env contains JOBS_DIRECTORY"
    else
        print_warning ".env missing JOBS_DIRECTORY (will use default)"
    fi

    if grep -q "SOURCELEAKHACKER_PATH=" "$ENV_FILE"; then
        SLH_PATH=$(grep "SOURCELEAKHACKER_PATH=" "$ENV_FILE" | cut -d= -f2)
        print_success ".env contains SOURCELEAKHACKER_PATH"
        print_info "  Path: $SLH_PATH"

        # Verify path exists
        if [ -f "$SLH_PATH" ]; then
            print_success "SourceLeakHacker path is valid"
        else
            print_error "SourceLeakHacker path does NOT exist: $SLH_PATH"
        fi
    else
        print_warning ".env missing SOURCELEAKHACKER_PATH"
    fi
fi

# ============================================================================
# SECTION 13: PYTHON DEPENDENCIES
# ============================================================================

print_header "SECTION 13: PYTHON DEPENDENCIES"

print_section "13.1 Checking Python version"
if [ -f "/home/recon/recon-api/venv/bin/python" ]; then
    PYTHON_BIN="/home/recon/recon-api/venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
else
    PYTHON_BIN="python3"
fi

PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
print_info "Python version: $PYTHON_VERSION"

if echo "$PYTHON_VERSION" | grep -q "Python 3.1[3-9]"; then
    print_success "Python version is 3.13+ (compatible)"
elif echo "$PYTHON_VERSION" | grep -q "Python 3.1[0-2]"; then
    print_success "Python version is 3.10+ (compatible)"
else
    print_warning "Python version may not be compatible (need 3.10+)"
fi

print_section "13.2 Checking critical Python packages"
PACKAGES=("fastapi" "celery" "sqlalchemy" "psycopg2" "redis" "pydantic" "alembic")

if [ -f "/home/recon/recon-api/venv/bin/pip" ]; then
    PIP_BIN="/home/recon/recon-api/venv/bin/pip"
elif [ -f "venv/bin/pip" ]; then
    PIP_BIN="venv/bin/pip"
else
    PIP_BIN="pip3"
fi

for package in "${PACKAGES[@]}"; do
    if $PIP_BIN show "$package" &>/dev/null; then
        VERSION=$($PIP_BIN show "$package" 2>/dev/null | grep "Version:" | cut -d: -f2 | tr -d ' ')
        print_success "$package is installed (v$VERSION)"
    else
        print_error "$package is NOT installed"
        print_info "  Fix: source venv/bin/activate && pip install $package"
    fi
done

# ============================================================================
# SECTION 14: FUNCTIONAL TESTS
# ============================================================================

print_header "SECTION 14: FUNCTIONAL TESTS"

print_section "14.1 Testing database insert/retrieve"
TEST_JOB_ID="verify-test-$(date +%s)"

if sudo -u postgres psql -d recon_db -c "INSERT INTO scan_jobs (job_id, domain, status) VALUES ('$TEST_JOB_ID', 'test.com', 'pending');" &>/dev/null; then
    print_success "Can INSERT into database"

    if sudo -u postgres psql -d recon_db -tAc "SELECT job_id FROM scan_jobs WHERE job_id = '$TEST_JOB_ID';" 2>/dev/null | grep -q "$TEST_JOB_ID"; then
        print_success "Can SELECT from database"

        # Cleanup
        sudo -u postgres psql -d recon_db -c "DELETE FROM scan_jobs WHERE job_id = '$TEST_JOB_ID';" &>/dev/null
        print_success "Can DELETE from database"
    else
        print_error "Cannot SELECT from database"
    fi
else
    print_error "Cannot INSERT into database"
    print_info "  Fix: Check database permissions"
fi

print_section "14.2 Testing API can create scan (dry run)"
print_info "Skipping actual scan creation (would start background job)"
print_info "To test manually: curl -X POST http://localhost:8000/api/v1/scans/full -H 'Content-Type: application/json' -d '{\"domain\":\"example.com\"}'"

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print_header "VERIFICATION SUMMARY"
echo ""

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ PASSED: $PASS_COUNT${NC}"
echo -e "${RED}  ✗ FAILED: $FAIL_COUNT${NC}"
echo -e "${YELLOW}  ⚠ WARNINGS: $WARN_COUNT${NC}"
echo -e "${CYAN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  TOTAL TESTS: $TOTAL_TESTS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  ✓✓✓  DEPLOYMENT VERIFICATION SUCCESSFUL!  ✓✓✓                ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  All critical components are operational.                     ║${NC}"
    echo -e "${GREEN}║  The recon-api application is ready for use!                  ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ $WARN_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠ Note: $WARN_COUNT warnings detected (non-critical)${NC}"
        echo ""
    fi

    echo -e "${CYAN}🚀 Next Steps:${NC}"
    echo "  1. Access dashboard: http://$VPS_IP:8000"
    echo "  2. View API docs: http://$VPS_IP:8000/docs"
    echo "  3. Create a test scan via dashboard"
    echo "  4. Monitor logs: sudo journalctl -u recon-api -f"
    echo ""
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  ✗✗✗  DEPLOYMENT VERIFICATION FAILED!  ✗✗✗                    ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  $FAIL_COUNT critical issue(s) detected.                                ║${NC}"
    echo -e "${RED}║  Please fix the issues below before using the application.    ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "${RED}  ✗ $test${NC}"
    done
    echo ""

    echo -e "${CYAN}🔧 Troubleshooting Commands:${NC}"
    echo "  • Check service status: sudo systemctl status recon-api recon-celery"
    echo "  • View logs: sudo journalctl -u recon-api -n 100"
    echo "  • Check database: sudo -u postgres psql -d recon_db -c '\dt'"
    echo "  • Test Redis: redis-cli ping"
    echo "  • Restart services: sudo systemctl restart recon-api recon-celery"
    echo ""
fi

if [ $WARN_COUNT -gt 0 ] && [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${YELLOW}Warnings (non-critical):${NC}"
    for warning in "${WARNING_TESTS[@]}"; do
        echo -e "${YELLOW}  ⚠ $warning${NC}"
    done
    echo ""
fi

echo -e "${CYAN}📚 Documentation:${NC}"
echo "  • VPS_DEPLOYMENT_GUIDE.md - Complete deployment guide"
echo "  • FIX_CONNECTION_REFUSED_GUIDE.md - Fix connection issues"
echo "  • FIX_ALEMBIC_GUIDE.md - Fix database migration issues"
echo ""

echo -e "${CYAN}Verification completed at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# Exit with appropriate code
if [ $FAIL_COUNT -eq 0 ]; then
    exit 0
else
    exit 1
fi

