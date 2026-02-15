# Deploy Delta Live Tables Pipeline

## Step 1: Upload Python File to Databricks

**Option A: Via Databricks UI**
1. Open Databricks workspace
2. Go to Workspace → Repos or Workspace folder
3. Create folder: `mining-genie-demo/pipelines/`
4. Upload file: `mining_realtime_dlt.py`

**Option B: Via Databricks CLI**
```bash
databricks workspace import \
  databricks/mining_realtime_dlt.py \
  /Workspace/Users/pravin.varma@databricks.com/mining-genie-demo/mining_realtime_dlt.py \
  --language PYTHON
```

## Step 2: Create DLT Pipeline via UI

1. Navigate to: **Workflows** → **Delta Live Tables** → **Create Pipeline**

2. **Pipeline Settings:**
   - **Pipeline name:** `mining_operations_realtime`
   - **Product edition:** Advanced
   - **Pipeline mode:** Continuous (not Triggered)

3. **Source Code:**
   - **Notebook/File:** Browse to uploaded `mining_realtime_dlt.py`

4. **Destination:**
   - **Catalog:** `ignition_genie`
   - **Target schema:** `mining_demo`
   - **Storage location:** Default (Unity Catalog managed)

5. **Compute:**
   - **Cluster mode:** Enhanced Autoscaling
   - **Cluster policy:** Unrestricted (or your org policy)
   - **Photon acceleration:** ✅ Enabled
   - **Min workers:** 1
   - **Max workers:** 3
   - **Node type:** `i3.xlarge` (or similar streaming-optimized instance)

6. **Advanced Configuration:**
   - **Runtime version:** 16.4 LTS or higher (required for Real-Time Mode)
   - **Add configuration:**
     - `spark.databricks.streaming.mode` = `realtime`
     - `spark.sql.shuffle.partitions` = `200`

7. **Development Mode:** ✅ Enable (for testing, disable for production)

8. Click **Create**

## Step 3: Validate and Start

1. Click **Validate** button
   - Should show: 9 tables detected
   - Dependencies: Bronze → Silver → Gold correctly ordered
   - Quality expectations: Defined

2. Click **Start**
   - Watch DAG visualization update
   - Monitor data flow: Bronze → Silver → Gold

## Step 4: Monitor Pipeline

**Expected Results (after 2-3 minutes):**
- ✅ Bronze table: ~18,000+ events ingested
- ✅ Silver table: Normalized sensor readings
- ✅ Gold tables: Aggregates and anomalies
- ✅ Pipeline latency: <1 second avg

**Check via SQL:**
```sql
-- 1. Count bronze events
SELECT COUNT(*) FROM ignition_genie.mining_demo.tag_events_bronze;

-- 2. Latest silver data
SELECT equipment_id, sensor_name, sensor_value, event_timestamp
FROM ignition_genie.mining_demo.equipment_sensors_normalized
ORDER BY event_timestamp DESC
LIMIT 20;

-- 3. 1-minute aggregates
SELECT window_start, equipment_id, sensor_name, avg_value, reading_count
FROM ignition_genie.mining_demo.equipment_performance_1min
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '10 minutes'
ORDER BY window_start DESC;

-- 4. Current equipment status
SELECT equipment_id, equipment_type, sensor_name, sensor_value, last_updated
FROM ignition_genie.mining_demo.equipment_current_status
WHERE equipment_type = 'Haul Truck'
ORDER BY equipment_id, sensor_name;

-- 5. Check for anomalies
SELECT *
FROM ignition_genie.mining_demo.sensor_anomalies
WHERE detected_at > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
ORDER BY severity DESC, deviation_score DESC;
```

## Step 5: Verify Latency

```sql
-- Check processing latency from pipeline metrics
SELECT
  minute,
  total_records,
  avg_latency_sec,
  max_latency_sec,
  distinct_equipment,
  quality_pct
FROM ignition_genie.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
ORDER BY minute DESC;

-- Target: avg_latency_sec < 1.0
```

## Troubleshooting

**Pipeline won't start:**
- Check Runtime version ≥ 16.4
- Verify source table exists: `ignition_genie.mining_ops.tag_events_raw`
- Check cluster permissions

**No data flowing:**
- Verify Zerobus is sending: `curl http://localhost:8183/system/zerobus/diagnostics`
- Check source table has data: `SELECT COUNT(*) FROM ignition_genie.mining_ops.tag_events_raw`
- Review DLT event log for errors

**High latency (>2s):**
- Reduce shuffle partitions: `spark.sql.shuffle.partitions = 100`
- Check cluster size (may need more workers)
- Verify Photon is enabled
- Check for cold start (first run always slower)

**Quality expectations failing:**
- Review Data Quality tab in DLT UI
- Check quarantine table: `SELECT * FROM <table> WHERE _rescued_data IS NOT NULL`
- Adjust expectation thresholds if too strict

## Next Steps

After pipeline is running successfully:
1. Deploy Genie Space (File 07/08)
2. Create Ignition Perspective UI with chat interface
3. Configure sample questions for Genie
4. Test end-to-end demo flow

## Current Status

✅ Ignition Gateway: Running on port 8183
✅ Physics Simulation: 107 tags updating at 1 Hz
✅ Zerobus Ingestion: 17,354+ events sent to Databricks
✅ Bronze Table: `ignition_genie.mining_ops.tag_events_raw`
⏳ DLT Pipeline: Ready to deploy
⏳ Genie Space: Pending (next step)
⏳ Perspective UI: Pending
