# Testing Execution Guide
## Mining Operations Genie Demo - Day 10 Testing Plan

This guide provides step-by-step instructions for executing the complete test suite before the customer demo.

---

## Pre-Testing Setup

### 1. Environment Configuration

Create a `.env` file in the testing directory:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-pat-token-here
DATABRICKS_WAREHOUSE_ID=4b9b953939869799
GENIE_SPACE_ID=your-genie-space-id

# Ignition Configuration
IGNITION_GATEWAY_URL=http://localhost:8088
IGNITION_USER=admin
IGNITION_PASSWORD=password

# Chat UI Configuration
CHAT_UI_URL=http://localhost:8088/system/perspective/mining_ops
```

### 2. Install Dependencies

```bash
# Create virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Verify System Status

Before running tests, ensure all components are running:

```bash
# Check Ignition Gateway
curl http://localhost:8088/system/gwinfo

# Check Databricks connectivity
databricks auth env

# Start SQL Warehouse (if stopped)
databricks sql warehouses start $DATABRICKS_WAREHOUSE_ID

# Verify DLT pipeline is running
databricks pipelines list
```

---

## Testing Schedule - Day 10

### Morning Session (2-3 hours) - Functional Validation

#### Phase 1: Component Tests (60 minutes)

**Test 1.1: Ignition Tags** (15 min)
```bash
python test_ignition_tags.py
```

Expected Results:
-  Gateway connectivity: PASS
-  Tags updating: PASS (105 tags)
-  Tag values realistic: PASS
-  No invalid values: PASS
-  CPU/Memory usage: PASS (<10% CPU)

Action if fails: Check Ignition Gateway logs, verify simulation scripts are running.

---

**Test 1.2: Databricks Pipeline** (20 min)
```bash
python test_databricks_pipeline.py
```

Expected Results:
-  Databricks connectivity: PASS
-  SQL Warehouse status: PASS (RUNNING)
-  DLT pipeline status: PASS (RUNNING, HEALTHY)
-  Bronze ingestion: PASS (>500 records/5min, 15 equipment)
-  Gold table quality: PASS
-  All equipment present: PASS

Action if fails:
- Bronze ingestion fails: Check Zerobus configuration, verify Gateway is sending data
- DLT pipeline fails: Check pipeline logs in Databricks UI
- Gold table quality fails: Review DLT transformations

---

**Test 1.3: Genie API** (25 min)
```bash
python test_genie_api.py
```

Expected Results:
-  Genie connectivity: PASS
-  Simple query: PASS (<5s)
-  Query accuracy (10 questions): PASS (8+/10 correct)
-  Query latency: PASS (<5s average)
-  Alarm integration: PASS

Action if fails:
- Connectivity fails: Verify Genie Space ID, check PAT token permissions
- Accuracy fails: Review Genie instructions, add sample questions
- Latency fails: Check SQL Warehouse size, optimize queries

---

#### Phase 2: Integration Tests (30 minutes)

**Test 2.1: End-to-End Flow** (15 min)
```bash
python test_integration_e2e.py
```

Expected Results:
-  Ignition → Databricks flow: PASS
-  Perspective → Chat: PASS
-  Real-time tag bindings: PASS
-  Fault scenario E2E: PASS

Action if fails:
- Flow test fails: Check each component individually
- Bindings fail: Verify Perspective view configuration

---

**Test 2.2: UI Tests** (15 min)
```bash
python test_chat_ui.py
```

Expected Results:
-  Chat UI loads: PASS
-  Visual quality: PASS (Perspective match)
-  Accessibility: PASS (score >90)
-  Responsive design: PASS

Action if fails:
- Visual quality fails: Review CSS, compare with Perspective styles
- Accessibility fails: Run Lighthouse audit, fix reported issues

---

#### Phase 3: Full Functional Suite (30 minutes)

```bash
python test_suite.py --functional --report
```

Review generated report:
```bash
cat test_reports/test_run_*.json | jq '.summary'
```

Sign-off criteria:
- [ ] Pass rate ≥ 95%
- [ ] Zero HIGH severity failures
- [ ] All Genie test questions answered correctly

---

### Midday Session (2-3 hours) - Performance Validation

