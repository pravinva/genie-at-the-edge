# Mining Operations Genie Demo - Testing Infrastructure

## Overview

Comprehensive testing framework for validating the Mining Operations Genie Demo system before customer presentation. This testing suite covers functional, performance, stability, integration, and UX testing across all components.

## Test Coverage

### 1. Functional Testing
- **Tag Simulation Validation** - Verify Ignition tags update realistically
- **Databricks Pipeline** - Validate data flows from bronze to gold
- **Genie Query Accuracy** - Test natural language understanding and responses
- **Alarm Integration** - Verify "Ask AI" button functionality

### 2. Performance Testing
- **End-to-End Latency** - Measure tag update to query response (<5s target)
- **Concurrent User Load** - Test multiple operators simultaneously
- **Cold Start Behavior** - SQL Warehouse startup time measurement
- **Throughput Benchmarks** - Data ingestion and query execution rates

### 3. Stability Testing
- **24-Hour Soak Test** - Continuous operation without degradation
- **Memory Leak Detection** - Monitor resource usage over time
- **Network Recovery** - Graceful handling of connectivity issues
- **Component Failure** - Test fault tolerance and recovery

### 4. Integration Testing
- **Ignition to Databricks** - End-to-end data flow validation
- **Perspective to Chat** - UI component communication
- **Real-Time Updates** - Tag bindings and live data synchronization
- **API Connectivity** - Genie API responses and error handling

### 5. User Experience Testing
- **Visual Quality** - Perspective styling consistency
- **Interaction Smoothness** - Animation and responsiveness (60 FPS)
- **Accessibility** - Keyboard navigation and screen reader support
- **Mobile Responsiveness** - Test on various screen sizes

## Quick Start

### Prerequisites

```bash
# Python 3.12+ required
python --version

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-pat-token"
export DATABRICKS_WAREHOUSE_ID="4b9b953939869799"
export GENIE_SPACE_ID="your-genie-space-id"
export IGNITION_GATEWAY_URL="http://localhost:8088"
```

### Run All Tests

```bash
# Execute complete test suite with reporting
python test_suite.py --all --report

# Run specific test category
python test_suite.py --functional
python test_suite.py --performance
python test_suite.py --integration

# Generate performance benchmarks
python performance_benchmarks.py --output test_reports/benchmark_$(date +%Y%m%d).json

# Run load testing
python load_testing.py --users 10 --duration 300
```

## Test Files

| File | Purpose | Duration |
|------|---------|----------|
| `test_suite.py` | Main test runner with all tests | 30-60 min |
| `test_ignition_tags.py` | Validate tag simulation behavior | 5 min |
| `test_databricks_pipeline.py` | DLT pipeline validation | 10 min |
| `test_genie_api.py` | Genie query accuracy tests | 15 min |
| `test_chat_ui.py` | UI functionality and styling | 10 min |
| `test_integration_e2e.py` | End-to-end flow validation | 20 min |
| `load_testing.py` | Concurrent user simulation | 5-30 min |
| `performance_benchmarks.py` | Latency and throughput metrics | 10 min |

## Test Reports

All test results are saved to `test_reports/` with timestamps:

```
test_reports/
├── test_run_20260215_143022.json       # Complete test results
├── benchmark_20260215.json              # Performance metrics
├── load_test_20260215_10users.json     # Load test results
└── soak_test_24h_20260215.json         # Stability test results
```

## Performance Targets

| Metric | Target | Acceptable | Failing |
|--------|--------|------------|---------|
| Tag Update → Bronze | <1s | <2s | >2s |
| Bronze → Gold (DLT) | <2s | <3s | >3s |
| Genie Query Response | <5s | <8s | >10s |
| End-to-End Latency | <8s | <12s | >15s |
| Concurrent Users (5) | <10s | <15s | >20s |
| 24-Hour Uptime | 99.9% | 99% | <99% |
| Browser Memory (4h) | <500MB | <1GB | >1GB |
| CPU (Ignition) | <10% | <20% | >30% |

## Test Execution Workflow

