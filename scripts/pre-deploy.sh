#!/bin/bash
# Pre-deployment validation script for Aether-Thread
# Usage: ./scripts/pre-deploy.sh
# This script validates code before committing/pushing to CI/CD

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
SOURCE_DIR="${SOURCE_DIR:-src}"
MAX_THREADS="${MAX_THREADS:-32}"
VERBOSE="${VERBOSE:-false}"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Pre-Deployment Validation (Aether)      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if aether is installed
echo -e "${BLUE}1️⃣  Checking Aether installation...${NC}"
if ! command -v aether &> /dev/null; then
    if ! python3 -c "import aether" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Aether not installed. Installing...${NC}"
        pip install aether-thread
    fi
fi
echo -e "${GREEN}✅ Aether found${NC}"
echo ""

# Check Python version
echo -e "${BLUE}2️⃣  Checking Python version...${NC}"
CURRENT_PYTHON=$(python3 --version | cut -d' ' -f2)
echo -e "Python version: ${CURRENT_PYTHON}"
echo -e "${GREEN}✅ Python ready${NC}"
echo ""

# Run standard thread-safety audit
echo -e "${BLUE}3️⃣  Running thread-safety audit...${NC}"
if aether check "$SOURCE_DIR" --verbose; then
    echo -e "${GREEN}✅ No standard thread-safety issues${NC}"
else
    echo -e "${RED}❌ Thread-safety issues found!${NC}"
    exit 1
fi
echo ""

# Run free-threaded specific checks
echo -e "${BLUE}4️⃣  Running free-threaded Python checks...${NC}"
if aether check "$SOURCE_DIR" --free-threaded --verbose; then
    echo -e "${GREEN}✅ No free-threading issues${NC}"
else
    echo -e "${RED}❌ Free-threading issues found!${NC}"
    exit 1
fi
echo ""

# Check environment
echo -e "${BLUE}5️⃣  Checking environment compatibility...${NC}"
if aether status; then
    echo -e "${GREEN}✅ Environment compatible${NC}"
else
    echo -e "${YELLOW}⚠️  Environment check had warnings${NC}"
fi
echo ""

# Optional: Run performance profile
if [ -f "tests/benchmark.py" ]; then
    echo -e "${BLUE}6️⃣  Profiling performance (optional)...${NC}"
    echo -e "${YELLOW}⏳ This may take 30+ seconds...${NC}"
    if aether profile tests/benchmark.py --max-threads "$MAX_THREADS" --duration 2.0; then
        echo -e "${GREEN}✅ Performance profiling complete${NC}"
    else
        echo -e "${YELLOW}⚠️  Performance profiling skipped${NC}"
    fi
    echo ""
fi

# Final summary
echo -e "${BLUE}═════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All pre-deployment checks passed!${NC}"
echo -e "${BLUE}═════════════════════════════════════════════${NC}"
echo ""
echo "📋 Summary:"
echo "  ✅ Standard thread-safety audit"
echo "  ✅ Free-threaded Python checks"
echo "  ✅ Environment compatibility"
echo ""
echo "🚀 You're ready to:"
echo "  1. git commit"
echo "  2. git push (triggers CI/CD)"
echo "  3. Create pull request"
echo ""