#### Phase 4: Performance Benchmarks (45 minutes)

**Test 4.1: Component Latency**
```bash
python performance_benchmarks.py --iterations 10
```

Review metrics:
```bash
cat test_reports/benchmark_*.json | jq '.benchmarks'
```

Expected Results:
- Tag → Bronze: avg <1s, max <2s
- Bronze → Gold: <2s
- Genie query: avg <5s, max <8s
- End-to-end: <8s total

Action if fails:
- High latency: Check DLT pipeline mode (should be Real-Time)
- Bronze ingestion slow: Verify Zerobus batching configuration
- Genie slow: Increase SQL Warehouse size, add liquid clustering

---

**Test 4.2: Load Testing** (30 minutes)

Start with light load:
```bash
python load_testing.py --users 3 --duration 180
```

Then test target load:
```bash
python load_testing.py --users 5 --duration 300
```

Expected Results:
- Success rate: ≥95%
- Average latency: <10s
- p95 latency: <15s
- No timeouts

Action if fails:
- High failure rate: Check SQL Warehouse capacity
- Timeouts: Increase Genie API timeout, check network
- Degraded performance: Consider larger warehouse or caching

---

**Test 4.3: Full Performance Suite** (45 minutes)
```bash
python test_suite.py --performance --report
```

Review detailed metrics, identify bottlenecks.

---

### Afternoon Session (2-3 hours) - Stability & Final Validation

#### Phase 5: Short Soak Test (1 hour)

Run abbreviated stability test:
```bash
python test_suite.py --stability --duration 3600
```

Monitor during test:
- CPU usage: <10% average
- Memory: <500MB browser, stable
- No errors in logs
- Data continues flowing

Full 24-hour test (overnight):
```bash
# Start in background
nohup python test_suite.py --stability --duration 86400 --report > soak_test.log 2>&1 &
```

Check progress:
```bash
tail -f soak_test.log
```

---

#### Phase 6: Demo Rehearsal (1 hour)

**Rehearsal 1: Cold Run**
- Start fresh (restart all components)
- Follow demo script exactly
- Time each section
- Note any issues

**Rehearsal 2: Fault Scenario Focus**
- Practice triggering fault
- Verify alarm fires at correct threshold
- Test "Ask AI" button workflow
- Ensure Genie response is helpful

**Rehearsal 3: Q&A Preparation**
- Prepare answers to anticipated questions
- Test follow-up queries
- Verify can drill into SQL/data
- Practice explaining architecture

Document rehearsal results:
```
Run 1: ___ minutes
Issues: _________________
Improvements: ___________

Run 2: ___ minutes
Issues: _________________
Improvements: ___________

Run 3: ___ minutes
Issues: _________________
Improvements: ___________
```

Target: <15 minutes, smooth flow, no technical issues

---

#### Phase 7: Final System Check (30 minutes)

**Pre-Demo Checklist:**

```bash
# Run complete smoke test
python test_suite.py --smoke --report

# Warm up SQL Warehouse
python test_genie_api.py --warmup

# Health check all components
python test_suite.py --health-check
```

System Sign-Off:
- [ ] All smoke tests pass
- [ ] SQL Warehouse is warm (RUNNING)
- [ ] Recent data in bronze table (<1 min old)
- [ ] DLT pipeline processing (HEALTHY)
- [ ] Genie responds quickly (<5s)
- [ ] Chat UI loads correctly
- [ ] Demo rehearsed 3+ times successfully
- [ ] Backup materials ready

---

## Demo Day Procedures

### Pre-Demo (30 minutes before)

1. **Start all components:**
```bash
# Start Ignition Gateway (if not running)
# Start DLT pipeline (if stopped)
databricks pipelines start <pipeline-id>

# Warm SQL Warehouse
databricks sql warehouses start $DATABRICKS_WAREHOUSE_ID

# Wait for warehouse to be RUNNING
databricks sql warehouses get $DATABRICKS_WAREHOUSE_ID
```

2. **Quick validation:**
```bash
python test_suite.py --smoke
```

3. **Pre-load Genie:**
```bash
# Run one test query to prime Genie
python test_genie_api.py --warmup
```

4. **Final visual check:**
- Open Perspective view
- Verify tags updating
- Check chat UI loads
- Test alarm button

