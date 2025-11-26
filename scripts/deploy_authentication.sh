#!/bin/bash

# ============================================================================
# AUTHENTICATION DEPLOYMENT SCRIPT
# ============================================================================
# This script deploys the authentication system to the VPS
#
# Usage:
#   bash scripts/deploy_authentication.sh
#
# What it does:
#   1. Installs required dependencies
#   2. Runs database migration
#   3. Creates admin user (interactive)
#   4. Restarts FastAPI service
#   5. Verifies deployment
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "AUTHENTICATION DEPLOYMENT SCRIPT"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on VPS
if [ ! -d "/home/recon/recon-api" ]; then
    echo -e "${RED}❌ Error: This script must be run on the VPS (124.197.22.184)${NC}"
    echo "   Please SSH to the VPS first:"
    echo "   ssh recon@124.197.22.184"
    exit 1
fi

# Change to project directory
cd /home/recon/recon-api

echo -e "${YELLOW}Step 1: Installing dependencies...${NC}"
source venv/bin/activate
pip install passlib[bcrypt]>=1.7.4
pip install python-jose[cryptography]>=3.3.0
pip install python-multipart>=0.0.6
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Running database migration...${NC}"
alembic upgrade head
echo -e "${GREEN}✅ Database migration complete${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating admin user...${NC}"
python3 scripts/create_admin_user.py
echo ""

echo -e "${YELLOW}Step 4: Restarting FastAPI service...${NC}"
sudo systemctl restart recon-api
sleep 3
echo -e "${GREEN}✅ Service restarted${NC}"
echo ""

echo -e "${YELLOW}Step 5: Checking service status...${NC}"
if sudo systemctl is-active --quiet recon-api; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "   Check logs with: sudo journalctl -u recon-api -n 50"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 6: Verifying deployment...${NC}"

# Test 1: Check if login page is accessible
echo -n "   Testing login page... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login | grep -q "200"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Test 2: Check if register page is accessible
echo -n "   Testing register page... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/register | grep -q "200"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Test 3: Check if root redirects to login
echo -n "   Testing root redirect... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "307\|302"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo ""
echo "============================================================================"
echo -e "${GREEN}✅ AUTHENTICATION DEPLOYMENT COMPLETE!${NC}"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Open browser: http://124.197.22.184:8000/"
echo "  2. Login with admin credentials"
echo "  3. Change admin password"
echo "  4. Create additional users as needed"
echo ""
echo "Documentation:"
echo "  - AUTHENTICATION_SUMMARY.md"
echo "  - AUTHENTICATION_IMPLEMENTATION_GUIDE.md"
echo ""
echo "Useful commands:"
echo "  - Check logs: sudo journalctl -u recon-api -f"
echo "  - Restart service: sudo systemctl restart recon-api"
echo "  - Create user: python3 scripts/create_admin_user.py"
echo ""

