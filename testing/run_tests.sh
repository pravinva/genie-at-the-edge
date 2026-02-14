#!/bin/bash
# Mining Operations Genie Demo - Test Execution Script
# Quick launcher for common test scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || {
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
}

# Check if dependencies are installed
if ! python -c "import databricks.sdk" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and configure your settings:${NC}"
    echo -e "  cp .env.example .env"
    echo -e "  # Edit .env with your Databricks and Ignition configuration"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to print section header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Parse command line arguments
COMMAND=${1:-help}

case "$COMMAND" in
    smoke)
        print_header "SMOKE TEST (5 minutes)"
        python test_suite.py --smoke --report
        ;;

    health)
        print_header "HEALTH CHECK"
        python test_suite.py --health-check --report
        ;;

    functional)
        print_header "FUNCTIONAL TESTS (30-45 minutes)"
        python test_suite.py --functional --report
        ;;

    performance)
        print_header "PERFORMANCE TESTS (45-60 minutes)"
        python test_suite.py --performance --report
        ;;

    integration)
        print_header "INTEGRATION TESTS (30 minutes)"
        python test_suite.py --integration --report
        ;;

    ui)
        print_header "UI TESTS (15-20 minutes)"
        python test_suite.py --ui --report
        ;;

    all)
        print_header "COMPLETE TEST SUITE (2-3 hours)"
        python test_suite.py --all --report
        ;;

    stability)
        DURATION=${2:-3600}
        print_header "STABILITY TEST (${DURATION}s)"
        python test_suite.py --stability --duration "$DURATION" --report
        ;;

    load)
        USERS=${2:-5}
        DURATION=${3:-300}
        print_header "LOAD TEST ($USERS users, ${DURATION}s)"
        python load_testing.py --users "$USERS" --duration "$DURATION"
        ;;

    benchmark)
        print_header "PERFORMANCE BENCHMARKS"
        python performance_benchmarks.py --iterations 10
        ;;

    warmup)
        print_header "WARMING UP SYSTEM"
        python test_genie_api.py --warmup
        print_success "SQL Warehouse warmed up"
        ;;

    quick)
        print_header "QUICK VALIDATION (Smoke + Health)"
        python test_suite.py --smoke --report
        echo ""
        python test_suite.py --health-check --report
        ;;

    demo-prep)
        print_header "DEMO PREPARATION"
        echo "1. Running health check..."
        python test_suite.py --health-check
        echo ""
        echo "2. Warming up SQL Warehouse..."
        python test_genie_api.py --warmup
        echo ""
        echo "3. Running smoke test..."
        python test_suite.py --smoke
        echo ""
        print_success "System ready for demo!"
        ;;

    reports)
        print_header "TEST REPORTS"
        if [ -d "test_reports" ] && [ "$(ls -A test_reports)" ]; then
            echo "Recent test reports:"
            ls -lht test_reports/ | head -10
            echo ""
            echo "View latest report:"
            LATEST=$(ls -t test_reports/test_run_*.json 2>/dev/null | head -1)
            if [ -n "$LATEST" ]; then
                echo "  cat $LATEST | jq '.summary'"
                cat "$LATEST" | jq '.summary' 2>/dev/null || cat "$LATEST"
            else
                print_warning "No test reports found"
            fi
        else
            print_warning "No test reports found. Run tests first."
        fi
        ;;

    clean)
        print_header "CLEANING TEST REPORTS"
        if [ -d "test_reports" ]; then
            COUNT=$(find test_reports -name "*.json" | wc -l)
            if [ "$COUNT" -gt 0 ]; then
                echo "Found $COUNT test reports"
                read -p "Delete all reports? (y/N) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm -f test_reports/*.json
                    print_success "Test reports deleted"
                else
                    print_warning "Cancelled"
                fi
            else
                print_warning "No test reports to clean"
            fi
        fi
        ;;

    install)
        print_header "INSTALLING DEPENDENCIES"
        pip install -r requirements.txt
        print_success "Dependencies installed"
        ;;

    help|*)
        echo -e "${BLUE}Mining Operations Genie Demo - Test Execution${NC}"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  smoke          - Quick smoke test (5 min)"
        echo "  health         - System health check"
        echo "  functional     - Functional tests (30-45 min)"
        echo "  performance    - Performance tests (45-60 min)"
        echo "  integration    - Integration tests (30 min)"
        echo "  ui             - UI tests (15-20 min)"
        echo "  all            - Complete test suite (2-3 hours)"
        echo "  stability [duration] - Stability test (default: 3600s)"
        echo "  load [users] [duration] - Load test (default: 5 users, 300s)"
        echo "  benchmark      - Performance benchmarks"
        echo "  warmup         - Warm up SQL Warehouse"
        echo "  quick          - Quick validation (smoke + health)"
        echo "  demo-prep      - Prepare system for demo"
        echo "  reports        - View test reports"
        echo "  clean          - Clean test reports"
        echo "  install        - Install dependencies"
        echo "  help           - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 smoke                    # Quick smoke test"
        echo "  $0 functional               # Run functional tests"
        echo "  $0 load 10 600              # Load test with 10 users for 10 min"
        echo "  $0 stability 86400          # 24-hour stability test"
        echo "  $0 demo-prep                # Prepare for demo"
        echo ""
        ;;
esac

echo ""