### During Demo

**If live demo fails:**

1. **Network issue:**
   - Switch to backup video
   - Explain: "Let me show you a recording of the system in action"
   - Continue with screenshot walkthrough

2. **Genie timeout:**
   - Refresh page
   - Try simpler query
   - If persists: "Let me show you a recent query result..."

3. **No data in tables:**
   - Check if pipeline stopped
   - Restart pipeline
   - While waiting: "Let me show you the architecture..."

### Post-Demo

1. **Capture results:**
```bash
# Save final test report
python test_suite.py --all --report

# Export for review
cp test_reports/test_run_*.json demo_validation_$(date +%Y%m%d).json
```

2. **Document feedback:**
- Customer questions asked
- Technical issues encountered
- Feature requests
- Next steps discussed

---

## Troubleshooting Common Issues

### Issue: Bronze table not updating

**Diagnosis:**
```bash
# Check Ignition Gateway logs
tail -f /path/to/ignition/logs/gateway.log | grep -i zerobus

# Verify tags are changing
# (Use Ignition Designer → Tag Browser)

# Check Databricks ingestion
databricks sql execute --warehouse-id $DATABRICKS_WAREHOUSE_ID \
  --query "SELECT count(*), max(ingestion_timestamp) FROM field_engineering.mining_demo.ot_telemetry_bronze"
```

**Solutions:**
- Restart Zerobus module
- Verify network connectivity
- Check Databricks token is valid
- Verify target table exists

---

### Issue: DLT pipeline errors

**Diagnosis:**
```bash
# Check pipeline status
databricks pipelines get <pipeline-id>

# View pipeline logs in Databricks UI
# Navigate to: Delta Live Tables → [Pipeline Name] → Latest Update → Event Log
```

**Solutions:**
- Check for schema mismatches
- Verify source table exists
- Review transformation logic
- Restart pipeline if transient error

---

### Issue: Genie slow or timing out

**Diagnosis:**
```bash
# Check warehouse status
databricks sql warehouses get $DATABRICKS_WAREHOUSE_ID

# Check warehouse query history
# (Databricks UI → SQL Warehouses → Query History)
```

**Solutions:**
- Increase warehouse size
- Start warehouse before demo (avoid cold start)
- Optimize Genie instructions
- Add sample questions for common queries

---

### Issue: UI not loading

**Diagnosis:**
```bash
# Check Perspective session
# Ignition Gateway → Status → Sessions

# Check browser console for errors
# (F12 → Console tab)

# Verify iframe URL is correct
```

**Solutions:**
- Clear browser cache
- Verify Databricks file hosting working
- Check CORS settings
- Use direct URL if iframe fails

---

## Test Metrics Reference

### Performance Targets

| Metric | Target | Acceptable | Failing |
|--------|--------|------------|---------|
| Tag → Bronze | <1s | <2s | >2s |
| Bronze → Gold | <2s | <3s | >3s |
| Genie Query | <5s | <8s | >10s |
| End-to-End | <8s | <12s | >15s |
| Concurrent (5 users) | <10s | <15s | >20s |
| Success Rate | >95% | >85% | <85% |

### Quality Gates

**Functional:**
- [ ] All 15 equipment present in data
- [ ] All 10 Genie test questions pass
- [ ] Alarm integration working
- [ ] No invalid values in tags

**Performance:**
- [ ] End-to-end latency <8s
- [ ] Load test success rate >95%
- [ ] No timeouts under normal load

**Stability:**
- [ ] 1-hour soak test passes
- [ ] Network recovery working
- [ ] No memory leaks

**UX:**
- [ ] Visual quality matches Perspective
- [ ] Accessibility score >90
- [ ] Smooth interactions (60 FPS)

---

## Final Sign-Off

**Testing Complete:** ___________
**Tested By:** ___________
**Date:** ___________

**Overall System Grade:** _____

- A: Production-ready, demo with confidence
- B: Minor issues, acceptable for demo with caveats
- C: Significant issues, address before demo
- F: Not ready, reschedule demo

**System Status:** READY / NOT READY for customer demo

**Notes:**
________________________________________
________________________________________
________________________________________

**Approved By:** ___________
**Date:** ___________
