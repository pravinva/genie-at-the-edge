# DLT Pipeline Quick Start Guide

**Goal:** Deploy mining operations Real-Time DLT pipeline in 30 minutes

---

## Prerequisites (5 minutes)

```bash
# 1. Install Databricks SDK
pip install databricks-sdk

# 2. Verify authentication
databricks workspace list /

# 3. Verify Zerobus is streaming data
# Check Ignition Gateway is sending data
```

---

## Step 1: Create Dimension Tables (5 minutes)

```sql
-- In Databricks SQL Editor
-- Copy and run: dimension_tables.sql

-- Quick verify
SELECT COUNT(*) FROM field_engineering.mining_demo.equipment_master;
-- Expected: 15

SELECT COUNT(*) FROM field_engineering.mining_demo.sensor_definitions;
-- Expected: 10
```

---

## Step 2: Deploy Pipeline (10 minutes)

### Option A: Automated (Recommended)

```bash
# Upload notebook first
databricks workspace import \
  mining_realtime_dlt.py \
  /Users/pravin.varma@databricks.com/mining_realtime_dlt \
  --language PYTHON

# Deploy and start
python deploy_pipeline.py --start

# Visit URL shown in output to monitor
```

### Option B: UI (If script fails)

1. Go to: **Workflows → Delta Live Tables → Create Pipeline**
2. Settings:
   - Name: `mining_operations_realtime`
   - Target: `field_engineering.mining_demo`
   - Notebook: Select uploaded `mining_realtime_dlt.py`
   - Cluster: Enhanced, 2-4 workers, i3.xlarge
   - Runtime: 16.4+
   - Photon: Enabled
3. Advanced:
   ```json
   {
     "spark.databricks.streaming.mode": "realtime",
     "spark.sql.shuffle.partitions": "200"
   }
   ```
4. Click **Start**

---

## Step 3: Validate (5 minutes)

```sql
-- Check pipeline is processing data
SELECT
  MAX(ingestion_timestamp) as last_data,
  COUNT(*) as record_count
FROM field_engineering.mining_demo.ot_telemetry_bronze
WHERE ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '10 minutes';
-- Expected: record_count > 0, last_data recent

-- Check latency
SELECT AVG(avg_latency_sec) as pipeline_latency
FROM field_engineering.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '10 minutes';
-- Expected: <1.0 second

-- Check equipment coverage
SELECT COUNT(DISTINCT equipment_id) as equipment_count
FROM field_engineering.mining_demo.equipment_current_status;
-- Expected: 15
```

---

## Step 4: Create Genie Space (5 minutes)

1. Go to: **AI & ML → Genie → Create Genie Space**
2. Configure:
   - Name: `Mining Operations Intelligence`
   - Warehouse: `4b9b953939869799`
   - Catalog: `field_engineering`
   - Schema: `mining_demo`
3. Click **Create**
4. Add tables:
   - equipment_performance_1min
   - equipment_current_status
   - ml_predictions
   - equipment_master
5. Copy instructions from `genie_space_setup.sql` → Settings → Instructions
6. Add sample questions from `genie_space_setup.sql`

---

## Test Genie

Try these questions:

```
What's the current status of all crushers?
Are there any equipment issues right now?
Show me equipment with highest vibration
```

Expected: Natural language responses with data from gold tables, <5s response time

---

## Success Criteria

 Pipeline running without errors
 All 15 equipment reporting data
 Latency < 1 second end-to-end
 Genie responds accurately to questions
 No data quality issues

---

## If Something Goes Wrong

### Pipeline fails to start
```bash
# Check logs in DLT UI
# Verify dimension tables exist
# Ensure DBR >= 16.4
```

### High latency
```sql
-- Run OPTIMIZE
OPTIMIZE field_engineering.mining_demo.equipment_performance_1min;
```

### No data flowing
```bash
# Check Zerobus stream
# Verify Ignition Gateway connectivity
# Review DLT event log for errors
```

### Genie not responding
```sql
-- Verify tables have data
SELECT COUNT(*) FROM field_engineering.mining_demo.equipment_current_status;

-- Check warehouse is running
-- Review Genie instructions are configured
```

---

## Next Steps

1. Run full validation: `validation_queries.sql`
2. Set up monitoring dashboard
3. Build chat UI (File 08)
4. Integrate with Perspective view

---

## Quick Reference

| Component | Location |
|-----------|----------|
| Pipeline UI | https://<workspace>/pipelines/<pipeline_id> |
| SQL Editor | https://<workspace>/sql/editor |
| Genie Spaces | https://<workspace>/genie |
| Monitoring | https://<workspace>/lakehouse-monitoring |

| Table | Purpose |
|-------|---------|
| ot_telemetry_bronze | Raw data from Zerobus |
| ot_sensors_normalized | Flattened sensor readings |
| equipment_performance_1min | 1-min aggregates |
| equipment_current_status | Latest readings |
| ml_predictions | Anomaly alerts |

| Query | Expected Result |
|-------|-----------------|
| Latency | <1.0 second |
| Equipment Count | 15 |
| Data Quality | >99% |
| Genie Response Time | <5 seconds |

---

**Total Time: 30 minutes**

Ready for File 08: Chat UI integration!