### Pre-Demo Testing (Day 10)

1. **Morning: Functional Validation** (2 hours)
   ```bash
   python test_suite.py --functional --report
   python test_ignition_tags.py
   python test_databricks_pipeline.py
   python test_genie_api.py
   ```

2. **Midday: Performance Testing** (2 hours)
   ```bash
   python performance_benchmarks.py
   python load_testing.py --users 5 --duration 300
   python test_integration_e2e.py
   ```

3. **Afternoon: UI & Integration** (2 hours)
   ```bash
   python test_chat_ui.py
   python test_integration_e2e.py --full
   # Manual visual inspection
   ```

4. **Overnight: Stability Testing** (24 hours)
   ```bash
   python test_suite.py --stability --duration 86400
   ```

### Demo Day Checklist

```bash
# Run quick smoke test (5 minutes)
python test_suite.py --smoke

# Verify all systems operational
python test_suite.py --health-check

# Warm up SQL Warehouse (prevent cold start)
python test_genie_api.py --warmup
```

## Troubleshooting

### Common Issues

**Test Fails: "Cannot connect to Ignition Gateway"**
```bash
# Check Gateway is running
curl http://localhost:8088/system/gwinfo

# Verify network connectivity
ping localhost
```

**Test Fails: "Databricks authentication error"**
```bash
# Verify token is valid
databricks auth env

# Test connection manually
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
     "$DATABRICKS_HOST/api/2.0/clusters/list"
```

**Test Fails: "No data in bronze table"**
```bash
# Check Zerobus is sending data
tail -f /path/to/ignition/logs/gateway.log | grep -i zerobus

# Query bronze table directly
databricks sql execute \
    --warehouse-id $DATABRICKS_WAREHOUSE_ID \
    --query "SELECT count(*) FROM field_engineering.mining_demo.ot_telemetry_bronze"
```

**Test Fails: "Genie timeout"**
```bash
# Check SQL Warehouse status
databricks sql warehouses get $DATABRICKS_WAREHOUSE_ID

# Start warehouse manually if stopped
databricks sql warehouses start $DATABRICKS_WAREHOUSE_ID
```

## Test Data Management

### Reset Test Environment

```bash
# Stop Ignition simulation
# Truncate test tables (optional)
databricks sql execute \
    --warehouse-id $DATABRICKS_WAREHOUSE_ID \
    --query "DELETE FROM field_engineering.mining_demo.ot_telemetry_bronze WHERE ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL 1 HOUR"

# Restart Ignition Gateway
# Re-run tests
```

### Generate Test Data

```bash
# Create synthetic data for testing
python generate_test_data.py --equipment 15 --duration 3600 --output test_data.json

# Load into bronze table
databricks sql execute \
    --warehouse-id $DATABRICKS_WAREHOUSE_ID \
    --file test_data.sql
```

## Continuous Integration

For automated testing in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: python test_suite.py --ci --report
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_reports/
```

## Sign-Off Checklist

Before demo, ensure ALL tests pass:

- [ ] All functional tests pass (10/10 Genie questions answered correctly)
- [ ] Performance targets met (end-to-end latency <8s)
- [ ] Stability test passed (24-hour soak test)
- [ ] Load testing successful (5 concurrent users)
- [ ] UI quality validated (visual inspection)
- [ ] Integration flows verified (alarm button → chat)
- [ ] Error handling tested (network interruption recovery)
- [ ] Accessibility score >90 (Lighthouse audit)
- [ ] Demo rehearsal completed 3+ times
- [ ] Backup plan ready (video/screenshots)

## Support

For issues or questions:
- Review `execution_guide.md` for detailed test procedures
- Check test output logs in `test_reports/`
- Examine component-specific test files for debugging

## Next Steps

After successful testing:
1. Review `test_reports/` for any warnings or performance issues
2. Address any "PASS with caveats" results
3. Practice demo flow 3+ times (see `../prompts/ralph_wiggum_12_demo.md`)
4. Ensure backup materials ready (video, screenshots)
5. Sign off on system readiness for customer presentation
